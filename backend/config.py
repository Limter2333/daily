"""
配置管理模块
"""

import os
import yaml
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    app_name: str = "每日早报晚报系统"
    app_version: str = "1.0.0"
    debug: bool = True

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # 数据库配置
    database_path: str = str(ROOT_DIR / "data" / "daily.db")

    # 定时任务配置
    morning_time: str = "07:30"
    evening_time: str = "20:00"
    aggregate_interval: int = 30

    # 新闻配置
    max_per_source: int = 10
    max_total: int = 50

    # AI 配置
    ai_provider: str = "openai"
    ai_api_key: str = ""
    ai_model: str = "gpt-3.5-turbo"
    ai_base_url: Optional[str] = None

    # 邮件配置
    email_enabled: bool = False
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_recipient: str = ""

    # 推送配置
    push_enabled: bool = False
    push_platform: str = "wechat"
    push_webhook_url: str = ""

    # 天气配置
    weather_city: str = "Beijing"

    class Config:
        env_file = str(ROOT_DIR / ".env")
        env_file_encoding = "utf-8"


def load_config() -> Settings:
    """加载配置"""
    # 从 YAML 文件加载基础配置
    config_path = ROOT_DIR / "config.yaml"
    yaml_config = {}

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}

    # 映射 YAML 配置到环境变量格式
    env_map = {}

    if "app" in yaml_config:
        env_map["APP_NAME"] = yaml_config["app"].get("name", "")
        env_map["APP_VERSION"] = yaml_config["app"].get("version", "")
        env_map["DEBUG"] = str(yaml_config["app"].get("debug", True)).lower()

    if "server" in yaml_config:
        env_map["HOST"] = yaml_config["server"].get("host", "0.0.0.0")
        env_map["PORT"] = str(yaml_config["server"].get("port", 8000))

    if "database" in yaml_config:
        env_map["DATABASE_PATH"] = str(ROOT_DIR / yaml_config["database"].get("path", "data/daily.db"))

    if "scheduler" in yaml_config:
        env_map["MORNING_TIME"] = yaml_config["scheduler"].get("morning_time", "07:30")
        env_map["EVENING_TIME"] = yaml_config["scheduler"].get("evening_time", "20:00")
        env_map["AGGREGATE_INTERVAL"] = str(yaml_config["scheduler"].get("aggregate_interval", 30))

    if "news" in yaml_config:
        env_map["MAX_PER_SOURCE"] = str(yaml_config["news"].get("max_per_source", 10))
        env_map["MAX_TOTAL"] = str(yaml_config["news"].get("max_total", 50))

    if "ai" in yaml_config:
        env_map["AI_PROVIDER"] = yaml_config["ai"].get("provider", "openai")
        env_map["AI_MODEL"] = yaml_config["ai"].get("model", "gpt-3.5-turbo")
        if yaml_config["ai"].get("base_url"):
            env_map["AI_BASE_URL"] = yaml_config["ai"]["base_url"]

    if "email" in yaml_config:
        env_map["EMAIL_ENABLED"] = str(yaml_config["email"].get("enabled", False)).lower()
        env_map["SMTP_SERVER"] = yaml_config["email"].get("smtp_server", "smtp.gmail.com")
        env_map["SMTP_PORT"] = str(yaml_config["email"].get("smtp_port", 587))
        env_map["SMTP_USERNAME"] = yaml_config["email"].get("username", "")
        env_map["SMTP_PASSWORD"] = yaml_config["email"].get("password", "")
        env_map["EMAIL_RECIPIENT"] = yaml_config["email"].get("recipient", "")

    if "push" in yaml_config:
        env_map["PUSH_ENABLED"] = str(yaml_config["push"].get("enabled", False)).lower()
        env_map["PUSH_PLATFORM"] = yaml_config["push"].get("platform", "wechat")
        env_map["PUSH_WEBHOOK_URL"] = yaml_config["push"].get("webhook_url", "")

    if "weather" in yaml_config:
        env_map["WEATHER_CITY"] = yaml_config["weather"].get("city", "Beijing")

    # 设置环境变量（仅当未设置时）
    for key, value in env_map.items():
        if key not in os.environ:
            os.environ[key] = str(value)

    return Settings()


# 全局配置实例
settings = load_config()
