import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Newspaper,
  TrendingUp,
  RefreshCw,
  ArrowRight,
  Clock,
  BarChart3,
} from 'lucide-react';
import NewsCard from './NewsCard';
import { getLatestNews, getCategoriesSummary, triggerAggregation, getStats } from '../services/api';
import type { NewsItem, CategorySummary, SystemStats, NewsCategory } from '../types';
import { CATEGORY_CONFIG } from '../types';

export default function Dashboard() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [categories, setCategories] = useState<CategorySummary>({});
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<NewsCategory | 'all'>('all');

  // 加载数据
  const loadData = async () => {
    try {
      setLoading(true);
      const [newsData, categoriesData, statsData] = await Promise.all([
        getLatestNews(30),
        getCategoriesSummary(),
        getStats(),
      ]);
      setNews(newsData);
      setCategories(categoriesData);
      setStats(statsData);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // 刷新新闻
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await triggerAggregation();
      await loadData();
    } catch (error) {
      console.error('刷新失败:', error);
    } finally {
      setRefreshing(false);
    }
  };

  // 过滤新闻
  const filteredNews =
    selectedCategory === 'all'
      ? news
      : news.filter((item) => item.category === selectedCategory);

  return (
    <div className="container-responsive">
      {/* 欢迎区域 */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">📰 每日新闻总览</h2>
            <p className="mt-1 text-gray-500">
              聚焦财经、科技、半导体、AI等重点新闻
            </p>
          </div>

          <div className="mt-4 md:mt-0 flex items-center space-x-3">
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              <span>{refreshing ? '刷新中...' : '刷新新闻'}</span>
            </button>

            <Link
              to="/briefings"
              className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <span>查看早报晚报</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl shadow-sm p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Newspaper className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">新闻总数</p>
              <p className="text-xl font-bold text-gray-900">
                {stats?.news_count || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <BarChart3 className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">早报晚报</p>
              <p className="text-xl font-bold text-gray-900">
                {stats?.briefing_count || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">今日更新</p>
              <p className="text-xl font-bold text-gray-900">
                {news.length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Clock className="w-5 h-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">最后更新</p>
              <p className="text-sm font-medium text-gray-900">
                {stats?.latest_news?.created_at
                  ? new Date(stats.latest_news.created_at).toLocaleTimeString('zh-CN')
                  : '暂无'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 分类筛选 */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              selectedCategory === 'all'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            全部
          </button>

          {Object.entries(CATEGORY_CONFIG).map(([key, config]) => {
            const category = key as NewsCategory;
            const count = categories[category]?.count || 0;

            return (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  selectedCategory === category
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {config.icon} {config.name}
                {count > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 text-xs bg-white/20 rounded-full">
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* 新闻列表 */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <RefreshCw className="w-8 h-8 text-primary-600 animate-spin" />
          <span className="ml-3 text-gray-500">加载中...</span>
        </div>
      ) : filteredNews.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <Newspaper className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">暂无新闻</h3>
          <p className="text-gray-500">点击"刷新新闻"获取最新资讯</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredNews.map((item) => (
            <NewsCard key={item.id} news={item} />
          ))}
        </div>
      )}
    </div>
  );
}
