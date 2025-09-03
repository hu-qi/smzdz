import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from app.services.performance import performance_monitor


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 检查是否为推荐API请求
        is_recommendation_api = request.url.path.startswith("/api/v1/recommend")
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算响应时间
            process_time = time.time() - start_time
            
            # 添加响应头
            response.headers["X-Process-Time"] = str(process_time)
            
            # 记录性能指标
            if is_recommendation_api:
                # 检查是否命中缓存（从响应中判断）
                cache_hit = getattr(request.state, 'cache_hit', False)
                await performance_monitor.record_api_call(
                    response_time=process_time,
                    cache_hit=cache_hit,
                    error=response.status_code >= 400
                )
                
                # 记录API访问日志
                logger.info(
                    f"API调用 - 路径: {request.url.path}, "
                    f"方法: {request.method}, "
                    f"状态码: {response.status_code}, "
                    f"响应时间: {process_time:.3f}s, "
                    f"缓存命中: {cache_hit}"
                )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # 记录错误
            if is_recommendation_api:
                await performance_monitor.record_api_call(
                    response_time=process_time,
                    cache_hit=False,
                    error=True
                )
            
            logger.error(f"请求处理异常: {e}, 响应时间: {process_time:.3f}s")
            raise


class CacheMiddleware(BaseHTTPMiddleware):
    """缓存中间件 - 标记缓存命中状态"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 初始化缓存状态
        request.state.cache_hit = False
        
        response = await call_next(request)
        return response