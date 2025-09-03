import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from app.services.recommendation_engine import RecommendationEngine
from app.models.schemas import CourseSelection, InnoProject, RecommendationType


class TestRecommendationEngine:
    """推荐引擎测试"""
    
    @pytest.fixture
    def engine(self):
        """创建推荐引擎实例"""
        return RecommendationEngine()
    
    @pytest.fixture
    def mock_user_data(self):
        """模拟用户数据"""
        return {
            "user_id": 51,
            "token": "test_token",
            "selections": [
                CourseSelection(
                    sele_id=1,
                    user_id=51,
                    user_name="测试用户",
                    course_title="自塾Python",
                    course_id=5,
                    chapter_title="第5课",
                    chapter_id=50,
                    current_serial=5,
                    deadline=datetime.now() + timedelta(days=2),
                    url="https://test.com/course/5"
                )
            ],
            "all_courses": [
                {
                    "id": 6,
                    "title": "自塾FastAPI",
                    "desc": "FastAPI教程",
                    "finish_selections_num": 8,
                    "director_name": "黎伟"
                }
            ],
            "projects": [
                InnoProject(
                    id=88,
                    task_serial="B035",
                    title="开发什么值得做智能体",
                    publisher="稳新",
                    taker=None,
                    taker_id=None,
                    status="发布",
                    deadline=datetime.now() + timedelta(days=7),
                    planed_hour=20.0,
                    bonus=400.0,
                    desc="开发推荐智能体",
                    create_time=datetime.now()
                )
            ],
            "goal": {
                "id": 1,
                "user_id": 51,
                "content": "完成智能体开发",
                "start_time": (datetime.now() - timedelta(days=25)).isoformat()
            },
            "reports": [
                {
                    "id": 1,
                    "user_id": 51,
                    "time_reported": 5.0,
                    "report_time": (datetime.now() - timedelta(days=10)).isoformat()
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_generate_recommendations(self, engine, mock_user_data):
        """测试生成推荐"""
        with patch.object(engine, '_fetch_user_data', return_value=mock_user_data):
            recommendations = await engine.generate_recommendations(51, "test_token")
            
            assert len(recommendations) > 0
            assert all(rec.score > 0 for rec in recommendations)
            assert len(recommendations) <= 3  # Top3限制
    
    @pytest.mark.asyncio
    async def test_recommend_courses(self, engine, mock_user_data):
        """测试课程推荐"""
        recommendations = await engine._recommend_courses(mock_user_data)
        
        # 应该包含紧急课程推荐
        urgent_recs = [r for r in recommendations if r.type == RecommendationType.COURSE_URGENT]
        assert len(urgent_recs) > 0
        
        # 检查紧急推荐的分数
        urgent_rec = urgent_recs[0]
        assert urgent_rec.urgency > 70  # 2天内DDL应该有高紧急度
        assert urgent_rec.score > 80
    
    @pytest.mark.asyncio
    async def test_recommend_projects(self, engine, mock_user_data):
        """测试项目推荐"""
        recommendations = await engine._recommend_projects(mock_user_data)
        
        # 应该包含任务认领推荐
        task_recs = [r for r in recommendations if r.type == RecommendationType.TASK_CLAIM]
        assert len(task_recs) > 0
        
        # 检查项目推荐
        task_rec = task_recs[0]
        assert task_rec.title == "认领任务「开发什么值得做智能体」"
        assert task_rec.importance > 60  # 高奖励项目应该有高重要度
    
    @pytest.mark.asyncio
    async def test_recommend_system_actions(self, engine, mock_user_data):
        """测试系统操作推荐"""
        recommendations = await engine._recommend_system_actions(mock_user_data)
        
        # 应该包含目标面谈推荐（距离上次>21天）
        goal_recs = [r for r in recommendations if r.type == RecommendationType.GOAL_TALK]
        assert len(goal_recs) > 0
        
        # 应该包含学时申报推荐（最近30天学时不足）
        report_recs = [r for r in recommendations if r.type == RecommendationType.REPORT_TIME]
        assert len(report_recs) > 0
    
    def test_calculate_urgency_score(self, engine):
        """测试紧急度计算"""
        # 测试课程紧急度
        assert engine._calculate_urgency_score(1, "COURSE") >= 90
        assert engine._calculate_urgency_score(3, "COURSE") >= 80
        assert engine._calculate_urgency_score(7, "COURSE") >= 60
        assert engine._calculate_urgency_score(30, "COURSE") <= 40
        
        # 测试项目紧急度
        assert engine._calculate_urgency_score(2, "PROJECT") >= 85
        assert engine._calculate_urgency_score(5, "PROJECT") >= 70
    
    def test_calculate_total_score(self, engine):
        """测试综合得分计算"""
        score = engine._calculate_total_score(
            urgency=90, 
            importance=80, 
            fit=85, 
            growth=70
        )
        
        # 验证加权计算
        expected = 90 * 0.35 + 80 * 0.30 + 85 * 0.25 + 70 * 0.10
        assert abs(score - expected) < 0.01
        assert score <= 100
    
    def test_select_top3_with_diversity(self, engine):
        """测试Top3多样性选择"""
        from app.models.schemas import RecommendationItem
        
        # 创建多个不同类型的推荐
        recommendations = [
            RecommendationItem(
                id="1", type=RecommendationType.COURSE_URGENT, title="课程1",
                description="", action_text="", action_url="", score=95,
                urgency=90, importance=80, personal_fit=85, growth_value=70,
                estimated_time="30min", reasons=[]
            ),
            RecommendationItem(
                id="2", type=RecommendationType.COURSE_POPULAR, title="课程2",
                description="", action_text="", action_url="", score=85,
                urgency=50, importance=70, personal_fit=90, growth_value=80,
                estimated_time="1h", reasons=[]
            ),
            RecommendationItem(
                id="3", type=RecommendationType.TASK_CLAIM, title="任务1",
                description="", action_text="", action_url="", score=92,
                urgency=80, importance=85, personal_fit=75, growth_value=85,
                estimated_time="2h", reasons=[]
            ),
            RecommendationItem(
                id="4", type=RecommendationType.GOAL_TALK, title="面谈1",
                description="", action_text="", action_url="", score=88,
                urgency=60, importance=90, personal_fit=95, growth_value=60,
                estimated_time="1h", reasons=[]
            )
        ]
        
        top3 = engine._select_top3_with_diversity(recommendations)
        
        assert len(top3) == 3
        # 验证类型多样性
        types = {rec.type.value.split('_')[0] for rec in top3}
        assert len(types) == 3  # 应该有3种不同类型


if __name__ == "__main__":
    pytest.main([__file__, "-v"])