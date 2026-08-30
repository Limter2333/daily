import { ExternalLink, Star, Clock, Sparkles, Loader2, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { analyzeNews } from '../services/api';
import { createLogger } from '../utils/logger';
import type { NewsItem } from '../types';
import { CATEGORY_CONFIG } from '../types';

const logger = createLogger('NewsCard');

interface NewsCardProps {
  news: NewsItem;
}

export default function NewsCard({ news }: NewsCardProps) {
  const categoryConfig = CATEGORY_CONFIG[news.category] || CATEGORY_CONFIG.other;
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [aiAvailable, setAiAvailable] = useState<boolean | null>(null);

  // 触发 AI 分析
  const handleAnalyze = async () => {
    // 如果已有分析结果，切换显示/隐藏
    if (analysis) {
      setShowAnalysis(!showAnalysis);
      logger.debug(`Toggle analysis display: news_id=${news.id}, show=${!showAnalysis}`);
      return;
    }

    // 开始分析
    logger.info(`Start AI analysis: news_id=${news.id}, title="${news.title.substring(0, 30)}..."`);
    setAnalyzing(true);
    setShowAnalysis(true);

    try {
      const result = await analyzeNews(news.id);
      if (result.success) {
        logger.info(`AI analysis completed: news_id=${news.id}, ai_available=${result.ai_available}`);
        setAnalysis(result.analysis);
        setAiAvailable(result.ai_available !== false);
      } else {
        logger.warn(`AI analysis failed: news_id=${news.id}, result=${JSON.stringify(result)}`);
        setAnalysis('分析请求失败，请稍后重试');
        setAiAvailable(false);
      }
    } catch (error) {
      logger.error(`AI analysis error: news_id=${news.id}`, error);
      setAnalysis('网络错误，请检查后端服务是否运行');
      setAiAvailable(false);
    } finally {
      setAnalyzing(false);
    }
  };

  // 格式化时间
  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);

    if (minutes < 60) {
      return `${minutes}分钟前`;
    } else if (hours < 24) {
      return `${hours}小时前`;
    } else {
      return date.toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric',
      });
    }
  };

  // 渲染重要性星星
  const renderImportance = (importance: number) => {
    const stars = Math.min(Math.ceil(importance / 2), 5);
    return (
      <div className="flex items-center space-x-0.5">
        {Array.from({ length: stars }).map((_, i) => (
          <Star
            key={i}
            className="w-3 h-3 text-yellow-400 fill-yellow-400"
          />
        ))}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden card-hover animate-fade-in">
      {/* 分类标签 */}
      <div className="px-4 pt-4 pb-2">
        <div className="flex items-center justify-between mb-2">
          <span
            className={`px-2.5 py-1 rounded-full text-xs font-medium ${categoryConfig.color}`}
          >
            {categoryConfig.icon} {categoryConfig.name}
          </span>
          <span className="text-xs text-gray-400">{news.source}</span>
        </div>

        {/* 标题 */}
        <h3 className="text-base font-semibold text-gray-900 line-clamp-2 mb-2">
          {news.title}
        </h3>

        {/* 摘要 */}
        {news.summary && (
          <p className="text-sm text-gray-600 line-clamp-3 mb-3">
            {news.summary}
          </p>
        )}
      </div>

      {/* 底部信息 */}
      <div className="px-4 pb-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {/* 重要性 */}
          {renderImportance(news.importance)}

          {/* 时间 */}
          {news.published_at && (
            <div className="flex items-center space-x-1 text-xs text-gray-400">
              <Clock className="w-3 h-3" />
              <span>{formatTime(news.published_at)}</span>
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center space-x-3">
          {/* AI 分析按钮 */}
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="flex items-center space-x-1 text-xs text-purple-600 hover:text-purple-700 transition-colors disabled:opacity-50"
          >
            {analyzing ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Sparkles className="w-3 h-3" />
            )}
            <span>{analyzing ? '分析中...' : 'AI 分析'}</span>
            {analysis && !analyzing && (
              showAnalysis ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />
            )}
          </button>

          {/* 阅读原文 */}
          {news.url && (
            <a
              href={news.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-1 text-xs text-primary-600 hover:text-primary-700 transition-colors"
            >
              <span>阅读原文</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>

      {/* AI 分析结果 */}
      {showAnalysis && (
        <div className="px-4 pb-4">
          <div className={`border rounded-lg p-3 ${
            analyzing
              ? 'bg-blue-50 border-blue-200'
              : aiAvailable === false
              ? 'bg-yellow-50 border-yellow-200'
              : 'bg-purple-50 border-purple-200'
          }`}>
            {/* 标题栏 */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-1">
                {analyzing ? (
                  <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin" />
                ) : aiAvailable === false ? (
                  <AlertCircle className="w-3.5 h-3.5 text-yellow-500" />
                ) : (
                  <Sparkles className="w-3.5 h-3.5 text-purple-500" />
                )}
                <span className={`text-xs font-medium ${
                  analyzing
                    ? 'text-blue-700'
                    : aiAvailable === false
                    ? 'text-yellow-700'
                    : 'text-purple-700'
                }`}>
                  {analyzing ? 'AI 分析中...' : aiAvailable === false ? '基础分析' : 'AI 分析'}
                </span>
              </div>
              {!analyzing && aiAvailable === false && (
                <span className="text-xs text-yellow-600">AI 暂不可用</span>
              )}
            </div>

            {/* 内容 */}
            {analyzing ? (
              <div className="flex flex-col items-center justify-center py-4 space-y-2">
                <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                <p className="text-xs text-blue-600">正在调用 AI 分析新闻...</p>
                <p className="text-xs text-blue-400">这可能需要几秒钟</p>
              </div>
            ) : analysis ? (
              <div className="text-xs text-gray-700 leading-relaxed whitespace-pre-line">
                {analysis}
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* 标签 */}
      {news.tags && (
        <div className="px-4 pb-3 flex flex-wrap gap-1">
          {news.tags.split(',').slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
            >
              {tag.trim()}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
