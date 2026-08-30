"""
新闻源单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.models import NewsItem, NewsCategory
from backend.sources.base import BaseNewsSource


class TestBaseNewsSource:
    """新闻源基类测试"""

    def test_create_news(self):
        """_create_news 应该创建正确的 NewsItem"""
        # 创建一个具体的子类来测试
        class TestSource(BaseNewsSource):
            async def _fetch_news(self):
                return []

            def get_source_name(self):
                return "test_source"

            def get_category(self):
                return NewsCategory.TECH

        source = TestSource()
        news = source._create_news(
            title="测试标题",
            summary="测试摘要",
            url="https://example.com",
            importance=8,
            tags="test,demo"
        )

        assert isinstance(news, NewsItem)
        assert news.title == "测试标题"
        assert news.summary == "测试摘要"
        assert news.source == "test_source"
        assert news.category == NewsCategory.TECH
        assert news.importance == 8
        assert news.tags == "test,demo"
        assert news.url == "https://example.com"
        assert news.is_sent is False

    def test_create_news_strips_title(self):
        """标题应该去除首尾空格"""
        class TestSource(BaseNewsSource):
            async def _fetch_news(self):
                return []

            def get_source_name(self):
                return "test"

            def get_category(self):
                return NewsCategory.OTHER

        source = TestSource()
        news = source._create_news(title="  有空格的标题  ")
        assert news.title == "有空格的标题"

    def test_create_news_default_values(self):
        """应该有正确的默认值"""
        class TestSource(BaseNewsSource):
            async def _fetch_news(self):
                return []

            def get_source_name(self):
                return "test"

            def get_category(self):
                return NewsCategory.OTHER

        source = TestSource()
        news = source._create_news(title="测试")

        assert news.summary is None
        assert news.content is None
        assert news.url is None
        assert news.importance == 5
        assert news.tags is None
        assert news.published_at is not None
        assert news.created_at is not None

    @pytest.mark.asyncio
    async def test_fetch_returns_empty_on_error(self):
        """获取失败时应该返回空列表"""
        class TestSource(BaseNewsSource):
            async def _fetch_news(self):
                raise Exception("网络错误")

            def get_source_name(self):
                return "test"

            def get_category(self):
                return NewsCategory.OTHER

        source = TestSource()
        result = await source.fetch()
        assert result == []

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """应该支持 async context manager"""
        class TestSource(BaseNewsSource):
            async def _fetch_news(self):
                return []

            def get_source_name(self):
                return "test"

            def get_category(self):
                return NewsCategory.OTHER

        source = TestSource()
        async with source:
            assert source.client is not None

        # 退出后 client 应该被关闭
        # httpx client 在 close 后无法直接检查，但不会有异常

    @pytest.mark.asyncio
    async def test_get_request_success(self):
        """_get 成功时应该返回响应"""
        class TestSource(BaseNewsSource):
            async def _fetch_news(self):
                return []

            def get_source_name(self):
                return "test"

            def get_category(self):
                return NewsCategory.OTHER

        source = TestSource()

        # 创建 mock client
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        # 直接设置 client，不通过 context manager
        source.client = mock_client
        response = await source._get("https://example.com")

        assert response == mock_response
        mock_client.get.assert_called_once_with("https://example.com")

    @pytest.mark.asyncio
    async def test_get_returns_none_on_error(self):
        """请求失败时应该返回 None"""
        class TestSource(BaseNewsSource):
            async def _fetch_news(self):
                return []

            def get_source_name(self):
                return "test"

            def get_category(self):
                return NewsCategory.OTHER

        source = TestSource()

        # 创建 mock client，让它抛出异常
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("网络错误")

        source.client = mock_client
        response = await source._get("https://example.com")

        assert response is None

    @pytest.mark.asyncio
    async def test_post_request_success(self):
        """_post 成功时应该返回响应"""
        class TestSource(BaseNewsSource):
            async def _fetch_news(self):
                return []

            def get_source_name(self):
                return "test"

            def get_category(self):
                return NewsCategory.OTHER

        source = TestSource()

        # 创建 mock client
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        source.client = mock_client
        response = await source._post(
            "https://example.com",
            json={"key": "value"}
        )

        assert response == mock_response
        mock_client.post.assert_called_once_with(
            "https://example.com",
            json={"key": "value"}
        )


class TestFinanceNewsSource:
    """财经新闻源测试"""

    def test_source_name(self):
        """应该返回正确的源名称"""
        from backend.sources.finance import FinanceNewsSource
        source = FinanceNewsSource()
        assert source.get_source_name() == "财经"

    def test_category(self):
        """应该返回财经类别"""
        from backend.sources.finance import FinanceNewsSource
        source = FinanceNewsSource()
        assert source.get_category() == NewsCategory.FINANCE


class TestTechNewsSource:
    """科技新闻源测试"""

    def test_source_name(self):
        """应该返回正确的源名称"""
        from backend.sources.tech import TechNewsSource
        source = TechNewsSource()
        assert source.get_source_name() == "科技"

    def test_category(self):
        """应该返回科技类别"""
        from backend.sources.tech import TechNewsSource
        source = TechNewsSource()
        assert source.get_category() == NewsCategory.TECH


class TestAIRoboticsNewsSource:
    """AI/机器人新闻源测试"""

    def test_source_name(self):
        """应该返回正确的源名称"""
        from backend.sources.ai_robotics import AIRoboticsNewsSource
        source = AIRoboticsNewsSource()
        assert source.get_source_name() == "AI/机器人"

    def test_category(self):
        """应该返回AI类别"""
        from backend.sources.ai_robotics import AIRoboticsNewsSource
        source = AIRoboticsNewsSource()
        assert source.get_category() == NewsCategory.AI


class TestGeneralNewsSource:
    """综合新闻源测试"""

    def test_source_name(self):
        """应该返回正确的源名称"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()
        assert source.get_source_name() == "综合"

    def test_category(self):
        """应该返回其他类别"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()
        assert source.get_category() == NewsCategory.OTHER

    @pytest.mark.asyncio
    async def test_fetch_zhihu_success(self):
        """测试知乎热榜获取成功"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {
                    "target": {"id": "123", "title": "知乎热榜话题1"},
                    "detail_text": "1000万热度"
                },
                {
                    "target": {"id": "456", "title": "知乎热榜话题2"},
                    "detail_text": "500万热度"
                }
            ]
        }

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_zhihu()
        assert len(result) == 2
        assert result[0].title == "知乎热榜话题1"
        assert result[0].source == "知乎热榜"
        assert "知乎" in result[0].tags

    @pytest.mark.asyncio
    async def test_fetch_zhihu_empty_response(self):
        """测试知乎热榜空响应"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()

        source.client = AsyncMock()
        source.client.get.return_value = None

        result = await source._fetch_zhihu()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_zhihu_exception(self):
        """测试知乎热榜异常处理"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()

        source.client = AsyncMock()
        source.client.get.side_effect = Exception("网络错误")

        result = await source._fetch_zhihu()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_toutiao_success(self):
        """测试今日头条热榜获取成功"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"Title": "头条新闻1", "HotValue": "1000万", "Url": "https://example.com/1"},
                {"Title": "头条新闻2", "HotValue": "500万", "Url": "https://example.com/2"}
            ]
        }

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_toutiao()
        assert len(result) == 2
        assert result[0].title == "头条新闻1"
        assert result[0].source == "今日头条"
        assert "今日头条" in result[0].tags

    @pytest.mark.asyncio
    async def test_fetch_toutiao_empty(self):
        """测试今日头条空数据"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_toutiao()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_v2ex_success(self):
        """测试 V2EX 热门话题获取成功"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"title": "V2EX话题1", "url": "https://v2ex.com/t/1", "node": {"title": "Python"}},
            {"title": "V2EX话题2", "url": "https://v2ex.com/t/2", "node": {"title": "Java"}}
        ]

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_v2ex()
        assert len(result) == 2
        assert result[0].title == "V2EX话题1"
        assert result[0].source == "V2EX"
        assert "Python" in result[0].tags

    @pytest.mark.asyncio
    async def test_fetch_v2ex_exception(self):
        """测试 V2EX 异常处理"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()

        source.client = AsyncMock()
        source.client.get.side_effect = Exception("API错误")

        result = await source._fetch_v2ex()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_hacker_news_success(self):
        """测试 Hacker News 获取成功"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()

        # 第一次调用获取 story IDs
        mock_ids_response = MagicMock()
        mock_ids_response.json.return_value = [1, 2]

        # 第二次调用获取 story 详情
        mock_story1 = MagicMock()
        mock_story1.json.return_value = {"title": "HN Story 1", "url": "https://example.com/1"}
        mock_story2 = MagicMock()
        mock_story2.json.return_value = {"title": "HN Story 2", "url": "https://example.com/2"}

        source.client = AsyncMock()
        source.client.get.side_effect = [mock_ids_response, mock_story1, mock_story2]

        result = await source._fetch_hacker_news()
        assert len(result) == 2
        assert result[0].title == "HN Story 1"
        assert result[0].source == "Hacker News"
        assert "Hacker News" in result[0].tags

    @pytest.mark.asyncio
    async def test_fetch_hacker_news_empty_ids(self):
        """测试 Hacker News 空 ID 列表"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = []

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_hacker_news()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_hacker_news_story_fetch_fails(self):
        """测试 Hacker News 获取单个故事失败"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()

        mock_ids_response = MagicMock()
        mock_ids_response.json.return_value = [1]

        source.client = AsyncMock()
        source.client.get.side_effect = [mock_ids_response, None]

        result = await source._fetch_hacker_news()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_news_integration(self):
        """测试综合新闻源完整获取流程"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()

        # Mock 所有子方法
        mock_zhihu = [MagicMock(title="知乎新闻")]
        mock_toutiao = [MagicMock(title="头条新闻")]
        mock_v2ex = [MagicMock(title="V2EX新闻")]
        mock_hn = [MagicMock(title="HN新闻")]

        with patch.object(source, '_fetch_zhihu', return_value=mock_zhihu), \
             patch.object(source, '_fetch_toutiao', return_value=mock_toutiao), \
             patch.object(source, '_fetch_v2ex', return_value=mock_v2ex), \
             patch.object(source, '_fetch_hacker_news', return_value=mock_hn):

            result = await source._fetch_news()
            assert len(result) == 4

    @pytest.mark.asyncio
    async def test_fetch_news_with_exceptions(self):
        """测试综合新闻源部分失败"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()

        mock_zhihu = [MagicMock(title="知乎新闻")]
        mock_v2ex = [MagicMock(title="V2EX新闻")]

        with patch.object(source, '_fetch_zhihu', return_value=mock_zhihu), \
             patch.object(source, '_fetch_toutiao', side_effect=Exception("失败")), \
             patch.object(source, '_fetch_v2ex', return_value=mock_v2ex), \
             patch.object(source, '_fetch_hacker_news', return_value=[]):

            result = await source._fetch_news()
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_fetch_news_limits_to_10(self):
        """测试综合新闻源限制返回10条"""
        from backend.sources.general import GeneralNewsSource
        source = GeneralNewsSource()

        # 创建超过10条新闻
        mock_news = [MagicMock(title=f"新闻{i}") for i in range(15)]

        with patch.object(source, '_fetch_zhihu', return_value=mock_news[:5]), \
             patch.object(source, '_fetch_toutiao', return_value=mock_news[5:10]), \
             patch.object(source, '_fetch_v2ex', return_value=mock_news[10:13]), \
             patch.object(source, '_fetch_hacker_news', return_value=mock_news[13:]):

            result = await source._fetch_news()
            assert len(result) == 10


class TestFinanceNewsSourceExtended:
    """财经新闻源扩展测试"""

    @pytest.mark.asyncio
    async def test_fetch_eastmoney_success(self):
        """测试东方财富获取成功"""
        from backend.sources.finance import FinanceNewsSource
        source = FinanceNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "list": [
                    {"title": "财经新闻1", "digest": "摘要1", "url": "https://example.com/1"},
                    {"title": "财经新闻2", "digest": "摘要2", "url": "https://example.com/2"}
                ]
            }
        }

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_eastmoney()
        assert len(result) == 2
        assert result[0].title == "财经新闻1"
        assert result[0].source == "东方财富"
        assert "东方财富" in result[0].tags

    @pytest.mark.asyncio
    async def test_fetch_eastmoney_empty(self):
        """测试东方财富空响应"""
        from backend.sources.finance import FinanceNewsSource
        source = FinanceNewsSource()

        source.client = AsyncMock()
        source.client.get.return_value = None

        result = await source._fetch_eastmoney()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_eastmoney_no_title(self):
        """测试东方财富无标题新闻"""
        from backend.sources.finance import FinanceNewsSource
        source = FinanceNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "list": [
                    {"title": "", "digest": "摘要", "url": "https://example.com"},
                    {"title": "有效标题", "digest": "摘要", "url": "https://example.com/2"}
                ]
            }
        }

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_eastmoney()
        assert len(result) == 1
        assert result[0].title == "有效标题"

    @pytest.mark.asyncio
    async def test_fetch_sina_finance_success(self):
        """测试新浪财经获取成功"""
        from backend.sources.finance import FinanceNewsSource
        source = FinanceNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {
                "data": [
                    {"title": "新浪新闻1", "summary": "摘要1", "url": "https://example.com/1"},
                    {"title": "新浪新闻2", "summary": "摘要2", "url": "https://example.com/2"}
                ]
            }
        }

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_sina_finance()
        assert len(result) == 2
        assert result[0].title == "新浪新闻1"
        assert result[0].source == "新浪财经"
        assert "新浪财经" in result[0].tags

    @pytest.mark.asyncio
    async def test_fetch_sina_finance_exception(self):
        """测试新浪财经异常处理"""
        from backend.sources.finance import FinanceNewsSource
        source = FinanceNewsSource()

        source.client = AsyncMock()
        source.client.get.side_effect = Exception("API错误")

        result = await source._fetch_sina_finance()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_wallstreetcn_success(self):
        """测试华尔街见闻获取成功"""
        from backend.sources.finance import FinanceNewsSource
        source = FinanceNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "items": [
                    {"title": "华尔街新闻1", "content_text": "内容1", "uri": "/article/1"},
                    {"title": "华尔街新闻2", "content_text": "内容2", "uri": "/article/2"}
                ]
            }
        }

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_wallstreetcn()
        assert len(result) == 2
        assert result[0].title == "华尔街新闻1"
        assert result[0].source == "华尔街见闻"
        assert "华尔街见闻" in result[0].tags
        assert "https://wallstcn.com/article/1" == result[0].url

    @pytest.mark.asyncio
    async def test_fetch_wallstreetcn_no_uri(self):
        """测试华尔街见闻无 URI"""
        from backend.sources.finance import FinanceNewsSource
        source = FinanceNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "items": [
                    {"title": "华尔街新闻1", "content_text": "内容1", "uri": ""}
                ]
            }
        }

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_wallstreetcn()
        assert len(result) == 1
        assert result[0].url is None

    @pytest.mark.asyncio
    async def test_fetch_news_integration(self):
        """测试财经新闻源完整获取流程"""
        from backend.sources.finance import FinanceNewsSource
        source = FinanceNewsSource()

        mock_eastmoney = [MagicMock(title="东方财富新闻")]
        mock_sina = [MagicMock(title="新浪新闻")]
        mock_wallstreet = [MagicMock(title="华尔街新闻")]

        with patch.object(source, '_fetch_eastmoney', return_value=mock_eastmoney), \
             patch.object(source, '_fetch_sina_finance', return_value=mock_sina), \
             patch.object(source, '_fetch_wallstreetcn', return_value=mock_wallstreet):

            result = await source._fetch_news()
            assert len(result) == 3

    @pytest.mark.asyncio
    async def test_fetch_news_with_exceptions(self):
        """测试财经新闻源部分失败"""
        from backend.sources.finance import FinanceNewsSource
        source = FinanceNewsSource()

        mock_eastmoney = [MagicMock(title="东方财富新闻")]

        with patch.object(source, '_fetch_eastmoney', return_value=mock_eastmoney), \
             patch.object(source, '_fetch_sina_finance', side_effect=Exception("失败")), \
             patch.object(source, '_fetch_wallstreetcn', return_value=[]):

            result = await source._fetch_news()
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_news_limits_to_10(self):
        """测试财经新闻源限制返回10条"""
        from backend.sources.finance import FinanceNewsSource
        source = FinanceNewsSource()

        mock_news = [MagicMock(title=f"新闻{i}") for i in range(15)]

        with patch.object(source, '_fetch_eastmoney', return_value=mock_news[:5]), \
             patch.object(source, '_fetch_sina_finance', return_value=mock_news[5:10]), \
             patch.object(source, '_fetch_wallstreetcn', return_value=mock_news[10:]):

            result = await source._fetch_news()
            assert len(result) == 10


class TestTechNewsSourceExtended:
    """科技新闻源扩展测试"""

    @pytest.mark.asyncio
    async def test_fetch_36kr_success(self):
        """测试36氪获取成功"""
        from backend.sources.tech import TechNewsSource
        source = TechNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "items": [
                    {"title": "36氪新闻1", "description": "描述1", "id": "1001"},
                    {"title": "36氪新闻2", "description": "描述2", "id": "1002"}
                ]
            }
        }

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_36kr()
        assert len(result) == 2
        assert result[0].title == "36氪新闻1"
        assert result[0].source == "36氪"
        assert "36氪" in result[0].tags
        assert "https://36kr.com/newsflashes/1001" == result[0].url

    @pytest.mark.asyncio
    async def test_fetch_36kr_empty(self):
        """测试36氪空响应"""
        from backend.sources.tech import TechNewsSource
        source = TechNewsSource()

        source.client = AsyncMock()
        source.client.get.return_value = None

        result = await source._fetch_36kr()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_36kr_no_id(self):
        """测试36氪无 ID"""
        from backend.sources.tech import TechNewsSource
        source = TechNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "items": [
                    {"title": "36氪新闻1", "description": "描述1", "id": ""}
                ]
            }
        }

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_36kr()
        assert len(result) == 1
        assert result[0].url is None

    @pytest.mark.asyncio
    async def test_fetch_sspai_success(self):
        """测试少数派获取成功"""
        from backend.sources.tech import TechNewsSource
        source = TechNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"title": "少数派文章1", "summary": "摘要1", "id": "2001"},
                {"title": "少数派文章2", "summary": "摘要2", "id": "2002"}
            ]
        }

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_sspai()
        assert len(result) == 2
        assert result[0].title == "少数派文章1"
        assert result[0].source == "少数派"
        assert "少数派" in result[0].tags
        assert "https://sspai.com/post/2001" == result[0].url

    @pytest.mark.asyncio
    async def test_fetch_sspai_exception(self):
        """测试少数派异常处理"""
        from backend.sources.tech import TechNewsSource
        source = TechNewsSource()

        source.client = AsyncMock()
        source.client.get.side_effect = Exception("API错误")

        result = await source._fetch_sspai()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_news_integration(self):
        """测试科技新闻源完整获取流程"""
        from backend.sources.tech import TechNewsSource
        source = TechNewsSource()

        mock_36kr = [MagicMock(title="36氪新闻")]
        mock_sspai = [MagicMock(title="少数派新闻")]

        with patch.object(source, '_fetch_36kr', return_value=mock_36kr), \
             patch.object(source, '_fetch_sspai', return_value=mock_sspai):

            result = await source._fetch_news()
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_fetch_news_with_exceptions(self):
        """测试科技新闻源部分失败"""
        from backend.sources.tech import TechNewsSource
        source = TechNewsSource()

        with patch.object(source, '_fetch_36kr', side_effect=Exception("失败")), \
             patch.object(source, '_fetch_sspai', return_value=[MagicMock(title="少数派新闻")]):

            result = await source._fetch_news()
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_news_limits_to_10(self):
        """测试科技新闻源限制返回10条"""
        from backend.sources.tech import TechNewsSource
        source = TechNewsSource()

        mock_news = [MagicMock(title=f"新闻{i}") for i in range(15)]

        with patch.object(source, '_fetch_36kr', return_value=mock_news[:8]), \
             patch.object(source, '_fetch_sspai', return_value=mock_news[8:]):

            result = await source._fetch_news()
            assert len(result) == 10


class TestAIRoboticsNewsSourceExtended:
    """AI/机器人新闻源扩展测试"""

    @pytest.mark.asyncio
    async def test_fetch_jiqizhixin_success(self):
        """测试机器之心获取成功"""
        from backend.sources.ai_robotics import AIRoboticsNewsSource
        source = AIRoboticsNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"title": "AI新闻1", "summary": "摘要1", "slug": "ai-news-1"},
                {"title": "AI新闻2", "summary": "摘要2", "slug": "ai-news-2"}
            ]
        }

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_jiqizhixin()
        assert len(result) == 2
        assert result[0].title == "AI新闻1"
        assert result[0].source == "机器之心"
        assert "机器之心" in result[0].tags
        assert "https://www.jiqizhixin.com/articles/ai-news-1" == result[0].url

    @pytest.mark.asyncio
    async def test_fetch_jiqizhixin_empty(self):
        """测试机器之心空响应"""
        from backend.sources.ai_robotics import AIRoboticsNewsSource
        source = AIRoboticsNewsSource()

        source.client = AsyncMock()
        source.client.get.return_value = None

        result = await source._fetch_jiqizhixin()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_jiqizhixin_no_slug(self):
        """测试机器之心无 slug"""
        from backend.sources.ai_robotics import AIRoboticsNewsSource
        source = AIRoboticsNewsSource()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"title": "AI新闻1", "summary": "摘要1", "slug": ""}
            ]
        }

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        result = await source._fetch_jiqizhixin()
        assert len(result) == 1
        assert result[0].url is None

    @pytest.mark.asyncio
    async def test_fetch_qbitai_success(self):
        """测试量子位获取成功"""
        from backend.sources.ai_robotics import AIRoboticsNewsSource
        source = AIRoboticsNewsSource()

        # Mock HTML 响应
        mock_html = """
        <html>
            <body>
                <article>
                    <h2>量子位新闻1</h2>
                    <a href="/article/1">链接</a>
                </article>
                <article>
                    <h3>量子位新闻2</h3>
                    <a href="https://example.com/2">链接</a>
                </article>
            </body>
        </html>
        """

        mock_response = MagicMock()
        mock_response.text = mock_html

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        with patch('bs4.BeautifulSoup') as mock_bs:
            # Mock BeautifulSoup
            mock_article1 = MagicMock()
            mock_title1 = MagicMock()
            mock_title1.get_text.return_value = "量子位新闻1"
            mock_link1 = MagicMock()
            mock_link1.get.return_value = "/article/1"
            mock_article1.find.side_effect = lambda x: mock_title1 if x in ["h2", "h3"] else mock_link1

            mock_article2 = MagicMock()
            mock_title2 = MagicMock()
            mock_title2.get_text.return_value = "量子位新闻2"
            mock_link2 = MagicMock()
            mock_link2.get.return_value = "https://example.com/2"
            mock_article2.find.side_effect = lambda x: mock_title2 if x in ["h2", "h3"] else mock_link2

            mock_soup = MagicMock()
            mock_soup.find_all.return_value = [mock_article1, mock_article2]
            mock_bs.return_value = mock_soup

            result = await source._fetch_qbitai()
            assert len(result) == 2
            assert result[0].title == "量子位新闻1"
            assert result[0].source == "量子位"
            assert "量子位" in result[0].tags

    @pytest.mark.asyncio
    async def test_fetch_qbitai_empty_html(self):
        """测试量子位空 HTML"""
        from backend.sources.ai_robotics import AIRoboticsNewsSource
        source = AIRoboticsNewsSource()

        mock_response = MagicMock()
        mock_response.text = "<html><body></body></html>"

        source.client = AsyncMock()
        source.client.get.return_value = mock_response

        with patch('bs4.BeautifulSoup') as mock_bs:
            mock_soup = MagicMock()
            mock_soup.find_all.return_value = []
            mock_bs.return_value = mock_soup

            result = await source._fetch_qbitai()
            assert result == []

    @pytest.mark.asyncio
    async def test_fetch_qbitai_exception(self):
        """测试量子位异常处理"""
        from backend.sources.ai_robotics import AIRoboticsNewsSource
        source = AIRoboticsNewsSource()

        source.client = AsyncMock()
        source.client.get.side_effect = Exception("网络错误")

        result = await source._fetch_qbitai()
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_news_integration(self):
        """测试AI新闻源完整获取流程"""
        from backend.sources.ai_robotics import AIRoboticsNewsSource
        source = AIRoboticsNewsSource()

        mock_jiqizhixin = [MagicMock(title="机器之心新闻")]
        mock_qbitai = [MagicMock(title="量子位新闻")]

        with patch.object(source, '_fetch_jiqizhixin', return_value=mock_jiqizhixin), \
             patch.object(source, '_fetch_qbitai', return_value=mock_qbitai):

            result = await source._fetch_news()
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_fetch_news_with_exceptions(self):
        """测试AI新闻源部分失败"""
        from backend.sources.ai_robotics import AIRoboticsNewsSource
        source = AIRoboticsNewsSource()

        with patch.object(source, '_fetch_jiqizhixin', side_effect=Exception("失败")), \
             patch.object(source, '_fetch_qbitai', return_value=[MagicMock(title="量子位新闻")]):

            result = await source._fetch_news()
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_news_limits_to_10(self):
        """测试AI新闻源限制返回10条"""
        from backend.sources.ai_robotics import AIRoboticsNewsSource
        source = AIRoboticsNewsSource()

        mock_news = [MagicMock(title=f"新闻{i}") for i in range(15)]

        with patch.object(source, '_fetch_jiqizhixin', return_value=mock_news[:8]), \
             patch.object(source, '_fetch_qbitai', return_value=mock_news[8:]):

            result = await source._fetch_news()
            assert len(result) == 10
