"""
新闻聚合服务 - 协调多个新闻源采集和分析
"""

import asyncio
from typing import List, Optional
from datetime import datetime

from backend.models import NewsItem, NewsCategory
from backend.database import Database
from backend.logger import get_logger
from backend.services.ai_analyzer import AIAnalyzer
from backend.sources import (
    GeneralNewsSource,
    FinanceNewsSource,
    TechNewsSource,
    AIRoboticsNewsSource,
)

logger = get_logger("news_aggregator")


class NewsAggregator:
    """新闻聚合服务"""

    def __init__(self, db: Database, analyzer: AIAnalyzer):
        self.db = db
        self.analyzer = analyzer
        self.sources = [
            FinanceNewsSource(),
            TechNewsSource(),
            AIRoboticsNewsSource(),
            GeneralNewsSource(),
        ]

    async def aggregate_all(self) -> List[NewsItem]:
        """从所有源聚合新闻"""
        logger.info("开始聚合新闻...")

        all_news = []

        # 并行获取所有源
        tasks = [source.fetch() for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            source_name = self.sources[i].__class__.__name__
            if isinstance(result, list):
                all_news.extend(result)
                logger.info(f"{source_name}: 获取 {len(result)} 条")
            else:
                logger.error(f"{source_name}: 获取失败 - {result}")

        logger.info(f"总计获取: {len(all_news)} 条")

        # 去重
        unique_news = self._deduplicate(all_news)
        logger.info(f"去重后: {len(unique_news)} 条")

        # AI 分析
        logger.info("开始 AI 分析...")
        analyzed_news = await self.analyzer.analyze_news_batch(unique_news[:30])

        # 按重要性排序
        analyzed_news.sort(key=lambda x: x.importance, reverse=True)

        # 保存到数据库
        saved_count = await self.db.save_news_batch(analyzed_news)
        logger.info(f"新增保存: {saved_count} 条")

        logger.info("新闻聚合完成")
        return analyzed_news

    def _deduplicate(self, news_list: List[NewsItem]) -> List[NewsItem]:
        """基于标题去重"""
        seen_titles = set()
        unique = []

        for news in news_list:
            # 简单的标题去重
            normalized_title = news.title.strip().lower()
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique.append(news)

        return unique

    async def get_categorized_news(self, limit_per_category: int = 5) -> dict:
        """获取分类后的新闻"""
        categories = {
            "finance": {"name": "[FINANCE] 财经", "items": []},
            "tech": {"name": "[TECH] 科技", "items": []},
            "semiconductor": {"name": "[CHIP] 半导体", "items": []},
            "ai": {"name": "[AI] AI/机器人", "items": []},
            "consumer": {"name": "[SHOP] 消费", "items": []},
            "other": {"name": "[NEWS] 其他", "items": []},
        }

        # 获取最新新闻
        news_list = await self.db.get_latest_news(limit=50)

        # 按类别分组
        for news in news_list:
            category = news.category.value if isinstance(news.category, NewsCategory) else news.category
            if category in categories:
                if len(categories[category]["items"]) < limit_per_category:
                    categories[category]["items"].append(news)

        # 移除空类别
        return {k: v for k, v in categories.items() if v["items"]}

    async def get_top_news(self, limit: int = 10) -> List[NewsItem]:
        """获取重要新闻"""
        return await self.db.get_news(
            limit=limit,
            order_by="importance DESC, created_at DESC"
        )

    async def get_news_by_category(self, category: str, limit: int = 20) -> List[NewsItem]:
        """获取指定类别的新闻"""
        return await self.db.get_news(
            category=category,
            limit=limit,
            order_by="importance DESC, created_at DESC"
        )
