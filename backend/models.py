"""
数据模型定义
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class NewsCategory(str, Enum):
    """新闻类别枚举"""
    FINANCE = "finance"          # 财经
    TECH = "tech"                # 科技
    SEMICONDUCTOR = "semiconductor"  # 半导体
    AI = "ai"                    # AI/机器人
    CONSUMER = "consumer"        # 消费
    OTHER = "other"              # 其他


class BriefingType(str, Enum):
    """早报/晚报类型枚举"""
    MORNING = "morning"  # 早报
    EVENING = "evening"  # 晚报


class NewsItem(BaseModel):
    """新闻条目模型"""
    id: Optional[int] = None
    title: str = Field(..., description="新闻标题")
    summary: Optional[str] = Field(None, description="新闻摘要")
    content: Optional[str] = Field(None, description="新闻内容")
    source: str = Field(..., description="新闻来源")
    source_url: Optional[str] = Field(None, description="来源URL")
    url: Optional[str] = Field(None, description="原文链接")
    category: NewsCategory = Field(NewsCategory.OTHER, description="新闻类别")
    importance: int = Field(5, ge=1, le=10, description="重要性评分 1-10")
    published_at: Optional[datetime] = Field(None, description="发布时间")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    is_sent: bool = Field(False, description="是否已发送")
    tags: Optional[str] = Field(None, description="标签，逗号分隔")

    class Config:
        from_attributes = True


class Briefing(BaseModel):
    """早报/晚报模型"""
    id: Optional[int] = None
    type: BriefingType = Field(..., description="类型：morning/evening")
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    news_ids: Optional[str] = Field(None, description="新闻ID列表，JSON格式")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    is_sent: bool = Field(False, description="是否已发送")

    class Config:
        from_attributes = True


class Settings(BaseModel):
    """系统设置模型（AI 配置从 .env 文件读取，不存储在数据库）"""
    # 天气配置
    weather_city: str = Field("Beijing", description="城市拼音")

    # 定时任务配置
    morning_time: str = Field("07:30", description="早报时间")
    evening_time: str = Field("20:00", description="晚报时间")

    # 邮件配置
    email_enabled: bool = Field(False, description="是否启用邮件")
    smtp_server: str = Field("smtp.gmail.com", description="SMTP服务器")
    smtp_port: int = Field(587, description="SMTP端口")
    smtp_username: str = Field("", description="SMTP用户名")
    smtp_password: str = Field("", description="SMTP密码")
    email_recipient: str = Field("", description="收件人邮箱")

    # 推送配置
    push_enabled: bool = Field(False, description="是否启用推送")
    push_platform: str = Field("wechat", description="推送平台")
    push_webhook_url: str = Field("", description="Webhook URL")

    class Config:
        from_attributes = True


class NewsListResponse(BaseModel):
    """新闻列表响应"""
    total: int
    items: List[NewsItem]
    page: int
    page_size: int


class BriefingListResponse(BaseModel):
    """早报/晚报列表响应"""
    total: int
    items: List[Briefing]


class ApiResponse(BaseModel):
    """通用API响应"""
    success: bool = True
    message: str = ""
    data: Optional[dict] = None
