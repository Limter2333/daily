import { TrendingUp, TrendingDown } from 'lucide-react';
import type { StockData, SectorData } from '../types';

interface StockTableProps {
  title: string;
  type: 'rise' | 'fall';
  stocks?: StockData[];
  sectors?: SectorData[];
}

export default function StockTable({ title, type, stocks, sectors }: StockTableProps) {
  const isRise = type === 'rise';

  const formatNumber = (num: number) => {
    if (num >= 100000000) {
      return (num / 100000000).toFixed(2) + '亿';
    }
    if (num >= 10000) {
      return (num / 10000).toFixed(2) + '万';
    }
    return num.toFixed(2);
  };

  const colorClass = isRise ? 'text-red-600' : 'text-green-600';
  const bgColorClass = isRise ? 'bg-red-50' : 'bg-green-50';
  const Icon = isRise ? TrendingUp : TrendingDown;

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      <div className={`${bgColorClass} px-4 py-3 flex items-center space-x-2`}>
        <Icon className={`w-4 h-4 ${colorClass}`} />
        <h4 className={`text-sm font-semibold ${colorClass}`}>{title}</h4>
      </div>

      {/* 板块表格 */}
      {sectors && sectors.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 text-xs text-gray-500 uppercase">
                <th className="px-4 py-2 text-left">板块</th>
                <th className="px-4 py-2 text-right">涨跌幅</th>
                <th className="px-4 py-2 text-left">领涨股</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sectors.map((sector, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-2.5 text-sm font-medium text-gray-900">
                    {sector.name}
                  </td>
                  <td className={`px-4 py-2.5 text-sm font-medium text-right ${colorClass}`}>
                    {isRise ? '+' : ''}{sector.changePercent.toFixed(2)}%
                  </td>
                  <td className="px-4 py-2.5 text-sm text-gray-600">
                    {sector.leadStock || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 个股表格 */}
      {stocks && stocks.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 text-xs text-gray-500 uppercase">
                <th className="px-4 py-2 text-left">代码</th>
                <th className="px-4 py-2 text-left">名称</th>
                <th className="px-4 py-2 text-right">价格</th>
                <th className="px-4 py-2 text-right">涨跌幅</th>
                <th className="px-4 py-2 text-right">成交额</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {stocks.map((stock, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-2.5 text-sm text-gray-600">
                    {stock.code}
                  </td>
                  <td className="px-4 py-2.5 text-sm font-medium text-gray-900">
                    {stock.name}
                  </td>
                  <td className={`px-4 py-2.5 text-sm font-medium text-right ${colorClass}`}>
                    {stock.price.toFixed(2)}
                  </td>
                  <td className={`px-4 py-2.5 text-sm font-medium text-right ${colorClass}`}>
                    {isRise ? '+' : ''}{stock.changePercent.toFixed(2)}%
                  </td>
                  <td className="px-4 py-2.5 text-sm text-gray-600 text-right">
                    {stock.amount ? formatNumber(stock.amount) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 无数据提示 */}
      {(!stocks || stocks.length === 0) && (!sectors || sectors.length === 0) && (
        <div className="px-4 py-8 text-center text-gray-500 text-sm">
          暂无数据
        </div>
      )}
    </div>
  );
}
