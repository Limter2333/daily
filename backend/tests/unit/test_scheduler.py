"""
定时任务调度服务测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from backend.models import Settings, Briefing, BriefingType
from backend.services.scheduler import TaskScheduler


@pytest.fixture
def mock_db():
    """Mock 数据库"""
    db = AsyncMock()
    db.get_settings = AsyncMock(return_value=Settings(
        morning_time="07:30",
        evening_time="20:00"
    ))
    return db


@pytest.fixture
def mock_aggregator():
    """Mock 新闻聚合器"""
    return AsyncMock()


@pytest.fixture
def mock_generator():
    """Mock 早报生成器"""
    generator = AsyncMock()
    generator.generate_morning_briefing = AsyncMock(return_value=Briefing(
        type=BriefingType.MORNING,
        title="测试早报",
        content="早报内容"
    ))
    generator.generate_evening_briefing = AsyncMock(return_value=Briefing(
        type=BriefingType.EVENING,
        title="测试晚报",
        content="晚报内容"
    ))
    return generator


@pytest.fixture
def mock_email_sender():
    """Mock 邮件发送器"""
    return AsyncMock()


@pytest.fixture
def mock_push_notifier():
    """Mock 推送通知器"""
    return AsyncMock()


@pytest.fixture
def scheduler(mock_db, mock_aggregator, mock_generator, mock_email_sender, mock_push_notifier):
    """创建调度器实例"""
    return TaskScheduler(
        db=mock_db,
        aggregator=mock_aggregator,
        generator=mock_generator,
        email_sender=mock_email_sender,
        push_notifier=mock_push_notifier
    )


class TestTaskScheduler:
    """定时任务调度器测试"""

    def test_init(self, scheduler):
        """初始化应该设置正确的属性"""
        assert scheduler._running is False
        assert scheduler.scheduler is not None

    @pytest.mark.asyncio
    async def test_start(self, scheduler):
        """启动应该设置运行状态"""
        await scheduler.start()

        assert scheduler._running is True
        assert len(scheduler.get_jobs()) == 3

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_start_already_running(self, scheduler):
        """重复启动应该跳过"""
        await scheduler.start()
        initial_job_count = len(scheduler.get_jobs())

        await scheduler.start()  # 再次启动

        assert len(scheduler.get_jobs()) == initial_job_count

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_stop(self, scheduler):
        """停止应该清除运行状态"""
        await scheduler.start()
        await scheduler.stop()

        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_stop_not_running(self, scheduler):
        """停止未运行的调度器应该跳过"""
        await scheduler.stop()

        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_update_schedule(self, scheduler, mock_db):
        """更新调度应该重新配置任务"""
        await scheduler.start()

        # 更新设置
        mock_db.get_settings = AsyncMock(return_value=Settings(
            morning_time="08:00",
            evening_time="21:00"
        ))

        await scheduler.update_schedule()

        # 验证任务已更新
        jobs = scheduler.get_jobs()
        assert len(jobs) == 3

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_update_schedule_not_running(self, scheduler):
        """未运行时更新调度应该跳过"""
        await scheduler.update_schedule()

        assert scheduler._running is False

    @pytest.mark.asyncio
    async def test_aggregate_news(self, scheduler, mock_aggregator):
        """聚合新闻应该调用聚合器"""
        await scheduler._aggregate_news()

        mock_aggregator.aggregate_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_aggregate_news_handles_error(self, scheduler, mock_aggregator):
        """聚合失败时应该捕获异常"""
        mock_aggregator.aggregate_all.side_effect = Exception("网络错误")

        # 不应该抛出异常
        await scheduler._aggregate_news()

    @pytest.mark.asyncio
    async def test_send_morning_briefing(self, scheduler, mock_generator, mock_db):
        """发送早报应该生成并发送"""
        # 配置邮件和推送
        mock_db.get_settings = AsyncMock(return_value=Settings(
            email_enabled=True,
            email_recipient="test@example.com",
            push_enabled=True,
            push_webhook_url="https://hook.example.com"
        ))

        await scheduler._send_morning_briefing()

        mock_generator.generate_morning_briefing.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_morning_briefing_empty(self, scheduler, mock_generator):
        """空早报应该跳过发送"""
        mock_generator.generate_morning_briefing = AsyncMock(return_value=None)

        await scheduler._send_morning_briefing()

        # 不应该调用发送
        scheduler.email_sender.send_briefing.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_evening_briefing(self, scheduler, mock_generator, mock_db):
        """发送晚报应该生成并发送"""
        mock_db.get_settings = AsyncMock(return_value=Settings(
            email_enabled=True,
            email_recipient="test@example.com",
            push_enabled=False
        ))

        await scheduler._send_evening_briefing()

        mock_generator.generate_evening_briefing.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_evening_briefing_empty(self, scheduler, mock_generator):
        """空晚报应该跳过发送"""
        mock_generator.generate_evening_briefing = AsyncMock(return_value=None)

        await scheduler._send_evening_briefing()

        scheduler.email_sender.send_briefing.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_briefing_email_disabled(self, scheduler, mock_db, mock_generator):
        """邮件禁用时不应该发送邮件"""
        mock_db.get_settings = AsyncMock(return_value=Settings(
            email_enabled=False,
            push_enabled=False
        ))

        await scheduler._send_morning_briefing()

        scheduler.email_sender.send_briefing.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_briefing_push_disabled(self, scheduler, mock_db, mock_generator):
        """推送禁用时不应该发送推送"""
        mock_db.get_settings = AsyncMock(return_value=Settings(
            email_enabled=False,
            push_enabled=False
        ))

        await scheduler._send_morning_briefing()

        scheduler.push_notifier.send_briefing.assert_not_called()

    @pytest.mark.asyncio
    async def test_trigger_morning_briefing(self, scheduler, mock_generator):
        """手动触发早报"""
        await scheduler.trigger_morning_briefing()

        mock_generator.generate_morning_briefing.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_evening_briefing(self, scheduler, mock_generator):
        """手动触发晚报"""
        await scheduler.trigger_evening_briefing()

        mock_generator.generate_evening_briefing.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_aggregation(self, scheduler, mock_aggregator):
        """手动触发聚合"""
        await scheduler.trigger_aggregation()

        mock_aggregator.aggregate_all.assert_called_once()

    def test_get_jobs(self, scheduler):
        """获取任务列表应该返回正确的格式"""
        jobs = scheduler.get_jobs()

        assert isinstance(jobs, list)
        # 未启动时应该为空
        assert len(jobs) == 0

    @pytest.mark.asyncio
    async def test_get_jobs_after_start(self, scheduler):
        """启动后应该返回任务列表"""
        await scheduler.start()

        jobs = scheduler.get_jobs()

        assert len(jobs) == 3

        # 检查任务格式
        for job in jobs:
            assert "id" in job
            assert "name" in job
            assert "trigger" in job

        await scheduler.stop()

    @pytest.mark.asyncio
    async def test_send_briefing_handles_error(self, scheduler, mock_generator, mock_db):
        """发送失败时应该捕获异常"""
        mock_db.get_settings = AsyncMock(return_value=Settings(
            email_enabled=True,
            email_recipient="test@example.com",
            push_enabled=False
        ))

        scheduler.email_sender.send_briefing = AsyncMock(side_effect=Exception("发送失败"))

        # 不应该抛出异常
        await scheduler._send_morning_briefing()
