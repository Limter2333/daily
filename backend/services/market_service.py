"""
市场数据服务 - 使用 AKShare 获取实时市场数据
"""

import asyncio
import akshare as ak
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from backend.logger import get_logger

logger = get_logger("MarketService")

# 线程池执行器，用于运行阻塞的 AKShare 调用
executor = ThreadPoolExecutor(max_workers=4)


class MarketService:
    """市场数据服务"""

    def __init__(self):
        self.logger = logger
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._cache_ttl = 300  # 5分钟缓存

    def _get_cache(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        if key in self._cache:
            if key in self._cache_time:
                if (datetime.now() - self._cache_time[key]).total_seconds() < self._cache_ttl:
                    return self._cache[key]
        return None

    def _set_cache(self, key: str, data: Any):
        """设置缓存"""
        self._cache[key] = data
        self._cache_time[key] = datetime.now()

    async def _run_in_thread(self, func, *args, **kwargs):
        """在线程池中运行阻塞函数"""
        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(executor, lambda: func(*args, **kwargs)),
                timeout=30.0  # 30秒超时
            )
        except asyncio.TimeoutError:
            self.logger.error(f"AKShare 调用超时: {func.__name__}")
            raise

    # ==================== 指数数据 ====================

    async def get_cn_indices(self) -> List[Dict[str, Any]]:
        """获取中国主要指数"""
        cache_key = "cn_indices"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        try:
            # 使用东方财富指数接口 - 获取沪深重要指数
            df = await self._run_in_thread(
                ak.stock_zh_index_spot_em,
                symbol="沪深重要指数"
            )

            # 主要指数代码
            main_indices = [
                "000001",  # 上证指数
                "399001",  # 深证成指
                "399006",  # 创业板指
                "000300",  # 沪深300
                "000905",  # 中证500
                "000852",  # 中证1000
                "399303",  # 国证2000
            ]

            indices = []
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                if code in main_indices:
                    indices.append({
                        "code": code,
                        "name": row.get("名称", ""),
                        "current": float(row.get("最新价", 0)),
                        "change": float(row.get("涨跌额", 0)),
                        "changePercent": float(row.get("涨跌幅", 0)),
                        "volume": float(row.get("成交量", 0)),
                        "amount": float(row.get("成交额", 0)),
                        "high": float(row.get("最高", 0)),
                        "low": float(row.get("最低", 0)),
                        "open": float(row.get("今开", 0)),
                        "prevClose": float(row.get("昨收", 0)),
                    })

            self._set_cache(cache_key, indices)
            return indices
        except Exception as e:
            self.logger.error(f"获取中国指数失败: {e}")
            return []

    async def get_us_indices(self) -> List[Dict[str, Any]]:
        """获取美国主要指数"""
        cache_key = "us_indices"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        try:
            # 使用东方财富全球指数接口
            df = await self._run_in_thread(
                ak.index_global_spot_em
            )

            if df is None or df.empty:
                self.logger.warning("获取美国指数数据为空")
                return []

            # 主要美国指数代码
            main_codes = {
                "DJIA": "道琼斯工业平均指数",
                "SPX": "标普500",
                "NDX": "纳斯达克综合指数",
                "IXIC": "纳斯达克综合指数",
            }

            indices = []
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                if code in main_codes:
                    indices.append({
                        "code": code,
                        "name": main_codes[code],
                        "current": float(row.get("最新价", 0)),
                        "change": float(row.get("涨跌额", 0)),
                        "changePercent": float(row.get("涨跌幅", 0)),
                        "volume": 0,
                        "amount": 0,
                        "high": float(row.get("最高", 0)) if "最高" in row.index else 0,
                        "low": float(row.get("最低", 0)) if "最低" in row.index else 0,
                        "open": float(row.get("开盘", 0)) if "开盘" in row.index else 0,
                        "prevClose": 0,
                    })

            self._set_cache(cache_key, indices)
            return indices
        except Exception as e:
            self.logger.error(f"获取美国指数失败: {e}")
            return []

    async def get_hk_indices(self) -> List[Dict[str, Any]]:
        """获取香港主要指数"""
        cache_key = "hk_indices"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        try:
            df = await self._run_in_thread(
                ak.stock_hk_index_spot_em
            )

            main_indices = ["HSI", "HSCEI", "HSTECH"]

            indices = []
            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                if code in main_indices:
                    indices.append({
                        "code": code,
                        "name": row.get("名称", ""),
                        "current": float(row.get("最新价", 0)),
                        "change": float(row.get("涨跌额", 0)),
                        "changePercent": float(row.get("涨跌幅", 0)),
                        "volume": float(row.get("成交量", 0)),
                        "amount": float(row.get("成交额", 0)),
                        "high": float(row.get("最高", 0)),
                        "low": float(row.get("最低", 0)),
                        "open": float(row.get("今开", 0)),
                        "prevClose": float(row.get("昨收", 0)),
                    })

            self._set_cache(cache_key, indices)
            return indices
        except Exception as e:
            self.logger.error(f"获取香港指数失败: {e}")
            return []

    # ==================== 板块数据 ====================

    async def get_cn_sectors(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取中国板块涨跌排行"""
        cache_key = "cn_sectors"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        try:
            df = await self._run_in_thread(
                ak.stock_board_industry_name_em
            )

            if df is None or df.empty:
                self.logger.warning("获取板块数据为空")
                return {"rise": [], "fall": []}

            sectors = []
            for _, row in df.iterrows():
                sectors.append({
                    "name": row.get("板块名称", ""),
                    "changePercent": float(row.get("涨跌幅", 0)),
                    "leadStock": row.get("领涨股票", ""),
                    "volume": float(row.get("总成交量", 0)),
                    "amount": float(row.get("总成交额", 0)),
                })

            # 排序
            sectors.sort(key=lambda x: x["changePercent"], reverse=True)

            result = {
                "rise": sectors[:5],  # 涨幅前5
                "fall": sectors[-5:][::-1] if len(sectors) >= 5 else sectors[::-1],  # 跌幅前5
            }

            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            self.logger.error(f"获取中国板块失败: {e}")
            return {"rise": [], "fall": []}

    # ==================== 个股数据 ====================

    async def get_cn_stocks(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取中国个股涨跌排行"""
        cache_key = "cn_stocks"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        try:
            df = await self._run_in_thread(
                ak.stock_zh_a_spot_em
            )

            if df is None or df.empty:
                self.logger.warning("获取个股数据为空")
                return {"rise": [], "fall": []}

            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    "code": str(row.get("代码", "")),
                    "name": row.get("名称", ""),
                    "price": float(row.get("最新价", 0)),
                    "changePercent": float(row.get("涨跌幅", 0)),
                    "change": float(row.get("涨跌额", 0)),
                    "volume": float(row.get("成交量", 0)),
                    "amount": float(row.get("成交额", 0)),
                })

            # 排序
            stocks.sort(key=lambda x: x["changePercent"], reverse=True)

            # 过滤 ST 股票
            stocks = [s for s in stocks if "ST" not in s["name"]]

            result = {
                "rise": stocks[:10],  # 涨幅前10
                "fall": stocks[-10:][::-1] if len(stocks) >= 10 else stocks[::-1],  # 跌幅前10
            }

            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            self.logger.error(f"获取中国个股失败: {e}")
            return {"rise": [], "fall": []}

    # ==================== 贵金属数据 ====================

    async def get_commodities(self) -> List[Dict[str, Any]]:
        """获取贵金属/大宗商品行情"""
        cache_key = "commodities"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        commodities = []

        # 定义要获取的商品列表
        commodity_symbols = [
            {"symbol": "XAU", "name": "黄金", "code": "XAUUSD", "unit": "美元/盎司", "category": "precious"},
            {"symbol": "XAG", "name": "白银", "code": "XAGUSD", "unit": "美元/盎司", "category": "precious"},
            {"symbol": "CL", "name": "原油", "code": "CL", "unit": "美元/桶", "category": "energy"},
            {"symbol": "HG", "name": "铜", "code": "HG", "unit": "美元/磅", "category": "metal"},
        ]

        # 并行获取所有商品数据
        async def fetch_commodity(symbol_info):
            try:
                df = await self._run_in_thread(
                    ak.futures_foreign_commodity_realtime,
                    symbol=symbol_info["symbol"]
                )
                if df is not None and not df.empty:
                    row = df.iloc[0]
                    return {
                        "code": symbol_info["code"],
                        "name": symbol_info["name"],
                        "current": float(row.get("最新价", 0)),
                        "change": float(row.get("涨跌额", 0)),
                        "changePercent": float(row.get("涨跌幅", 0)),
                        "open": float(row.get("开盘价", 0)) if "开盘价" in row.index else 0,
                        "high": float(row.get("最高价", 0)) if "最高价" in row.index else 0,
                        "low": float(row.get("最低价", 0)) if "最低价" in row.index else 0,
                        "prevClose": float(row.get("昨日收盘价", 0)) if "昨日收盘价" in row.index else 0,
                        "unit": symbol_info["unit"],
                        "category": symbol_info["category"],
                    }
            except Exception as e:
                self.logger.warning(f"获取{symbol_info['name']}失败: {e}")
            return None

        try:
            # 并行获取所有商品
            tasks = [fetch_commodity(info) for info in commodity_symbols]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 收集成功的结果
            for result in results:
                if result is not None and not isinstance(result, Exception):
                    commodities.append(result)

            # 获取国内黄金（上海黄金交易所）
            try:
                df_domestic = await self._run_in_thread(
                    ak.spot_golden_benchmark_sge
                )
                if df_domestic is not None and not df_domestic.empty:
                    latest = df_domestic.iloc[-1] if len(df_domestic) > 0 else None
                    if latest is not None:
                        price = float(latest.get("早盘价", 0)) or float(latest.get("晚盘价", 0))
                        if price > 0:
                            commodities.append({
                                "code": "AU9999",
                                "name": "国内黄金",
                                "current": price,
                                "change": 0,
                                "changePercent": 0,
                                "open": 0,
                                "high": 0,
                                "low": 0,
                                "prevClose": 0,
                                "unit": "元/克",
                                "category": "precious",
                            })
            except Exception as e:
                self.logger.warning(f"获取国内黄金失败: {e}")

            self._set_cache(cache_key, commodities)
            return commodities
        except Exception as e:
            self.logger.error(f"获取大宗商品失败: {e}")
            return []

    # ==================== 综合接口 ====================

    async def get_market_overview(self) -> Dict[str, Any]:
        """获取首页市场概览"""
        try:
            # 并行获取数据
            cn_indices, commodities = await asyncio.gather(
                self.get_cn_indices(),
                self.get_commodities(),
                return_exceptions=True
            )

            # 处理异常
            if isinstance(cn_indices, Exception):
                cn_indices = []
            if isinstance(commodities, Exception):
                commodities = []

            # 精选指数
            selected_indices = []
            for idx in cn_indices:
                if idx["code"] in ["000001", "399001", "399006"]:
                    selected_indices.append(idx)

            return {
                "indices": selected_indices,
                "commodities": commodities,
                "updateTime": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"获取市场概览失败: {e}")
            return {"indices": [], "commodities": [], "updateTime": datetime.now().isoformat()}

    async def get_market_detail(self, market: str = "cn") -> Dict[str, Any]:
        """获取市场详情"""
        try:
            if market == "cn":
                indices, sectors, stocks = await asyncio.gather(
                    self.get_cn_indices(),
                    self.get_cn_sectors(),
                    self.get_cn_stocks(),
                    return_exceptions=True
                )
            elif market == "us":
                indices = await self.get_us_indices()
                sectors = {"rise": [], "fall": []}
                stocks = {"rise": [], "fall": []}
            elif market == "hk":
                indices = await self.get_hk_indices()
                sectors = {"rise": [], "fall": []}
                stocks = {"rise": [], "fall": []}
            elif market == "commodities":
                indices = await self.get_commodities()
                sectors = {"rise": [], "fall": []}
                stocks = {"rise": [], "fall": []}
            else:
                return {"indices": [], "sectors": {"rise": [], "fall": []}, "stocks": {"rise": [], "fall": []}, "updateTime": datetime.now().isoformat()}

            # 处理异常
            if isinstance(indices, Exception):
                indices = []
            if isinstance(sectors, Exception):
                sectors = {"rise": [], "fall": []}
            if isinstance(stocks, Exception):
                stocks = {"rise": [], "fall": []}

            return {
                "indices": indices if isinstance(indices, list) else [],
                "sectors": sectors if isinstance(sectors, dict) else {"rise": [], "fall": []},
                "stocks": stocks if isinstance(stocks, dict) else {"rise": [], "fall": []},
                "updateTime": datetime.now().isoformat(),
            }
        except Exception as e:
            self.logger.error(f"获取市场详情失败: {e}")
            return {"indices": [], "sectors": {"rise": [], "fall": []}, "stocks": {"rise": [], "fall": []}}


# 全局实例
market_service = MarketService()
