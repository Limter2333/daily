/**
 * NewsCard 组件测试
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '../../test/test-utils'
import NewsCard from '../NewsCard'
import type { NewsItem } from '../../types'

describe('NewsCard', () => {
  const mockNews: NewsItem = {
    id: 1,
    title: '测试新闻标题',
    summary: '这是测试新闻的摘要内容',
    content: '这是测试新闻的完整内容',
    source: '测试来源',
    source_url: 'https://source.example.com',
    url: 'https://example.com',
    category: 'tech',
    importance: 8,
    published_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
    is_sent: false,
    tags: '标签1,标签2,标签3',
  }

  it('应该渲染新闻标题', () => {
    render(<NewsCard news={mockNews} />)
    expect(screen.getByText('测试新闻标题')).toBeInTheDocument()
  })

  it('应该渲染新闻摘要', () => {
    render(<NewsCard news={mockNews} />)
    expect(screen.getByText('这是测试新闻的摘要内容')).toBeInTheDocument()
  })

  it('应该渲染新闻来源', () => {
    render(<NewsCard news={mockNews} />)
    expect(screen.getByText('测试来源')).toBeInTheDocument()
  })

  it('应该渲染分类标签', () => {
    render(<NewsCard news={mockNews} />)
    // 科技分类应该显示
    expect(screen.getByText(/科技/)).toBeInTheDocument()
  })

  it('应该渲染标签', () => {
    render(<NewsCard news={mockNews} />)
    expect(screen.getByText('标签1')).toBeInTheDocument()
    expect(screen.getByText('标签2')).toBeInTheDocument()
    expect(screen.getByText('标签3')).toBeInTheDocument()
  })

  it('应该渲染阅读原文链接', () => {
    render(<NewsCard news={mockNews} />)
    const link = screen.getByText('阅读原文')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', 'https://example.com')
    expect(link.closest('a')).toHaveAttribute('target', '_blank')
  })

  it('没有摘要时不渲染摘要区域', () => {
    const newsWithoutSummary = { ...mockNews, summary: null }
    render(<NewsCard news={newsWithoutSummary} />)
    expect(screen.queryByText('这是测试新闻的摘要内容')).not.toBeInTheDocument()
  })

  it('没有URL时不渲染链接', () => {
    const newsWithoutUrl = { ...mockNews, url: null }
    render(<NewsCard news={newsWithoutUrl} />)
    expect(screen.queryByText('阅读原文')).not.toBeInTheDocument()
  })

  it('没有标签时不渲染标签区域', () => {
    const newsWithoutTags = { ...mockNews, tags: null }
    render(<NewsCard news={newsWithoutTags} />)
    expect(screen.queryByText('标签1')).not.toBeInTheDocument()
  })

  it('应该显示重要性星星', () => {
    const { container } = render(<NewsCard news={mockNews} />)
    // importance=8 应该显示 4 颗星 (ceil(8/2)=4)
    const stars = container.querySelectorAll('.text-yellow-400')
    expect(stars.length).toBe(4)
  })

  it('重要性为10时最多显示5颗星', () => {
    const highImportanceNews = { ...mockNews, importance: 10 }
    const { container } = render(<NewsCard news={highImportanceNews} />)
    const stars = container.querySelectorAll('.text-yellow-400')
    expect(stars.length).toBe(5)
  })
})
