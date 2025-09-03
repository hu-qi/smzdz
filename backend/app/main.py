from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import sys

from app.core.config import get_settings
from app.api.recommendations import router as recommendations_router
from app.api.admin import router as admin_router
from app.middleware.performance_middleware import PerformanceMiddleware, CacheMiddleware
from app.services.performance import precompute_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 什么值得做智能体服务启动")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug Mode: {settings.debug}")
    
    # 启动后台预计算服务
    await precompute_service.start_background_tasks()
    
    yield
    
    # 关闭时执行
    await precompute_service.stop_background_tasks()
    logger.info("👋 什么值得做智能体服务关闭")


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=settings.log_format,
        colorize=True
    )
    
    # 创建应用实例
    app = FastAPI(
        title="什么值得做智能体 API",
        description="为自塾平台提供个性化推荐服务的智能体",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # 添加性能监控中间件
    app.add_middleware(PerformanceMiddleware)
    app.add_middleware(CacheMiddleware)
    
    # 注册路由
    app.include_router(recommendations_router)
    app.include_router(admin_router)
    
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": "🎯 什么值得做智能体服务运行中",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/v1/health"
        }
    
    return app


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )