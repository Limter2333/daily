"""
服务层单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.models import NewsItem, NewsCategory, BriefingType
from backend.services.ai_analyzer import AIAnalyzer


class TestAIAnalyzer:
    """AI 分析服务测试"""

    def test_init_without_api_key(self):
        """没有 API Key 时应该使用规则引擎"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None
            mock_settings.ai_provider = "openai"

            analyzer = AIAnalyzer()
            assert analyzer.client is None

    def test_init_with_api_key(self):
        """有 API Key 时应该创建客户端"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = "test_key"
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None
            mock_settings.ai_provider = "openai"

            analyzer = AIAnalyzer(api_key="test_key")
            assert analyzer.client is not None
            assert analyzer.client_type == "openai"

    def test_init_with_anthropic_provider(self):
        """Anthropic 协议应该创建 httpx 客户端"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = "sk-test-key"
            mock_settings.ai_model = "claude-sonnet-4-20250514"
            mock_settings.ai_base_url = "https://api.xiaomimimo.com/anthropic"
            mock_settings.ai_provider = "anthropic"

            analyzer = AIAnalyzer(api_key="sk-test-key", provider="anthropic")
            assert analyzer.client is not None
            assert analyzer.client_type == "anthropic"

    def test_rule_based_analysis_finance(self):
        """规则引擎应该正确分类财经新闻"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news = NewsItem(
                title="央行宣布降息0.25个百分点",
                source="eastmoney"
            )

            result = analyzer._rule_based_analysis(news)
            assert result.category == NewsCategory.FINANCE

    def test_rule_based_analysis_tech(self):
        """规则引擎应该正确分类科技新闻"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news = NewsItem(
                title="苹果发布新一代 iPhone",
                source="36kr"
            )

            result = analyzer._rule_based_analysis(news)
            assert result.category == NewsCategory.TECH

    def test_rule_based_analysis_ai(self):
        """规则引擎应该正确分类 AI 新闻"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news = NewsItem(
                title="人工智能大模型技术取得重大突破",
                source="jiqizhixin"
            )

            result = analyzer._rule_based_analysis(news)
            assert result.category == NewsCategory.AI

    def test_rule_based_analysis_semiconductor(self):
        """规则引擎应该正确分类半导体新闻"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news = NewsItem(
                title="台积电宣布 3nm 制程量产",
                source="tech"
            )

            result = analyzer._rule_based_analysis(news)
            assert result.category == NewsCategory.SEMICONDUCTOR

    def test_rule_based_analysis_other(self):
        """无法分类时应该归为其他"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news = NewsItem(
                title="今日天气晴朗",
                source="weather"
            )

            result = analyzer._rule_based_analysis(news)
            assert result.category == NewsCategory.OTHER

    def test_rule_based_analysis_generates_summary(self):
        """没有摘要时应该自动生成"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news = NewsItem(title="测试标题", source="test")

            result = analyzer._rule_based_analysis(news)
            assert result.summary is not None
            assert len(result.summary) > 0

    def test_rule_based_analysis_preserves_existing_summary(self):
        """有摘要时应该保留原有摘要"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news = NewsItem(
                title="测试标题",
                source="test",
                summary="原有摘要"
            )

            result = analyzer._rule_based_analysis(news)
            assert result.summary == "原有摘要"

    def test_rule_based_analysis_importance_scoring(self):
        """重要性评分应该在合理范围内"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news = NewsItem(title="测试", source="test")

            result = analyzer._rule_based_analysis(news)
            assert 1 <= result.importance <= 10

    def test_rule_based_analysis_with_important_keywords(self):
        """包含重要关键词时应该提高重要性"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()

            # 普通新闻
            news1 = NewsItem(title="普通新闻", source="test")
            result1 = analyzer._rule_based_analysis(news1)

            # 包含重要关键词的新闻
            news2 = NewsItem(title="重大突破！某公司发布革命性产品", source="test")
            result2 = analyzer._rule_based_analysis(news2)

            assert result2.importance >= result1.importance

    def test_rule_based_analysis_generates_tags(self):
        """没有标签时应该自动生成"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news = NewsItem(title="测试", source="test")

            result = analyzer._rule_based_analysis(news)
            assert result.tags is not None
            assert "test" in result.tags

    @pytest.mark.asyncio
    async def test_analyze_without_client(self):
        """没有客户端时应该使用规则引擎"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news = NewsItem(title="央行降息", source="test")

            result = await analyzer.analyze_news(news)
            assert result.category == NewsCategory.FINANCE

    @pytest.mark.asyncio
    async def test_analyze_batch(self):
        """批量分析应该处理所有新闻"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news_list = [
                NewsItem(title="央行降息", source="test"),
                NewsItem(title="苹果发布新手机", source="test"),
                NewsItem(title="人工智能深度学习算法突破", source="test"),
            ]

            results = await analyzer.analyze_news_batch(news_list)
            assert len(results) == 3
            assert results[0].category == NewsCategory.FINANCE
            assert results[1].category == NewsCategory.TECH
            assert results[2].category == NewsCategory.AI

    @pytest.mark.asyncio
    async def test_analyze_news_with_ai_success(self):
        """AI 分析成功时应该更新新闻"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = "test_key"
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer(api_key="test_key")

            # Mock OpenAI 响应
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = '{"category": "finance", "summary": "测试摘要", "importance": 8, "tags": "财经,央行"}'
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]

            analyzer.client = AsyncMock()
            analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)

            news = NewsItem(title="央行降息", source="test")
            result = await analyzer.analyze_news(news)

            assert result.category == NewsCategory.FINANCE
            assert result.summary == "测试摘要"
            assert result.importance == 8
            assert result.tags == "财经,央行"

    @pytest.mark.asyncio
    async def test_analyze_news_with_ai_json_in_markdown(self):
        """AI 返回 markdown 格式 JSON 时应该正确解析"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = "test_key"
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer(api_key="test_key")

            # Mock OpenAI 响应，返回 markdown 格式
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = '```json\n{"category": "tech", "summary": "科技新闻", "importance": 7, "tags": "科技"}\n```'
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]

            analyzer.client = AsyncMock()
            analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)

            news = NewsItem(title="苹果发布新手机", source="test")
            result = await analyzer.analyze_news(news)

            assert result.category == NewsCategory.TECH
            assert result.summary == "科技新闻"

    @pytest.mark.asyncio
    async def test_analyze_news_with_ai_failure(self):
        """AI 分析失败时应该回退到规则引擎"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = "test_key"
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer(api_key="test_key")

            # Mock OpenAI 响应抛出异常
            analyzer.client = AsyncMock()
            analyzer.client.chat.completions.create = AsyncMock(side_effect=Exception("API错误"))

            news = NewsItem(title="央行降息", source="test")
            result = await analyzer.analyze_news(news)

            # 应该回退到规则引擎
            assert result.category == NewsCategory.FINANCE

    @pytest.mark.asyncio
    async def test_analyze_news_importance_clamping(self):
        """AI 返回的重要性评分应该被限制在 1-10"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = "test_key"
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer(api_key="test_key")

            # Mock 返回超出范围的重要性
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = '{"category": "other", "summary": "测试", "importance": 15, "tags": "test"}'
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]

            analyzer.client = AsyncMock()
            analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)

            news = NewsItem(title="测试", source="test")
            result = await analyzer.analyze_news(news)

            assert result.importance == 10  # 被限制为 10

    @pytest.mark.asyncio
    async def test_analyze_news_importance_lower_clamp(self):
        """AI 返回的低重要性评分应该被限制为 1"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = "test_key"
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer(api_key="test_key")

            # Mock 返回低于范围的重要性
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = '{"category": "other", "summary": "测试", "importance": -5, "tags": "test"}'
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]

            analyzer.client = AsyncMock()
            analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)

            news = NewsItem(title="测试", source="test")
            result = await analyzer.analyze_news(news)

            assert result.importance == 1  # 被限制为 1

    @pytest.mark.asyncio
    async def test_generate_briefing_summary_with_client(self):
        """有客户端时应该生成摘要"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = "test_key"
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer(api_key="test_key")

            # Mock OpenAI 响应
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = "今日重要新闻摘要"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]

            analyzer.client = AsyncMock()
            analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)

            news_list = [
                NewsItem(title="新闻1", source="test", category=NewsCategory.FINANCE),
                NewsItem(title="新闻2", source="test", category=NewsCategory.TECH),
            ]

            result = await analyzer.generate_briefing_summary(news_list, "morning")
            assert result == "今日重要新闻摘要"

    @pytest.mark.asyncio
    async def test_generate_briefing_summary_without_client(self):
        """没有客户端时应该返回空字符串"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()

            news_list = [NewsItem(title="新闻1", source="test")]
            result = await analyzer.generate_briefing_summary(news_list, "morning")
            assert result == ""

    @pytest.mark.asyncio
    async def test_generate_briefing_summary_empty_list(self):
        """空新闻列表时应该返回空字符串"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = "test_key"
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer(api_key="test_key")

            result = await analyzer.generate_briefing_summary([], "morning")
            assert result == ""

    @pytest.mark.asyncio
    async def test_generate_briefing_summary_failure(self):
        """生成摘要失败时应该返回空字符串"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = "test_key"
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer(api_key="test_key")

            # Mock 抛出异常
            analyzer.client = AsyncMock()
            analyzer.client.chat.completions.create = AsyncMock(side_effect=Exception("API错误"))

            news_list = [NewsItem(title="新闻1", source="test")]
            result = await analyzer.generate_briefing_summary(news_list, "morning")
            assert result == ""

    @pytest.mark.asyncio
    async def test_generate_briefing_summary_evening(self):
        """晚报摘要应该正确生成"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = "test_key"
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer(api_key="test_key")

            # Mock OpenAI 响应
            mock_response = MagicMock()
            mock_choice = MagicMock()
            mock_message = MagicMock()
            mock_message.content = "今日晚报摘要"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]

            analyzer.client = AsyncMock()
            analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)

            news_list = [NewsItem(title="新闻1", source="test", category=NewsCategory.FINANCE)]
            result = await analyzer.generate_briefing_summary(news_list, "evening")
            assert result == "今日晚报摘要"

    def test_rule_based_analysis_source_weights(self):
        """不同来源应该有不同的权重"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()

            # 高权重来源
            news1 = NewsItem(title="普通新闻", source="华尔街见闻")
            result1 = analyzer._rule_based_analysis(news1)

            # 低权重来源
            news2 = NewsItem(title="普通新闻", source="知乎热榜")
            result2 = analyzer._rule_based_analysis(news2)

            # 高权重来源的重要性应该更高
            assert result1.importance >= result2.importance

    def test_rule_based_analysis_consumer_category(self):
        """规则引擎应该正确分类消费新闻"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news = NewsItem(title="双十一购物节销售额创纪录", source="test")

            result = analyzer._rule_based_analysis(news)
            assert result.category == NewsCategory.CONSUMER

    def test_rule_based_analysis_generates_category_tag(self):
        """非 OTHER 类别时应该生成包含类别的标签"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news = NewsItem(title="央行降息", source="test")

            result = analyzer._rule_based_analysis(news)
            assert "finance" in result.tags

    def test_rule_based_analysis_preserves_existing_tags(self):
        """有标签时应该保留原有标签"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            news = NewsItem(title="测试", source="test", tags="原有标签")

            result = analyzer._rule_based_analysis(news)
            assert result.tags == "原有标签"

    def test_rule_based_analysis_long_title_summary(self):
        """长标题应该被截断生成摘要"""
        with patch('backend.services.ai_analyzer.settings') as mock_settings:
            mock_settings.ai_api_key = ""
            mock_settings.ai_model = "gpt-3.5-turbo"
            mock_settings.ai_base_url = None

            analyzer = AIAnalyzer()
            long_title = "这是一个非常长的标题" * 10
            news = NewsItem(title=long_title, source="test")

            result = analyzer._rule_based_analysis(news)
            assert len(result.summary) <= 53  # 50 + "..."
