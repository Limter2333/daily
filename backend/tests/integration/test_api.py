"""
API 端点集成测试
"""

import pytest
from datetime import datetime
from httpx import AsyncClient, ASGITransport

from backend.models import NewsItem, Briefing, NewsCategory, BriefingType


class TestHealthAPI:
    """健康检查 API 测试"""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """健康检查应该返回正常状态"""
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestNewsAPI:
    """新闻 API 测试"""

    @pytest.mark.asyncio
    async def test_get_news_empty(self, async_client: AsyncClient):
        """空数据库应该返回空列表"""
        response = await async_client.get("/api/news")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_get_news_with_data(self, async_client_with_news: AsyncClient):
        """有数据时应该返回新闻列表"""
        response = await async_client_with_news.get("/api/news")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        assert len(data["items"]) > 0

    @pytest.mark.asyncio
    async def test_get_news_with_category_filter(self, async_client_with_news: AsyncClient):
        """按类别过滤应该只返回该类别"""
        response = await async_client_with_news.get("/api/news?category=finance")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["category"] == "finance"

    @pytest.mark.asyncio
    async def test_get_news_with_pagination(self, async_client_with_news: AsyncClient):
        """分页应该返回正确数量"""
        response = await async_client_with_news.get("/api/news?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    async def test_get_latest_news(self, async_client_with_news: AsyncClient):
        """获取最新新闻"""
        response = await async_client_with_news.get("/api/news/latest?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_news_by_id(self, async_client_with_news: AsyncClient):
        """根据ID获取新闻"""
        # 先获取一个新闻ID
        list_response = await async_client_with_news.get("/api/news?limit=1")
        news_list = list_response.json()["items"]

        if news_list:
            news_id = news_list[0]["id"]
            response = await async_client_with_news.get(f"/api/news/{news_id}")
            assert response.status_code == 200
            assert response.json()["id"] == news_id

    @pytest.mark.asyncio
    async def test_get_news_not_found(self, async_client: AsyncClient):
        """获取不存在的新闻应该返回404"""
        response = await async_client.get("/api/news/99999")
        assert response.status_code == 404
        assert response.json()["detail"] == "新闻不存在"

    @pytest.mark.asyncio
    async def test_get_categories_summary(self, async_client_with_news: AsyncClient):
        """获取类别统计"""
        response = await async_client_with_news.get("/api/news/categories/summary")
        assert response.status_code == 200
        data = response.json()
        assert "finance" in data
        assert "tech" in data
        assert "ai" in data


class TestBriefingAPI:
    """早晚报 API 测试"""

    @pytest.mark.asyncio
    async def test_get_briefings_empty(self, async_client: AsyncClient):
        """空数据库应该返回空列表"""
        response = await async_client.get("/api/briefings")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_get_briefings_with_data(self, async_client_with_briefings: AsyncClient):
        """有数据时应该返回早晚报列表"""
        response = await async_client_with_briefings.get("/api/briefings")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0

    @pytest.mark.asyncio
    async def test_get_briefings_with_type_filter(self, async_client_with_briefings: AsyncClient):
        """按类型过滤"""
        response = await async_client_with_briefings.get("/api/briefings?type=morning")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["type"] == "morning"

    @pytest.mark.asyncio
    async def test_get_briefing_by_id(self, async_client_with_briefings: AsyncClient):
        """根据ID获取早晚报"""
        list_response = await async_client_with_briefings.get("/api/briefings?limit=1")
        briefings = list_response.json()["items"]

        if briefings:
            briefing_id = briefings[0]["id"]
            response = await async_client_with_briefings.get(f"/api/briefings/{briefing_id}")
            assert response.status_code == 200
            assert response.json()["id"] == briefing_id

    @pytest.mark.asyncio
    async def test_get_briefing_not_found(self, async_client: AsyncClient):
        """获取不存在的早晚报应该返回404"""
        response = await async_client.get("/api/briefings/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_latest_briefing(self, async_client_with_briefings: AsyncClient):
        """获取最新早晚报"""
        response = await async_client_with_briefings.get("/api/briefings/latest")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_latest_briefing_not_found(self, async_client: AsyncClient):
        """没有早晚报时应该返回404"""
        response = await async_client.get("/api/briefings/latest")
        assert response.status_code == 404


class TestSettingsAPI:
    """设置 API 测试"""

    @pytest.mark.asyncio
    async def test_get_settings(self, async_client: AsyncClient):
        """获取设置"""
        response = await async_client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        assert "morning_time" in data
        assert "evening_time" in data

    @pytest.mark.asyncio
    async def test_update_settings(self, async_client: AsyncClient):
        """更新设置"""
        new_settings = {
            "morning_time": "08:00",
            "evening_time": "21:00",
            "email_enabled": False,
            "push_enabled": False,
            "ai_api_key": "test",
            "ai_model": "gpt-4"
        }
        response = await async_client.put("/api/settings", json=new_settings)
        assert response.status_code == 200
        data = response.json()
        assert data["morning_time"] == "08:00"
        assert data["evening_time"] == "21:00"


class TestStatsAPI:
    """统计 API 测试"""

    @pytest.mark.asyncio
    async def test_get_stats(self, async_client: AsyncClient):
        """获取系统统计"""
        response = await async_client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "news_count" in data
        assert "briefing_count" in data


class TestSchedulerAPI:
    """定时任务 API 测试"""

    @pytest.mark.asyncio
    async def test_get_scheduler_jobs(self, async_client: AsyncClient):
        """获取定时任务列表"""
        response = await async_client.get("/api/scheduler/jobs")
        assert response.status_code == 200


class TestGenerateBriefingAPI:
    """生成早晚报 API 测试"""

    @pytest.mark.asyncio
    async def test_generate_invalid_type(self, async_client: AsyncClient):
        """无效类型应该返回400"""
        response = await async_client.post("/api/briefings/generate/invalid")
        assert response.status_code == 400
        assert "类型必须是" in response.json()["detail"]


class TestTriggerAPI:
    """触发操作 API 测试"""

    @pytest.mark.asyncio
    async def test_trigger_invalid_send_type(self, async_client: AsyncClient):
        """无效发送类型应该返回400"""
        response = await async_client.post("/api/send/invalid")
        assert response.status_code == 400
