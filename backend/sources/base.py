"""
新闻源基类
"""

import httpx
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.models import NewsItem, NewsCategory
from backend.logger import get_logger


class BaseNewsSource(ABC):
    """新闻源基类"""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.timeout = 15.0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.logger = get_logger(self.__class__.__name__)

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers,
            follow_redirects=True
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def fetch(self) -> List[NewsItem]:
        """获取新闻列表"""
        try:
            async with self:
                return await self._fetch_news()
        except Exception as e:
            self.logger.error(f"获取新闻失败: {e}")
            return []

    @abstractmethod
    async def _fetch_news(self) -> List[NewsItem]:
        """子类实现：获取新闻"""
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """返回新闻源名称"""
        pass

    @abstractmethod
    def get_category(self) -> NewsCategory:
        """返回新闻类别"""
        pass

    async def _get(self, url: str, **kwargs) -> Optional[httpx.Response]:
        """发送 GET 请求"""
        try:
            response = await self.client.get(url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            self.logger.error(f"请求失败 {url}: {e}")
            return None

    async def _post(self, url: str, **kwargs) -> Optional[httpx.Response]:
        """发送 POST 请求"""
        try:
            response = await self.client.post(url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            self.logger.error(f"请求失败 {url}: {e}")
            return None

    def _create_news(
        self,
        title: str,
        summary: Optional[str] = None,
        content: Optional[str] = None,
        url: Optional[str] = None,
        published_at: Optional[datetime] = None,
        importance: int = 5,
        tags: Optional[str] = None
    ) -> NewsItem:
        """创建新闻条目"""
        return NewsItem(
            title=title.strip(),
            summary=summary,
            content=content,
            source=self.get_source_name(),
            source_url=url,
            url=url,
            category=self.get_category(),
            importance=importance,
            published_at=published_at or datetime.now(),
            created_at=datetime.now(),
            is_sent=False,
            tags=tags
        )
