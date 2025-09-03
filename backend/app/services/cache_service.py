from typing import Optional, Any
import json
import redis.asyncio as redis
from loguru import logger
from app.core.config import get_settings

settings = get_settings()


class CacheService:
    """Redis缓存服务"""
    
    def __init__(self):
        self.redis_url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        if settings.redis_password:
            self.redis_url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        
        self.redis = None
        self.prefix = settings.cache_prefix
    
    async def _get_redis(self):
        """获取Redis连接"""
        if self.redis is None:
            try:
                self.redis = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Redis连接成功")
            except Exception as e:
                logger.error(f"Redis连接失败: {e}")
                # 如果Redis不可用，使用内存缓存作为降级方案
                self.redis = InMemoryCache()
        return self.redis
    
    def _make_key(self, key: str) -> str:
        """生成带前缀的缓存键"""
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        try:
            redis = await self._get_redis()
            cache_key = self._make_key(key)
            data = await redis.get(cache_key)
            
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"获取缓存失败: key={key}, 错误={e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存数据"""
        try:
            redis = await self._get_redis()
            cache_key = self._make_key(key)
            data = json.dumps(value, ensure_ascii=False, default=str)
            
            if ttl:
                await redis.setex(cache_key, ttl, data)
            else:
                await redis.set(cache_key, data)
            
            logger.debug(f"缓存设置成功: key={key}")
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败: key={key}, 错误={e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存数据"""
        try:
            redis = await self._get_redis()
            cache_key = self._make_key(key)
            result = await redis.delete(cache_key)
            
            logger.debug(f"缓存删除: key={key}, 结果={result}")
            return result > 0
            
        except Exception as e:
            logger.error(f"删除缓存失败: key={key}, 错误={e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            redis = await self._get_redis()
            cache_key = self._make_key(key)
            result = await redis.exists(cache_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"检查缓存失败: key={key}, 错误={e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        try:
            redis = await self._get_redis()
            cache_pattern = self._make_key(pattern)
            keys = await redis.keys(cache_pattern)
            
            if keys:
                result = await redis.delete(*keys)
                logger.info(f"清除缓存: 模式={pattern}, 数量={result}")
                return result
            
            return 0
            
        except Exception as e:
            logger.error(f"清除缓存失败: pattern={pattern}, 错误={e}")
            return 0


class InMemoryCache:
    """内存缓存作为Redis的降级方案"""
    
    def __init__(self):
        self.cache = {}
        logger.warning("使用内存缓存作为Redis降级方案")
    
    async def get(self, key: str) -> Optional[str]:
        return self.cache.get(key)
    
    async def set(self, key: str, value: str) -> None:
        self.cache[key] = value
    
    async def setex(self, key: str, ttl: int, value: str) -> None:
        # 简化版本，不实现TTL
        self.cache[key] = value
    
    async def delete(self, key: str) -> int:
        if key in self.cache:
            del self.cache[key]
            return 1
        return 0
    
    async def exists(self, key: str) -> int:
        return 1 if key in self.cache else 0
    
    async def keys(self, pattern: str) -> list:
        # 简化版本，返回所有键
        return list(self.cache.keys())
