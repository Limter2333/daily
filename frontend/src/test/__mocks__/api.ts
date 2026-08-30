/**
 * API Mock
 */

import { vi } from 'vitest'

export const mockNews = [
  {
    id: 1,
    title: '测试新闻1',
    summary: '这是测试新闻摘要',
    source: 'test_source',
    category: 'tech',
    importance: 8,
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    title: '测试新闻2',
    summary: '这是测试新闻摘要2',
    source: 'test_source',
    category: 'finance',
    importance: 7,
    created_at: new Date().toISOString(),
  },
]

export const mockBriefing = {
  id: 1,
  type: 'morning',
  title: '测试早报',
  content: '这是测试早报内容',
  created_at: new Date().toISOString(),
}

export const mockApiResponse = {
  success: true,
  message: '操作成功',
  data: null,
}

/**
 * 创建 mock API 函数
 */
export const createMockApi = () => ({
  getNews: vi.fn().mockResolvedValue({
    total: mockNews.length,
    items: mockNews,
    page: 1,
    page_size: 20,
  }),
  getLatestNews: vi.fn().mockResolvedValue(mockNews),
  getNewsById: vi.fn().mockResolvedValue(mockNews[0]),
  getBriefings: vi.fn().mockResolvedValue({
    total: 1,
    items: [mockBriefing],
  }),
  getLatestBriefing: vi.fn().mockResolvedValue(mockBriefing),
  generateBriefing: vi.fn().mockResolvedValue(mockApiResponse),
  getSettings: vi.fn().mockResolvedValue({
    morning_time: '07:30',
    evening_time: '20:00',
  }),
  updateSettings: vi.fn().mockResolvedValue(mockApiResponse),
})
