"""
Knowledge Keeper - AI 知识管家
主应用入口
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import init_db, close_db
from .api import bookmarks_router, tags_router, chat_router, search_router, config_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    print("🚀 正在启动 Knowledge Keeper...")
    await init_db()
    print("✅ 数据库初始化完成")
    print(f"🤖 AI 提供商: {settings.ai_provider}")
    
    yield
    
    # 关闭时清理资源
    print("👋 正在关闭 Knowledge Keeper...")
    await close_db()
    print("✅ 资源清理完成")


# 创建应用实例
app = FastAPI(
    title="Knowledge Keeper",
    description="AI 驱动的知识管理应用 - 一站式知识收集、整理、学习平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(bookmarks_router, prefix="/api")
app.include_router(tags_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(config_router, prefix="/api")

# ==================== 动态加载本地私有模块 ====================
# 这些模块存放在 app/local/ 目录下，不会同步到 GitHub
import os

local_modules_path = os.path.join(os.path.dirname(__file__), "local")
if os.path.exists(local_modules_path):
    # 尝试加载微信公众号管理模块
    try:
        from .local.wechat import wechat_router
        app.include_router(wechat_router, prefix="/api/wechat", tags=["微信公众号管理"])
        print("✅ 已加载本地模块: 微信公众号管理 (/api/wechat)")
    except ImportError as e:
        print(f"⚠️ 微信公众号模块加载失败: {e}")
    except Exception as e:
        print(f"⚠️ 微信公众号模块加载异常: {e}")
    
    # 尝试加载 AI 创作模块
    try:
        from .local.create import router as create_router
        app.include_router(create_router, prefix="/api/local", tags=["AI 创作"])
        print("✅ 已加载本地模块: AI 创作 (/api/local/create)")
    except ImportError as e:
        print(f"⚠️ AI 创作模块加载失败: {e}")
    except Exception as e:
        print(f"⚠️ AI 创作模块加载异常: {e}")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Knowledge Keeper",
        "version": "1.0.0",
        "description": "AI 驱动的知识管理应用",
        "docs": "/docs",
        "api": "/api"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "ai_provider": settings.ai_provider
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug
    )
