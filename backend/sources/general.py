"""
综合新闻源 - 知乎、今日头条、V2EX、Hacker News
"""

from typing import List
from datetime import datetime

from backend.sources.base import BaseNewsSource
from backend.models import NewsItem, NewsCategory


class GeneralNewsSource(BaseNewsSource):
    """综合新闻源"""

    def get_source_name(self) -> str:
        return "综合"

    def get_category(self) -> NewsCategory:
        return NewsCategory.OTHER

    async def _fetch_news(self) -> List[NewsItem]:
        """从多个综合源获取新闻"""
        all_news = []

        # 并行获取各个源
        import asyncio
        tasks = [
            self._fetch_zhihu(),
            self._fetch_toutiao(),
            self._fetch_v2ex(),
            self._fetch_hacker_news(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_news.extend(result)

        return all_news[:10]  # 限制数量

    async def _fetch_zhihu(self) -> List[NewsItem]:
        """获取知乎热榜"""
        news_list = []
        try:
            url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=10"
            response = await self._get(url)
            if not response:
                return []

            data = response.json()
            for item in data.get("data", []):
                target = item.get("target", {})
                title = target.get("title", "")
                detail = item.get("detail_text", "")

                if title:
                    news = self._create_news(
                        title=title,
                        summary=f"知乎热榜: {detail}" if detail else None,
                        url=f"https://www.zhihu.com/question/{target.get('id', '')}",
                        importance=6,
                        tags="知乎,热榜"
                    )
                    news.source = "知乎热榜"
                    news_list.append(news)

        except Exception as e:
            self.logger.error(f"知乎热榜获取失败: {e}")

        return news_list

    async def _fetch_toutiao(self) -> List[NewsItem]:
        """获取今日头条热榜"""
        news_list = []
        try:
            url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
            response = await self._get(url)
            if not response:
                return []

            data = response.json()
            for item in data.get("data", [])[:10]:
                title = item.get("Title", "")
                hot_value = item.get("HotValue", "")

                if title:
                    news = self._create_news(
                        title=title,
                        summary=f"热度: {hot_value}" if hot_value else None,
                        url=item.get("Url", ""),
                        importance=5,
                        tags="今日头条,热榜"
                    )
                    news.source = "今日头条"
                    news_list.append(news)

        except Exception as e:
            self.logger.error(f"今日头条获取失败: {e}")

        return news_list

    async def _fetch_v2ex(self) -> List[NewsItem]:
        """获取 V2EX 热门话题"""
        news_list = []
        try:
            url = "https://www.v2ex.com/api/topics/hot.json"
            response = await self._get(url)
            if not response:
                return []

            data = response.json()
            for item in data[:10]:
                title = item.get("title", "")
                node = item.get("node", {}).get("title", "")

                if title:
                    news = self._create_news(
                        title=title,
                        url=item.get("url", ""),
                        importance=4,
                        tags=f"V2EX,{node}" if node else "V2EX"
                    )
                    news.source = "V2EX"
                    news_list.append(news)

        except Exception as e:
            self.logger.error(f"V2EX 获取失败: {e}")

        return news_list

    async def _fetch_hacker_news(self) -> List[NewsItem]:
        """获取 Hacker News 头条"""
        news_list = []
        try:
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = await self._get(url)
            if not response:
                return []

            story_ids = response.json()[:5]

            for sid in story_ids:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                story_resp = await self._get(story_url)
                if story_resp:
                    story = story_resp.json()
                    title = story.get("title", "")

                    if title:
                        news = self._create_news(
                            title=title,
                            url=story.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                            importance=5,
                            tags="Hacker News"
                        )
                        news.source = "Hacker News"
                        news_list.append(news)

        except Exception as e:
            self.logger.error(f"Hacker News 获取失败: {e}")

        return news_list
