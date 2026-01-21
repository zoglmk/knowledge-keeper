# API 路由
from .bookmarks import router as bookmarks_router
from .tags import router as tags_router
from .chat import router as chat_router
from .search import router as search_router
from .config import router as config_router

__all__ = ['bookmarks_router', 'tags_router', 'chat_router', 'search_router', 'config_router']
