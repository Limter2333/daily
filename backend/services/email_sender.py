"""
邮件发送服务
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional
from datetime import datetime

from backend.models import Briefing
from backend.config import settings
from backend.logger import get_logger

logger = get_logger("email_sender")


class EmailSender:
    """邮件发送服务"""

    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.smtp_server = smtp_server or settings.smtp_server
        self.smtp_port = smtp_port or settings.smtp_port
        self.username = username or settings.smtp_username
        self.password = password or settings.smtp_password

    async def send_briefing(self, briefing: Briefing, recipient: str) -> bool:
        """发送早报/晚报邮件"""
        try:
            # 创建邮件
            msg = MIMEMultipart("alternative")
            msg["Subject"] = briefing.title
            msg["From"] = self.username
            msg["To"] = recipient

            # 纯文本内容
            text_content = briefing.content
            msg.attach(MIMEText(text_content, "plain", "utf-8"))

            # HTML 内容
            html_content = self._convert_to_html(briefing)
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"邮件已发送至 {recipient}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    def _convert_to_html(self, briefing: Briefing) -> str:
        """将早报/晚报转换为 HTML 格式"""
        type_name = "早报" if "早报" in briefing.title else "晚报"
        gradient_color = "from-indigo-500 to-purple-600" if type_name == "早报" else "from-orange-500 to-pink-600"

        # 处理内容，保留换行和格式
        content_lines = briefing.content.split("\n")
        html_lines = []

        for line in content_lines:
            # 处理标题行
            if line.startswith("🌅") or line.startswith("🌆"):
                html_lines.append(f'<h2 style="margin-top: 20px;">{line}</h2>')
            elif line.startswith("💰") or line.startswith("💻") or line.startswith("🔬") or \
                 line.startswith("[AI]") or line.startswith("[SHOP]") or line.startswith("[NEWS]"):
                html_lines.append(f'<h3 style="color: #4F46E5; margin-top: 15px;">{line}</h3>')
            elif line.startswith("─"):
                html_lines.append('<hr style="border: 1px solid #E5E7EB;">')
            elif line.startswith("═"):
                html_lines.append('<hr style="border: 2px solid #4F46E5;">')
            elif line.startswith("[STATS]") or line.startswith("[CHART]"):
                html_lines.append(f'<p style="color: #6B7280; font-size: 14px;">{line}</p>')
            elif line.strip():
                # 处理带链接的行
                if "🔗" in line:
                    parts = line.split("🔗")
                    if len(parts) == 2:
                        url = parts[1].strip()
                        html_lines.append(f'{parts[0]}<a href="{url}" style="color: #4F46E5;">阅读原文</a>')
                    else:
                        html_lines.append(f"<p>{line}</p>")
                else:
                    html_lines.append(f"<p>{line}</p>")
            else:
                html_lines.append("<br>")

        content_html = "\n".join(html_lines)

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #374151;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            background: #ffffff;
            padding: 30px;
            border: 1px solid #E5E7EB;
            border-top: none;
        }}
        .footer {{
            background: #F9FAFB;
            padding: 20px;
            text-align: center;
            border: 1px solid #E5E7EB;
            border-top: none;
            border-radius: 0 0 10px 10px;
            font-size: 12px;
            color: #6B7280;
        }}
        h2 {{ color: #1F2937; }}
        h3 {{ color: #4F46E5; }}
        a {{ color: #4F46E5; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        p {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin: 0; font-size: 24px;">{briefing.title}</h1>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">每日早报晚报系统</p>
    </div>
    <div class="content">
        {content_html}
    </div>
    <div class="footer">
        <p>此邮件由每日早报晚报系统自动发送</p>
        <p>发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
"""
