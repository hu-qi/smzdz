import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json
from datetime import datetime

from app.main import app
from app.models.schemas import RecommendationItem, RecommendationType

# 创建测试客户端
client = TestClient(app)


@pytest.fixture
def mock_recommendation():
    """模拟推荐数据"""
    return RecommendationItem(
        id="test_rec_001",
        type=RecommendationType.COURSE_URGENT,
        title="完成《自塾Python》第5课",
        description="学习Python循环与条件语句",
        action_text="立即学习",
        action_url="/course/python-101#lesson-5",
        score=92.0,
        urgency=85.0,
        importance=90.0,
        personal_fit=95.0,
        growth_value=75.0,
        estimated_time="45分钟",
        deadline=datetime.now(),
        reasons=["距离DDL还有2天", "入塾必修课程"]
    )


class TestRecommendationAPI:
    """推荐API测试"""
    
    def test_health_check(self):
        """测试健康检查接口"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "what-to-do-agent"
    
    def test_root_endpoint(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "什么值得做智能体" in data["message"]
        assert data["version"] == "1.0.0"
    
    @patch('app.api.recommendations.recommendation_engine.generate_recommendations')
    @patch('app.api.recommendations.cache_service.get')
    @patch('app.api.recommendations.cache_service.set')
    def test_get_top3_recommendations_without_cache(
        self, 
        mock_cache_set, 
        mock_cache_get, 
        mock_generate_recs,
        mock_recommendation
    ):
        """测试获取Top3推荐（无缓存）"""
        # 设置mock返回值
        mock_cache_get.return_value = None
        mock_generate_recs.return_value = [mock_recommendation]
        mock_cache_set.return_value = True
        
        # 模拟认证header
        headers = {"Authorization": "Bearer test_token"}
        
        response = client.get("/api/v1/recommend/top3", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 200
        assert "recommendations" in data["data"]
        assert len(data["data"]["recommendations"]) == 1
        assert data["data"]["recommendations"][0]["title"] == "完成《自塾Python》第5课"
    
    @patch('app.api.recommendations.cache_service.get')
    def test_get_top3_recommendations_with_cache(self, mock_cache_get):
        """测试获取Top3推荐（有缓存）"""
        # 设置缓存返回值
        cached_data = {
            "recommendations": [
                {
                    "id": "cached_rec_001",
                    "type": "COURSE_URGENT",
                    "title": "缓存的推荐",
                    "score": 88.0
                }
            ],
            "user_id": 51,
            "last_updated": datetime.now().isoformat()
        }
        mock_cache_get.return_value = cached_data
        
        headers = {"Authorization": "Bearer test_token"}
        
        response = client.get("/api/v1/recommend/top3", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["recommendations"][0]["title"] == "缓存的推荐"
    
    def test_get_recommendations_without_auth(self):
        """测试无认证获取推荐"""
        response = client.get("/api/v1/recommend/top3")
        assert response.status_code == 401
    
    def test_submit_feedback(self):
        """测试提交反馈"""
        headers = {"Authorization": "Bearer test_token"}
        
        response = client.post(
            "/api/v1/recommend/feedback",
            headers=headers,
            json={
                "recommendation_id": "test_rec_001",
                "feedback_type": "like"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["feedback_recorded"] is True
    
    @patch('app.api.recommendations.cache_service.get')
    def test_explain_recommendation(self, mock_cache_get):
        """测试推荐解释"""
        # 设置缓存数据
        cached_data = {
            "recommendations": [
                {
                    "id": "test_rec_001",
                    "title": "测试推荐",
                    "score": 92.0,
                    "urgency": 85.0,
                    "importance": 90.0,
                    "personal_fit": 95.0,
                    "growth_value": 75.0,
                    "type": "COURSE_URGENT",
                    "reasons": ["测试理由1", "测试理由2"]
                }
            ]
        }
        mock_cache_get.return_value = cached_data
        
        headers = {"Authorization": "Bearer test_token"}
        
        response = client.get(
            "/api/v1/recommend/explain/test_rec_001",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 200
        assert "score_breakdown" in data["data"]
        assert data["data"]["title"] == "测试推荐"


class TestAdminAPI:
    """管理员API测试"""
    
    def test_get_performance_stats(self):
        """测试获取性能统计"""
        response = client.get("/api/v1/admin/performance")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 200
        assert "performance_stats" in data["data"]
    
    def test_reset_performance_stats(self):
        """测试重置性能统计"""
        response = client.post("/api/v1/admin/performance/reset")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 200
        assert "reset_timestamp" in data["data"]
    
    def test_get_system_status(self):
        """测试获取系统状态"""
        response = client.get("/api/v1/admin/system/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["service_name"] == "什么值得做智能体"
        assert data["data"]["version"] == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])