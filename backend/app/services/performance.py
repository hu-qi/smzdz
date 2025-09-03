import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger

from app.services.recommendation_engine import RecommendationEngine
from app.services.cache_service import CacheService
from app.core.config import get_settings

settings = get_settings()


class PrecomputeService:
    """预计算服务 - 在后台预先计算用户推荐"""
    
    def __init__(self):
        self.recommendation_engine = RecommendationEngine()
        self.cache_service = CacheService()
        self.running = False
        
    async def start_background_tasks(self):
        """启动后台任务"""
        if self.running:
            return
            
        self.running = True
        logger.info("启动预计算后台任务")
        
        # 启动定时任务
        asyncio.create_task(self._daily_precompute_task())
        asyncio.create_task(self._hourly_refresh_task())
        asyncio.create_task(self._cache_cleanup_task())
    
    async def stop_background_tasks(self):
        """停止后台任务"""
        self.running = False
        logger.info("停止预计算后台任务")
    
    async def _daily_precompute_task(self):
        """每日预计算任务 - 在凌晨6点执行"""
        while self.running:
            try:
                now = datetime.now()
                # 计算下次执行时间（明天6点）
                next_run = now.replace(hour=6, minute=0, second=0, microsecond=0)
                if now.hour >= 6:
                    next_run += timedelta(days=1)
                
                sleep_seconds = (next_run - now).total_seconds()
                logger.info(f"下次预计算时间: {next_run}, 等待 {sleep_seconds:.0f} 秒")
                
                await asyncio.sleep(sleep_seconds)
                
                if self.running:
                    await self._precompute_all_users()
                    
            except Exception as e:
                logger.error(f"每日预计算任务错误: {e}")
                await asyncio.sleep(3600)  # 错误时等待1小时后重试
    
    async def _hourly_refresh_task(self):
        """每小时刷新活跃用户推荐"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # 等待1小时
                
                if self.running:
                    await self._refresh_active_users()
                    
            except Exception as e:
                logger.error(f"每小时刷新任务错误: {e}")
                await asyncio.sleep(1800)  # 错误时等待30分钟后重试
    
    async def _cache_cleanup_task(self):
        """缓存清理任务 - 每6小时执行一次"""
        while self.running:
            try:
                await asyncio.sleep(6 * 3600)  # 等待6小时
                
                if self.running:
                    await self._cleanup_expired_cache()
                    
            except Exception as e:
                logger.error(f"缓存清理任务错误: {e}")
                await asyncio.sleep(3600)  # 错误时等待1小时后重试
    
    async def _precompute_all_users(self):
        """预计算所有用户的推荐"""
        logger.info("开始预计算所有用户推荐")
        
        try:
            # 这里应该从数据库获取活跃用户列表
            # 暂时使用示例用户ID
            active_user_ids = await self._get_active_user_ids()
            
            total_users = len(active_user_ids)
            success_count = 0
            
            for i, user_info in enumerate(active_user_ids):
                try:
                    user_id = user_info["user_id"]
                    token = user_info.get("token", "")  # 实际应用中需要有效token
                    
                    # 生成推荐
                    recommendations = await self.recommendation_engine.generate_recommendations(
                        user_id, token
                    )
                    
                    # 缓存结果
                    cache_key = f"recommendations:user:{user_id}"
                    cache_data = {
                        "recommendations": [rec.dict() for rec in recommendations],
                        "user_id": user_id,
                        "last_updated": datetime.now().isoformat(),
                        "next_refresh": (datetime.now() + timedelta(hours=2)).isoformat(),
                        "algorithm_version": "1.0"
                    }
                    
                    await self.cache_service.set(cache_key, cache_data, ttl=7200)
                    success_count += 1
                    
                    if i % 10 == 0:  # 每处理10个用户记录一次日志
                        logger.info(f"预计算进度: {i}/{total_users}")
                    
                    # 避免过于频繁的API调用
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"用户{user_id}预计算失败: {e}")
                    continue
            
            logger.info(f"预计算完成: 成功 {success_count}/{total_users}")
            
        except Exception as e:
            logger.error(f"预计算所有用户失败: {e}")
    
    async def _refresh_active_users(self):
        """刷新活跃用户推荐"""
        logger.info("开始刷新活跃用户推荐")
        
        try:
            # 获取最近1小时有活动的用户
            active_user_ids = await self._get_recently_active_users()
            
            refresh_count = 0
            for user_info in active_user_ids:
                try:
                    user_id = user_info["user_id"]
                    token = user_info.get("token", "")
                    
                    # 检查缓存是否需要刷新
                    cache_key = f"recommendations:user:{user_id}"
                    cached_data = await self.cache_service.get(cache_key)
                    
                    should_refresh = False
                    if not cached_data:
                        should_refresh = True
                    else:
                        last_updated = datetime.fromisoformat(cached_data["last_updated"])
                        if (datetime.now() - last_updated).total_seconds() > 3600:  # 1小时
                            should_refresh = True
                    
                    if should_refresh:
                        recommendations = await self.recommendation_engine.generate_recommendations(
                            user_id, token
                        )
                        
                        cache_data = {
                            "recommendations": [rec.dict() for rec in recommendations],
                            "user_id": user_id,
                            "last_updated": datetime.now().isoformat(),
                            "next_refresh": (datetime.now() + timedelta(hours=2)).isoformat(),
                            "algorithm_version": "1.0"
                        }
                        
                        await self.cache_service.set(cache_key, cache_data, ttl=7200)
                        refresh_count += 1
                        
                        await asyncio.sleep(0.1)
                
                except Exception as e:
                    logger.error(f"用户{user_id}刷新失败: {e}")
                    continue
            
            logger.info(f"活跃用户刷新完成: {refresh_count} 个用户")
            
        except Exception as e:
            logger.error(f"刷新活跃用户失败: {e}")
    
    async def _cleanup_expired_cache(self):
        """清理过期缓存"""
        logger.info("开始清理过期缓存")
        
        try:
            # 清理推荐缓存（保留最近24小时的）
            pattern = "recommendations:*"
            cleared_count = await self.cache_service.clear_pattern(pattern)
            logger.info(f"清理缓存完成: {cleared_count} 个键")
            
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
    
    async def _get_active_user_ids(self) -> List[Dict]:
        """获取活跃用户ID列表"""
        # 这里是示例数据，实际应该从数据库查询
        # 应该查询最近30天有活动的用户
        return [
            {"user_id": 51, "token": ""},  # 子瑜
            {"user_id": 1, "token": ""},   # 稳新
            {"user_id": 74, "token": ""},  # 人杰
            {"user_id": 2, "token": ""},   # 暄郝
            {"user_id": 7, "token": ""},   # 珞索
        ]
    
    async def _get_recently_active_users(self) -> List[Dict]:
        """获取最近活跃的用户"""
        # 这里是示例数据，实际应该从数据库查询最近1小时有活动的用户
        return [
            {"user_id": 51, "token": ""},  # 子瑜
            {"user_id": 1, "token": ""},   # 稳新
        ]


class PerformanceMonitor:
    """性能监控服务"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.metrics = {
            "api_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0,
            "error_count": 0
        }
    
    async def record_api_call(self, response_time: float, cache_hit: bool = False, error: bool = False):
        """记录API调用指标"""
        self.metrics["api_calls"] += 1
        
        if cache_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1
        
        if error:
            self.metrics["error_count"] += 1
        
        # 计算平均响应时间
        current_avg = self.metrics["avg_response_time"]
        call_count = self.metrics["api_calls"]
        self.metrics["avg_response_time"] = (current_avg * (call_count - 1) + response_time) / call_count
    
    async def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        cache_hit_rate = 0
        if self.metrics["api_calls"] > 0:
            cache_hit_rate = self.metrics["cache_hits"] / self.metrics["api_calls"] * 100
        
        return {
            "total_api_calls": self.metrics["api_calls"],
            "cache_hit_rate": f"{cache_hit_rate:.2f}%",
            "cache_hits": self.metrics["cache_hits"],
            "cache_misses": self.metrics["cache_misses"],
            "avg_response_time": f"{self.metrics['avg_response_time']:.3f}s",
            "error_count": self.metrics["error_count"],
            "error_rate": f"{(self.metrics['error_count'] / max(self.metrics['api_calls'], 1) * 100):.2f}%"
        }
    
    async def reset_metrics(self):
        """重置指标"""
        self.metrics = {
            "api_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0,
            "error_count": 0
        }


# 全局实例
precompute_service = PrecomputeService()
performance_monitor = PerformanceMonitor()