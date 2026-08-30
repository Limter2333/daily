"""
AI/机器人新闻源 - 机器之心、量子位
"""

from typing import List
from datetime import datetime

from backend.sources.base import BaseNewsSource
from backend.models import NewsItem, NewsCategory


class AIRoboticsNewsSource(BaseNewsSource):
    """AI/机器人新闻源"""

    def get_source_name(self) -> str:
        return "AI/机器人"

    def get_category(self) -> NewsCategory:
        return NewsCategory.AI

    async def _fetch_news(self) -> List[NewsItem]:
        """从多个AI源获取新闻"""
        all_news = []

        import asyncio
        tasks = [
            self._fetch_jiqizhixin(),
            self._fetch_qbitai(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_news.extend(result)

        return all_news[:10]

    async def _fetch_jiqizhixin(self) -> List[NewsItem]:
        """获取机器之心快讯"""
        news_list = []
        try:
            url = "https://www.jiqizhixin.com/api/v1/articles"
            params = {
                "page": 1,
                "per_page": 10,
                "type": "news"
            }
            response = await self._get(url, params=params)
            if not response:
                return []

            data = response.json()
            for item in data.get("data", []):
                title = item.get("title", "")
                summary = item.get("summary", "")
                art_slug = item.get("slug", "")

                if title:
                    news = self._create_news(
                        title=title,
                        summary=summary[:100] if summary else None,
                        url=f"https://www.jiqizhixin.com/articles/{art_slug}" if art_slug else None,
                        importance=7,
                        tags="机器之心,AI"
                    )
                    news.source = "机器之心"
                    news_list.append(news)

        except Exception as e:
            self.logger.error(f"机器之心获取失败: {e}")

        return news_list

    async def _fetch_qbitai(self) -> List[NewsItem]:
        """获取量子位快讯"""
        news_list = []
        try:
            # 量子位使用 RSS 或网页抓取
            url = "https://www.qbitai.com/"
            response = await self._get(url)
            if not response:
                return []

            # 简单的 HTML 解析
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "lxml")

            # 查找文章列表
            articles = soup.find_all("article", limit=10)
            for article in articles:
                title_elem = article.find("h2") or article.find("h3")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link_elem = article.find("a")
                link = link_elem.get("href", "") if link_elem else ""

                if title:
                    news = self._create_news(
                        title=title,
                        url=link if link.startswith("http") else f"https://www.qbitai.com{link}",
                        importance=7,
                        tags="量子位,AI"
                    )
                    news.source = "量子位"
                    news_list.append(news)

        except Exception as e:
            self.logger.error(f"量子位获取失败: {e}")

        return news_list
