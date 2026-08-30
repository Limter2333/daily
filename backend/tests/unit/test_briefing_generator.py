"""
早报/晚报生成服务测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.models import NewsItem, Briefing, BriefingType, NewsCategory
from backend.services.briefing_generator import BriefingGenerator


@pytest.fixture
def mock_db():
    """Mock 数据库"""
    db = AsyncMock()
    db.get_news = AsyncMock(return_value=[])
    db.save_briefing = AsyncMock(return_value=1)
    db.get_latest_briefing = AsyncMock(return_value=None)
    return db


@pytest.fixture
def mock_analyzer():
    """Mock AI 分析器"""
    analyzer = AsyncMock()
    analyzer.generate_briefing_summary = AsyncMock(return_value="今日概览摘要")
    return analyzer


@pytest.fixture
def sample_news_list():
    """示例新闻列表"""
    return [
        NewsItem(
            id=1,
            title="财经新闻1",
            summary="财经摘要1",
            source="eastmoney",
            category=NewsCategory.FINANCE,
            importance=8,
            url="https://example.com/1"
        ),
        NewsItem(
            id=2,
            title="科技新闻1",
            summary="科技摘要1",
            source="36kr",
            category=NewsCategory.TECH,
            importance=7,
            url="https://example.com/2"
        ),
        NewsItem(
            id=3,
            title="AI新闻1",
            summary="AI摘要1",
            source="jiqizhixin",
            category=NewsCategory.AI,
            importance=9,
            url="https://example.com/3"
        ),
    ]


class TestBriefingGenerator:
    """早报/晚报生成器测试"""

    @pytest.mark.asyncio
    async def test_generate_morning_briefing_with_news(self, mock_db, mock_analyzer, sample_news_list):
        """有新闻时应该生成早报"""
        mock_db.get_news.return_value = sample_news_list

        generator = BriefingGenerator(mock_db, mock_analyzer)
        briefing = await generator.generate_morning_briefing()

        assert briefing is not None
        assert briefing.type == BriefingType.MORNING
        assert "早报" in briefing.title
        assert "财经新闻1" in briefing.content
        assert "科技新闻1" in briefing.content
        assert "AI新闻1" in briefing.content
        assert briefing.news_ids is not None
        assert mock_db.save_briefing.called

    @pytest.mark.asyncio
    async def test_generate_morning_briefing_without_news(self, mock_db, mock_analyzer):
        """没有新闻时应该返回空早报"""
        mock_db.get_news.return_value = []

        generator = BriefingGenerator(mock_db, mock_analyzer)
        briefing = await generator.generate_morning_briefing()

        assert briefing is not None
        assert briefing.type == BriefingType.MORNING
        assert "暂无新闻" in briefing.content
        assert briefing.news_ids == "[]"

    @pytest.mark.asyncio
    async def test_generate_evening_briefing_with_news(self, mock_db, mock_analyzer, sample_news_list):
        """有新闻时应该生成晚报"""
        mock_db.get_news.return_value = sample_news_list

        generator = BriefingGenerator(mock_db, mock_analyzer)
        briefing = await generator.generate_evening_briefing()

        assert briefing is not None
        assert briefing.type == BriefingType.EVENING
        assert "晚报" in briefing.title
        assert "财经新闻1" in briefing.content
        assert mock_db.save_briefing.called

    @pytest.mark.asyncio
    async def test_generate_evening_briefing_without_news(self, mock_db, mock_analyzer):
        """没有新闻时应该返回空晚报"""
        mock_db.get_news.return_value = []

        generator = BriefingGenerator(mock_db, mock_analyzer)
        briefing = await generator.generate_evening_briefing()

        assert briefing is not None
        assert briefing.type == BriefingType.EVENING
        assert "暂无新闻" in briefing.content

    @pytest.mark.asyncio
    async def test_briefing_includes_summary(self, mock_db, mock_analyzer, sample_news_list):
        """早报应该包含 AI 生成的摘要"""
        mock_db.get_news.return_value = sample_news_list
        mock_analyzer.generate_briefing_summary.return_value = "这是今日概览"

        generator = BriefingGenerator(mock_db, mock_analyzer)
        briefing = await generator.generate_morning_briefing()

        assert "今日概览" in briefing.content

    @pytest.mark.asyncio
    async def test_briefing_without_summary(self, mock_db, mock_analyzer, sample_news_list):
        """没有摘要时应该正常生成"""
        mock_db.get_news.return_value = sample_news_list
        mock_analyzer.generate_briefing_summary.return_value = ""

        generator = BriefingGenerator(mock_db, mock_analyzer)
        briefing = await generator.generate_morning_briefing()

        assert briefing is not None
        assert "今日概览" not in briefing.content

    @pytest.mark.asyncio
    async def test_format_briefing_groups_by_category(self, mock_db, mock_analyzer, sample_news_list):
        """应该按类别分组显示"""
        generator = BriefingGenerator(mock_db, mock_analyzer)
        content = await generator._format_briefing(sample_news_list, "morning")

        assert "财经" in content
        assert "科技" in content
        assert "AI/机器人" in content

    @pytest.mark.asyncio
    async def test_format_briefing_morning_greeting(self, mock_db, mock_analyzer, sample_news_list):
        """早报应该有早上好问候"""
        generator = BriefingGenerator(mock_db, mock_analyzer)
        content = await generator._format_briefing(sample_news_list, "morning")

        assert "早上好" in content

    @pytest.mark.asyncio
    async def test_format_briefing_evening_greeting(self, mock_db, mock_analyzer, sample_news_list):
        """晚报应该有晚上好问候"""
        generator = BriefingGenerator(mock_db, mock_analyzer)
        content = await generator._format_briefing(sample_news_list, "evening")

        assert "晚上好" in content

    @pytest.mark.asyncio
    async def test_format_briefing_includes_stats(self, mock_db, mock_analyzer, sample_news_list):
        """应该包含统计信息"""
        generator = BriefingGenerator(mock_db, mock_analyzer)
        content = await generator._format_briefing(sample_news_list, "morning")

        assert "共 3 条新闻" in content
        assert "分类统计" in content

    @pytest.mark.asyncio
    async def test_format_briefing_includes_source(self, mock_db, mock_analyzer, sample_news_list):
        """应该包含新闻来源"""
        generator = BriefingGenerator(mock_db, mock_analyzer)
        content = await generator._format_briefing(sample_news_list, "morning")

        assert "eastmoney" in content
        assert "36kr" in content

    @pytest.mark.asyncio
    async def test_format_briefing_includes_urls(self, mock_db, mock_analyzer, sample_news_list):
        """应该包含新闻链接"""
        generator = BriefingGenerator(mock_db, mock_analyzer)
        content = await generator._format_briefing(sample_news_list, "morning")

        assert "https://example.com/1" in content
        assert "https://example.com/2" in content

    @pytest.mark.asyncio
    async def test_format_briefing_limits_per_category(self, mock_db, mock_analyzer):
        """每个类别最多显示5条"""
        # 创建6条同类新闻
        news_list = [
            NewsItem(
                id=i,
                title=f"新闻{i}",
                source="test",
                category=NewsCategory.TECH,
                importance=5
            )
            for i in range(6)
        ]

        generator = BriefingGenerator(mock_db, mock_analyzer)
        content = await generator._format_briefing(news_list, "morning")

        # 只显示前5条（索引0-4）
        assert "新闻0" in content
        assert "新闻4" in content
        assert "新闻5" not in content

    def test_empty_briefing_morning(self, mock_db, mock_analyzer):
        """空早报应该有正确的类型"""
        generator = BriefingGenerator(mock_db, mock_analyzer)
        briefing = generator._empty_briefing(BriefingType.MORNING)

        assert briefing.type == BriefingType.MORNING
        assert "早报" in briefing.title
        assert "暂无新闻" in briefing.content
        assert briefing.news_ids == "[]"
        assert briefing.is_sent is False

    def test_empty_briefing_evening(self, mock_db, mock_analyzer):
        """空晚报应该有正确的类型"""
        generator = BriefingGenerator(mock_db, mock_analyzer)
        briefing = generator._empty_briefing(BriefingType.EVENING)

        assert briefing.type == BriefingType.EVENING
        assert "晚报" in briefing.title

    @pytest.mark.asyncio
    async def test_get_latest_briefing(self, mock_db, mock_analyzer):
        """获取最新早报应该调用数据库"""
        expected = Briefing(
            type=BriefingType.MORNING,
            title="测试早报",
            content="内容"
        )
        mock_db.get_latest_briefing.return_value = expected

        generator = BriefingGenerator(mock_db, mock_analyzer)
        result = await generator.get_latest_briefing("morning")

        assert result == expected
        mock_db.get_latest_briefing.assert_called_once_with("morning")

    @pytest.mark.asyncio
    async def test_get_latest_briefing_none(self, mock_db, mock_analyzer):
        """没有早报时应该返回 None"""
        mock_db.get_latest_briefing.return_value = None

        generator = BriefingGenerator(mock_db, mock_analyzer)
        result = await generator.get_latest_briefing()

        assert result is None

    @pytest.mark.asyncio
    async def test_briefing_news_ids_format(self, mock_db, mock_analyzer, sample_news_list):
        """新闻ID应该是JSON格式"""
        mock_db.get_news.return_value = sample_news_list

        generator = BriefingGenerator(mock_db, mock_analyzer)
        briefing = await generator.generate_morning_briefing()

        import json
        news_ids = json.loads(briefing.news_ids)
        assert news_ids == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_briefing_not_sent_initially(self, mock_db, mock_analyzer, sample_news_list):
        """新生成的早报应该是未发送状态"""
        mock_db.get_news.return_value = sample_news_list

        generator = BriefingGenerator(mock_db, mock_analyzer)
        briefing = await generator.generate_morning_briefing()

        assert briefing.is_sent is False
