"""
新闻聚合服务测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.models import NewsItem, NewsCategory
from backend.services.news_aggregator import NewsAggregator


@pytest.fixture
def mock_db():
    """Mock 数据库"""
    db = AsyncMock()
    db.save_news_batch = AsyncMock(return_value=5)
    db.get_latest_news = AsyncMock(return_value=[])
    db.get_news = AsyncMock(return_value=[])
    return db


@pytest.fixture
def mock_analyzer():
    """Mock AI 分析器"""
    analyzer = AsyncMock()

    async def mock_analyze_batch(news_list):
        for news in news_list:
            news.importance = 7
            news.summary = news.summary or "AI摘要"
        return news_list

    analyzer.analyze_news_batch = AsyncMock(side_effect=mock_analyze_batch)
    return analyzer


@pytest.fixture
def sample_news():
    """示例新闻"""
    return [
        NewsItem(title="财经新闻", source="eastmoney", category=NewsCategory.FINANCE),
        NewsItem(title="科技新闻", source="36kr", category=NewsCategory.TECH),
        NewsItem(title="AI新闻", source="jiqizhixin", category=NewsCategory.AI),
    ]


class TestNewsAggregator:
    """新闻聚合器测试"""

    def test_init(self, mock_db, mock_analyzer):
        """初始化应该设置正确的属性"""
        aggregator = NewsAggregator(mock_db, mock_analyzer)

        assert aggregator.db == mock_db
        assert aggregator.analyzer == mock_analyzer
        assert len(aggregator.sources) == 4

    @pytest.mark.asyncio
    async def test_aggregate_all_success(self, mock_db, mock_analyzer, sample_news):
        """成功聚合新闻"""
        # Mock 所有新闻源
        mock_sources = []
        for i in range(4):
            source = AsyncMock()
            source.fetch = AsyncMock(return_value=[sample_news[i % 3]])
            mock_sources.append(source)

        aggregator = NewsAggregator(mock_db, mock_analyzer)
        aggregator.sources = mock_sources

        result = await aggregator.aggregate_all()

        assert len(result) > 0
        assert mock_db.save_news_batch.called
        assert mock_analyzer.analyze_news_batch.called

    @pytest.mark.asyncio
    async def test_aggregate_all_handles_source_error(self, mock_db, mock_analyzer):
        """新闻源失败时应该继续处理其他源"""
        # 一个源失败，一个源成功
        failing_source = AsyncMock()
        failing_source.fetch = AsyncMock(side_effect=Exception("网络错误"))

        success_source = AsyncMock()
        success_source.fetch = AsyncMock(return_value=[
            NewsItem(title="测试新闻", source="test", category=NewsCategory.TECH)
        ])

        aggregator = NewsAggregator(mock_db, mock_analyzer)
        aggregator.sources = [failing_source, success_source]

        result = await aggregator.aggregate_all()

        assert len(result) > 0
        assert mock_db.save_news_batch.called

    @pytest.mark.asyncio
    async def test_aggregate_all_deduplicates(self, mock_db, mock_analyzer):
        """应该去重"""
        # 两个源返回相同标题的新闻
        source1 = AsyncMock()
        source1.fetch = AsyncMock(return_value=[
            NewsItem(title="重复新闻", source="source1", category=NewsCategory.TECH)
        ])

        source2 = AsyncMock()
        source2.fetch = AsyncMock(return_value=[
            NewsItem(title="重复新闻", source="source2", category=NewsCategory.TECH)
        ])

        aggregator = NewsAggregator(mock_db, mock_analyzer)
        aggregator.sources = [source1, source2]

        result = await aggregator.aggregate_all()

        # 去重后应该只有一条
        titles = [n.title for n in result]
        assert titles.count("重复新闻") == 1

    @pytest.mark.asyncio
    async def test_aggregate_all_empty_sources(self, mock_db, mock_analyzer):
        """所有源都返回空时应该返回空列表"""
        empty_source = AsyncMock()
        empty_source.fetch = AsyncMock(return_value=[])

        aggregator = NewsAggregator(mock_db, mock_analyzer)
        aggregator.sources = [empty_source, empty_source]

        result = await aggregator.aggregate_all()

        assert result == []

    def test_deduplicate(self, mock_db, mock_analyzer):
        """去重应该基于标题"""
        aggregator = NewsAggregator(mock_db, mock_analyzer)

        news_list = [
            NewsItem(title="新闻A", source="source1"),
            NewsItem(title="新闻B", source="source1"),
            NewsItem(title="新闻A", source="source2"),  # 重复
            NewsItem(title="新闻C", source="source1"),
        ]

        result = aggregator._deduplicate(news_list)

        assert len(result) == 3
        titles = [n.title for n in result]
        assert "新闻A" in titles
        assert "新闻B" in titles
        assert "新闻C" in titles

    def test_deduplicate_case_insensitive(self, mock_db, mock_analyzer):
        """去重应该不区分大小写"""
        aggregator = NewsAggregator(mock_db, mock_analyzer)

        news_list = [
            NewsItem(title="News A", source="source1"),
            NewsItem(title="news a", source="source2"),  # 重复（不同大小写）
        ]

        result = aggregator._deduplicate(news_list)

        assert len(result) == 1

    def test_deduplicate_strips_whitespace(self, mock_db, mock_analyzer):
        """去重应该忽略首尾空格"""
        aggregator = NewsAggregator(mock_db, mock_analyzer)

        news_list = [
            NewsItem(title="  新闻A  ", source="source1"),
            NewsItem(title="新闻A", source="source2"),  # 重复
        ]

        result = aggregator._deduplicate(news_list)

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_categorized_news(self, mock_db, mock_analyzer, sample_news):
        """获取分类新闻应该按类别分组"""
        mock_db.get_latest_news.return_value = sample_news

        aggregator = NewsAggregator(mock_db, mock_analyzer)
        result = await aggregator.get_categorized_news(limit_per_category=5)

        assert "finance" in result
        assert "tech" in result
        assert "ai" in result
        assert len(result["finance"]["items"]) == 1
        assert len(result["tech"]["items"]) == 1
        assert len(result["ai"]["items"]) == 1

    @pytest.mark.asyncio
    async def test_get_categorized_news_limits_items(self, mock_db, mock_analyzer):
        """每个类别应该限制数量"""
        # 创建多条同类新闻
        news_list = [
            NewsItem(title=f"科技新闻{i}", source="test", category=NewsCategory.TECH)
            for i in range(10)
        ]
        mock_db.get_latest_news.return_value = news_list

        aggregator = NewsAggregator(mock_db, mock_analyzer)
        result = await aggregator.get_categorized_news(limit_per_category=3)

        assert len(result["tech"]["items"]) == 3

    @pytest.mark.asyncio
    async def test_get_categorized_news_empty(self, mock_db, mock_analyzer):
        """没有新闻时应该返回空字典"""
        mock_db.get_latest_news.return_value = []

        aggregator = NewsAggregator(mock_db, mock_analyzer)
        result = await aggregator.get_categorized_news()

        assert result == {}

    @pytest.mark.asyncio
    async def test_get_top_news(self, mock_db, mock_analyzer, sample_news):
        """获取重要新闻应该调用数据库"""
        mock_db.get_news.return_value = sample_news

        aggregator = NewsAggregator(mock_db, mock_analyzer)
        result = await aggregator.get_top_news(limit=10)

        assert len(result) == 3
        mock_db.get_news.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_news_by_category(self, mock_db, mock_analyzer, sample_news):
        """按类别获取新闻应该调用数据库"""
        mock_db.get_news.return_value = [sample_news[0]]

        aggregator = NewsAggregator(mock_db, mock_analyzer)
        result = await aggregator.get_news_by_category("finance", limit=5)

        assert len(result) == 1
        mock_db.get_news.assert_called_once()
