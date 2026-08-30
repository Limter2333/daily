"""
数据模型单元测试
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from backend.models import (
    NewsItem, Briefing, Settings,
    NewsCategory, BriefingType,
    NewsListResponse, BriefingListResponse, ApiResponse
)


class TestNewsCategory:
    """新闻类别枚举测试"""

    def test_all_categories_exist(self):
        """所有类别都应该存在"""
        assert NewsCategory.FINANCE == "finance"
        assert NewsCategory.TECH == "tech"
        assert NewsCategory.SEMICONDUCTOR == "semiconductor"
        assert NewsCategory.AI == "ai"
        assert NewsCategory.CONSUMER == "consumer"
        assert NewsCategory.OTHER == "other"

    def test_category_from_string(self):
        """可以从字符串创建类别"""
        assert NewsCategory("finance") == NewsCategory.FINANCE
        assert NewsCategory("tech") == NewsCategory.TECH


class TestNewsItem:
    """新闻条目模型测试"""

    def test_create_news_with_required_fields(self):
        """必填字段应该能创建新闻"""
        news = NewsItem(
            title="测试标题",
            source="test_source"
        )
        assert news.title == "测试标题"
        assert news.source == "test_source"
        assert news.category == NewsCategory.OTHER  # 默认值
        assert news.importance == 5  # 默认值
        assert news.is_sent is False  # 默认值

    def test_create_news_with_all_fields(self):
        """所有字段应该能创建新闻"""
        now = datetime.now()
        news = NewsItem(
            title="完整标题",
            summary="摘要",
            content="内容",
            source="test_source",
            source_url="https://example.com",
            url="https://example.com/news",
            category=NewsCategory.TECH,
            importance=8,
            published_at=now,
            created_at=now,
            is_sent=True,
            tags="tag1,tag2"
        )
        assert news.title == "完整标题"
        assert news.summary == "摘要"
        assert news.content == "内容"
        assert news.category == NewsCategory.TECH
        assert news.importance == 8
        assert news.is_sent is True
        assert news.tags == "tag1,tag2"

    def test_news_missing_title_raises_error(self):
        """缺少标题应该报错"""
        with pytest.raises(ValidationError):
            NewsItem(source="test_source")

    def test_news_missing_source_raises_error(self):
        """缺少来源应该报错"""
        with pytest.raises(ValidationError):
            NewsItem(title="测试标题")

    def test_importance_validation(self):
        """重要性评分应该在 1-10 之间"""
        # 有效值
        news = NewsItem(title="测试", source="test", importance=1)
        assert news.importance == 1

        news = NewsItem(title="测试", source="test", importance=10)
        assert news.importance == 10

        # 无效值
        with pytest.raises(ValidationError):
            NewsItem(title="测试", source="test", importance=0)

        with pytest.raises(ValidationError):
            NewsItem(title="测试", source="test", importance=11)

    def test_default_created_at(self):
        """默认创建时间应该自动设置"""
        news = NewsItem(title="测试", source="test")
        assert news.created_at is not None
        assert isinstance(news.created_at, datetime)

    def test_news_to_dict(self):
        """新闻应该能转换为字典"""
        news = NewsItem(
            title="测试",
            source="test",
            category=NewsCategory.TECH
        )
        data = news.model_dump()
        assert data["title"] == "测试"
        assert data["source"] == "test"
        assert data["category"] == "tech"


class TestBriefing:
    """早晚报模型测试"""

    def test_create_morning_briefing(self):
        """应该能创建早报"""
        briefing = Briefing(
            type=BriefingType.MORNING,
            title="早报标题",
            content="早报内容"
        )
        assert briefing.type == BriefingType.MORNING
        assert briefing.title == "早报标题"
        assert briefing.content == "早报内容"
        assert briefing.is_sent is False

    def test_create_evening_briefing(self):
        """应该能创建晚报"""
        briefing = Briefing(
            type=BriefingType.EVENING,
            title="晚报标题",
            content="晚报内容"
        )
        assert briefing.type == BriefingType.EVENING

    def test_briefing_missing_type_raises_error(self):
        """缺少类型应该报错"""
        with pytest.raises(ValidationError):
            Briefing(title="标题", content="内容")

    def test_briefing_missing_title_raises_error(self):
        """缺少标题应该报错"""
        with pytest.raises(ValidationError):
            Briefing(type=BriefingType.MORNING, content="内容")

    def test_briefing_with_news_ids(self):
        """应该能关联新闻ID"""
        briefing = Briefing(
            type=BriefingType.MORNING,
            title="早报",
            content="内容",
            news_ids="[1, 2, 3]"
        )
        assert briefing.news_ids == "[1, 2, 3]"


class TestSettings:
    """设置模型测试"""

    def test_default_settings(self):
        """默认设置应该有正确的值"""
        settings = Settings()
        assert settings.morning_time == "07:30"
        assert settings.evening_time == "20:00"
        assert settings.email_enabled is False
        assert settings.push_enabled is False

    def test_custom_settings(self):
        """应该能自定义设置"""
        settings = Settings(
            morning_time="08:00",
            evening_time="21:00",
            email_enabled=True,
        )
        assert settings.morning_time == "08:00"
        assert settings.evening_time == "21:00"
        assert settings.email_enabled is True


class TestResponseModels:
    """响应模型测试"""

    def test_news_list_response(self):
        """新闻列表响应应该包含必要字段"""
        response = NewsListResponse(
            total=10,
            items=[],
            page=1,
            page_size=20
        )
        assert response.total == 10
        assert response.items == []
        assert response.page == 1
        assert response.page_size == 20

    def test_briefing_list_response(self):
        """早晚报列表响应应该包含必要字段"""
        response = BriefingListResponse(
            total=5,
            items=[]
        )
        assert response.total == 5
        assert response.items == []

    def test_api_response_success(self):
        """成功响应应该有默认值"""
        response = ApiResponse()
        assert response.success is True
        assert response.message == ""
        assert response.data is None

    def test_api_response_with_data(self):
        """响应可以包含数据"""
        response = ApiResponse(
            success=True,
            message="操作成功",
            data={"id": 1}
        )
        assert response.data == {"id": 1}
