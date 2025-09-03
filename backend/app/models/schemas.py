from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class RecommendationType(str, Enum):
    """推荐类型枚举"""
    COURSE_URGENT = "COURSE_URGENT"           # 紧急学习任务
    COURSE_POPULAR = "COURSE_POPULAR"         # 热门课程学习
    TASK_CLAIM = "TASK_CLAIM"                 # 项目任务认领
    GOAL_TALK = "GOAL_TALK"                   # 目标面谈预约
    REPORT_TIME = "REPORT_TIME"               # 学时补报申请
    PROFILE_COMPLETE = "PROFILE_COMPLETE"     # 个人资料完善
    EXAM_PUBLISH = "EXAM_PUBLISH"             # 试卷发布
    COURSE_PUBLISH = "COURSE_PUBLISH"         # 课程发布


class UrgencyLevel(str, Enum):
    """紧急度级别"""
    CRITICAL = "critical"  # 24小时内
    HIGH = "high"         # 3天内
    MEDIUM = "medium"     # 7天内
    LOW = "low"           # 30天内


class RecommendationItem(BaseModel):
    """推荐项目数据模型"""
    id: str = Field(..., description="推荐项目唯一ID")
    type: RecommendationType = Field(..., description="推荐类型")
    title: str = Field(..., description="推荐标题")
    description: str = Field(..., description="推荐描述")
    action_text: str = Field(..., description="操作按钮文字")
    action_url: str = Field(..., description="操作链接")
    
    # 得分相关
    score: float = Field(..., ge=0, le=100, description="综合得分")
    urgency: float = Field(..., ge=0, le=100, description="紧急度得分")
    importance: float = Field(..., ge=0, le=100, description="重要度得分")
    personal_fit: float = Field(..., ge=0, le=100, description="个人匹配度得分")
    growth_value: float = Field(..., ge=0, le=100, description="成长价值得分")
    
    # 额外信息
    estimated_time: str = Field(..., description="预计用时")
    deadline: Optional[datetime] = Field(None, description="截止时间")
    urgency_level: Optional[UrgencyLevel] = Field(None, description="紧急度级别")
    reasons: List[str] = Field(default=[], description="推荐理由")
    
    # 元数据
    source_id: Optional[str] = Field(None, description="数据源ID")
    source_type: Optional[str] = Field(None, description="数据源类型")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class RecommendationResponse(BaseModel):
    """推荐响应数据模型"""
    recommendations: List[RecommendationItem] = Field(..., description="推荐列表")
    user_id: Optional[int] = Field(None, description="用户ID")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")
    next_refresh: Optional[datetime] = Field(None, description="下次刷新时间")
    algorithm_version: str = Field(default="1.0", description="算法版本")


class UserProfile(BaseModel):
    """用户画像数据模型"""
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    skills: List[str] = Field(default=[], description="技能标签")
    interests: List[str] = Field(default=[], description="兴趣偏好")
    completed_courses: List[int] = Field(default=[], description="已完成课程ID列表")
    current_courses: List[int] = Field(default=[], description="当前学习课程ID列表")
    project_history: List[str] = Field(default=[], description="项目参与历史")
    learning_style: Optional[str] = Field(None, description="学习风格")
    activity_level: Optional[str] = Field(None, description="活跃度级别")


class CourseSelection(BaseModel):
    """选课数据模型"""
    sele_id: int
    user_id: int
    user_name: str
    course_title: str
    course_id: int
    chapter_title: str
    chapter_id: int
    current_serial: int
    deadline: datetime
    url: str
    shushi_id: Optional[int] = None
    shushi_name: Optional[str] = None


class InnoProject(BaseModel):
    """创新项目数据模型"""
    id: int
    task_serial: str
    title: str
    publisher: str
    taker: Optional[str] = None
    taker_id: Optional[int] = None
    status: Optional[str] = "待认领"  # 允许None，默认值
    deadline: datetime
    planed_hour: float
    bonus: Optional[float] = 0.0  # 允许None，默认值
    task_text: Optional[str] = None
    desc: Optional[str] = None
    create_time: datetime


class APIResponse(BaseModel):
    """通用API响应模型"""
    code: int = Field(default=200, description="响应状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")