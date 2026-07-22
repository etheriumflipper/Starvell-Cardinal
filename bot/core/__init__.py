"""
Основные компоненты бота.
"""

# Патч Python 3.8 должен примениться до любых async/aiohttp импортов
from . import py38_compat  # noqa: F401

from .config import BotConfig, ConfigManager
from .storage import Database
from .services import StarvellService
from .notifications import NotificationManager, NotificationType, init_notifications, get_notification_manager
from .middlewares import *

__all__ = [
    'BotConfig', 
    'ConfigManager', 
    'Database', 
    'StarvellService',
    'NotificationManager',
    'NotificationType',
    'init_notifications',
    'get_notification_manager',
    'py38_compat',
]
