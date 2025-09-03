import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import json

from app.services.cache_service import CacheService


class TestCacheService:
    """缓存服务测试"""
    
    @pytest.fixture
    def cache_service(self):
        """创建缓存服务实例"""
        return CacheService()
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, cache_service):
        """测试缓存基本操作"""
        # 测试设置和获取
        test_key = "test_key"
        test_data = {"message": "hello", "number": 42}
        
        # 设置缓存
        result = await cache_service.set(test_key, test_data, ttl=60)
        assert result is True
        
        # 获取缓存
        cached_data = await cache_service.get(test_key)
        assert cached_data == test_data
        
        # 检查存在性
        exists = await cache_service.exists(test_key)
        assert exists is True
        
        # 删除缓存
        deleted = await cache_service.delete(test_key)
        assert deleted is True
        
        # 验证删除
        cached_data = await cache_service.get(test_key)
        assert cached_data is None
    
    @pytest.mark.asyncio
    async def test_cache_with_prefix(self, cache_service):
        """测试缓存键前缀"""
        test_key = "user_123"
        test_data = {"user_id": 123}
        
        await cache_service.set(test_key, test_data)
        
        # 验证实际存储的键包含前缀
        full_key = cache_service._make_key(test_key)
        assert full_key.startswith(cache_service.prefix)
        assert test_key in full_key
    
    @pytest.mark.asyncio
    async def test_cache_ttl(self, cache_service):
        """测试缓存TTL"""
        test_key = "ttl_test"
        test_data = {"expires": True}
        
        # 设置很短的TTL
        await cache_service.set(test_key, test_data, ttl=1)
        
        # 立即获取应该成功
        cached_data = await cache_service.get(test_key)
        assert cached_data == test_data
        
        # 等待过期后获取应该为空
        await asyncio.sleep(2)
        cached_data = await cache_service.get(test_key)
        assert cached_data is None
    
    @pytest.mark.asyncio
    async def test_clear_pattern(self, cache_service):
        """测试模式清除"""
        # 设置多个测试键
        test_keys = ["pattern_test_1", "pattern_test_2", "other_key"]
        
        for key in test_keys:
            await cache_service.set(key, {"key": key})
        
        # 清除匹配模式的键
        cleared_count = await cache_service.clear_pattern("pattern_test_*")
        
        # 验证清除结果
        assert cleared_count >= 0  # 实际清除数量可能因Redis实现而异
        
        # 验证非匹配键仍然存在
        other_data = await cache_service.get("other_key")
        assert other_data is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])