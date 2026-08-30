"""
早报/晚报生成服务
"""

import json
from datetime import datetime, timedelta
from typing import List, Optional

from backend.models import NewsItem, Briefing, BriefingType, NewsCategory
from backend.database import Database
from backend.logger import get_logger
from backend.services.ai_analyzer import AIAnalyzer

logger = get_logger("briefing_generator")


class BriefingGenerator:
    """早报/晚报生成服务"""

    def __init__(self, db: Database, analyzer: AIAnalyzer):
        self.db = db
        self.analyzer = analyzer

    async def generate_morning_briefing(self) -> Briefing:
        """生成早报"""
        logger.info("生成早报...")

        # 获取昨日至今的重要新闻
        yesterday = datetime.now() - timedelta(days=1)
        news_list = await self.db.get_news(
            start_date=yesterday,
            limit=30,
            order_by="importance DESC, created_at DESC"
        )

        if not news_list:
            logger.warning("暂无新闻，跳过早报生成")
            return self._empty_briefing(BriefingType.MORNING)

        # 生成内容
        content = await self._format_briefing(news_list, "morning")

        # 生成整体摘要
        summary = await self.analyzer.generate_briefing_summary(news_list, "morning")
        if summary:
            content = f"[概览] {summary}\n\n{content}"

        # 创建早报对象
        briefing = Briefing(
            type=BriefingType.MORNING,
            title=f"每日早报 - {datetime.now().strftime('%Y年%m月%d日')}",
            content=content,
            news_ids=json.dumps([n.id for n in news_list if n.id]),
            created_at=datetime.now(),
            is_sent=False
        )

        # 保存到数据库
        briefing_id = await self.db.save_briefing(briefing)
        briefing.id = briefing_id

        logger.info(f"早报生成完成，包含 {len(news_list)} 条新闻")
        return briefing

    async def generate_evening_briefing(self) -> Briefing:
        """生成晚报"""
        logger.info("生成晚报...")

        # 获取今日新闻
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        news_list = await self.db.get_news(
            start_date=today,
            limit=30,
            order_by="importance DESC, created_at DESC"
        )

        if not news_list:
            logger.warning("暂无新闻，跳过晚报生成")
            return self._empty_briefing(BriefingType.EVENING)

        # 生成内容
        content = await self._format_briefing(news_list, "evening")

        # 生成整体摘要
        summary = await self.analyzer.generate_briefing_summary(news_list, "evening")
        if summary:
            content = f"[概览] {summary}\n\n{content}"

        # 创建晚报对象
        briefing = Briefing(
            type=BriefingType.EVENING,
            title=f"每日晚报 - {datetime.now().strftime('%Y年%m月%d日')}",
            content=content,
            news_ids=json.dumps([n.id for n in news_list if n.id]),
            created_at=datetime.now(),
            is_sent=False
        )

        # 保存到数据库
        briefing_id = await self.db.save_briefing(briefing)
        briefing.id = briefing_id

        logger.info(f"晚报生成完成，包含 {len(news_list)} 条新闻")
        return briefing

    async def _format_briefing(self, news_list: List[NewsItem], briefing_type: str) -> str:
        """格式化早报/晚报内容"""
        # 按类别分组
        categories = {
            NewsCategory.FINANCE: {"name": "💰 财经", "items": []},
            NewsCategory.TECH: {"name": "💻 科技", "items": []},
            NewsCategory.SEMICONDUCTOR: {"name": "🔬 半导体", "items": []},
            NewsCategory.AI: {"name": "[AI] AI/机器人", "items": []},
            NewsCategory.CONSUMER: {"name": "[SHOP] 消费", "items": []},
            NewsCategory.OTHER: {"name": "[NEWS] 其他", "items": []},
        }

        for news in news_list:
            category = news.category if isinstance(news.category, NewsCategory) else NewsCategory.OTHER
            if category in categories:
                categories[category]["items"].append(news)

        # 生成内容
        lines = []

        if briefing_type == "morning":
            lines.append("🌅 早上好！以下是今日早报：\n")
        else:
            lines.append("🌆 晚上好！以下是今日晚报：\n")

        for category, data in categories.items():
            if not data["items"]:
                continue

            lines.append(f"\n{data['name']}")
            lines.append("─" * 40)

            for i, item in enumerate(data["items"][:5], 1):
                # 标题
                lines.append(f"{i}. {item.title}")

                # 摘要
                if item.summary:
                    lines.append(f"   📝 {item.summary}")

                # 来源和重要性
                importance_stars = "⭐" * min(item.importance // 2, 5)
                lines.append(f"   [NEWS] {item.source} | 重要性: {importance_stars}")

                # 链接
                if item.url:
                    lines.append(f"   🔗 {item.url}")

                lines.append("")

        # 底部统计
        lines.append("\n" + "═" * 50)
        lines.append(f"[STATS] 共 {len(news_list)} 条新闻")

        # 类别统计
        category_counts = {}
        for news in news_list:
            cat = news.category.value if isinstance(news.category, NewsCategory) else news.category
            category_counts[cat] = category_counts.get(cat, 0) + 1

        stats = " | ".join([f"{cat}: {count}" for cat, count in category_counts.items()])
        lines.append(f"[CHART] 分类统计: {stats}")

        return "\n".join(lines)

    def _empty_briefing(self, briefing_type: BriefingType) -> Briefing:
        """创建空的早报/晚报"""
        type_name = "早报" if briefing_type == BriefingType.MORNING else "晚报"
        return Briefing(
            type=briefing_type,
            title=f"每日{type_name} - {datetime.now().strftime('%Y年%m月%d日')}",
            content=f"暂无新闻数据，请稍后再试。",
            news_ids="[]",
            created_at=datetime.now(),
            is_sent=False
        )

    async def get_latest_briefing(self, briefing_type: Optional[str] = None) -> Optional[Briefing]:
        """获取最新的早报/晚报"""
        return await self.db.get_latest_briefing(briefing_type)
