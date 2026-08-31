import { useState, useEffect } from 'react';
import { RefreshCw, Clock, TrendingUp, BarChart3 } from 'lucide-react';
import IndexCard from './IndexCard';
import StockTable from './StockTable';
import { getMarketDetail } from '../services/api';
import type { MarketType, MarketDetail as MarketDetailType } from '../types';
import { MARKET_CONFIG } from '../types';

export default function MarketPage() {
  const [activeMarket, setActiveMarket] = useState<MarketType>('cn');
  const [data, setData] = useState<MarketDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const markets: MarketType[] = ['cn', 'us', 'hk', 'commodities'];

  const loadData = async (market: MarketType) => {
    try {
      setLoading(true);
      const result = await getMarketDetail(market);
      setData(result);
    } catch (err) {
      console.error('加载市场数据失败:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(activeMarket);
  }, [activeMarket]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData(activeMarket);
    setRefreshing(false);
  };

  const handleMarketChange = (market: MarketType) => {
    setActiveMarket(market);
  };

  return (
    <div className="container-responsive">
      {/* 页面标题 */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">📊 全球市场行情</h2>
            <p className="mt-1 text-gray-500">
              查看全球主要市场指数、板块和个股行情
            </p>
          </div>

          <div className="mt-4 md:mt-0 flex items-center space-x-3">
            {data?.updateTime && (
              <div className="flex items-center space-x-1 text-sm text-gray-500">
                <Clock className="w-4 h-4" />
                <span>更新于 {new Date(data.updateTime).toLocaleTimeString('zh-CN')}</span>
              </div>
            )}
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              <span>{refreshing ? '刷新中...' : '刷新'}</span>
            </button>
          </div>
        </div>

        {/* 市场选择菜单 */}
        <div className="mt-6 flex flex-wrap gap-2">
          {markets.map((market) => {
            const marketConfig = MARKET_CONFIG[market];
            return (
              <button
                key={market}
                onClick={() => handleMarketChange(market)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeMarket === market
                    ? 'bg-primary-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                <span>{marketConfig.icon}</span>
                <span>{marketConfig.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 加载状态 */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
          <span className="ml-3 text-gray-500">加载中...</span>
        </div>
      ) : (
        <>
          {/* 指数区域 */}
          {data?.indices && data.indices.length > 0 && (
            <div className="mb-6">
              {activeMarket === 'commodities' ? (
                // 大宗商品按分类显示
                <>
                  {/* 贵金属 */}
                  {data.indices.some(i => i.category === 'precious') && (
                    <div className="mb-6">
                      <div className="flex items-center space-x-2 mb-4">
                        <TrendingUp className="w-5 h-5 text-yellow-600" />
                        <h3 className="text-lg font-semibold text-gray-900">贵金属</h3>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        {data.indices.filter(i => i.category === 'precious').map((index) => (
                          <IndexCard key={index.code} index={index} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 能源 */}
                  {data.indices.some(i => i.category === 'energy') && (
                    <div className="mb-6">
                      <div className="flex items-center space-x-2 mb-4">
                        <TrendingUp className="w-5 h-5 text-orange-600" />
                        <h3 className="text-lg font-semibold text-gray-900">能源</h3>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        {data.indices.filter(i => i.category === 'energy').map((index) => (
                          <IndexCard key={index.code} index={index} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 金属 */}
                  {data.indices.some(i => i.category === 'metal') && (
                    <div className="mb-6">
                      <div className="flex items-center space-x-2 mb-4">
                        <TrendingUp className="w-5 h-5 text-blue-600" />
                        <h3 className="text-lg font-semibold text-gray-900">金属</h3>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        {data.indices.filter(i => i.category === 'metal').map((index) => (
                          <IndexCard key={index.code} index={index} />
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                // 其他市场直接显示
                <>
                  <div className="flex items-center space-x-2 mb-4">
                    <TrendingUp className="w-5 h-5 text-primary-600" />
                    <h3 className="text-lg font-semibold text-gray-900">主要指数</h3>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {data.indices.map((index) => (
                      <IndexCard key={index.code} index={index} />
                    ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* 板块排行（仅中国市场） */}
          {activeMarket === 'cn' && data?.sectors && (
            <div className="mb-6">
              <div className="flex items-center space-x-2 mb-4">
                <BarChart3 className="w-5 h-5 text-primary-600" />
                <h3 className="text-lg font-semibold text-gray-900">板块排行</h3>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <StockTable
                  title="涨幅榜"
                  type="rise"
                  sectors={data.sectors.rise}
                />
                <StockTable
                  title="跌幅榜"
                  type="fall"
                  sectors={data.sectors.fall}
                />
              </div>
            </div>
          )}

          {/* 个股排行（仅中国市场） */}
          {activeMarket === 'cn' && data?.stocks && (
            <div className="mb-6">
              <div className="flex items-center space-x-2 mb-4">
                <BarChart3 className="w-5 h-5 text-primary-600" />
                <h3 className="text-lg font-semibold text-gray-900">个股排行</h3>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <StockTable
                  title="涨幅榜"
                  type="rise"
                  stocks={data.stocks.rise}
                />
                <StockTable
                  title="跌幅榜"
                  type="fall"
                  stocks={data.stocks.fall}
                />
              </div>
            </div>
          )}

          {/* 其他市场提示 */}
          {activeMarket !== 'cn' && activeMarket !== 'commodities' && (
            <div className="bg-white rounded-xl shadow-sm p-8 text-center">
              <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {MARKET_CONFIG[activeMarket].icon} {MARKET_CONFIG[activeMarket].name}市场
              </h3>
              <p className="text-gray-500">
                {activeMarket === 'us' && '美股板块和个股数据开发中...'}
                {activeMarket === 'hk' && '港股板块和个股数据开发中...'}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
