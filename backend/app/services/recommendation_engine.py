from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone
import uuid
import asyncio
from loguru import logger

from app.models.schemas import (
    RecommendationItem, RecommendationType, UrgencyLevel,
    CourseSelection, InnoProject, UserProfile
)
from app.services.zishu_api import ZishuAPIClient
from app.core.config import get_settings

settings = get_settings()


class RecommendationEngine:
    """推荐引擎核心类"""
    
    def __init__(self):
        self.api_client = ZishuAPIClient()
        self.algorithm_weights = {
            "urgency": settings.algorithm_weights_urgency,
            "importance": settings.algorithm_weights_importance,
            "personal_fit": settings.algorithm_weights_personal_fit,
            "growth_value": settings.algorithm_weights_growth_value
        }
        
    async def generate_recommendations(self, user_id: int, token: str) -> List[RecommendationItem]:
        """生成用户推荐"""
        try:
            # 并发获取用户数据
            user_data = await self._fetch_user_data(user_id, token)
            
            # 生成各类推荐
            course_recs = await self._recommend_courses(user_data)
            project_recs = await self._recommend_projects(user_data)
            system_recs = await self._recommend_system_actions(user_data)
            
            # 合并所有推荐
            all_recommendations = course_recs + project_recs + system_recs
            
            # 排序并选择Top3，确保多样性
            top3 = self._select_top3_with_diversity(all_recommendations)
            
            logger.info(f"为用户{user_id}生成了{len(top3)}个推荐")
            return top3
            
        except Exception as e:
            logger.error(f"生成推荐失败: 用户{user_id}, 错误: {e}")
            return []
    
    async def _fetch_user_data(self, user_id: int, token: str) -> Dict:
        """并发获取用户相关数据"""
        # 检查是否使用模拟数据
        if settings.use_mock_data:
            logger.warning("当前使用模拟数据模式，设置USE_MOCK_DATA=false使用真实API")
            return self._get_mock_user_data(user_id, token)
            
        # 使用真实 API 获取数据
        logger.info(f"从真实自塾API获取用户{user_id}数据")
        tasks = [
            self.api_client.get_user_selections(token),
            self.api_client.get_all_courses(),
            self.api_client.get_current_projects(),
            self.api_client.get_user_goal(user_id),
            self.api_client.get_user_reports(user_id),
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 记录API调用结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"API调用{i}失败: {result}")
            
            return {
                "selections": results[0] if not isinstance(results[0], Exception) else [],
                "all_courses": results[1] if not isinstance(results[1], Exception) else [],
                "projects": results[2] if not isinstance(results[2], Exception) else [],
                "goal": results[3] if not isinstance(results[3], Exception) else None,
                "reports": results[4] if not isinstance(results[4], Exception) else [],
                "user_id": user_id,
                "token": token
            }
        except Exception as e:
            logger.error(f"获取用户数据失败: {e}")
            logger.warning("获取真实数据失败，降级使用模拟数据")
            return self._get_mock_user_data(user_id, token)
    
    async def _recommend_courses(self, user_data: Dict) -> List[RecommendationItem]:
        """推荐课程学习"""
        recommendations = []
        selections = user_data.get("selections", [])
        all_courses = user_data.get("all_courses", [])
        
        # 1. 紧急学习任务 - 即将DDL的课程
        for selection in selections:
            # 确保时间对象都有时区信息
            now = datetime.now(timezone.utc)
            if selection.deadline.tzinfo is None:
                deadline = selection.deadline.replace(tzinfo=timezone.utc)
            else:
                deadline = selection.deadline
            
            days_to_deadline = (deadline - now).days
            
            if days_to_deadline <= 3:  # 3天内DDL
                urgency_score = self._calculate_urgency_score(days_to_deadline, "COURSE")
                importance_score = 85  # 已选课程重要度高
                fit_score = 90  # 用户已选择，说明适合
                growth_score = 70
                
                total_score = self._calculate_total_score(
                    urgency_score, importance_score, fit_score, growth_score
                )
                
                urgency_level = self._get_urgency_level(days_to_deadline * 24)
                
                rec = RecommendationItem(
                    id=f"course_urgent_{selection.sele_id}",
                    type=RecommendationType.COURSE_URGENT,
                    title=f"完成《{selection.course_title}》{selection.chapter_title}",
                    description=f"第{selection.current_serial}课 - {selection.chapter_title}",
                    action_text="立即学习",
                    action_url=selection.url,
                    score=total_score,
                    urgency=urgency_score,
                    importance=importance_score,
                    personal_fit=fit_score,
                    growth_value=growth_score,
                    estimated_time="30-45分钟",
                    deadline=deadline,
                    urgency_level=urgency_level,
                    reasons=[
                        f"距离DDL还有{days_to_deadline}天",
                        "已选课程需要完成",
                        f"塾师: {selection.shushi_name}" if selection.shushi_name else ""
                    ],
                    source_id=str(selection.course_id),
                    source_type="course_selection"
                )
                recommendations.append(rec)
        
        # 2. 热门课程推荐 - 完成人数多且用户未选的课程
        selected_course_ids = {s.course_id for s in selections}
        
        for course in all_courses:
            if (course["id"] not in selected_course_ids and 
                course.get("finish_selections_num", 0) >= 5):  # 至少5人完成
                
                urgency_score = 30  # 非紧急
                importance_score = 60 + min(course.get("finish_selections_num", 0) * 2, 30)
                fit_score = 50  # 基础匹配度
                growth_score = 80  # 新技能学习价值高
                
                total_score = self._calculate_total_score(
                    urgency_score, importance_score, fit_score, growth_score
                )
                
                if total_score >= 60:  # 分数阈值
                    rec = RecommendationItem(
                        id=f"course_popular_{course['id']}",
                        type=RecommendationType.COURSE_POPULAR,
                        title=f"学习热门课程《{course['title']}》",
                        description=course.get("desc", "")[:100] + "..." if len(course.get("desc", "")) > 100 else course.get("desc", ""),
                        action_text="立即选课",
                        action_url=f"/course/{course['id']}",
                        score=total_score,
                        urgency=urgency_score,
                        importance=importance_score,
                        personal_fit=fit_score,
                        growth_value=growth_score,
                        estimated_time="1-2周",
                        deadline=None,
                        urgency_level=UrgencyLevel.LOW,
                        reasons=[
                            f"已有{course.get('finish_selections_num', 0)}人完成",
                            "热门推荐课程",
                            f"导师: {course.get('director_name', '未知')}"
                        ],
                        source_id=str(course["id"]),
                        source_type="course_popular"
                    )
                    recommendations.append(rec)
        
        return recommendations
    
    async def _recommend_projects(self, user_data: Dict) -> List[RecommendationItem]:
        """推荐项目任务"""
        recommendations = []
        projects = user_data.get("projects", [])
        
        for project in projects:
            # 只推荐无人认领的任务
            if project.taker_id is None:
                # 确保时间对象都有时区信息
                now = datetime.now(timezone.utc)
                if project.deadline.tzinfo is None:
                    deadline = project.deadline.replace(tzinfo=timezone.utc)
                else:
                    deadline = project.deadline
                
                days_to_deadline = (deadline - now).days
                
                urgency_score = self._calculate_urgency_score(days_to_deadline, "PROJECT")
                importance_score = min(60 + (project.bonus or 0) / 10, 90)  # 奖励越高越重要
                fit_score = self._calculate_project_fit_score(project, user_data)
                growth_score = min(60 + project.planed_hour * 2, 90)  # 预计工时越多成长价值越高
                
                total_score = self._calculate_total_score(
                    urgency_score, importance_score, fit_score, growth_score
                )
                
                if total_score >= 50:  # 项目推荐阈值
                    rec = RecommendationItem(
                        id=f"task_claim_{project.id}",
                        type=RecommendationType.TASK_CLAIM,
                        title=f"认领任务「{project.title}」",
                        description=project.desc[:100] + "..." if len(project.desc) > 100 else project.desc,
                        action_text="立即认领",
                        action_url=f"/inno/task/{project.id}",
                        score=total_score,
                        urgency=urgency_score,
                        importance=importance_score,
                        personal_fit=fit_score,
                        growth_value=growth_score,
                        estimated_time=f"{project.planed_hour}小时",
                        deadline=deadline,
                        urgency_level=self._get_urgency_level(days_to_deadline * 24),
                        reasons=[
                            f"奖励: {project.bonus or 0}鲸币",
                            f"发布者: {project.publisher}",
                            f"预计工时: {project.planed_hour}小时",
                            "无人认领的任务"
                        ],
                        source_id=str(project.id),
                        source_type="project_task"
                    )
                    recommendations.append(rec)
        
        return recommendations
    
    async def _recommend_system_actions(self, user_data: Dict) -> List[RecommendationItem]:
        """推荐系统级操作"""
        recommendations = []
        
        # 1. 目标面谈推荐
        goal = user_data.get("goal")
        if goal:
            # 检查是否需要目标面谈
            start_time_str = goal["start_time"]
            # 处理时间字符串，确保有时区信息
            if "+" not in start_time_str and "Z" not in start_time_str:
                start_time_str += "+00:00"
            
            start_time = datetime.fromisoformat(start_time_str)
            now = datetime.now(timezone.utc)
            
            # 确保 start_time 有时区信息
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
                
            days_since_start = (now - start_time).days
            
            if days_since_start > 21:  # 超过21天未面谈
                urgency_score = min(50 + days_since_start, 90)
                importance_score = 75
                fit_score = 100  # 个人目标，完全匹配
                growth_score = 85
                
                total_score = self._calculate_total_score(
                    urgency_score, importance_score, fit_score, growth_score
                )
                
                rec = RecommendationItem(
                    id=f"goal_talk_{goal['id']}",
                    type=RecommendationType.GOAL_TALK,
                    title=f"预约目标面谈（距上次{days_since_start}天）",
                    description=f"当前目标: {goal['content'][:50]}...",
                    action_text="立即预约",
                    action_url="/user/goaltalk/new",
                    score=total_score,
                    urgency=urgency_score,
                    importance=importance_score,
                    personal_fit=fit_score,
                    growth_value=growth_score,
                    estimated_time="60分钟",
                    deadline=None,
                    urgency_level=UrgencyLevel.MEDIUM,
                    reasons=[
                        f"距离上次目标制定已{days_since_start}天",
                        "定期复盘有助于目标达成",
                        "个性化指导"
                    ],
                    source_id=str(goal["id"]),
                    source_type="goal_management"
                )
                recommendations.append(rec)
        
        # 2. 学时申报推荐
        reports = user_data.get("reports", [])
        if reports:
            # 计算最近30天的学时
            now = datetime.now(timezone.utc)
            thirty_days_ago = now - timedelta(days=30)
            
            recent_reports = []
            for r in reports:
                report_time_str = r["report_time"]
                # 处理时间字符串
                if "+" not in report_time_str and "Z" not in report_time_str:
                    report_time_str += "+00:00"
                    
                report_time = datetime.fromisoformat(report_time_str)
                if report_time.tzinfo is None:
                    report_time = report_time.replace(tzinfo=timezone.utc)
                    
                if report_time > thirty_days_ago:
                    recent_reports.append(r)
            recent_hours = sum(r.get("time_reported", 0) for r in recent_reports)
            
            if recent_hours < 10:  # 最近30天学时不足10小时
                urgency_score = 60
                importance_score = 70
                fit_score = 90
                growth_score = 50
                
                total_score = self._calculate_total_score(
                    urgency_score, importance_score, fit_score, growth_score
                )
                
                rec = RecommendationItem(
                    id="report_time_reminder",
                    type=RecommendationType.REPORT_TIME,
                    title="补充学时申报记录",
                    description=f"最近30天仅申报{recent_hours:.1f}小时，建议补充学习记录",
                    action_text="去申报",
                    action_url="/user/reports/new",
                    score=total_score,
                    urgency=urgency_score,
                    importance=importance_score,
                    personal_fit=fit_score,
                    growth_value=growth_score,
                    estimated_time="10-15分钟",
                    deadline=None,
                    urgency_level=UrgencyLevel.MEDIUM,
                    reasons=[
                        f"最近30天仅申报{recent_hours:.1f}小时",
                        "学时记录有助于学习规划",
                        "完善学习档案"
                    ],
                    source_id="time_report",
                    source_type="system_reminder"
                )
                recommendations.append(rec)
        
        return recommendations
    
    def _calculate_urgency_score(self, days_left: int, task_type: str) -> float:
        """计算紧急度得分"""
        if task_type == "COURSE":
            if days_left <= 1:
                return 95
            elif days_left <= 3:
                return 85
            elif days_left <= 7:
                return 70
            elif days_left <= 14:
                return 50
            else:
                return 30
        elif task_type == "PROJECT":
            if days_left <= 3:
                return 90
            elif days_left <= 7:
                return 75
            elif days_left <= 14:
                return 60
            else:
                return 40
        
        return 25
    
    def _calculate_project_fit_score(self, project: InnoProject, user_data: Dict) -> float:
        """计算项目匹配度"""
        # 这里是简化版本，实际应该基于用户技能和项目需求匹配
        base_score = 50
        
        # 根据项目奖励调整匹配度
        bonus = project.bonus or 0
        if bonus > 200:
            base_score += 20
        elif bonus > 100:
            base_score += 10
        
        # 根据工时要求调整
        if project.planed_hour <= 10:
            base_score += 15  # 短期任务更容易参与
        
        return min(base_score, 95)
    
    def _calculate_total_score(self, urgency: float, importance: float, 
                             fit: float, growth: float) -> float:
        """计算综合得分"""
        total = (
            urgency * self.algorithm_weights["urgency"] +
            importance * self.algorithm_weights["importance"] +
            fit * self.algorithm_weights["personal_fit"] +
            growth * self.algorithm_weights["growth_value"]
        )
        return min(total, 100)
    
    def _get_urgency_level(self, hours_left: int) -> UrgencyLevel:
        """获取紧急度级别"""
        if hours_left <= settings.urgency_critical:
            return UrgencyLevel.CRITICAL
        elif hours_left <= settings.urgency_high:
            return UrgencyLevel.HIGH
        elif hours_left <= settings.urgency_medium:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW
    
    def _select_top3_with_diversity(self, recommendations: List[RecommendationItem]) -> List[RecommendationItem]:
        """选择Top3推荐，确保类型多样性"""
        if not recommendations:
            return []
        
        # 按分数排序
        sorted_recs = sorted(recommendations, key=lambda x: x.score, reverse=True)
        
        selected = []
        used_types = set()
        
        # 优先选择不同类型的推荐
        for rec in sorted_recs:
            if len(selected) >= 3:
                break
                
            rec_category = rec.type.value.split('_')[0]  # COURSE, TASK, GOAL等
            
            if rec_category not in used_types:
                selected.append(rec)
                used_types.add(rec_category)
        
        # 如果不够3个，从剩余中按分数选择
        for rec in sorted_recs:
            if len(selected) >= 3:
                break
            if rec not in selected:
                selected.append(rec)
        
        return selected[:3]
    
    def _get_mock_user_data(self, user_id: int, token: str) -> Dict:
        """开发环境下的模拟数据"""
        from app.models.schemas import CourseSelection, InnoProject
        
        # 模拟选课数据
        mock_selections = [
            CourseSelection(
                sele_id=1,
                user_id=user_id,
                user_name="测试用户",
                course_title="Python编程基础",
                course_id=101,
                chapter_title="第5课：循环与条件语句",
                chapter_id=105,
                current_serial=5,
                deadline=datetime.now() + timedelta(days=2),  # 2天后截止
                url="/course/python-101#lesson-5",
                shushi_id=1,
                shushi_name="张老师"
            ),
            CourseSelection(
                sele_id=2,
                user_id=user_id,
                user_name="测试用户",
                course_title="数据结构与算法",
                course_id=102,
                chapter_title="第3课：树与图",
                chapter_id=203,
                current_serial=3,
                deadline=datetime.now() + timedelta(days=7),  # 7天后截止
                url="/course/algorithm-101#lesson-3",
                shushi_id=2,
                shushi_name="李老师"
            )
        ]
        
        # 模拟课程数据
        mock_courses = [
            {
                "id": 103,
                "title": "Vue.js前端开发",
                "desc": "从零开始学习Vue.js框架，掌握现代前端开发技巧",
                "director_name": "王老师",
                "finish_selections_num": 12
            },
            {
                "id": 104,
                "title": "机器学习入门",
                "desc": "系统学习机器学习的基本概念和常用算法",
                "director_name": "陈老师",
                "finish_selections_num": 8
            }
        ]
        
        # 模拟项目数据
        mock_projects = [
            InnoProject(
                id=201,
                task_serial="TASK-001",
                title="官网首页优化",
                publisher="产品经理",
                taker=None,
                taker_id=None,
                status="待认领",
                deadline=datetime.now() + timedelta(days=10),
                planed_hour=15,
                bonus=300,
                task_text="优化官网首页的加载速度和用户体验",
                desc="需要优化官网首页的性能，提升用户访问体验，包括图片压缩、代码优化等工作。",
                create_time=datetime.now() - timedelta(days=3)
            ),
            InnoProject(
                id=202,
                task_serial="TASK-002",
                title="用户反馈系统开发",
                publisher="技术经理",
                taker=None,
                taker_id=None,
                status="待认领",
                deadline=datetime.now() + timedelta(days=5),
                planed_hour=25,
                bonus=500,
                task_text="开发一个用户反馈收集系统",
                desc="开发一个完整的用户反馈系统，包括反馈提交、分类、处理和回复功能。",
                create_time=datetime.now() - timedelta(days=1)
            )
        ]
        
        # 模拟目标数据
        mock_goal = {
            "id": 1,
            "user_id": user_id,
            "content": "掌握全栈开发技能，成为一名优秀的软件开发工程师",
            "start_time": (datetime.now() - timedelta(days=25)).isoformat(),  # 25天前制定
            "target_date": (datetime.now() + timedelta(days=180)).isoformat()
        }
        
        # 模拟学时申报数据
        mock_reports = [
            {
                "id": 1,
                "user_id": user_id,
                "report_time": (datetime.now() - timedelta(days=5)).isoformat(),
                "time_reported": 2.5,
                "activity": "Python编程学习"
            },
            {
                "id": 2,
                "user_id": user_id,
                "report_time": (datetime.now() - timedelta(days=15)).isoformat(),
                "time_reported": 3.0,
                "activity": "算法题目练习"
            }
        ]
        
        logger.warning("⚠️  正在使用模拟数据生成推荐，不是真实用户数据！")
        logger.info(f"要使用真实API，请设置环境变量USE_MOCK_DATA=false")
        
        return {
            "selections": mock_selections,
            "all_courses": mock_courses,
            "projects": mock_projects,
            "goal": mock_goal,
            "reports": mock_reports,
            "user_id": user_id,
            "token": token
        }