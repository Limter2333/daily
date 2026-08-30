"""
推送通知服务 - 支持企业微信、钉钉
"""

import httpx
from typing import Optional
from datetime import datetime

from backend.models import Briefing
from backend.config import settings
from backend.logger import get_logger

logger = get_logger("push_notifier")


class PushNotifier:
    """推送通知服务"""

    def __init__(
        self,
        platform: Optional[str] = None,
        webhook_url: Optional[str] = None
    ):
        self.platform = platform or settings.push_platform
        self.webhook_url = webhook_url or settings.push_webhook_url

    async def send_briefing(self, briefing: Briefing) -> bool:
        """发送早报/晚报推送"""
        if not self.webhook_url:
            logger.warning("未配置 Webhook URL，跳过推送")
            return False

        try:
            if self.platform == "wechat":
                return await self._send_wechat(briefing)
            elif self.platform == "dingtalk":
                return await self._send_dingtalk(briefing)
            else:
                logger.warning(f"不支持的推送平台: {self.platform}")
                return False
        except Exception as e:
            logger.error(f"推送失败: {e}")
            return False

    async def _send_wechat(self, briefing: Briefing) -> bool:
        """发送企业微信推送"""
        # 截取内容（微信限制）
        content = briefing.content[:2048]

        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.webhook_url,
                json=data,
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    logger.info("企业微信推送成功")
                    return True
                else:
                    logger.error(f"企业微信推送失败: {result}")
                    return False
            else:
                logger.error(f"企业微信推送失败: HTTP {response.status_code}")
                return False

    async def _send_dingtalk(self, briefing: Briefing) -> bool:
        """发送钉钉推送"""
        # 截取内容（钉钉限制）
        content = briefing.content[:2048]

        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": briefing.title,
                "text": content
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.webhook_url,
                json=data,
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("errcode") == 0:
                    logger.info("钉钉推送成功")
                    return True
                else:
                    logger.error(f"钉钉推送失败: {result}")
                    return False
            else:
                logger.error(f"钉钉推送失败: HTTP {response.status_code}")
                return False
