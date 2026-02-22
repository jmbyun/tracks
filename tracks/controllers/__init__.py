"""
API route controllers.
"""

from .chat import router as chat_router
from .history import router as history_router
from .heartbeat import router as heartbeat_router
from .telegram import router as telegram_router
from .settings import router as settings_router
from .browser import router as browser_router
from .connection.google import router as google_router


routers = [
    chat_router,
    history_router,
    heartbeat_router,
    telegram_router,
    settings_router,
    browser_router,
    google_router,
]

