"""
数据库配置和连接管理
使用 SQLAlchemy 异步引擎
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .config import settings

# 创建异步数据库引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_debug,  # 调试模式下打印 SQL
    future=True,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 创建基础模型类
Base = declarative_base()


async def get_db():
    """
    获取数据库会话的依赖注入函数
    用于 FastAPI 的 Depends
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库，创建所有表"""
    # 动态导入本地模块的模型（如果存在）
    import os
    local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "local")
    if os.path.exists(local_path):
        try:
            from ..local.create.models import Creation, CreationTemplate
            print("  └ 已加载创作模块模型")
        except ImportError:
            pass  # 模块不存在时跳过
        except Exception as e:
            print(f"  └ 创作模块模型加载失败: {e}")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
