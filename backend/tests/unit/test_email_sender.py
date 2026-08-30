"""
邮件发送服务测试
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from backend.models import Briefing, BriefingType
from backend.services.email_sender import EmailSender


@pytest.fixture
def email_sender():
    """创建邮件发送器实例"""
    with patch('backend.services.email_sender.settings') as mock_settings:
        mock_settings.smtp_server = "smtp.test.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_username = "test@test.com"
        mock_settings.smtp_password = "password"
        return EmailSender()


@pytest.fixture
def sample_briefing():
    """示例早报"""
    return Briefing(
        type=BriefingType.MORNING,
        title="每日早报 - 2025年01月01日",
        content="""🌅 早上好！以下是今日早报：

💰 财经
────────────────────────────────────────
1. 央行宣布降息0.25个百分点
   📝 央行今日宣布下调基准利率
   📰 东方财富 | 重要性: ⭐⭐⭐⭐
   🔗 https://example.com/1

══════════════════════════════════════════════════
📊 共 1 条新闻
📈 分类统计: finance: 1""",
        news_ids="[1]",
        created_at=datetime.now()
    )


class TestEmailSender:
    """邮件发送器测试"""

    def test_init_with_defaults(self):
        """使用默认配置初始化"""
        with patch('backend.services.email_sender.settings') as mock_settings:
            mock_settings.smtp_server = "smtp.default.com"
            mock_settings.smtp_port = 587
            mock_settings.smtp_username = "default@test.com"
            mock_settings.smtp_password = "default_pass"

            sender = EmailSender()

            assert sender.smtp_server == "smtp.default.com"
            assert sender.smtp_port == 587
            assert sender.username == "default@test.com"
            assert sender.password == "default_pass"

    def test_init_with_custom_params(self):
        """使用自定义参数初始化"""
        sender = EmailSender(
            smtp_server="smtp.custom.com",
            smtp_port=465,
            username="custom@test.com",
            password="custom_pass"
        )

        assert sender.smtp_server == "smtp.custom.com"
        assert sender.smtp_port == 465
        assert sender.username == "custom@test.com"
        assert sender.password == "custom_pass"

    def test_convert_to_html_morning(self, email_sender, sample_briefing):
        """早报应该转换为 HTML"""
        html = email_sender._convert_to_html(sample_briefing)

        assert "<!DOCTYPE html>" in html
        assert "每日早报" in html
        assert "央行宣布降息" in html
        assert "早上好" in html

    def test_convert_to_html_evening(self, email_sender):
        """晚报应该转换为 HTML"""
        briefing = Briefing(
            type=BriefingType.EVENING,
            title="每日晚报 - 2025年01月01日",
            content="🌆 晚上好！以下是今日晚报：\n\n科技新闻"
        )

        html = email_sender._convert_to_html(briefing)

        assert "晚报" in html
        assert "晚上好" in html

    def test_convert_to_html_with_links(self, email_sender, sample_briefing):
        """链接应该转换为 HTML 链接"""
        html = email_sender._convert_to_html(sample_briefing)

        assert 'href="https://example.com/1"' in html
        assert "阅读原文" in html

    def test_convert_to_html_with_categories(self, email_sender, sample_briefing):
        """类别应该转换为标题"""
        html = email_sender._convert_to_html(sample_briefing)

        assert "💰 财经" in html

    def test_convert_to_html_with_stats(self, email_sender, sample_briefing):
        """统计信息应该包含在内"""
        html = email_sender._convert_to_html(sample_briefing)

        assert "共 1 条新闻" in html
        assert "分类统计" in html

    def test_convert_to_html_with_horizontal_rules(self, email_sender, sample_briefing):
        """分隔线应该转换为 hr 标签"""
        html = email_sender._convert_to_html(sample_briefing)

        assert "<hr" in html

    @pytest.mark.asyncio
    @patch('backend.services.email_sender.smtplib.SMTP')
    async def test_send_briefing_success(self, mock_smtp_class, email_sender, sample_briefing):
        """成功发送邮件"""
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        result = await email_sender.send_briefing(sample_briefing, "recipient@test.com")

        assert result is True
        mock_smtp_class.assert_called_once_with("smtp.test.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@test.com", "password")
        mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.services.email_sender.smtplib.SMTP')
    async def test_send_briefing_failure(self, mock_smtp_class, email_sender, sample_briefing):
        """发送失败时应该返回 False"""
        mock_smtp_class.side_effect = Exception("连接失败")

        result = await email_sender.send_briefing(sample_briefing, "recipient@test.com")

        assert result is False

    @pytest.mark.asyncio
    @patch('backend.services.email_sender.smtplib.SMTP')
    async def test_send_briefing_login_failure(self, mock_smtp_class, email_sender, sample_briefing):
        """登录失败时应该返回 False"""
        mock_server = MagicMock()
        mock_server.login.side_effect = Exception("认证失败")
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        result = await email_sender.send_briefing(sample_briefing, "recipient@test.com")

        assert result is False

    def test_convert_to_html_empty_content(self, email_sender):
        """空内容应该正常处理"""
        briefing = Briefing(
            type=BriefingType.MORNING,
            title="测试早报",
            content=""
        )

        html = email_sender._convert_to_html(briefing)

        assert "<!DOCTYPE html>" in html
        assert "测试早报" in html

    def test_convert_to_html_preserves_formatting(self, email_sender):
        """应该保留基本格式"""
        briefing = Briefing(
            type=BriefingType.MORNING,
            title="测试早报",
            content="第一行\n\n第二行\n第三行"
        )

        html = email_sender._convert_to_html(briefing)

        assert "第一行" in html
        assert "第二行" in html
        assert "第三行" in html
