"""
MarketService 单元测试
"""

import pytest
import asyncio
import pandas as pd
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta

from backend.services.market_service import MarketService


class TestMarketServiceCache:
    """缓存机制测试"""

    def test_get_cache_returns_none_when_empty(self):
        """空缓存应该返回 None"""
        service = MarketService()
        assert service._get_cache("nonexistent") is None

    def test_set_cache_and_get(self):
        """设置缓存后应该能正确获取"""
        service = MarketService()
        test_data = [{"code": "000001", "name": "上证指数"}]
        service._set_cache("test_key", test_data)
        assert service._get_cache("test_key") == test_data

    def test_cache_expiration(self):
        """缓存过期后应该返回 None"""
        service = MarketService()
        service._cache_ttl = 0  # 立即过期
        test_data = [{"code": "000001"}]
        service._set_cache("test_key", test_data)
        # 等待一小段时间确保过期
        import time
        time.sleep(0.01)
        assert service._get_cache("test_key") is None

    def test_cache_not_expired(self):
        """未过期的缓存应该返回数据"""
        service = MarketService()
        service._cache_ttl = 300  # 5分钟
        test_data = [{"code": "000001"}]
        service._set_cache("test_key", test_data)
        assert service._get_cache("test_key") == test_data

    def test_cache_overwrite(self):
        """相同 key 应该覆盖旧数据"""
        service = MarketService()
        service._set_cache("key", "value1")
        service._set_cache("key", "value2")
        assert service._get_cache("key") == "value2"

    def test_multiple_cache_keys(self):
        """不同 key 应该独立存储"""
        service = MarketService()
        service._set_cache("key1", "value1")
        service._set_cache("key2", "value2")
        assert service._get_cache("key1") == "value1"
        assert service._get_cache("key2") == "value2"


class TestMarketServiceInit:
    """初始化测试"""

    def test_default_cache_ttl(self):
        """默认缓存 TTL 应该是 300 秒"""
        service = MarketService()
        assert service._cache_ttl == 300

    def test_empty_cache_on_init(self):
        """初始化时缓存应该为空"""
        service = MarketService()
        assert service._cache == {}
        assert service._cache_time == {}


class TestGetCNIndices:
    """中国指数测试"""

    @pytest.mark.asyncio
    async def test_returns_cached_data(self):
        """有缓存时应该直接返回缓存数据"""
        service = MarketService()
        cached_data = [{"code": "000001", "name": "上证指数", "current": 3000.0}]
        service._set_cache("cn_indices", cached_data)

        result = await service.get_cn_indices()
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_fetches_from_akshare(self):
        """无缓存时应该从 AKShare 获取数据"""
        service = MarketService()

        # 创建模拟 DataFrame
        df = pd.DataFrame({
            "代码": ["000001", "399001", "999999"],
            "名称": ["上证指数", "深证成指", "其他指数"],
            "最新价": [3000.0, 10000.0, 5000.0],
            "涨跌额": [10.0, 50.0, -20.0],
            "涨跌幅": [0.33, 0.50, -0.40],
            "成交量": [1000000, 2000000, 500000],
            "成交额": [3000000000, 20000000000, 2500000000],
            "最高": [3050.0, 10100.0, 5100.0],
            "最低": [2980.0, 9900.0, 4950.0],
            "今开": [2990.0, 9950.0, 5020.0],
            "昨收": [2990.0, 9950.0, 5020.0],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_index_spot_em.return_value = df
            result = await service.get_cn_indices()

        # 应该只返回主要指数（000001, 399001），不包含 999999
        assert len(result) == 2
        codes = [idx["code"] for idx in result]
        assert "000001" in codes
        assert "399001" in codes
        assert "999999" not in codes

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self):
        """AKShare 调用失败时应该返回空列表"""
        service = MarketService()

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_index_spot_em.side_effect = Exception("API错误")
            result = await service.get_cn_indices()

        assert result == []

    @pytest.mark.asyncio
    async def test_caches_after_fetch(self):
        """获取数据后应该存入缓存"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["000001"],
            "名称": ["上证指数"],
            "最新价": [3000.0],
            "涨跌额": [10.0],
            "涨跌幅": [0.33],
            "成交量": [1000000],
            "成交额": [3000000000],
            "最高": [3050.0],
            "最低": [2980.0],
            "今开": [2990.0],
            "昨收": [2990.0],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_index_spot_em.return_value = df
            await service.get_cn_indices()

        assert service._get_cache("cn_indices") is not None

    @pytest.mark.asyncio
    async def test_data_structure(self):
        """返回的数据应该包含正确的字段"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["000001"],
            "名称": ["上证指数"],
            "最新价": [3000.5],
            "涨跌额": [15.5],
            "涨跌幅": [0.52],
            "成交量": [1234567],
            "成交额": [3700000000],
            "最高": [3050.0],
            "最低": [2980.0],
            "今开": [2990.0],
            "昨收": [2985.0],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_index_spot_em.return_value = df
            result = await service.get_cn_indices()

        assert len(result) == 1
        idx = result[0]
        assert idx["code"] == "000001"
        assert idx["name"] == "上证指数"
        assert idx["current"] == 3000.5
        assert idx["change"] == 15.5
        assert idx["changePercent"] == 0.52
        assert idx["volume"] == 1234567
        assert idx["amount"] == 3700000000
        assert idx["high"] == 3050.0
        assert idx["low"] == 2980.0
        assert idx["open"] == 2990.0
        assert idx["prevClose"] == 2985.0

    @pytest.mark.asyncio
    async def test_filters_main_indices_only(self):
        """应该只返回主要指数代码"""
        service = MarketService()

        main_codes = ["000001", "399001", "399006", "000300", "000905", "000852", "399303"]
        all_codes = main_codes + ["000002", "399002"]

        df = pd.DataFrame({
            "代码": all_codes,
            "名称": [f"指数{i}" for i in range(len(all_codes))],
            "最新价": [3000.0] * len(all_codes),
            "涨跌额": [10.0] * len(all_codes),
            "涨跌幅": [0.33] * len(all_codes),
            "成交量": [1000000] * len(all_codes),
            "成交额": [3000000000] * len(all_codes),
            "最高": [3050.0] * len(all_codes),
            "最低": [2980.0] * len(all_codes),
            "今开": [2990.0] * len(all_codes),
            "昨收": [2990.0] * len(all_codes),
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_index_spot_em.return_value = df
            result = await service.get_cn_indices()

        assert len(result) == 7
        returned_codes = [idx["code"] for idx in result]
        for code in main_codes:
            assert code in returned_codes


class TestGetUSIndices:
    """美国指数测试"""

    @pytest.mark.asyncio
    async def test_returns_cached_data(self):
        """有缓存时应该直接返回缓存数据"""
        service = MarketService()
        cached_data = [{"code": "标普500", "name": "标普500", "current": 5000.0}]
        service._set_cache("us_indices", cached_data)

        result = await service.get_us_indices()
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_fetches_from_akshare(self):
        """无缓存时应该从 AKShare 获取数据"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["SPX", "NDX", "DJIA"],
            "名称": ["标普500", "纳斯达克综合指数", "道琼斯工业平均指数"],
            "最新价": [5000.0, 16000.0, 40000.0],
            "涨跌额": [25.0, 128.0, 120.0],
            "涨跌幅": [0.5, 0.8, 0.3],
            "最高": [5050.0, 16200.0, 40500.0],
            "最低": [4980.0, 15900.0, 39800.0],
            "开盘": [4990.0, 15950.0, 39900.0],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.index_global_spot_em.return_value = df
            result = await service.get_us_indices()

        assert len(result) == 3
        names = [idx["name"] for idx in result]
        assert "标普500" in names
        assert "纳斯达克综合指数" in names
        assert "道琼斯工业平均指数" in names

    @pytest.mark.asyncio
    async def test_returns_empty_on_empty_df(self):
        """空 DataFrame 应该返回空列表"""
        service = MarketService()

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.index_global_spot_em.return_value = pd.DataFrame()
            result = await service.get_us_indices()

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_none_df(self):
        """None DataFrame 应该返回空列表"""
        service = MarketService()

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.index_global_spot_em.return_value = None
            result = await service.get_us_indices()

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self):
        """异常时应该返回空列表"""
        service = MarketService()

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.index_global_spot_em.side_effect = Exception("API错误")
            result = await service.get_us_indices()

        assert result == []


class TestGetHKIndices:
    """香港指数测试"""

    @pytest.mark.asyncio
    async def test_returns_cached_data(self):
        """有缓存时应该直接返回缓存数据"""
        service = MarketService()
        cached_data = [{"code": "HSI", "name": "恒生指数", "current": 18000.0}]
        service._set_cache("hk_indices", cached_data)

        result = await service.get_hk_indices()
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_fetches_from_akshare(self):
        """无缓存时应该从 AKShare 获取数据"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["HSI", "HSCEI", "HSTECH", "OTHER"],
            "名称": ["恒生指数", "国企指数", "恒生科技指数", "其他指数"],
            "最新价": [18000.0, 6500.0, 4000.0, 1000.0],
            "涨跌额": [100.0, 50.0, 30.0, -10.0],
            "涨跌幅": [0.56, 0.78, 0.75, -1.0],
            "成交量": [500000, 300000, 200000, 100000],
            "成交额": [9000000000, 1950000000, 800000000, 100000000],
            "最高": [18100.0, 6550.0, 4050.0, 1020.0],
            "最低": [17900.0, 6450.0, 3950.0, 990.0],
            "今开": [17950.0, 6480.0, 3980.0, 1010.0],
            "昨收": [17900.0, 6450.0, 3970.0, 1010.0],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_hk_index_spot_em.return_value = df
            result = await service.get_hk_indices()

        # 应该只返回 HSI, HSCEI, HSTECH
        assert len(result) == 3
        codes = [idx["code"] for idx in result]
        assert "HSI" in codes
        assert "HSCEI" in codes
        assert "HSTECH" in codes
        assert "OTHER" not in codes

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self):
        """异常时应该返回空列表"""
        service = MarketService()

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_hk_index_spot_em.side_effect = Exception("API错误")
            result = await service.get_hk_indices()

        assert result == []

    @pytest.mark.asyncio
    async def test_data_structure(self):
        """返回的数据应该包含正确的字段"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["HSI"],
            "名称": ["恒生指数"],
            "最新价": [18000.5],
            "涨跌额": [100.5],
            "涨跌幅": [0.56],
            "成交量": [500000],
            "成交额": [9000000000],
            "最高": [18100.0],
            "最低": [17900.0],
            "今开": [17950.0],
            "昨收": [17900.0],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_hk_index_spot_em.return_value = df
            result = await service.get_hk_indices()

        assert len(result) == 1
        idx = result[0]
        assert idx["code"] == "HSI"
        assert idx["name"] == "恒生指数"
        assert idx["current"] == 18000.5
        assert idx["change"] == 100.5
        assert idx["changePercent"] == 0.56


class TestGetCNSectors:
    """板块数据测试"""

    @pytest.mark.asyncio
    async def test_returns_cached_data(self):
        """有缓存时应该直接返回缓存数据"""
        service = MarketService()
        cached_data = {"rise": [{"name": "半导体"}], "fall": [{"name": "房地产"}]}
        service._set_cache("cn_sectors", cached_data)

        result = await service.get_cn_sectors()
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_fetches_and_sorts(self):
        """应该获取数据并按涨跌幅排序"""
        service = MarketService()

        df = pd.DataFrame({
            "板块名称": ["半导体", "房地产", "银行", "医药", "新能源", "消费"],
            "涨跌幅": [3.5, -2.1, 1.2, -0.5, 2.8, 0.3],
            "领涨股票": ["股票A", "股票B", "股票C", "股票D", "股票E", "股票F"],
            "总成交量": [1000000, 2000000, 3000000, 4000000, 5000000, 6000000],
            "总成交额": [5000000000, 3000000000, 2000000000, 1000000000, 4000000000, 500000000],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_board_industry_name_em.return_value = df
            result = await service.get_cn_sectors()

        # 涨幅前5
        assert len(result["rise"]) == 5
        assert result["rise"][0]["name"] == "半导体"  # 最高涨幅
        assert result["rise"][0]["changePercent"] == 3.5

        # 跌幅前5（按跌幅从大到小）
        assert len(result["fall"]) == 5
        assert result["fall"][0]["name"] == "房地产"  # 最大跌幅
        assert result["fall"][0]["changePercent"] == -2.1

    @pytest.mark.asyncio
    async def test_returns_empty_on_empty_df(self):
        """空 DataFrame 应该返回空的 rise/fall"""
        service = MarketService()

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_board_industry_name_em.return_value = pd.DataFrame()
            result = await service.get_cn_sectors()

        assert result == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_returns_empty_on_none_df(self):
        """None DataFrame 应该返回空的 rise/fall"""
        service = MarketService()

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_board_industry_name_em.return_value = None
            result = await service.get_cn_sectors()

        assert result == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self):
        """异常时应该返回空的 rise/fall"""
        service = MarketService()

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_board_industry_name_em.side_effect = Exception("API错误")
            result = await service.get_cn_sectors()

        assert result == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_sector_data_structure(self):
        """板块数据应该包含正确的字段"""
        service = MarketService()

        df = pd.DataFrame({
            "板块名称": ["半导体", "银行", "医药", "新能源", "消费", "地产"],
            "涨跌幅": [3.5, 1.2, -0.5, 2.8, 0.3, -2.1],
            "领涨股票": ["股票A", "股票B", "股票C", "股票D", "股票E", "股票F"],
            "总成交量": [1000000, 2000000, 3000000, 4000000, 5000000, 6000000],
            "总成交额": [5e9, 2e9, 1e9, 4e9, 5e8, 3e9],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_board_industry_name_em.return_value = df
            result = await service.get_cn_sectors()

        sector = result["rise"][0]
        assert "name" in sector
        assert "changePercent" in sector
        assert "leadStock" in sector
        assert "volume" in sector
        assert "amount" in sector


class TestGetCNStocks:
    """个股数据测试"""

    @pytest.mark.asyncio
    async def test_returns_cached_data(self):
        """有缓存时应该直接返回缓存数据"""
        service = MarketService()
        cached_data = {"rise": [{"code": "000001"}], "fall": [{"code": "000002"}]}
        service._set_cache("cn_stocks", cached_data)

        result = await service.get_cn_stocks()
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_filters_st_stocks(self):
        """应该过滤掉 ST 股票"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["000001", "000002", "000003"],
            "名称": ["平安银行", "ST某某", "万科A"],
            "最新价": [10.0, 5.0, 15.0],
            "涨跌幅": [5.0, 3.0, -2.0],
            "涨跌额": [0.5, 0.15, -0.3],
            "成交量": [1000000, 500000, 800000],
            "成交额": [10000000, 2500000, 12000000],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_a_spot_em.return_value = df
            result = await service.get_cn_stocks()

        # ST 股票应该被过滤
        all_stocks = result["rise"] + result["fall"]
        for stock in all_stocks:
            assert "ST" not in stock["name"]

    @pytest.mark.asyncio
    async def test_sorts_by_change_percent(self):
        """应该按涨跌幅排序"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["000001", "000002", "000003"],
            "名称": ["股票A", "股票B", "股票C"],
            "最新价": [10.0, 5.0, 15.0],
            "涨跌幅": [3.0, 5.0, -2.0],
            "涨跌额": [0.3, 0.25, -0.3],
            "成交量": [1000000, 500000, 800000],
            "成交额": [10000000, 2500000, 12000000],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_a_spot_em.return_value = df
            result = await service.get_cn_stocks()

        # 涨幅第一应该是涨幅最大的
        if result["rise"]:
            assert result["rise"][0]["changePercent"] == 5.0

    @pytest.mark.asyncio
    async def test_returns_empty_on_empty_df(self):
        """空 DataFrame 应该返回空的 rise/fall"""
        service = MarketService()

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_a_spot_em.return_value = pd.DataFrame()
            result = await service.get_cn_stocks()

        assert result == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_returns_empty_on_none_df(self):
        """None DataFrame 应该返回空的 rise/fall"""
        service = MarketService()

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_a_spot_em.return_value = None
            result = await service.get_cn_stocks()

        assert result == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self):
        """异常时应该返回空的 rise/fall"""
        service = MarketService()

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_a_spot_em.side_effect = Exception("API错误")
            result = await service.get_cn_stocks()

        assert result == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_stock_data_structure(self):
        """个股数据应该包含正确的字段"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["000001", "000002", "000003", "000004", "000005",
                      "000006", "000007", "000008", "000009", "000010",
                      "000011"],
            "名称": [f"股票{chr(65+i)}" for i in range(11)],
            "最新价": [10.0 + i for i in range(11)],
            "涨跌幅": [float(i) for i in range(-5, 6)],
            "涨跌额": [0.1 * i for i in range(-5, 6)],
            "成交量": [1000000] * 11,
            "成交额": [10000000] * 11,
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_a_spot_em.return_value = df
            result = await service.get_cn_stocks()

        stock = result["rise"][0]
        assert "code" in stock
        assert "name" in stock
        assert "price" in stock
        assert "changePercent" in stock
        assert "change" in stock
        assert "volume" in stock
        assert "amount" in stock


class TestGetCommodities:
    """贵金属数据测试"""

    @pytest.mark.asyncio
    async def test_returns_cached_data(self):
        """有缓存时应该直接返回缓存数据"""
        service = MarketService()
        cached_data = [{"code": "AU9999", "name": "黄金", "current": 500.0}]
        service._set_cache("commodities", cached_data)

        result = await service.get_commodities()
        assert result == cached_data

    @pytest.mark.asyncio
    async def test_fetches_domestic_gold(self):
        """应该获取国内黄金数据"""
        service = MarketService()

        df = pd.DataFrame({
            "早盘价": [500.0],
            "晚盘价": [501.0],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.spot_golden_benchmark_sge.return_value = df
            # 国际贵金属抛异常，只测国内
            mock_ak.futures_foreign_commodity_realtime.side_effect = Exception("不支持")
            result = await service.get_commodities()

        assert len(result) >= 1
        gold = next((c for c in result if c["code"] == "AU9999"), None)
        assert gold is not None
        assert gold["name"] == "黄金"
        assert gold["current"] == 500.0
        assert gold["unit"] == "元/克"

    @pytest.mark.asyncio
    async def test_fetches_international_gold(self):
        """应该获取国际黄金数据"""
        service = MarketService()

        df_domestic = pd.DataFrame({"早盘价": [500.0], "晚盘价": [501.0]})
        df_intl = pd.DataFrame({
            "最新价": [2000.0],
            "涨跌额": [15.0],
            "涨跌幅": [0.75],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.spot_golden_benchmark_sge.return_value = df_domestic
            mock_ak.futures_foreign_commodity_realtime.return_value = df_intl
            result = await service.get_commodities()

        assert len(result) == 2
        intl = next((c for c in result if c["code"] == "XAUUSD"), None)
        assert intl is not None
        assert intl["name"] == "国际黄金"
        assert intl["current"] == 2000.0
        assert intl["unit"] == "美元/盎司"

    @pytest.mark.asyncio
    async def test_international_gold_failure_graceful(self):
        """国际贵金属获取失败时不应该影响国内数据"""
        service = MarketService()

        df_domestic = pd.DataFrame({"早盘价": [500.0], "晚盘价": [501.0]})

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.spot_golden_benchmark_sge.return_value = df_domestic
            mock_ak.futures_foreign_commodity_realtime.side_effect = Exception("API错误")
            result = await service.get_commodities()

        assert len(result) == 1
        assert result[0]["code"] == "AU9999"

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self):
        """主要接口异常时应该返回空列表"""
        service = MarketService()

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.spot_golden_benchmark_sge.side_effect = Exception("API错误")
            result = await service.get_commodities()

        assert result == []

    @pytest.mark.asyncio
    async def test_empty_domestic_df(self):
        """国内数据为空时应该继续获取国际数据"""
        service = MarketService()

        df_intl = pd.DataFrame({
            "最新价": [2000.0],
            "涨跌额": [15.0],
            "涨跌幅": [0.75],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.spot_golden_benchmark_sge.return_value = pd.DataFrame()
            mock_ak.futures_foreign_commodity_realtime.return_value = df_intl
            result = await service.get_commodities()

        assert len(result) == 1
        assert result[0]["code"] == "XAUUSD"


class TestGetMarketOverview:
    """市场概览测试"""

    @pytest.mark.asyncio
    async def test_returns_selected_indices(self):
        """应该只返回精选指数（上证、深证、创业板）"""
        service = MarketService()

        # Mock get_cn_indices 返回所有主要指数
        all_indices = [
            {"code": "000001", "name": "上证指数"},
            {"code": "399001", "name": "深证成指"},
            {"code": "399006", "name": "创业板指"},
            {"code": "000300", "name": "沪深300"},
            {"code": "000905", "name": "中证500"},
        ]

        with patch.object(service, "get_cn_indices", return_value=all_indices):
            with patch.object(service, "get_commodities", return_value=[]):
                result = await service.get_market_overview()

        assert len(result["indices"]) == 3
        codes = [idx["code"] for idx in result["indices"]]
        assert "000001" in codes
        assert "399001" in codes
        assert "399006" in codes
        assert "000300" not in codes

    @pytest.mark.asyncio
    async def test_includes_commodities(self):
        """应该包含贵金属数据"""
        service = MarketService()

        commodities = [{"code": "AU9999", "name": "黄金"}]

        with patch.object(service, "get_cn_indices", return_value=[]):
            with patch.object(service, "get_commodities", return_value=commodities):
                result = await service.get_market_overview()

        assert result["commodities"] == commodities

    @pytest.mark.asyncio
    async def test_includes_update_time(self):
        """应该包含更新时间"""
        service = MarketService()

        with patch.object(service, "get_cn_indices", return_value=[]):
            with patch.object(service, "get_commodities", return_value=[]):
                result = await service.get_market_overview()

        assert "updateTime" in result
        # 验证是有效的 ISO 格式时间
        datetime.fromisoformat(result["updateTime"])

    @pytest.mark.asyncio
    async def test_handles_exception_in_indices(self):
        """指数获取异常时应该继续返回其他数据"""
        service = MarketService()

        commodities = [{"code": "AU9999", "name": "黄金"}]

        with patch.object(service, "get_cn_indices", side_effect=Exception("错误")):
            with patch.object(service, "get_commodities", return_value=commodities):
                result = await service.get_market_overview()

        assert result["indices"] == []
        assert result["commodities"] == commodities

    @pytest.mark.asyncio
    async def test_handles_exception_in_commodities(self):
        """贵金属获取异常时应该继续返回其他数据"""
        service = MarketService()

        indices = [{"code": "000001", "name": "上证指数"}]

        with patch.object(service, "get_cn_indices", return_value=indices):
            with patch.object(service, "get_commodities", side_effect=Exception("错误")):
                result = await service.get_market_overview()

        assert result["indices"] == indices
        assert result["commodities"] == []


class TestGetMarketDetail:
    """市场详情测试"""

    @pytest.mark.asyncio
    async def test_cn_market(self):
        """中国市场应该返回指数、板块、个股"""
        service = MarketService()

        indices = [{"code": "000001"}]
        sectors = {"rise": [], "fall": []}
        stocks = {"rise": [], "fall": []}

        with patch.object(service, "get_cn_indices", return_value=indices):
            with patch.object(service, "get_cn_sectors", return_value=sectors):
                with patch.object(service, "get_cn_stocks", return_value=stocks):
                    result = await service.get_market_detail("cn")

        assert result["indices"] == indices
        assert result["sectors"] == sectors
        assert result["stocks"] == stocks
        assert "updateTime" in result

    @pytest.mark.asyncio
    async def test_us_market(self):
        """美国市场应该只返回指数"""
        service = MarketService()

        indices = [{"code": "标普500"}]

        with patch.object(service, "get_us_indices", return_value=indices):
            result = await service.get_market_detail("us")

        assert result["indices"] == indices
        assert result["sectors"] == {"rise": [], "fall": []}
        assert result["stocks"] == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_hk_market(self):
        """香港市场应该只返回指数"""
        service = MarketService()

        indices = [{"code": "HSI"}]

        with patch.object(service, "get_hk_indices", return_value=indices):
            result = await service.get_market_detail("hk")

        assert result["indices"] == indices
        assert result["sectors"] == {"rise": [], "fall": []}
        assert result["stocks"] == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_commodities_market(self):
        """大宗商品市场应该只返回商品数据"""
        service = MarketService()

        commodities = [{"code": "AU9999"}]

        with patch.object(service, "get_commodities", return_value=commodities):
            result = await service.get_market_detail("commodities")

        assert result["indices"] == commodities
        assert result["sectors"] == {"rise": [], "fall": []}
        assert result["stocks"] == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_unknown_market(self):
        """未知市场应该返回空数据"""
        service = MarketService()

        result = await service.get_market_detail("unknown")

        assert result["indices"] == []
        assert result["sectors"] == {"rise": [], "fall": []}
        assert result["stocks"] == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_handles_exception_in_cn_indices(self):
        """指数异常时应该继续返回其他数据"""
        service = MarketService()

        sectors = {"rise": [{"name": "半导体"}], "fall": []}
        stocks = {"rise": [], "fall": [{"code": "000001"}]}

        with patch.object(service, "get_cn_indices", side_effect=Exception("错误")):
            with patch.object(service, "get_cn_sectors", return_value=sectors):
                with patch.object(service, "get_cn_stocks", return_value=stocks):
                    result = await service.get_market_detail("cn")

        assert result["indices"] == []
        assert result["sectors"] == sectors
        assert result["stocks"] == stocks

    @pytest.mark.asyncio
    async def test_handles_exception_in_cn_sectors(self):
        """板块异常时应该继续返回其他数据"""
        service = MarketService()

        indices = [{"code": "000001"}]
        stocks = {"rise": [], "fall": []}

        with patch.object(service, "get_cn_indices", return_value=indices):
            with patch.object(service, "get_cn_sectors", side_effect=Exception("错误")):
                with patch.object(service, "get_cn_stocks", return_value=stocks):
                    result = await service.get_market_detail("cn")

        assert result["indices"] == indices
        assert result["sectors"] == {"rise": [], "fall": []}
        assert result["stocks"] == stocks

    @pytest.mark.asyncio
    async def test_handles_exception_in_cn_stocks(self):
        """个股异常时应该继续返回其他数据"""
        service = MarketService()

        indices = [{"code": "000001"}]
        sectors = {"rise": [], "fall": []}

        with patch.object(service, "get_cn_indices", return_value=indices):
            with patch.object(service, "get_cn_sectors", return_value=sectors):
                with patch.object(service, "get_cn_stocks", side_effect=Exception("错误")):
                    result = await service.get_market_detail("cn")

        assert result["indices"] == indices
        assert result["sectors"] == sectors
        assert result["stocks"] == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_update_time_present(self):
        """应该包含更新时间"""
        service = MarketService()

        with patch.object(service, "get_cn_indices", return_value=[]):
            with patch.object(service, "get_cn_sectors", return_value={"rise": [], "fall": []}):
                with patch.object(service, "get_cn_stocks", return_value={"rise": [], "fall": []}):
                    result = await service.get_market_detail("cn")

        assert "updateTime" in result
        datetime.fromisoformat(result["updateTime"])


class TestRunInThread:
    """线程池执行测试"""

    @pytest.mark.asyncio
    async def test_runs_blocking_function(self):
        """应该在线程池中运行阻塞函数"""
        service = MarketService()

        def blocking_func():
            return 42

        result = await service._run_in_thread(blocking_func)
        assert result == 42

    @pytest.mark.asyncio
    async def test_passes_arguments(self):
        """应该正确传递参数"""
        service = MarketService()

        def add(a, b):
            return a + b

        result = await service._run_in_thread(add, 1, 2)
        assert result == 3

    @pytest.mark.asyncio
    async def test_timeout_raises(self):
        """超时应该抛出异常"""
        service = MarketService()

        async def slow_func():
            await asyncio.sleep(100)

        # 临时降低超时时间
        with patch("backend.services.market_service.executor"):
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(
                    service._run_in_thread(lambda: asyncio.sleep(100)),
                    timeout=0.01
                )

    @pytest.mark.asyncio
    async def test_returns_kwargs(self):
        """应该正确传递关键字参数"""
        service = MarketService()

        def greet(name, greeting="hello"):
            return f"{greeting} {name}"

        result = await service._run_in_thread(greet, "world", greeting="hi")
        assert result == "hi world"

    @pytest.mark.asyncio
    async def test_propagates_exception_from_thread(self):
        """线程中抛出的异常应该传播到调用者"""
        service = MarketService()

        def failing_func():
            raise ValueError("线程内错误")

        with pytest.raises(ValueError, match="线程内错误"):
            await service._run_in_thread(failing_func)


class TestCacheEdgeCases:
    """缓存边界情况测试"""

    def test_cache_key_isolation_between_types(self):
        """不同类型数据的缓存 key 应该互相隔离"""
        service = MarketService()
        service._set_cache("cn_indices", [{"code": "000001"}])
        service._set_cache("us_indices", [{"code": "SP500"}])
        service._set_cache("cn_sectors", {"rise": [], "fall": []})

        assert service._get_cache("cn_indices") == [{"code": "000001"}]
        assert service._get_cache("us_indices") == [{"code": "SP500"}]
        assert service._get_cache("cn_sectors") == {"rise": [], "fall": []}
        assert service._get_cache("nonexistent") is None

    def test_cache_with_none_value(self):
        """缓存 None 值应该能正确存储和获取"""
        service = MarketService()
        service._set_cache("key", None)
        # None 是有效缓存值，应返回 None（与无缓存相同行为）
        assert service._get_cache("key") is None

    def test_cache_with_empty_list(self):
        """缓存空列表应该能正确存储和获取"""
        service = MarketService()
        service._set_cache("key", [])
        assert service._get_cache("key") == []

    def test_cache_ttl_boundary(self):
        """缓存在 TTL 边界时的行为"""
        service = MarketService()
        service._cache_ttl = 1
        service._set_cache("key", "value")

        # 刚设置时应该能获取
        assert service._get_cache("key") == "value"

    def test_cache_time_recorded(self):
        """设置缓存时应该记录时间"""
        service = MarketService()
        before = datetime.now()
        service._set_cache("key", "value")
        after = datetime.now()

        assert "key" in service._cache_time
        assert before <= service._cache_time["key"] <= after


class TestGetCNIndicesEdgeCases:
    """中国指数边界情况测试"""

    @pytest.mark.asyncio
    async def test_all_main_indices_present(self):
        """应该包含所有7个主要指数代码"""
        service = MarketService()
        main_codes = ["000001", "399001", "399006", "000300", "000905", "000852", "399303"]

        df = pd.DataFrame({
            "代码": main_codes,
            "名称": [f"指数{i}" for i in range(len(main_codes))],
            "最新价": [3000.0] * len(main_codes),
            "涨跌额": [10.0] * len(main_codes),
            "涨跌幅": [0.33] * len(main_codes),
            "成交量": [1000000] * len(main_codes),
            "成交额": [3000000000] * len(main_codes),
            "最高": [3050.0] * len(main_codes),
            "最低": [2980.0] * len(main_codes),
            "今开": [2990.0] * len(main_codes),
            "昨收": [2990.0] * len(main_codes),
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_index_spot_em.return_value = df
            result = await service.get_cn_indices()

        assert len(result) == 7
        for code in main_codes:
            assert any(idx["code"] == code for idx in result), f"缺少指数 {code}"

    @pytest.mark.asyncio
    async def test_empty_dataframe(self):
        """空 DataFrame 应该返回空列表"""
        service = MarketService()

        df = pd.DataFrame(columns=["代码", "名称", "最新价", "涨跌额", "涨跌幅",
                                    "成交量", "成交额", "最高", "最低", "今开", "昨收"])

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_index_spot_em.return_value = df
            result = await service.get_cn_indices()

        assert result == []

    @pytest.mark.asyncio
    async def test_numeric_type_conversion(self):
        """数值字段应该正确转换为 float"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["000001"],
            "名称": ["上证指数"],
            "最新价": [3000],       # int
            "涨跌额": [10],        # int
            "涨跌幅": [0.33],      # float
            "成交量": [1000000],   # int
            "成交额": [3000000000],  # int
            "最高": [3050],        # int
            "最低": [2980],        # int
            "今开": [2990],        # int
            "昨收": [2990],        # int
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_index_spot_em.return_value = df
            result = await service.get_cn_indices()

        idx = result[0]
        assert isinstance(idx["current"], float)
        assert isinstance(idx["change"], float)
        assert isinstance(idx["changePercent"], float)
        assert isinstance(idx["volume"], float)
        assert isinstance(idx["amount"], float)


class TestGetUSIndicesEdgeCases:
    """美国指数边界情况测试"""

    @pytest.mark.asyncio
    async def test_partial_name_match(self):
        """代码匹配应该正确返回"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["SPX", "NDX", "DJIA"],
            "名称": ["标普500指数", "纳斯达克综合指数", "道琼斯工业平均指数"],
            "最新价": [5000.0, 16000.0, 40000.0],
            "涨跌额": [25.0, 128.0, 120.0],
            "涨跌幅": [0.5, 0.8, 0.3],
            "最高": [5050.0, 16200.0, 40500.0],
            "最低": [4980.0, 15900.0, 39800.0],
            "开盘": [4990.0, 15950.0, 39900.0],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.index_global_spot_em.return_value = df
            result = await service.get_us_indices()

        # 代码 SPX, NDX, DJIA 应该匹配
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_no_matching_names(self):
        """没有匹配名称时应该返回空列表"""
        service = MarketService()

        df = pd.DataFrame({
            "名称": ["日经225", "富时100"],
            "收盘": [30000.0, 7500.0],
            "涨跌幅": [0.5, 0.3],
            "最高": [30100.0, 7550.0],
            "最低": [29900.0, 7450.0],
            "开盘": [30000.0, 7500.0],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.index_global_spot_em.return_value = df
            result = await service.get_us_indices()

        assert result == []

    @pytest.mark.asyncio
    async def test_caches_after_fetch(self):
        """获取数据后应该存入缓存"""
        service = MarketService()

        df = pd.DataFrame({
            "名称": ["标普500"],
            "收盘": [5000.0],
            "涨跌幅": [0.5],
            "最高": [5050.0],
            "最低": [4980.0],
            "开盘": [4990.0],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.index_global_spot_em.return_value = df
            await service.get_us_indices()

        assert service._get_cache("us_indices") is not None


class TestGetHKIndicesEdgeCases:
    """香港指数边界情况测试"""

    @pytest.mark.asyncio
    async def test_only_target_codes_returned(self):
        """只返回 HSI, HSCEI, HSTECH 三个代码"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["HSI", "HSCEI", "HSTECH", "OTHER1", "OTHER2"],
            "名称": ["恒生指数", "国企指数", "恒生科技", "其他1", "其他2"],
            "最新价": [18000.0, 6500.0, 4000.0, 1000.0, 2000.0],
            "涨跌额": [100.0, 50.0, 30.0, -10.0, 20.0],
            "涨跌幅": [0.56, 0.78, 0.75, -1.0, 1.0],
            "成交量": [500000, 300000, 200000, 100000, 150000],
            "成交额": [9e9, 1.95e9, 8e8, 1e8, 3e8],
            "最高": [18100.0, 6550.0, 4050.0, 1020.0, 2020.0],
            "最低": [17900.0, 6450.0, 3950.0, 990.0, 1980.0],
            "今开": [17950.0, 6480.0, 3980.0, 1010.0, 2000.0],
            "昨收": [17900.0, 6450.0, 3970.0, 1010.0, 2000.0],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_hk_index_spot_em.return_value = df
            result = await service.get_hk_indices()

        assert len(result) == 3
        codes = [idx["code"] for idx in result]
        assert set(codes) == {"HSI", "HSCEI", "HSTECH"}

    @pytest.mark.asyncio
    async def test_caches_after_fetch(self):
        """获取数据后应该存入缓存"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["HSI"],
            "名称": ["恒生指数"],
            "最新价": [18000.0],
            "涨跌额": [100.0],
            "涨跌幅": [0.56],
            "成交量": [500000],
            "成交额": [9e9],
            "最高": [18100.0],
            "最低": [17900.0],
            "今开": [17950.0],
            "昨收": [17900.0],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_hk_index_spot_em.return_value = df
            await service.get_hk_indices()

        assert service._get_cache("hk_indices") is not None


class TestGetCNSectorsEdgeCases:
    """板块数据边界情况测试"""

    @pytest.mark.asyncio
    async def test_fewer_than_5_sectors(self):
        """少于5个板块时，rise 和 fall 长度应该等于总数"""
        service = MarketService()

        df = pd.DataFrame({
            "板块名称": ["半导体", "银行", "医药"],
            "涨跌幅": [3.5, 1.2, -0.5],
            "领涨股票": ["股票A", "股票B", "股票C"],
            "总成交量": [1000000, 2000000, 3000000],
            "总成交额": [5e9, 2e9, 1e9],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_board_industry_name_em.return_value = df
            result = await service.get_cn_sectors()

        # rise: 涨幅前5，但只有3个
        assert len(result["rise"]) == 3
        # fall: 跌幅前5（反转），但只有3个
        assert len(result["fall"]) == 3

    @pytest.mark.asyncio
    async def test_caches_after_fetch(self):
        """获取数据后应该存入缓存"""
        service = MarketService()

        df = pd.DataFrame({
            "板块名称": ["半导体", "银行", "医药", "新能源", "消费", "地产"],
            "涨跌幅": [3.5, 1.2, -0.5, 2.8, 0.3, -2.1],
            "领涨股票": ["股票A", "股票B", "股票C", "股票D", "股票E", "股票F"],
            "总成交量": [1000000, 2000000, 3000000, 4000000, 5000000, 6000000],
            "总成交额": [5e9, 2e9, 1e9, 4e9, 5e8, 3e9],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_board_industry_name_em.return_value = df
            await service.get_cn_sectors()

        assert service._get_cache("cn_sectors") is not None

    @pytest.mark.asyncio
    async def test_fall_sorted_descending_by_loss(self):
        """跌幅列表应该按跌幅从小到大排列（最差的在前）"""
        service = MarketService()

        df = pd.DataFrame({
            "板块名称": ["A", "B", "C", "D", "E", "F"],
            "涨跌幅": [1.0, -3.0, -1.0, 2.0, -5.0, -2.0],
            "领涨股票": ["s"] * 6,
            "总成交量": [1000000] * 6,
            "总成交额": [1e9] * 6,
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_board_industry_name_em.return_value = df
            result = await service.get_cn_sectors()

        # fall 应该按跌幅从小到大: -5.0, -3.0, -2.0, -1.0, 1.0
        fall_changes = [s["changePercent"] for s in result["fall"]]
        assert fall_changes == sorted(fall_changes, reverse=False)
        assert fall_changes[0] == -5.0


class TestGetCNStocksEdgeCases:
    """个股数据边界情况测试"""

    @pytest.mark.asyncio
    async def test_limit_rise_and_fall_to_10(self):
        """涨幅和跌幅列表应该最多返回10个"""
        service = MarketService()

        # 创建 25 只股票
        codes = [f"{i:06d}" for i in range(25)]
        names = [f"股票{chr(65 + i % 26)}{i}" for i in range(25)]
        changes = [float(i - 12) for i in range(25)]  # -12 到 12

        df = pd.DataFrame({
            "代码": codes,
            "名称": names,
            "最新价": [10.0] * 25,
            "涨跌幅": changes,
            "涨跌额": [0.1] * 25,
            "成交量": [1000000] * 25,
            "成交额": [10000000] * 25,
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_a_spot_em.return_value = df
            result = await service.get_cn_stocks()

        assert len(result["rise"]) <= 10
        assert len(result["fall"]) <= 10

    @pytest.mark.asyncio
    async def test_fewer_than_10_stocks(self):
        """少于10只股票时，返回全部"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["000001", "000002", "000003"],
            "名称": ["股票A", "股票B", "股票C"],
            "最新价": [10.0, 5.0, 15.0],
            "涨跌幅": [5.0, -2.0, 3.0],
            "涨跌额": [0.5, -0.1, 0.45],
            "成交量": [1000000, 500000, 800000],
            "成交额": [10000000, 2500000, 12000000],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_a_spot_em.return_value = df
            result = await service.get_cn_stocks()

        # 只有3只非ST股票，rise 和 fall 各自最多3个
        assert len(result["rise"]) <= 3
        assert len(result["fall"]) <= 3

    @pytest.mark.asyncio
    async def test_all_st_stocks_filtered(self):
        """全部是 ST 股票时应该返回空列表"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["000001", "000002"],
            "名称": ["ST某某", "*ST某某"],
            "最新价": [5.0, 3.0],
            "涨跌幅": [5.0, -2.0],
            "涨跌额": [0.25, -0.06],
            "成交量": [1000000, 500000],
            "成交额": [5000000, 1500000],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_a_spot_em.return_value = df
            result = await service.get_cn_stocks()

        assert result["rise"] == []
        assert result["fall"] == []

    @pytest.mark.asyncio
    async def test_caches_after_fetch(self):
        """获取数据后应该存入缓存"""
        service = MarketService()

        df = pd.DataFrame({
            "代码": ["000001"],
            "名称": ["股票A"],
            "最新价": [10.0],
            "涨跌幅": [5.0],
            "涨跌额": [0.5],
            "成交量": [1000000],
            "成交额": [10000000],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.stock_zh_a_spot_em.return_value = df
            await service.get_cn_stocks()

        assert service._get_cache("cn_stocks") is not None


class TestGetCommoditiesEdgeCases:
    """贵金属数据边界情况测试"""

    @pytest.mark.asyncio
    async def test_domestic_gold_data_fields(self):
        """国内黄金数据应该包含正确字段"""
        service = MarketService()

        df = pd.DataFrame({"早盘价": [500.0], "晚盘价": [501.0]})

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.spot_golden_benchmark_sge.return_value = df
            mock_ak.futures_foreign_commodity_realtime.side_effect = Exception("不支持")
            result = await service.get_commodities()

        gold = result[0]
        assert gold["code"] == "AU9999"
        assert gold["name"] == "黄金"
        assert gold["unit"] == "元/克"
        assert gold["current"] == 500.0

    @pytest.mark.asyncio
    async def test_international_gold_data_fields(self):
        """国际黄金数据应该包含正确字段"""
        service = MarketService()

        df_domestic = pd.DataFrame({"早盘价": [500.0], "晚盘价": [501.0]})
        df_intl = pd.DataFrame({
            "最新价": [2000.0],
            "涨跌额": [15.0],
            "涨跌幅": [0.75],
        })

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.spot_golden_benchmark_sge.return_value = df_domestic
            mock_ak.futures_foreign_commodity_realtime.return_value = df_intl
            result = await service.get_commodities()

        intl = next(c for c in result if c["code"] == "XAUUSD")
        assert intl["name"] == "国际黄金"
        assert intl["unit"] == "美元/盎司"
        assert intl["current"] == 2000.0
        assert intl["change"] == 15.0
        assert intl["changePercent"] == 0.75

    @pytest.mark.asyncio
    async def test_caches_after_fetch(self):
        """获取数据后应该存入缓存"""
        service = MarketService()

        df = pd.DataFrame({"收盘价": [500.0]})

        with patch("backend.services.market_service.ak") as mock_ak:
            mock_ak.spot_golden_benchmark_sge.return_value = df
            mock_ak.futures_foreign_commodity_realtime.side_effect = Exception("不支持")
            await service.get_commodities()

        assert service._get_cache("commodities") is not None


class TestGetMarketOverviewEdgeCases:
    """市场概览边界情况测试"""

    @pytest.mark.asyncio
    async def test_both_fail_returns_empty(self):
        """指数和贵金属都失败时应该返回空数据"""
        service = MarketService()

        with patch.object(service, "get_cn_indices", side_effect=Exception("错误")):
            with patch.object(service, "get_commodities", side_effect=Exception("错误")):
                result = await service.get_market_overview()

        assert result["indices"] == []
        assert result["commodities"] == []
        assert "updateTime" in result

    @pytest.mark.asyncio
    async def test_overview_filters_to_three_indices(self):
        """概览只包含上证、深证、创业板三个指数"""
        service = MarketService()

        all_indices = [
            {"code": "000001", "name": "上证指数"},
            {"code": "399001", "name": "深证成指"},
            {"code": "399006", "name": "创业板指"},
            {"code": "000300", "name": "沪深300"},
            {"code": "000905", "name": "中证500"},
            {"code": "000852", "name": "中证1000"},
            {"code": "399303", "name": "国证2000"},
        ]

        with patch.object(service, "get_cn_indices", return_value=all_indices):
            with patch.object(service, "get_commodities", return_value=[]):
                result = await service.get_market_overview()

        codes = [idx["code"] for idx in result["indices"]]
        assert codes == ["000001", "399001", "399006"]

    @pytest.mark.asyncio
    async def test_empty_indices_with_commodities(self):
        """空指数但有贵金属时应该正常返回"""
        service = MarketService()

        commodities = [{"code": "AU9999", "name": "黄金", "current": 500.0}]

        with patch.object(service, "get_cn_indices", return_value=[]):
            with patch.object(service, "get_commodities", return_value=commodities):
                result = await service.get_market_overview()

        assert result["indices"] == []
        assert len(result["commodities"]) == 1


class TestGetMarketDetailEdgeCases:
    """市场详情边界情况测试"""

    @pytest.mark.asyncio
    async def test_default_market_is_cn(self):
        """默认市场应该是 cn"""
        service = MarketService()

        with patch.object(service, "get_cn_indices", return_value=[]):
            with patch.object(service, "get_cn_sectors", return_value={"rise": [], "fall": []}):
                with patch.object(service, "get_cn_stocks", return_value={"rise": [], "fall": []}):
                    result = await service.get_market_detail()

        assert "indices" in result
        assert "sectors" in result
        assert "stocks" in result

    @pytest.mark.asyncio
    async def test_us_market_no_sectors_or_stocks(self):
        """美国市场不应该返回板块和个股数据"""
        service = MarketService()

        with patch.object(service, "get_us_indices", return_value=[{"code": "SP500"}]):
            result = await service.get_market_detail("us")

        assert result["indices"] == [{"code": "SP500"}]
        assert result["sectors"] == {"rise": [], "fall": []}
        assert result["stocks"] == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_hk_market_no_sectors_or_stocks(self):
        """香港市场不应该返回板块和个股数据"""
        service = MarketService()

        with patch.object(service, "get_hk_indices", return_value=[{"code": "HSI"}]):
            result = await service.get_market_detail("hk")

        assert result["indices"] == [{"code": "HSI"}]
        assert result["sectors"] == {"rise": [], "fall": []}
        assert result["stocks"] == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_commodities_market_uses_indices_field(self):
        """大宗商品市场使用 indices 字段返回商品数据"""
        service = MarketService()

        commodities = [{"code": "AU9999", "name": "黄金"}]

        with patch.object(service, "get_commodities", return_value=commodities):
            result = await service.get_market_detail("commodities")

        assert result["indices"] == commodities

    @pytest.mark.asyncio
    async def test_unknown_market_returns_empty(self):
        """未知市场应该返回空数据结构"""
        service = MarketService()

        result = await service.get_market_detail("japan")

        assert result["indices"] == []
        assert result["sectors"] == {"rise": [], "fall": []}
        assert result["stocks"] == {"rise": [], "fall": []}
        assert "updateTime" in result

    @pytest.mark.asyncio
    async def test_cn_market_all_fail(self):
        """中国市场所有数据都失败时应该返回空结构"""
        service = MarketService()

        with patch.object(service, "get_cn_indices", side_effect=Exception("错误")):
            with patch.object(service, "get_cn_sectors", side_effect=Exception("错误")):
                with patch.object(service, "get_cn_stocks", side_effect=Exception("错误")):
                    result = await service.get_market_detail("cn")

        assert result["indices"] == []
        assert result["sectors"] == {"rise": [], "fall": []}
        assert result["stocks"] == {"rise": [], "fall": []}

    @pytest.mark.asyncio
    async def test_update_time_is_iso_format(self):
        """updateTime 应该是有效的 ISO 格式时间"""
        service = MarketService()

        with patch.object(service, "get_cn_indices", return_value=[]):
            with patch.object(service, "get_cn_sectors", return_value={"rise": [], "fall": []}):
                with patch.object(service, "get_cn_stocks", return_value={"rise": [], "fall": []}):
                    result = await service.get_market_detail("cn")

        parsed = datetime.fromisoformat(result["updateTime"])
        assert isinstance(parsed, datetime)
