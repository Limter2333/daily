"""
日志模块 - 将日志输出到 ./logs/backend 目录
"""

import os
import sys
from pathlib import Path
from loguru import logger
from datetime import datetime

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
LOG_DIR = ROOT_DIR / "logs" / "backend"

# 确保日志目录存在
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 移除默认的 stderr handler
logger.remove()

# 添加控制台输出（INFO 级别）
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[request_id]}</cyan> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    colorize=True
)

# 添加文件输出 - 所有日志
logger.add(
    str(LOG_DIR / "app_{time:YYYY-MM-DD}.log"),
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[request_id]} | {name}:{function}:{line} - {message}",
    rotation="00:00",  # 每天午夜轮转
    retention="30 days",  # 保留 30 天
    compression="zip",  # 压缩旧日志
    encoding="utf-8",
    enqueue=True  # 异步写入
)

# 添加错误日志文件
logger.add(
    str(LOG_DIR / "error_{time:YYYY-MM-DD}.log"),
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[request_id]} | {name}:{function}:{line} - {message}\n{exception}",
    rotation="00:00",
    retention="90 days",  # 错误日志保留更久
    compression="zip",
    encoding="utf-8",
    enqueue=True
)

# 添加 API 请求日志
logger.add(
    str(LOG_DIR / "api_{time:YYYY-MM-DD}.log"),
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
    rotation="00:00",
    retention="14 days",
    compression="zip",
    encoding="utf-8",
    enqueue=True,
    filter=lambda record: "api" in record["extra"].get("module", "")
)

# 导出 logger 实例
__all__ = ["logger"]


def get_logger(module_name: str = "app"):
    """获取带有模块名称的 logger，自动附带默认 request_id"""
    return logger.bind(module=module_name, request_id="-")
