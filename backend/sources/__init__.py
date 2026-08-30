"""
新闻源模块
"""

from backend.sources.base import BaseNewsSource
from backend.sources.general import GeneralNewsSource
from backend.sources.finance import FinanceNewsSource
from backend.sources.tech import TechNewsSource
from backend.sources.ai_robotics import AIRoboticsNewsSource

__all__ = [
    "BaseNewsSource",
    "GeneralNewsSource",
    "FinanceNewsSource",
    "TechNewsSource",
    "AIRoboticsNewsSource",
]
