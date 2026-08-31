import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, ArrowRight, RefreshCw, Clock } from 'lucide-react';
import IndexCard from './IndexCard';
import { getMarketOverview } from '../services/api';
import type { MarketOverview as MarketOverviewType } from '../types';

export default function MarketOverview() {
  const [data, setData] = useState<MarketOverviewType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await getMarketOverview();
      setData(result);
    } catch (err) {
      console.error('加载市场数据失败:', err);
      setError('加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <div className="flex items-center space-x-2 mb-4">
          <TrendingUp className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900">📈 市场指数监控</h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 text-primary-600 animate-spin" />
          <span className="ml-2 text-gray-500">加载市场数据...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <div className="flex items-center space-x-2 mb-4">
          <TrendingUp className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900">📈 市场指数监控</h3>
        </div>
        <div className="text-center py-8">
          <p className="text-gray-500">暂无市场数据</p>
          <button
            onClick={loadData}
            className="mt-2 text-primary-600 hover:text-primary-700 text-sm"
          >
            点击重试
          </button>
        </div>
      </div>
    );
  }

  const hasIndices = data.indices && data.indices.length > 0;
  const hasCommodities = data.commodities && data.commodities.length > 0;

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900">📈 市场指数监控</h3>
        </div>

        <div className="flex items-center space-x-4">
          {data.updateTime && (
            <div className="flex items-center space-x-1 text-xs text-gray-500">
              <Clock className="w-3 h-3" />
              <span>更新于 {new Date(data.updateTime).toLocaleTimeString('zh-CN')}</span>
            </div>
          )}
          <Link
            to="/market"
            className="flex items-center space-x-1 text-primary-600 hover:text-primary-700 text-sm font-medium"
          >
            <span>查看详情</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* 主要指数 */}
      {hasIndices && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-500 mb-3">主要指数</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.indices.map((index) => (
              <IndexCard key={index.code} index={index} compact />
            ))}
          </div>
        </div>
      )}

      {/* 贵金属 */}
      {hasCommodities && (
        <div>
          <h4 className="text-sm font-medium text-gray-500 mb-3">贵金属/大宗商品</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.commodities.map((commodity) => (
              <IndexCard key={commodity.code} index={commodity} compact />
            ))}
          </div>
        </div>
      )}

      {/* 无数据提示 */}
      {!hasIndices && !hasCommodities && (
        <div className="text-center py-4">
          <p className="text-gray-500 text-sm">暂无市场数据，请稍后刷新</p>
        </div>
      )}
    </div>
  );
}
