"""
数据库操作单元测试
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta

from backend.database import Database
from backend.models import NewsItem, Briefing, Settings, NewsCategory, BriefingType


class TestDatabaseInit:
    """数据库初始化测试"""

    @pytest.mark.asyncio
    async def test_init_creates_tables(self, test_db: Database):
        """初始化应该创建所有表"""
        import aiosqlite
        async with aiosqlite.connect(test_db.db_path) as db:
            # 检查表是否存在
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in await cursor.fetchall()}

            assert "news" in tables
            assert "briefing" in tables
            assert "settings" in tables

    @pytest.mark.asyncio
    async def test_init_creates_indexes(self, test_db: Database):
        """初始化应该创建索引"""
        import aiosqlite
        async with aiosqlite.connect(test_db.db_path) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            )
            indexes = {row[0] for row in await cursor.fetchall()}

            assert "idx_news_category" in indexes
            assert "idx_news_created" in indexes
            assert "idx_briefing_type" in indexes


class TestNewsOperations:
    """新闻操作测试"""

    @pytest.mark.asyncio
    async def test_save_news(self, test_db: Database, sample_news: NewsItem):
        """保存新闻应该返回ID"""
        news_id = await test_db.save_news(sample_news)
        assert news_id is not None
        assert news_id > 0

    @pytest.mark.asyncio
    async def test_save_and_get_news(self, test_db: Database, sample_news: NewsItem):
        """保存后应该能获取新闻"""
        news_id = await test_db.save_news(sample_news)
        retrieved = await test_db.get_news_by_id(news_id)

        assert retrieved is not None
        assert retrieved.title == sample_news.title
        assert retrieved.source == sample_news.source
        assert retrieved.category == sample_news.category

    @pytest.mark.asyncio
    async def test_get_nonexistent_news(self, test_db: Database):
        """获取不存在的新闻应该返回None"""
        news = await test_db.get_news_by_id(99999)
        assert news is None

    @pytest.mark.asyncio
    async def test_save_news_batch(self, test_db: Database, sample_news_list: list):
        """批量保存应该返回保存数量"""
        count = await test_db.save_news_batch(sample_news_list)
        assert count == len(sample_news_list)

    @pytest.mark.asyncio
    async def test_save_batch_deduplication(self, test_db: Database):
        """批量保存应该去重"""
        news1 = NewsItem(title="重复标题", source="test", category=NewsCategory.TECH)
        news2 = NewsItem(title="重复标题", source="test", category=NewsCategory.TECH)

        count = await test_db.save_news_batch([news1, news2])
        assert count == 1  # 只保存一条

    @pytest.mark.asyncio
    async def test_get_news_with_category_filter(self, db_with_news: Database):
        """按类别过滤应该只返回该类别新闻"""
        news_list = await db_with_news.get_news(category="finance")
        assert all(n.category == NewsCategory.FINANCE for n in news_list)

    @pytest.mark.asyncio
    async def test_get_news_with_pagination(self, db_with_news: Database):
        """分页应该返回正确数量"""
        # 第一页
        page1 = await db_with_news.get_news(limit=2, offset=0)
        assert len(page1) <= 2

        # 第二页
        page2 = await db_with_news.get_news(limit=2, offset=2)
        # 页应该不同（如果有足够数据）
        if len(page1) == 2 and len(page2) > 0:
            assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_get_news_count(self, db_with_news: Database):
        """计数应该返回正确数量"""
        total = await db_with_news.get_news_count()
        assert total == 3  # db_with_news 有3条新闻

        # 按类别计数
        finance_count = await db_with_news.get_news_count(category="finance")
        assert finance_count == 1

    @pytest.mark.asyncio
    async def test_get_latest_news(self, db_with_news: Database):
        """获取最新新闻应该按重要性排序"""
        news_list = await db_with_news.get_latest_news(limit=10)
        assert len(news_list) > 0
        # 检查是否按重要性降序
        for i in range(len(news_list) - 1):
            assert news_list[i].importance >= news_list[i + 1].importance

    @pytest.mark.asyncio
    async def test_mark_news_sent(self, db_with_news: Database):
        """标记已发送应该更新状态"""
        news_list = await db_with_news.get_news(limit=1)
        assert len(news_list) > 0

        news_id = news_list[0].id
        await db_with_news.mark_news_sent([news_id])

        updated = await db_with_news.get_news_by_id(news_id)
        assert updated.is_sent is True


class TestBriefingOperations:
    """早晚报操作测试"""

    @pytest.mark.asyncio
    async def test_save_briefing(self, test_db: Database, sample_briefing: Briefing):
        """保存早晚报应该返回ID"""
        briefing_id = await test_db.save_briefing(sample_briefing)
        assert briefing_id is not None
        assert briefing_id > 0

    @pytest.mark.asyncio
    async def test_save_and_get_briefing(self, test_db: Database, sample_briefing: Briefing):
        """保存后应该能获取早晚报"""
        briefing_id = await test_db.save_briefing(sample_briefing)
        retrieved = await test_db.get_briefing_by_id(briefing_id)

        assert retrieved is not None
        assert retrieved.title == sample_briefing.title
        assert retrieved.type == sample_briefing.type

    @pytest.mark.asyncio
    async def test_get_briefings_with_type_filter(self, db_with_briefings: Database):
        """按类型过滤应该只返回该类型早晚报"""
        briefings = await db_with_briefings.get_briefings(briefing_type="morning")
        assert all(b.type == BriefingType.MORNING for b in briefings)

    @pytest.mark.asyncio
    async def test_get_latest_briefing(self, db_with_briefings: Database):
        """获取最新早晚报"""
        briefing = await db_with_briefings.get_latest_briefing()
        assert briefing is not None
        assert briefing.type == BriefingType.MORNING

    @pytest.mark.asyncio
    async def test_get_latest_briefing_by_type(self, db_with_briefings: Database):
        """按类型获取最新早晚报"""
        briefing = await db_with_briefings.get_latest_briefing(briefing_type="morning")
        assert briefing is not None
        assert briefing.type == BriefingType.MORNING

    @pytest.mark.asyncio
    async def test_get_nonexistent_briefing(self, test_db: Database):
        """获取不存在的早晚报应该返回None"""
        briefing = await test_db.get_briefing_by_id(99999)
        assert briefing is None


class TestSettingsOperations:
    """设置操作测试"""

    @pytest.mark.asyncio
    async def test_save_and_get_settings(self, test_db: Database, sample_settings: Settings):
        """保存后应该能获取设置"""
        await test_db.save_settings(sample_settings)
        retrieved = await test_db.get_settings()

        assert retrieved.morning_time == sample_settings.morning_time
        assert retrieved.evening_time == sample_settings.evening_time

    @pytest.mark.asyncio
    async def test_get_setting_single(self, test_db: Database):
        """获取单个设置"""
        await test_db.set_setting("test_key", "test_value")
        value = await test_db.get_setting("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_get_setting_default(self, test_db: Database):
        """获取不存在的设置应该返回默认值"""
        value = await test_db.get_setting("nonexistent", "default")
        assert value == "default"

    @pytest.mark.asyncio
    async def test_update_settings(self, test_db: Database):
        """更新设置应该覆盖旧值"""
        settings1 = Settings(morning_time="07:00")
        settings2 = Settings(morning_time="08:00")

        await test_db.save_settings(settings1)
        await test_db.save_settings(settings2)

        retrieved = await test_db.get_settings()
        assert retrieved.morning_time == "08:00"
