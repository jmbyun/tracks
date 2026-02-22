"""
API route controllers.
"""

from .chat import router as chat_router
from .history import router as history_router
from .heartbeat import router as heartbeat_router
from .agents import router as agents_router
from .settings import router as settings_router
from .connection.google import router as connection_google_router
from .connection.instagram import router as connection_instagram_router
from .connection.twitter import router as connection_twitter_router
from .telegram import router as telegram_router
from .browser import router as browser_router

routers = [
    chat_router,
    history_router,
    heartbeat_router,
    telegram_router,
    settings_router,
    browser_router,
    connection_google_router,
    connection_instagram_router,
    connection_twitter_router,
    agents_router,
]
