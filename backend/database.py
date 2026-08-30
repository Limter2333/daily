"""
数据库操作模块
"""

import aiosqlite
import json
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path

from backend.models import NewsItem, Briefing, Settings, NewsCategory, BriefingType
from backend.config import settings


class Database:
    """SQLite 数据库操作类"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.database_path
        # 确保数据目录存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init_db(self):
        """初始化数据库表"""
        async with aiosqlite.connect(self.db_path) as db:
            # 创建新闻表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    summary TEXT,
                    content TEXT,
                    source TEXT NOT NULL,
                    source_url TEXT,
                    url TEXT,
                    category TEXT DEFAULT 'other',
                    importance INTEGER DEFAULT 5,
                    published_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_sent BOOLEAN DEFAULT FALSE,
                    tags TEXT
                )
            """)

            # 创建早报/晚报表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS briefing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    news_ids TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_sent BOOLEAN DEFAULT FALSE
                )
            """)

            # 创建设置表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # 创建索引
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_category ON news(category)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_created ON news(created_at)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_news_importance ON news(importance)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_briefing_type ON briefing(type)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_briefing_created ON briefing(created_at)
            """)

            await db.commit()

    # ==================== 新闻操作 ====================

    async def save_news(self, news: NewsItem) -> int:
        """保存新闻，返回ID"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO news (title, summary, content, source, source_url, url,
                                  category, importance, published_at, created_at, is_sent, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                news.title,
                news.summary,
                news.content,
                news.source,
                news.source_url,
                news.url,
                news.category.value if isinstance(news.category, NewsCategory) else news.category,
                news.importance,
                news.published_at.isoformat() if news.published_at else None,
                news.created_at.isoformat(),
                news.is_sent,
                news.tags
            ))
            await db.commit()
            return cursor.lastrowid

    async def save_news_batch(self, news_list: List[NewsItem]) -> int:
        """批量保存新闻"""
        async with aiosqlite.connect(self.db_path) as db:
            count = 0
            for news in news_list:
                # 检查是否已存在（基于标题）
                cursor = await db.execute(
                    "SELECT id FROM news WHERE title = ?", (news.title,)
                )
                if await cursor.fetchone():
                    continue

                await db.execute("""
                    INSERT INTO news (title, summary, content, source, source_url, url,
                                      category, importance, published_at, created_at, is_sent, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    news.title,
                    news.summary,
                    news.content,
                    news.source,
                    news.source_url,
                    news.url,
                    news.category.value if isinstance(news.category, NewsCategory) else news.category,
                    news.importance,
                    news.published_at.isoformat() if news.published_at else None,
                    news.created_at.isoformat(),
                    news.is_sent,
                    news.tags
                ))
                count += 1

            await db.commit()
            return count

    async def get_news(
        self,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "importance DESC, created_at DESC"
    ) -> List[NewsItem]:
        """获取新闻列表"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            query = "SELECT * FROM news WHERE 1=1"
            params = []

            if category and category != "all":
                query += " AND category = ?"
                params.append(category)

            if start_date:
                query += " AND created_at >= ?"
                params.append(start_date.isoformat())

            if end_date:
                query += " AND created_at <= ?"
                params.append(end_date.isoformat())

            query += f" ORDER BY {order_by} LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

            return [self._row_to_news(row) for row in rows]

    async def get_news_by_id(self, news_id: int) -> Optional[NewsItem]:
        """根据ID获取新闻"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM news WHERE id = ?", (news_id,))
            row = await cursor.fetchone()
            return self._row_to_news(row) if row else None

    async def get_news_count(self, category: Optional[str] = None) -> int:
        """获取新闻总数"""
        async with aiosqlite.connect(self.db_path) as db:
            query = "SELECT COUNT(*) FROM news"
            params = []

            if category and category != "all":
                query += " WHERE category = ?"
                params.append(category)

            cursor = await db.execute(query, params)
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_latest_news(self, limit: int = 20) -> List[NewsItem]:
        """获取最新新闻（按重要性排序）"""
        yesterday = datetime.now() - timedelta(days=1)
        return await self.get_news(
            start_date=yesterday,
            limit=limit,
            order_by="importance DESC, created_at DESC"
        )

    async def mark_news_sent(self, news_ids: List[int]):
        """标记新闻为已发送"""
        if not news_ids:
            return

        async with aiosqlite.connect(self.db_path) as db:
            placeholders = ",".join(["?" for _ in news_ids])
            await db.execute(
                f"UPDATE news SET is_sent = TRUE WHERE id IN ({placeholders})",
                news_ids
            )
            await db.commit()

    def _row_to_news(self, row) -> NewsItem:
        """将数据库行转换为 NewsItem"""
        return NewsItem(
            id=row["id"],
            title=row["title"],
            summary=row["summary"],
            content=row["content"],
            source=row["source"],
            source_url=row["source_url"],
            url=row["url"],
            category=NewsCategory(row["category"]) if row["category"] else NewsCategory.OTHER,
            importance=row["importance"],
            published_at=datetime.fromisoformat(row["published_at"]) if row["published_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            is_sent=bool(row["is_sent"]),
            tags=row["tags"]
        )

    # ==================== 早报/晚报操作 ====================

    async def save_briefing(self, briefing: Briefing) -> int:
        """保存早报/晚报"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO briefing (type, title, content, news_ids, created_at, is_sent)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                briefing.type.value if isinstance(briefing.type, BriefingType) else briefing.type,
                briefing.title,
                briefing.content,
                briefing.news_ids,
                briefing.created_at.isoformat(),
                briefing.is_sent
            ))
            await db.commit()
            return cursor.lastrowid

    async def get_briefings(
        self,
        briefing_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Briefing]:
        """获取早报/晚报列表"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            query = "SELECT * FROM briefing WHERE 1=1"
            params = []

            if briefing_type:
                query += " AND type = ?"
                params.append(briefing_type)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()

            return [self._row_to_briefing(row) for row in rows]

    async def get_briefing_by_id(self, briefing_id: int) -> Optional[Briefing]:
        """根据ID获取早报/晚报"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM briefing WHERE id = ?", (briefing_id,))
            row = await cursor.fetchone()
            return self._row_to_briefing(row) if row else None

    async def get_latest_briefing(self, briefing_type: Optional[str] = None) -> Optional[Briefing]:
        """获取最新的早报/晚报"""
        briefings = await self.get_briefings(briefing_type=briefing_type, limit=1)
        return briefings[0] if briefings else None

    def _row_to_briefing(self, row) -> Briefing:
        """将数据库行转换为 Briefing"""
        return Briefing(
            id=row["id"],
            type=BriefingType(row["type"]) if row["type"] else BriefingType.MORNING,
            title=row["title"],
            content=row["content"],
            news_ids=row["news_ids"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            is_sent=bool(row["is_sent"])
        )

    # ==================== 设置操作 ====================

    async def get_settings(self) -> Settings:
        """获取系统设置"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM settings")
            rows = await cursor.fetchall()

            settings_dict = {row["key"]: row["value"] for row in rows}

            # 转换布尔值
            def to_bool(val: str) -> bool:
                return val.lower() in ("true", "1", "yes")

            return Settings(
                weather_city=settings_dict.get("weather_city", "Beijing"),
                morning_time=settings_dict.get("morning_time", "07:30"),
                evening_time=settings_dict.get("evening_time", "20:00"),
                email_enabled=to_bool(settings_dict.get("email_enabled", "false")),
                smtp_server=settings_dict.get("smtp_server", "smtp.gmail.com"),
                smtp_port=int(settings_dict.get("smtp_port", "587")),
                smtp_username=settings_dict.get("smtp_username", ""),
                smtp_password=settings_dict.get("smtp_password", ""),
                email_recipient=settings_dict.get("email_recipient", ""),
                push_enabled=to_bool(settings_dict.get("push_enabled", "false")),
                push_platform=settings_dict.get("push_platform", "wechat"),
                push_webhook_url=settings_dict.get("push_webhook_url", "")
            )

    async def save_settings(self, settings: Settings):
        """保存系统设置（AI 配置不保存到数据库，从 .env 文件读取）"""
        async with aiosqlite.connect(self.db_path) as db:
            settings_dict = {
                "weather_city": settings.weather_city,
                "morning_time": settings.morning_time,
                "evening_time": settings.evening_time,
                "email_enabled": str(settings.email_enabled).lower(),
                "smtp_server": settings.smtp_server,
                "smtp_port": str(settings.smtp_port),
                "smtp_username": settings.smtp_username,
                "smtp_password": settings.smtp_password,
                "email_recipient": settings.email_recipient,
                "push_enabled": str(settings.push_enabled).lower(),
                "push_platform": settings.push_platform,
                "push_webhook_url": settings.push_webhook_url,
            }

            for key, value in settings_dict.items():
                await db.execute("""
                    INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
                """, (key, value))

            await db.commit()

    async def get_setting(self, key: str, default: str = "") -> str:
        """获取单个设置"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = await cursor.fetchone()
            return row[0] if row else default

    async def set_setting(self, key: str, value: str):
        """设置单个配置"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
            """, (key, value))
            await db.commit()


# 全局数据库实例
db = Database()
