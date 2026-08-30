"""
定时任务调度服务
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from typing import Optional
from datetime import datetime

from backend.services.news_aggregator import NewsAggregator
from backend.services.briefing_generator import BriefingGenerator
from backend.services.email_sender import EmailSender
from backend.services.push_notifier import PushNotifier
from backend.database import Database
from backend.logger import get_logger

logger = get_logger("scheduler")


class TaskScheduler:
    """定时任务调度服务"""

    def __init__(
        self,
        db: Database,
        aggregator: NewsAggregator,
        generator: BriefingGenerator,
        email_sender: EmailSender,
        push_notifier: PushNotifier
    ):
        self.db = db
        self.aggregator = aggregator
        self.generator = generator
        self.email_sender = email_sender
        self.push_notifier = push_notifier
        self.scheduler = AsyncIOScheduler()
        self._running = False

    async def start(self):
        """启动定时任务"""
        if self._running:
            logger.warning("调度器已在运行")
            return

        # 获取设置
        settings = await self.db.get_settings()
        morning_hour, morning_minute = settings.morning_time.split(":")
        evening_hour, evening_minute = settings.evening_time.split(":")

        # 新闻聚合任务（每30分钟）
        self.scheduler.add_job(
            self._aggregate_news,
            IntervalTrigger(minutes=30),
            id="aggregate_news",
            name="新闻聚合",
            replace_existing=True
        )

        # 早报任务
        self.scheduler.add_job(
            self._send_morning_briefing,
            CronTrigger(hour=int(morning_hour), minute=int(morning_minute)),
            id="morning_briefing",
            name="早报推送",
            replace_existing=True
        )

        # 晚报任务
        self.scheduler.add_job(
            self._send_evening_briefing,
            CronTrigger(hour=int(evening_hour), minute=int(evening_minute)),
            id="evening_briefing",
            name="晚报推送",
            replace_existing=True
        )

        self.scheduler.start()
        self._running = True

        logger.info("Scheduler started")
        logger.info(f"  - News aggregation: every 30 minutes")
        logger.info(f"  - Morning briefing: {settings.morning_time}")
        logger.info(f"  - Evening briefing: {settings.evening_time}")

    async def stop(self):
        """停止定时任务"""
        if self._running:
            self.scheduler.shutdown()
            self._running = False
            logger.info("Scheduler stopped")

    async def update_schedule(self):
        """更新定时任务配置"""
        if not self._running:
            return

        # 获取最新设置
        settings = await self.db.get_settings()
        morning_hour, morning_minute = settings.morning_time.split(":")
        evening_hour, evening_minute = settings.evening_time.split(":")

        # 更新早报任务
        self.scheduler.reschedule_job(
            "morning_briefing",
            trigger=CronTrigger(hour=int(morning_hour), minute=int(morning_minute))
        )

        # 更新晚报任务
        self.scheduler.reschedule_job(
            "evening_briefing",
            trigger=CronTrigger(hour=int(evening_hour), minute=int(evening_minute))
        )

        logger.info("定时任务配置已更新")
        logger.info(f"  - 早报: 每天 {settings.morning_time}")
        logger.info(f"  - 晚报: 每天 {settings.evening_time}")

    async def _aggregate_news(self):
        """聚合新闻任务"""
        try:
            logger.info("定时任务: 新闻聚合")
            await self.aggregator.aggregate_all()
        except Exception as e:
            logger.error(f"新闻聚合失败: {e}")

    async def _send_morning_briefing(self):
        """发送早报任务"""
        try:
            logger.info("定时任务: 早报推送")

            # 生成早报
            briefing = await self.generator.generate_morning_briefing()

            if not briefing or not briefing.content:
                logger.warning("早报内容为空，跳过推送")
                return

            # 获取设置
            settings_data = await self.db.get_settings()

            # 发送邮件
            if settings_data.email_enabled and settings_data.email_recipient:
                await self.email_sender.send_briefing(briefing, settings_data.email_recipient)

            # 发送推送
            if settings_data.push_enabled and settings_data.push_webhook_url:
                await self.push_notifier.send_briefing(briefing)

        except Exception as e:
            logger.error(f"早报推送失败: {e}")

    async def _send_evening_briefing(self):
        """发送晚报任务"""
        try:
            logger.info("定时任务: 晚报推送")

            # 生成晚报
            briefing = await self.generator.generate_evening_briefing()

            if not briefing or not briefing.content:
                logger.warning("晚报内容为空，跳过推送")
                return

            # 获取设置
            settings_data = await self.db.get_settings()

            # 发送邮件
            if settings_data.email_enabled and settings_data.email_recipient:
                await self.email_sender.send_briefing(briefing, settings_data.email_recipient)

            # 发送推送
            if settings_data.push_enabled and settings_data.push_webhook_url:
                await self.push_notifier.send_briefing(briefing)

        except Exception as e:
            logger.error(f"晚报推送失败: {e}")

    async def trigger_morning_briefing(self):
        """手动触发早报"""
        await self._send_morning_briefing()

    async def trigger_evening_briefing(self):
        """手动触发晚报"""
        await self._send_evening_briefing()

    async def trigger_aggregation(self):
        """手动触发新闻聚合"""
        await self._aggregate_news()

    def get_jobs(self):
        """获取所有定时任务"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs
