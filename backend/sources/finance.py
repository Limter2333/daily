"""
财经新闻源 - 东方财富、新浪财经、雪球、华尔街见闻
"""

from typing import List
from datetime import datetime

from backend.sources.base import BaseNewsSource
from backend.models import NewsItem, NewsCategory


class FinanceNewsSource(BaseNewsSource):
    """财经新闻源"""

    def get_source_name(self) -> str:
        return "财经"

    def get_category(self) -> NewsCategory:
        return NewsCategory.FINANCE

    async def _fetch_news(self) -> List[NewsItem]:
        """从多个财经源获取新闻"""
        all_news = []

        import asyncio
        tasks = [
            self._fetch_eastmoney(),
            self._fetch_sina_finance(),
            self._fetch_wallstreetcn(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_news.extend(result)

        return all_news[:10]

    async def _fetch_eastmoney(self) -> List[NewsItem]:
        """获取东方财富快讯"""
        news_list = []
        try:
            url = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"
            params = {
                "columns": "74,467",
                "pageSize": 10,
                "pageIndex": 0,
                "client": "web",
                "biz": "web_home_channel"
            }
            response = await self._get(url, params=params)
            if not response:
                return []

            data = response.json()
            for item in data.get("data", {}).get("list", []):
                title = item.get("title", "")
                summary = item.get("digest", "")
                art_url = item.get("url", "")

                if title:
                    news = self._create_news(
                        title=title,
                        summary=summary[:100] if summary else None,
                        url=art_url,
                        importance=7,
                        tags="东方财富,财经"
                    )
                    news.source = "东方财富"
                    news_list.append(news)

        except Exception as e:
            self.logger.error(f"东方财富获取失败: {e}")

        return news_list

    async def _fetch_sina_finance(self) -> List[NewsItem]:
        """获取新浪财经要闻"""
        news_list = []
        try:
            url = "https://feed.mix.sina.com.cn/api/roll/get"
            params = {
                "pageid": "153",
                "lid": "2516",
                "k": "",
                "num": 10,
                "page": 0,
                "r": "0.1"
            }
            response = await self._get(url, params=params)
            if not response:
                return []

            data = response.json()
            for item in data.get("result", {}).get("data", []):
                title = item.get("title", "")
                summary = item.get("summary", "")
                art_url = item.get("url", "")

                if title:
                    news = self._create_news(
                        title=title,
                        summary=summary[:100] if summary else None,
                        url=art_url,
                        importance=6,
                        tags="新浪财经,财经"
                    )
                    news.source = "新浪财经"
                    news_list.append(news)

        except Exception as e:
            self.logger.error(f"新浪财经获取失败: {e}")

        return news_list

    async def _fetch_wallstreetcn(self) -> List[NewsItem]:
        """获取华尔街见闻快讯"""
        news_list = []
        try:
            url = "https://api-one.wallstcn.com/apiv1/content/lives"
            params = {
                "channel": "global-channel",
                "limit": 10
            }
            response = await self._get(url, params=params)
            if not response:
                return []

            data = response.json()
            for item in data.get("data", {}).get("items", []):
                title = item.get("title", "")
                content = item.get("content_text", "")
                art_url = item.get("uri", "")

                if title:
                    news = self._create_news(
                        title=title,
                        summary=content[:100] if content else None,
                        url=f"https://wallstcn.com{art_url}" if art_url else None,
                        importance=7,
                        tags="华尔街见闻,财经"
                    )
                    news.source = "华尔街见闻"
                    news_list.append(news)

        except Exception as e:
            self.logger.error(f"华尔街见闻获取失败: {e}")

        return news_list
