"""
科技新闻源 - 36氪、少数派、TechCrunch
"""

from typing import List
from datetime import datetime

from backend.sources.base import BaseNewsSource
from backend.models import NewsItem, NewsCategory


class TechNewsSource(BaseNewsSource):
    """科技新闻源"""

    def get_source_name(self) -> str:
        return "科技"

    def get_category(self) -> NewsCategory:
        return NewsCategory.TECH

    async def _fetch_news(self) -> List[NewsItem]:
        """从多个科技源获取新闻"""
        all_news = []

        import asyncio
        tasks = [
            self._fetch_36kr(),
            self._fetch_sspai(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_news.extend(result)

        return all_news[:10]

    async def _fetch_36kr(self) -> List[NewsItem]:
        """获取36氪快讯"""
        news_list = []
        try:
            url = "https://36kr.com/api/newsflash?per_page=10"
            response = await self._get(url)
            if not response:
                return []

            data = response.json()
            for item in data.get("data", {}).get("items", []):
                title = item.get("title", "")
                desc = item.get("description", "")[:100]
                news_id = item.get("id", "")

                if title:
                    news = self._create_news(
                        title=title,
                        summary=desc if desc else None,
                        url=f"https://36kr.com/newsflashes/{news_id}" if news_id else None,
                        importance=6,
                        tags="36氪,科技"
                    )
                    news.source = "36氪"
                    news_list.append(news)

        except Exception as e:
            self.logger.error(f"36氪获取失败: {e}")

        return news_list

    async def _fetch_sspai(self) -> List[NewsItem]:
        """获取少数派热榜"""
        news_list = []
        try:
            url = "https://sspai.com/api/v1/articles"
            params = {
                "offset": 0,
                "limit": 10,
                "type": "recommend_to_home",
                "sort": "recommend_to_home_at",
                "include_total": "false"
            }
            response = await self._get(url, params=params)
            if not response:
                return []

            data = response.json()
            for item in data.get("data", []):
                title = item.get("title", "")
                summary = item.get("summary", "")
                art_id = item.get("id", "")

                if title:
                    news = self._create_news(
                        title=title,
                        summary=summary[:100] if summary else None,
                        url=f"https://sspai.com/post/{art_id}" if art_id else None,
                        importance=5,
                        tags="少数派,科技"
                    )
                    news.source = "少数派"
                    news_list.append(news)

        except Exception as e:
            self.logger.error(f"少数派获取失败: {e}")

        return news_list
