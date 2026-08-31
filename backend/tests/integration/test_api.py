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


# ==================== 市场数据 API 测试 ====================

class TestMarketOverviewAPI:
    """市场概览 API 测试"""

    @pytest.mark.asyncio
    async def test_get_market_overview_success(self, async_client: AsyncClient):
        """正常获取市场概览"""
        from unittest.mock import patch, AsyncMock

        mock_data = {
            "indices": [
                {"code": "000001", "name": "上证指数", "current": 3000.0, "change": 10.0, "changePercent": 0.33}
            ],
            "commodities": [
                {"code": "AU9999", "name": "黄金", "current": 500.0}
            ],
            "updateTime": "2025-01-01T08:00:00"
        }

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_market_overview = AsyncMock(return_value=mock_data)
            response = await async_client.get("/api/market/overview")

        assert response.status_code == 200
        data = response.json()
        assert "indices" in data
        assert "commodities" in data
        assert "updateTime" in data

    @pytest.mark.asyncio
    async def test_get_market_overview_error(self, async_client: AsyncClient):
        """服务异常时应该返回500"""
        from unittest.mock import patch, AsyncMock

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_market_overview = AsyncMock(side_effect=Exception("服务错误"))
            response = await async_client.get("/api/market/overview")

        assert response.status_code == 500


class TestMarketIndicesAPI:
    """市场指数 API 测试"""

    @pytest.mark.asyncio
    async def test_get_cn_indices(self, async_client: AsyncClient):
        """获取中国指数"""
        from unittest.mock import patch, AsyncMock

        mock_indices = [
            {"code": "000001", "name": "上证指数", "current": 3000.0},
            {"code": "399001", "name": "深证成指", "current": 10000.0},
        ]

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_cn_indices = AsyncMock(return_value=mock_indices)
            response = await async_client.get("/api/market/indices?market=cn")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["code"] == "000001"

    @pytest.mark.asyncio
    async def test_get_us_indices(self, async_client: AsyncClient):
        """获取美国指数"""
        from unittest.mock import patch, AsyncMock

        mock_indices = [
            {"code": "标普500", "name": "标普500", "current": 5000.0},
        ]

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_us_indices = AsyncMock(return_value=mock_indices)
            response = await async_client.get("/api/market/indices?market=us")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_get_hk_indices(self, async_client: AsyncClient):
        """获取香港指数"""
        from unittest.mock import patch, AsyncMock

        mock_indices = [
            {"code": "HSI", "name": "恒生指数", "current": 18000.0},
        ]

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_hk_indices = AsyncMock(return_value=mock_indices)
            response = await async_client.get("/api/market/indices?market=hk")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_get_indices_default_market_is_cn(self, async_client: AsyncClient):
        """默认市场参数应该是 cn"""
        from unittest.mock import patch, AsyncMock

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_cn_indices = AsyncMock(return_value=[])
            response = await async_client.get("/api/market/indices")

        assert response.status_code == 200
        mock_service.get_cn_indices.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_indices_invalid_market(self, async_client: AsyncClient):
        """无效市场参数应该返回400"""
        response = await async_client.get("/api/market/indices?market=japan")
        assert response.status_code == 400
        assert "市场参数无效" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_indices_service_error(self, async_client: AsyncClient):
        """服务异常时应该返回500"""
        from unittest.mock import patch, AsyncMock

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_cn_indices = AsyncMock(side_effect=Exception("服务错误"))
            response = await async_client.get("/api/market/indices?market=cn")

        assert response.status_code == 500


class TestMarketSectorsAPI:
    """板块 API 测试"""

    @pytest.mark.asyncio
    async def test_get_cn_sectors(self, async_client: AsyncClient):
        """获取中国板块排行"""
        from unittest.mock import patch, AsyncMock

        mock_sectors = {
            "rise": [{"name": "半导体", "changePercent": 3.5}],
            "fall": [{"name": "房地产", "changePercent": -2.1}],
        }

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_cn_sectors = AsyncMock(return_value=mock_sectors)
            response = await async_client.get("/api/market/sectors?market=cn")

        assert response.status_code == 200
        data = response.json()
        assert "rise" in data
        assert "fall" in data
        assert len(data["rise"]) == 1

    @pytest.mark.asyncio
    async def test_get_sectors_default_market_is_cn(self, async_client: AsyncClient):
        """默认市场应该是 cn"""
        from unittest.mock import patch, AsyncMock

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_cn_sectors = AsyncMock(return_value={"rise": [], "fall": []})
            response = await async_client.get("/api/market/sectors")

        assert response.status_code == 200
        mock_service.get_cn_sectors.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_sectors_non_cn_returns_empty(self, async_client: AsyncClient):
        """非 cn 市场应该返回空数据"""
        response = await async_client.get("/api/market/sectors?market=us")
        assert response.status_code == 200
        data = response.json()
        assert data == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_get_sectors_service_error(self, async_client: AsyncClient):
        """服务异常时应该返回500"""
        from unittest.mock import patch, AsyncMock

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_cn_sectors = AsyncMock(side_effect=Exception("服务错误"))
            response = await async_client.get("/api/market/sectors?market=cn")

        assert response.status_code == 500


class TestMarketStocksAPI:
    """个股 API 测试"""

    @pytest.mark.asyncio
    async def test_get_cn_stocks(self, async_client: AsyncClient):
        """获取中国个股排行"""
        from unittest.mock import patch, AsyncMock

        mock_stocks = {
            "rise": [{"code": "000001", "name": "股票A", "changePercent": 5.0}],
            "fall": [{"code": "000002", "name": "股票B", "changePercent": -3.0}],
        }

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_cn_stocks = AsyncMock(return_value=mock_stocks)
            response = await async_client.get("/api/market/stocks?market=cn")

        assert response.status_code == 200
        data = response.json()
        assert "rise" in data
        assert "fall" in data

    @pytest.mark.asyncio
    async def test_get_stocks_default_market_is_cn(self, async_client: AsyncClient):
        """默认市场应该是 cn"""
        from unittest.mock import patch, AsyncMock

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_cn_stocks = AsyncMock(return_value={"rise": [], "fall": []})
            response = await async_client.get("/api/market/stocks")

        assert response.status_code == 200
        mock_service.get_cn_stocks.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stocks_non_cn_returns_empty(self, async_client: AsyncClient):
        """非 cn 市场应该返回空数据"""
        response = await async_client.get("/api/market/stocks?market=us")
        assert response.status_code == 200
        data = response.json()
        assert data == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_get_stocks_service_error(self, async_client: AsyncClient):
        """服务异常时应该返回500"""
        from unittest.mock import patch, AsyncMock

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_cn_stocks = AsyncMock(side_effect=Exception("服务错误"))
            response = await async_client.get("/api/market/stocks?market=cn")

        assert response.status_code == 500


class TestMarketDetailAPI:
    """市场详情 API 测试"""

    @pytest.mark.asyncio
    async def test_get_cn_detail(self, async_client: AsyncClient):
        """获取中国市场详情"""
        from unittest.mock import patch, AsyncMock

        mock_detail = {
            "indices": [{"code": "000001", "name": "上证指数"}],
            "sectors": {"rise": [{"name": "半导体"}], "fall": []},
            "stocks": {"rise": [], "fall": [{"code": "000002"}]},
            "updateTime": "2025-01-01T08:00:00",
        }

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_market_detail = AsyncMock(return_value=mock_detail)
            response = await async_client.get("/api/market/detail?market=cn")

        assert response.status_code == 200
        data = response.json()
        assert "indices" in data
        assert "sectors" in data
        assert "stocks" in data
        assert "updateTime" in data

    @pytest.mark.asyncio
    async def test_get_detail_default_market_is_cn(self, async_client: AsyncClient):
        """默认市场应该是 cn"""
        from unittest.mock import patch, AsyncMock

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_market_detail = AsyncMock(return_value={
                "indices": [], "sectors": {"rise": [], "fall": []},
                "stocks": {"rise": [], "fall": []}, "updateTime": "2025-01-01T08:00:00"
            })
            response = await async_client.get("/api/market/detail")

        assert response.status_code == 200
        mock_service.get_market_detail.assert_called_once_with("cn")

    @pytest.mark.asyncio
    async def test_get_us_detail(self, async_client: AsyncClient):
        """获取美国市场详情"""
        from unittest.mock import patch, AsyncMock

        mock_detail = {
            "indices": [{"code": "标普500"}],
            "sectors": {"rise": [], "fall": []},
            "stocks": {"rise": [], "fall": []},
            "updateTime": "2025-01-01T08:00:00",
        }

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_market_detail = AsyncMock(return_value=mock_detail)
            response = await async_client.get("/api/market/detail?market=us")

        assert response.status_code == 200
        mock_service.get_market_detail.assert_called_once_with("us")

    @pytest.mark.asyncio
    async def test_get_detail_service_error(self, async_client: AsyncClient):
        """服务异常时应该返回500"""
        from unittest.mock import patch, AsyncMock

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_market_detail = AsyncMock(side_effect=Exception("服务错误"))
            response = await async_client.get("/api/market/detail?market=cn")

        assert response.status_code == 500


class TestCommoditiesAPI:
    """贵金属 API 测试"""

    @pytest.mark.asyncio
    async def test_get_commodities(self, async_client: AsyncClient):
        """获取贵金属行情"""
        from unittest.mock import patch, AsyncMock

        mock_commodities = [
            {"code": "AU9999", "name": "黄金", "current": 500.0, "unit": "元/克"},
            {"code": "XAUUSD", "name": "国际黄金", "current": 2000.0, "unit": "美元/盎司"},
        ]

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_commodities = AsyncMock(return_value=mock_commodities)
            response = await async_client.get("/api/market/commodities")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["code"] == "AU9999"
        assert data[1]["code"] == "XAUUSD"

    @pytest.mark.asyncio
    async def test_get_commodities_empty(self, async_client: AsyncClient):
        """无数据时应该返回空列表"""
        from unittest.mock import patch, AsyncMock

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_commodities = AsyncMock(return_value=[])
            response = await async_client.get("/api/market/commodities")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_commodities_service_error(self, async_client: AsyncClient):
        """服务异常时应该返回500"""
        from unittest.mock import patch, AsyncMock

        with patch("backend.main.market_service") as mock_service:
            mock_service.get_commodities = AsyncMock(side_effect=Exception("服务错误"))
            response = await async_client.get("/api/market/commodities")

        assert response.status_code == 500
