import httpx
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from loguru import logger
from app.core.config import get_settings
from app.models.schemas import CourseSelection, InnoProject

settings = get_settings()


class ZishuAPIClient:
    """自塾API客户端"""
    
    def __init__(self):
        self.base_url = settings.zishu_api_base
        self.timeout = settings.zishu_timeout
        
    async def _make_request(self, method: str, endpoint: str, 
                          headers: Optional[Dict] = None, 
                          params: Optional[Dict] = None,
                          json_data: Optional[Dict] = None) -> Any:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"API请求失败: {url}, 错误: {e}")
                raise
            except Exception as e:
                logger.error(f"未知错误: {e}")
                raise
    
    async def authenticate(self, phone: str, password: str) -> Dict:
        """用户认证"""
        data = {
            "phone": phone,
            "password": password
        }
        return await self._make_request(
            "POST", 
            "/users/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            json_data=data
        )
    
    async def get_all_courses(self) -> List[Dict]:
        """获取所有课程"""
        return await self._make_request("GET", endpoint="/course/fetch_all_courses")
    
    async def get_user_selections(self, token: str) -> List[CourseSelection]:
        """获取用户选课信息"""
        headers = {"Authorization": f"Bearer {token}"}
        data = await self._make_request("GET", "/course/fetch_selections", headers=headers)
        
        # 转换为Pydantic模型
        selections = []
        for item in data:
            try:
                # 处理时间字段
                deadline_str = item["deadline"]
                if deadline_str.endswith("Z"):
                    deadline_str = deadline_str.replace("Z", "+00:00")
                elif "+" not in deadline_str and "Z" not in deadline_str:
                    deadline_str += "+00:00"
                
                selection = CourseSelection(
                    sele_id=item["sele_id"],
                    user_id=item["user_id"],
                    user_name=item["user_name"],
                    course_title=item["course_title"],
                    course_id=item["course_id"],
                    chapter_title=item["chapter_title"],
                    chapter_id=item["chapter_id"],
                    current_serial=item["current_serial"],
                    deadline=datetime.fromisoformat(deadline_str),
                    url=item["url"],
                    shushi_id=item.get("shushi_id"),
                    shushi_name=item.get("shushi_name")
                )
                selections.append(selection)
            except Exception as e:
                logger.warning(f"解析选课数据失败: {item.get('course_title', 'Unknown')}, 错误: {e}")
                continue
        
        return selections
    
    async def get_all_groups(self) -> List[Dict]:
        """获取所有创新小组"""
        return await self._make_request("GET", "/inno/fetch_allgroup")
    
    async def get_current_projects(self) -> List[InnoProject]:
        """获取当前项目"""
        data = await self._make_request("GET", "/inno/fetch_current_projects")
        
        # 转换为Pydantic模型
        projects = []
        for item in data:
            try:
                # 处理时间字段
                deadline_str = item["deadline"]
                if deadline_str.endswith("Z"):
                    deadline_str = deadline_str.replace("Z", "+00:00")
                elif "+" not in deadline_str and "Z" not in deadline_str:
                    deadline_str += "+00:00"
                
                create_time_str = item["create_time"]
                if "+" not in create_time_str and "Z" not in create_time_str:
                    create_time_str += "+00:00"
                
                project = InnoProject(
                    id=item["id"],
                    task_serial=item["task_serial"],
                    title=item["title"],
                    publisher=item["publisher"],
                    taker=item.get("taker"),
                    taker_id=item.get("taker_id"),
                    status=item.get("status", "待认领"),  # 默认状态
                    deadline=datetime.fromisoformat(deadline_str),
                    planed_hour=item["planed_hour"],
                    bonus=item.get("bonus", 0.0) or 0.0,  # 处理None值
                    task_text=item.get("task_text"),
                    desc=item.get("desc", ""),
                    create_time=datetime.fromisoformat(create_time_str)
                )
                projects.append(project)
            except Exception as e:
                logger.warning(f"解析项目数据失败: {item.get('title', 'Unknown')}, 错误: {e}")
                continue
        
        return projects
    
    async def get_user_goal(self, user_id: int) -> Optional[Dict]:
        """获取用户目标"""
        try:
            return await self._make_request("GET", f"/users/fetch_goal/{user_id}")
        except:
            return None
    
    async def get_user_reports(self, user_id: int) -> List[Dict]:
        """获取用户学时申报记录"""
        try:
            return await self._make_request("GET", f"/users/fetch_reports/{user_id}")
        except:
            return []
    
    async def get_questions(self, token: str) -> List[Dict]:
        """获取题库"""
        headers = {"Authorization": f"Bearer {token}"}
        try:
            return await self._make_request("GET", "/ques/showques", headers=headers)
        except:
            return []
    
    async def get_test_papers(self, token: str) -> List[Dict]:
        """获取试卷"""
        headers = {"Authorization": f"Bearer {token}"}
        try:
            return await self._make_request("GET", "/ques/showtest", headers=headers)
        except:
            return []