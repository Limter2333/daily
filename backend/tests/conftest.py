"""
测试配置 - 提供测试 fixtures 和辅助工具
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from backend.main import app
from backend.database import Database
from backend.models import NewsItem, Briefing, NewsCategory, BriefingType, Settings


# ==================== 事件循环配置 ====================

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==================== 数据库 Fixtures ====================

@pytest.fixture
async def test_db(tmp_path) -> AsyncGenerator[Database, None]:
    """创建临时测试数据库"""
    db_path = str(tmp_path / "test.db")
    db = Database(db_path=db_path)
    await db.init_db()
    yield db
    # 清理（tmp_path 会自动清理）


@pytest.fixture
async def db_with_news(test_db: Database) -> Database:
    """预填充新闻数据的数据库"""
    news_items = [
        NewsItem(
            title="财经新闻1",
            summary="这是财经新闻摘要",
            source="eastmoney",
            category=NewsCategory.FINANCE,
            importance=8,
            created_at=datetime.now()
        ),
        NewsItem(
            title="科技新闻1",
            summary="这是科技新闻摘要",
            source="36kr",
            category=NewsCategory.TECH,
            importance=7,
            created_at=datetime.now()
        ),
        NewsItem(
            title="AI新闻1",
            summary="这是AI新闻摘要",
            source="jiqizhixin",
            category=NewsCategory.AI,
            importance=9,
            created_at=datetime.now()
        ),
    ]

    for news in news_items:
        await test_db.save_news(news)

    return test_db


@pytest.fixture
async def db_with_briefings(test_db: Database) -> Database:
    """预填充早晚报数据的数据库"""
    briefing = Briefing(
        type=BriefingType.MORNING,
        title="早报 2025-01-01",
        content="这是早报内容",
        news_ids="[1, 2, 3]",
        created_at=datetime.now()
    )
    await test_db.save_briefing(briefing)
    return test_db


# ==================== 客户端 Fixtures ====================

@pytest.fixture
async def async_client(test_db: Database):
    """异步测试客户端 - 使用测试数据库"""
    import backend.main as main_module

    # 保存原始 db 实例
    original_db = main_module.db

    # 替换为测试数据库
    main_module.db = test_db

    # 同时替换依赖此 db 的服务
    original_aggregator_db = main_module.aggregator.db
    original_generator_db = main_module.generator.db
    main_module.aggregator.db = test_db
    main_module.generator.db = test_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # 恢复原始 db 实例
    main_module.db = original_db
    main_module.aggregator.db = original_aggregator_db
    main_module.generator.db = original_generator_db


@pytest.fixture
async def async_client_with_news(db_with_news: Database):
    """带新闻数据的异步测试客户端"""
    import backend.main as main_module

    original_db = main_module.db
    original_aggregator_db = main_module.aggregator.db
    original_generator_db = main_module.generator.db

    main_module.db = db_with_news
    main_module.aggregator.db = db_with_news
    main_module.generator.db = db_with_news

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    main_module.db = original_db
    main_module.aggregator.db = original_aggregator_db
    main_module.generator.db = original_generator_db


@pytest.fixture
async def async_client_with_briefings(db_with_briefings: Database):
    """带早晚报数据的异步测试客户端"""
    import backend.main as main_module

    original_db = main_module.db
    original_aggregator_db = main_module.aggregator.db
    original_generator_db = main_module.generator.db

    main_module.db = db_with_briefings
    main_module.aggregator.db = db_with_briefings
    main_module.generator.db = db_with_briefings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    main_module.db = original_db
    main_module.aggregator.db = original_aggregator_db
    main_module.generator.db = original_generator_db


# ==================== 测试数据 Fixtures ====================

@pytest.fixture
def sample_news() -> NewsItem:
    """示例新闻数据"""
    return NewsItem(
        title="测试新闻标题",
        summary="这是测试新闻的摘要",
        content="这是测试新闻的完整内容",
        source="test_source",
        source_url="https://example.com/news/1",
        url="https://example.com/news/1",
        category=NewsCategory.TECH,
        importance=7,
        published_at=datetime.now(),
        tags="test,demo"
    )


@pytest.fixture
def sample_news_list() -> list[NewsItem]:
    """示例新闻列表"""
    return [
        NewsItem(
            title=f"新闻标题 {i}",
            summary=f"摘要 {i}",
            source="test_source",
            category=NewsCategory.TECH,
            importance=5 + i,
            created_at=datetime.now()
        )
        for i in range(5)
    ]


@pytest.fixture
def sample_briefing() -> Briefing:
    """示例早晚报数据"""
    return Briefing(
        type=BriefingType.MORNING,
        title="测试早报",
        content="这是测试早报的内容",
        news_ids="[1, 2, 3]"
    )


@pytest.fixture
def sample_settings() -> Settings:
    """示例设置数据（AI 配置从 .env 文件读取，不在此设置）"""
    return Settings(
        morning_time="08:00",
        evening_time="20:00",
        email_enabled=False,
        push_enabled=False,
    )


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_ai_response(monkeypatch):
    """Mock AI 分析响应"""
    async def mock_analyze(self, news: NewsItem) -> NewsItem:
        news.importance = 7
        news.summary = news.summary or "AI生成的摘要"
        return news

    async def mock_analyze_batch(self, news_list: list) -> list:
        for news in news_list:
            news.importance = 7
            news.summary = news.summary or "AI生成的摘要"
        return news_list

    from backend.services.ai_analyzer import AIAnalyzer
    monkeypatch.setattr(AIAnalyzer, "analyze", mock_analyze)
    monkeypatch.setattr(AIAnalyzer, "analyze_news_batch", mock_analyze_batch)


# ==================== 辅助工具 ====================

@pytest.fixture
def assert_response():
    """响应断言辅助工具"""
    class ResponseAsserter:
        @staticmethod
        def assert_success(response, status_code=200):
            assert response.status_code == status_code, \
                f"Expected {status_code}, got {response.status_code}: {response.text}"
            return response.json()

        @staticmethod
        def assert_error(response, status_code, detail=None):
            assert response.status_code == status_code
            if detail:
                assert response.json()["detail"] == detail

        @staticmethod
        def assert_paginated(response, expected_keys=["total", "items"]):
            data = response.json()
            for key in expected_keys:
                assert key in data, f"Missing key: {key}"
            return data

    return ResponseAsserter()
