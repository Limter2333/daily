/**
 * 新闻类别
 */
export type NewsCategory = 'finance' | 'tech' | 'semiconductor' | 'ai' | 'consumer' | 'other';

/**
 * 新闻类别配置
 */
export const CATEGORY_CONFIG: Record<NewsCategory, { name: string; icon: string; color: string }> = {
  finance: { name: '财经', icon: '💰', color: 'bg-green-100 text-green-800' },
  tech: { name: '科技', icon: '💻', color: 'bg-blue-100 text-blue-800' },
  semiconductor: { name: '半导体', icon: '🔬', color: 'bg-purple-100 text-purple-800' },
  ai: { name: 'AI/机器人', icon: '🤖', color: 'bg-orange-100 text-orange-800' },
  consumer: { name: '消费', icon: '🛒', color: 'bg-pink-100 text-pink-800' },
  other: { name: '其他', icon: '📰', color: 'bg-gray-100 text-gray-800' },
};

/**
 * 新闻条目
 */
export interface NewsItem {
  id: number;
  title: string;
  summary: string | null;
  content: string | null;
  source: string;
  source_url: string | null;
  url: string | null;
  category: NewsCategory;
  importance: number;
  published_at: string | null;
  created_at: string;
  is_sent: boolean;
  tags: string | null;
}

/**
 * 早报/晚报类型
 */
export type BriefingType = 'morning' | 'evening';

/**
 * 早报/晚报
 */
export interface Briefing {
  id: number;
  type: BriefingType;
  title: string;
  content: string;
  news_ids: string | null;
  created_at: string;
  is_sent: boolean;
}

/**
 * 系统设置（AI 配置从 .env 文件读取，不在前端显示）
 */
export interface Settings {
  weather_city: string;
  morning_time: string;
  evening_time: string;
  email_enabled: boolean;
  smtp_server: string;
  smtp_port: number;
  smtp_username: string;
  smtp_password: string;
  email_recipient: string;
  push_enabled: boolean;
  push_platform: string;
  push_webhook_url: string;
}

/**
 * AI 配置状态（只读）
 */
export interface AISettingsStatus {
  ai_available: boolean;
  ai_provider: string;
  ai_model: string;
  ai_base_url: string | null;
  ai_api_key_set: boolean;
  message: string;
}

/**
 * 新闻列表响应
 */
export interface NewsListResponse {
  total: number;
  items: NewsItem[];
  page: number;
  page_size: number;
}

/**
 * 早报/晚报列表响应
 */
export interface BriefingListResponse {
  total: number;
  items: Briefing[];
}

/**
 * API 响应
 */
export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

/**
 * 分类统计
 */
export interface CategorySummary {
  [key: string]: {
    name: string;
    count: number;
  };
}

/**
 * 定时任务
 */
export interface SchedulerJob {
  id: string;
  name: string;
  next_run: string | null;
  trigger: string;
}

/**
 * 系统统计
 */
export interface SystemStats {
  news_count: number;
  briefing_count: number;
  latest_news: NewsItem | null;
  latest_briefing: Briefing | null;
}

// ==================== 市场数据类型 ====================

/**
 * 市场类型
 */
export type MarketType = 'cn' | 'us' | 'hk' | 'commodities';

/**
 * 市场配置
 */
export const MARKET_CONFIG: Record<MarketType, { name: string; icon: string }> = {
  cn: { name: '中国', icon: '🇨🇳' },
  us: { name: '美国', icon: '🇺🇸' },
  hk: { name: '香港', icon: '🇭🇰' },
  commodities: { name: '大宗商品', icon: '🏆' },
};

/**
 * 市场指数
 */
export interface MarketIndex {
  code: string;
  name: string;
  current: number;
  change: number;
  changePercent: number;
  volume?: number;
  amount?: number;
  high?: number;
  low?: number;
  open?: number;
  prevClose?: number;
}

/**
 * 板块数据
 */
export interface SectorData {
  name: string;
  changePercent: number;
  leadStock?: string;
  volume?: number;
  amount?: number;
}

/**
 * 个股数据
 */
export interface StockData {
  code: string;
  name: string;
  price: number;
  changePercent: number;
  change: number;
  volume?: number;
  amount?: number;
}

/**
 * 市场概览（首页用）
 */
export interface MarketOverview {
  indices: MarketIndex[];
  commodities: MarketIndex[];
  updateTime: string;
}

/**
 * 市场详情
 */
export interface MarketDetail {
  indices: MarketIndex[];
  sectors: {
    rise: SectorData[];
    fall: SectorData[];
  };
  stocks: {
    rise: StockData[];
    fall: StockData[];
  };
  updateTime: string;
}
