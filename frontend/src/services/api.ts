import axios from 'axios';
import { createLogger } from '../utils/logger';
import type {
  NewsItem,
  Briefing,
  Settings,
  NewsListResponse,
  BriefingListResponse,
  ApiResponse,
  CategorySummary,
  SchedulerJob,
  SystemStats,
  MarketType,
  MarketIndex,
  MarketOverview,
  MarketDetail,
  SectorData,
  StockData,
} from '../types';

const logger = createLogger('api');

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const startTime = Date.now();
    config.metadata = { startTime };

    // 记录请求
    logger.info(`→ ${config.method?.toUpperCase()} ${config.url}`);

    // 记录请求参数
    if (config.params) {
      logger.debug(`  Params: ${JSON.stringify(config.params)}`);
    }

    // 记录请求体
    if (config.data && ['post', 'put', 'patch'].includes(config.method || '')) {
      const bodyStr = typeof config.data === 'string'
        ? config.data
        : JSON.stringify(config.data);
      logger.debug(`  Body: ${bodyStr.substring(0, 500)}`);
    }

    return config;
  },
  (error) => {
    logger.error('Request Setup Error:', error.message);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    const startTime = response.config.metadata?.startTime;
    const duration = startTime ? Date.now() - startTime : 0;

    // 记录成功响应
    logger.info(
      `← ${response.config.method?.toUpperCase()} ${response.config.url} | ` +
      `Status: ${response.status} | Duration: ${duration}ms`
    );

    // 记录响应数据（调试模式）
    if (response.data) {
      const dataStr = JSON.stringify(response.data).substring(0, 300);
      logger.debug(`  Response: ${dataStr}`);
    }

    return response.data;
  },
  (error) => {
    const startTime = error.config?.metadata?.startTime;
    const duration = startTime ? Date.now() - startTime : 0;

    // 记录错误响应
    if (error.response) {
      // 服务器返回了错误状态码
      logger.error(
        `← ${error.config?.method?.toUpperCase()} ${error.config?.url} | ` +
        `Status: ${error.response.status} | Duration: ${duration}ms`
      );
      logger.error(`  Error: ${error.response.data?.detail || error.message}`);
    } else if (error.request) {
      // 请求发送但没有收到响应
      logger.error(
        `← ${error.config?.method?.toUpperCase()} ${error.config?.url} | ` +
        `No Response | Duration: ${duration}ms`
      );
      logger.error(`  Error: Network error or timeout`);
    } else {
      // 请求设置出错
      logger.error(`Request Error: ${error.message}`);
    }

    return Promise.reject(error);
  }
);

// ==================== 新闻 API ====================

/**
 * 获取新闻列表
 */
export const getNews = async (
  category?: string,
  page: number = 1,
  pageSize: number = 20,
  orderBy: string = 'importance DESC, created_at DESC'
): Promise<NewsListResponse> => {
  return api.get('/news', {
    params: { category, page, page_size: pageSize, order_by: orderBy },
  });
};

/**
 * 获取最新新闻
 */
export const getLatestNews = async (limit: number = 20): Promise<NewsItem[]> => {
  return api.get('/news/latest', { params: { limit } });
};

/**
 * 获取新闻详情
 */
export const getNewsDetail = async (newsId: number): Promise<NewsItem> => {
  return api.get(`/news/${newsId}`);
};

/**
 * 获取分类统计
 */
export const getCategoriesSummary = async (): Promise<CategorySummary> => {
  return api.get('/news/categories/summary');
};

// ==================== 早报/晚报 API ====================

/**
 * 获取早报/晚报列表
 */
export const getBriefings = async (
  type?: string,
  page: number = 1,
  pageSize: number = 10
): Promise<BriefingListResponse> => {
  return api.get('/briefings', {
    params: { type, page, page_size: pageSize },
  });
};

/**
 * 获取最新的早报/晚报
 */
export const getLatestBriefing = async (type?: string): Promise<Briefing> => {
  return api.get('/briefings/latest', { params: { type } });
};

/**
 * 获取早报/晚报详情
 */
export const getBriefingDetail = async (briefingId: number): Promise<Briefing> => {
  return api.get(`/briefings/${briefingId}`);
};

/**
 * 生成早报/晚报
 */
export const generateBriefing = async (type: string): Promise<ApiResponse> => {
  return api.post(`/briefings/generate/${type}`);
};

// ==================== AI 分析 API ====================

/**
 * AI 分析单条新闻
 */
export const analyzeNews = async (newsId: number): Promise<{
  success: boolean;
  news_id: number;
  category: string;
  importance: number;
  analysis: string;
  ai_available?: boolean;
}> => {
  return api.post(`/news/${newsId}/analyze`, null, {
    timeout: 120000, // AI 分析需要较长时间，超时设为120秒
  });
};

// ==================== 设置 API ====================

/**
 * 获取设置
 */
export const getSettings = async (): Promise<Settings> => {
  return api.get('/settings');
};

/**
 * 更新设置
 */
export const updateSettings = async (settings: Settings): Promise<Settings> => {
  return api.put('/settings', settings);
};

/**
 * 获取 AI 配置状态（只读）
 */
export const getAISettingsStatus = async (): Promise<{
  ai_available: boolean;
  ai_provider: string;
  ai_model: string;
  ai_base_url: string | null;
  ai_api_key_set: boolean;
  message: string;
}> => {
  return api.get('/settings/ai');
};

// ==================== 操作 API ====================

/**
 * 触发新闻聚合
 */
export const triggerAggregation = async (): Promise<ApiResponse> => {
  return api.post('/aggregate');
};

/**
 * 触发发送
 */
export const triggerSend = async (type: string): Promise<ApiResponse> => {
  return api.post(`/send/${type}`);
};

/**
 * 获取定时任务列表
 */
export const getSchedulerJobs = async (): Promise<SchedulerJob[]> => {
  return api.get('/scheduler/jobs');
};

// ==================== 系统 API ====================

/**
 * 健康检查
 */
export const healthCheck = async (): Promise<{ status: string; version: string; timestamp: string }> => {
  return api.get('/health');
};

/**
 * 获取系统统计
 */
export const getStats = async (): Promise<SystemStats> => {
  return api.get('/stats');
};

// ==================== 市场数据 API ====================

/**
 * 获取首页市场概览
 */
export const getMarketOverview = async (): Promise<MarketOverview> => {
  return api.get('/market/overview');
};

/**
 * 获取市场指数
 */
export const getMarketIndices = async (market: MarketType): Promise<MarketIndex[]> => {
  return api.get('/market/indices', { params: { market } });
};

/**
 * 获取板块涨跌排行
 */
export const getMarketSectors = async (market: MarketType): Promise<{ rise: SectorData[]; fall: SectorData[] }> => {
  return api.get('/market/sectors', { params: { market } });
};

/**
 * 获取个股涨跌排行
 */
export const getMarketStocks = async (market: MarketType): Promise<{ rise: StockData[]; fall: StockData[] }> => {
  return api.get('/market/stocks', { params: { market } });
};

/**
 * 获取市场详情（指数+板块+个股）
 */
export const getMarketDetail = async (market: MarketType): Promise<MarketDetail> => {
  return api.get('/market/detail', { params: { market } });
};

/**
 * 获取贵金属行情
 */
export const getCommodities = async (): Promise<MarketIndex[]> => {
  return api.get('/market/commodities');
};

export default api;
