"""
AI 分析服务 - 使用 LLM 进行新闻分类、摘要生成、重要性评估
支持 OpenAI 和 Anthropic 兼容协议
"""

import json
from typing import Optional, List
from openai import AsyncOpenAI

from backend.models import NewsItem, NewsCategory
from backend.config import settings
from backend.logger import get_logger

logger = get_logger("ai_analyzer")


class AIAnalyzer:
    """AI 分析服务"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None, provider: Optional[str] = None):
        self.api_key = api_key or settings.ai_api_key
        self.model = model or settings.ai_model
        self.base_url = base_url or settings.ai_base_url
        self.provider = provider or settings.ai_provider

        if self.api_key:
            if self.provider == "anthropic":
                self._init_anthropic_client()
            else:
                self._init_openai_client()
        else:
            self.client = None
            logger.warning("未配置 AI API Key，将使用规则引擎进行分析")

    def _init_openai_client(self):
        """初始化 OpenAI 兼容客户端"""
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        self.client = AsyncOpenAI(**client_kwargs)
        self.client_type = "openai"

    def _init_anthropic_client(self):
        """初始化 Anthropic 兼容客户端"""
        import httpx
        self.client = httpx.AsyncClient(
            base_url=self.base_url or "https://api.xiaomimimo.com/anthropic",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            timeout=60.0
        )
        self.client_type = "anthropic"

    async def analyze_news(self, news: NewsItem) -> NewsItem:
        """分析单条新闻（分类、摘要、评分）"""
        if not self.client:
            return self._rule_based_analysis(news)

        try:
            prompt = f"""请分析以下新闻，并返回 JSON 格式的结果：

新闻标题：{news.title}
新闻来源：{news.source}
新闻内容：{news.content[:500] if news.content else '无'}

请返回以下格式的 JSON：
{{
    "category": "类别（finance/tech/semiconductor/ai/consumer/other）",
    "summary": "一句话摘要（不超过50字）",
    "importance": 重要性评分（1-10的整数），
    "tags": "标签1,标签2"
}}

只返回 JSON，不要其他内容。"""

            if self.client_type == "anthropic":
                result_text = await self._call_anthropic(prompt)
            else:
                result_text = await self._call_openai(prompt)

            # 解析 JSON
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            result = json.loads(result_text)

            # 更新新闻
            news.category = NewsCategory(result.get("category", "other"))
            news.summary = result.get("summary", news.summary)
            news.importance = min(10, max(1, int(result.get("importance", 5))))
            news.tags = result.get("tags", news.tags)

        except Exception as e:
            logger.error(f"AI 分析失败，使用规则引擎: {e}")
            news = self._rule_based_analysis(news)

        return news

    async def _call_openai(self, prompt: str) -> str:
        """调用 OpenAI 兼容 API"""
        logger.debug(f"调用 OpenAI API: model={self.model}, base_url={self.base_url}")
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的新闻分析师，擅长对新闻进行分类和评估。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            if not response.choices:
                logger.warning("OpenAI API 返回空 choices")
                return ""
            choice = response.choices[0]
            logger.debug(f"finish_reason: {choice.finish_reason}")
            # 优先使用 content，如果为空则尝试 reasoning_content
            content = choice.message.content
            if not content:
                # mimo 模型可能把内容放在 reasoning_content
                reasoning = getattr(choice.message, 'reasoning_content', None)
                if reasoning:
                    logger.info("content 为空，使用 reasoning_content")
                    content = reasoning
            if not content:
                logger.warning(f"OpenAI API 返回空内容, finish_reason={choice.finish_reason}")
                return ""
            logger.debug(f"OpenAI API 响应长度: {len(content)}")
            return content.strip()
        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {type(e).__name__}: {e}")
            raise

    async def _call_anthropic(self, prompt: str) -> str:
        """调用 Anthropic 兼容 API"""
        response = await self.client.post(
            "/v1/messages",
            json={
                "model": self.model,
                "max_tokens": 200,
                "system": "你是一个专业的新闻分析师，擅长对新闻进行分类和评估。",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"].strip()

    async def analyze_news_batch(self, news_list: List[NewsItem]) -> List[NewsItem]:
        """批量分析新闻"""
        analyzed = []
        for news in news_list:
            result = await self.analyze_news(news)
            analyzed.append(result)
        return analyzed

    def _rule_based_analysis(self, news: NewsItem) -> NewsItem:
        """基于规则的分析（无需 AI）"""
        title = news.title.lower()

        # 分类规则
        category_keywords = {
            NewsCategory.FINANCE: [
                "股票", "基金", "证券", "股市", "A股", "港股", "美股",
                "财经", "金融", "投资", "理财", "银行", "保险", "债券",
                "牛市", "熊市", "涨停", "跌停", "行情", "大盘", "指数",
                "央行", "利率", "通胀", "GDP", "经济", "贸易", "汇率"
            ],
            NewsCategory.TECH: [
                "科技", "技术", "互联网", "软件", "硬件", "编程", "开发",
                "苹果", "谷歌", "微软", "亚马逊", "Meta", "字节", "腾讯",
                "阿里", "百度", "京东", "小米", "华为", "三星", "特斯拉",
                "产品", "发布", "更新", "升级", "创新", "创业", "融资"
            ],
            NewsCategory.SEMICONDUCTOR: [
                "半导体", "芯片", "集成电路", "晶圆", "光刻", "封装",
                "台积电", "英特尔", "AMD", "英伟达", "高通", "联发科",
                "中芯", "华虹", "存储", "内存", "闪存", "CPU", "GPU",
                "制程", "工艺", "产能", "良率", "EDA", "IP核"
            ],
            NewsCategory.AI: [
                "人工智能", "AI", "机器学习", "深度学习", "大模型", "GPT",
                "ChatGPT", "大语言模型", "LLM", "神经网络", "算法",
                "机器人", "自动驾驶", "计算机视觉", "自然语言", "NLP",
                "生成式", "AIGC", "智能", "训练", "推理", "模型"
            ],
            NewsCategory.CONSUMER: [
                "消费", "购物", "电商", "零售", "品牌", "市场",
                "双十一", "618", "直播", "带货", "种草", "测评",
                "手机", "电脑", "数码", "家电", "服装", "美妆",
                "食品", "餐饮", "旅游", "出行", "外卖"
            ]
        }

        # 计算各类别匹配度
        scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in title)
            if score > 0:
                scores[category] = score

        # 选择匹配度最高的类别
        if scores:
            news.category = max(scores, key=scores.get)
        else:
            news.category = NewsCategory.OTHER

        # 生成摘要（如果没有）
        if not news.summary:
            news.summary = news.title[:50] + "..." if len(news.title) > 50 else news.title

        # 评估重要性（基于规则）
        importance = 5

        # 来源权重
        source_weights = {
            "华尔街见闻": 2,
            "东方财富": 2,
            "36氪": 1,
            "机器之心": 2,
            "量子位": 2,
            "知乎热榜": 0,
            "今日头条": 0,
            "V2EX": 0,
            "Hacker News": 1,
        }

        for source, weight in source_weights.items():
            if source in news.source:
                importance += weight
                break

        # 关键词权重
        important_keywords = ["重大", "突破", "首次", "创纪录", "暴跌", "暴涨", "紧急", "突发", "宣布", "发布"]
        for kw in important_keywords:
            if kw in title:
                importance += 1

        news.importance = min(10, max(1, importance))

        # 生成标签
        if not news.tags:
            tags = [news.source]
            if news.category != NewsCategory.OTHER:
                tags.append(news.category.value)
            news.tags = ",".join(tags)

        return news

    async def generate_briefing_summary(self, news_list: List[NewsItem], briefing_type: str) -> str:
        """生成早报/晚报的整体摘要"""
        if not self.client or not news_list:
            return ""

        try:
            news_text = "\n".join([
                f"- [{n.category.value}] {n.title}" for n in news_list[:20]
            ])

            type_name = "早报" if briefing_type == "morning" else "晚报"

            prompt = f"""请为以下{type_name}新闻生成一段简短的整体概述（不超过200字）：

{news_text}

要求：
1. 总结今日/昨日的重要趋势和热点
2. 突出最重要的几条新闻
3. 语言简洁专业

只返回概述文本，不要其他内容。"""

            if self.client_type == "anthropic":
                result_text = await self._call_anthropic_summary(prompt)
            else:
                result_text = await self._call_openai_summary(prompt)

            return result_text

        except Exception as e:
            logger.error("生成摘要失败", error=str(e))
            return ""

    async def _call_openai_summary(self, prompt: str) -> str:
        """调用 OpenAI 兼容 API 生成摘要"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的新闻编辑，擅长撰写新闻概述。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()

    async def _call_anthropic_summary(self, prompt: str) -> str:
        """调用 Anthropic 兼容 API 生成摘要"""
        response = await self.client.post(
            "/v1/messages",
            json={
                "model": self.model,
                "max_tokens": 300,
                "system": "你是一个专业的新闻编辑，擅长撰写新闻概述。",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"].strip()
