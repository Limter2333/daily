import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { MarketIndex } from '../types';

interface IndexCardProps {
  index: MarketIndex;
  compact?: boolean;
}

export default function IndexCard({ index, compact = false }: IndexCardProps) {
  const isPositive = index.changePercent > 0;
  const isNegative = index.changePercent < 0;

  const colorClass = isPositive
    ? 'text-red-600'
    : isNegative
    ? 'text-green-600'
    : 'text-gray-600';

  const bgColorClass = isPositive
    ? 'bg-red-50'
    : isNegative
    ? 'bg-green-50'
    : 'bg-gray-50';

  const formatNumber = (num: number) => {
    if (num >= 10000) {
      return (num / 10000).toFixed(2) + '万';
    }
    return num.toFixed(2);
  };

  const getCategoryLabel = (category?: string) => {
    switch (category) {
      case 'precious': return '贵金属';
      case 'energy': return '能源';
      case 'metal': return '金属';
      default: return '';
    }
  };

  const TrendIcon = isPositive ? TrendingUp : isNegative ? TrendingDown : Minus;

  if (compact) {
    return (
      <div className={`${bgColorClass} rounded-lg p-3 border border-gray-100`}>
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-900 truncate">{index.name}</span>
          <TrendIcon className={`w-4 h-4 ${colorClass}`} />
        </div>
        <div className={`text-lg font-bold ${colorClass}`}>
          {formatNumber(index.current)}
        </div>
        <div className={`text-xs ${colorClass}`}>
          {isPositive ? '+' : ''}{index.changePercent.toFixed(2)}%
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-4 border border-gray-100 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <h3 className="text-sm font-medium text-gray-600">{index.name}</h3>
          {index.category && (
            <span className="px-2 py-0.5 text-xs bg-gray-100 text-gray-500 rounded-full">
              {getCategoryLabel(index.category)}
            </span>
          )}
        </div>
        <div className={`p-1.5 rounded-lg ${bgColorClass}`}>
          <TrendIcon className={`w-4 h-4 ${colorClass}`} />
        </div>
      </div>

      <div className={`text-2xl font-bold ${colorClass} mb-2`}>
        {formatNumber(index.current)}
        {index.unit && (
          <span className="text-sm font-normal text-gray-500 ml-1">{index.unit}</span>
        )}
      </div>

      <div className="flex items-center space-x-3">
        <span className={`text-sm font-medium ${colorClass}`}>
          {isPositive ? '+' : ''}{index.change.toFixed(2)}
        </span>
        <span className={`text-sm font-medium ${colorClass}`}>
          {isPositive ? '+' : ''}{index.changePercent.toFixed(2)}%
        </span>
      </div>

      {index.volume !== undefined && index.volume > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>成交量</span>
            <span>{formatNumber(index.volume)}</span>
          </div>
        </div>
      )}

      {index.high !== undefined && index.low !== undefined && (
        <div className="mt-2">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>最高 {formatNumber(index.high)}</span>
            <span>最低 {formatNumber(index.low)}</span>
          </div>
        </div>
      )}
    </div>
  );
}
