"""
推送通知服务测试
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from backend.models import Briefing, BriefingType
from backend.services.push_notifier import PushNotifier


@pytest.fixture
def sample_briefing():
    """示例早报"""
    return Briefing(
        type=BriefingType.MORNING,
        title="每日早报 - 2025年01月01日",
        content="早报内容：今日财经新闻...",
        created_at=datetime.now()
    )


class TestPushNotifier:
    """推送通知器测试"""

    def test_init_with_defaults(self):
        """使用默认配置初始化"""
        with patch('backend.services.push_notifier.settings') as mock_settings:
            mock_settings.push_platform = "wechat"
            mock_settings.push_webhook_url = "https://hook.example.com"

            notifier = PushNotifier()

            assert notifier.platform == "wechat"
            assert notifier.webhook_url == "https://hook.example.com"

    def test_init_with_custom_params(self):
        """使用自定义参数初始化"""
        notifier = PushNotifier(
            platform="dingtalk",
            webhook_url="https://custom.hook.com"
        )

        assert notifier.platform == "dingtalk"
        assert notifier.webhook_url == "https://custom.hook.com"

    @pytest.mark.asyncio
    async def test_send_briefing_no_webhook(self, sample_briefing):
        """没有 Webhook URL 时应该跳过"""
        notifier = PushNotifier(webhook_url="")

        result = await notifier.send_briefing(sample_briefing)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_briefing_unsupported_platform(self, sample_briefing):
        """不支持的平台应该返回 False"""
        notifier = PushNotifier(
            platform="unsupported",
            webhook_url="https://hook.example.com"
        )

        result = await notifier.send_briefing(sample_briefing)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_wechat_success(self, sample_briefing):
        """企业微信推送成功"""
        notifier = PushNotifier(
            platform="wechat",
            webhook_url="https://hook.example.com"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": 0}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await notifier.send_briefing(sample_briefing)

        assert result is True

    @pytest.mark.asyncio
    async def test_send_wechat_failure(self, sample_briefing):
        """企业微信推送失败"""
        notifier = PushNotifier(
            platform="wechat",
            webhook_url="https://hook.example.com"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": -1, "errmsg": "invalid"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await notifier.send_briefing(sample_briefing)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_wechat_http_error(self, sample_briefing):
        """企业微信 HTTP 错误"""
        notifier = PushNotifier(
            platform="wechat",
            webhook_url="https://hook.example.com"
        )

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await notifier.send_briefing(sample_briefing)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_dingtalk_success(self, sample_briefing):
        """钉钉推送成功"""
        notifier = PushNotifier(
            platform="dingtalk",
            webhook_url="https://hook.example.com"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": 0}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await notifier.send_briefing(sample_briefing)

        assert result is True

    @pytest.mark.asyncio
    async def test_send_dingtalk_failure(self, sample_briefing):
        """钉钉推送失败"""
        notifier = PushNotifier(
            platform="dingtalk",
            webhook_url="https://hook.example.com"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": -1, "errmsg": "invalid"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await notifier.send_briefing(sample_briefing)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_briefing_network_error(self, sample_briefing):
        """网络错误时应该返回 False"""
        notifier = PushNotifier(
            platform="wechat",
            webhook_url="https://hook.example.com"
        )

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("网络错误"))

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await notifier.send_briefing(sample_briefing)

        assert result is False

    @pytest.mark.asyncio
    async def test_send_wechat_content_truncated(self):
        """内容应该截断到2048字符"""
        long_content = "A" * 3000
        briefing = Briefing(
            type=BriefingType.MORNING,
            title="测试早报",
            content=long_content
        )

        notifier = PushNotifier(
            platform="wechat",
            webhook_url="https://hook.example.com"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": 0}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

            await notifier.send_briefing(briefing)

            # 检查发送的内容是否被截断
            call_args = mock_client.post.call_args
            data = call_args[1].get('json', {})
            content = data.get('markdown', {}).get('content', '')
            assert len(content) <= 2048

    @pytest.mark.asyncio
    async def test_send_dingtalk_content_truncated(self):
        """钉钉内容应该截断到2048字符"""
        long_content = "A" * 3000
        briefing = Briefing(
            type=BriefingType.MORNING,
            title="测试早报",
            content=long_content
        )

        notifier = PushNotifier(
            platform="dingtalk",
            webhook_url="https://hook.example.com"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errcode": 0}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

            await notifier.send_briefing(briefing)

            call_args = mock_client.post.call_args
            data = call_args[1].get('json', {})
            content = data.get('markdown', {}).get('text', '')
            assert len(content) <= 2048
