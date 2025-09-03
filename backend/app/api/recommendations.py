from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import Optional
from datetime import datetime, timedelta
import json
from loguru import logger

from app.models.schemas import APIResponse, RecommendationResponse
from app.services.recommendation_engine import RecommendationEngine
from app.services.cache_service import CacheService

router = APIRouter(prefix="/api/v1", tags=["recommendations"])

# 初始化服务
recommendation_engine = RecommendationEngine()
cache_service = CacheService()


def extract_token(authorization: Optional[str] = Header(None)) -> str:
    """从Header中提取token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少Authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    return authorization[7:]  # 移除 "Bearer " 前缀


def extract_user_id(authorization: Optional[str] = Header(None)) -> int:
    """从token中提取用户ID（简化版本）"""
    # 这里是简化版本，实际应该解析JWT token获取用户ID
    # 暂时使用固定用户ID进行测试
    return 51  # 对应子瑜的user_id


@router.get("/recommend/top3", response_model=APIResponse)
async def get_top3_recommendations(
    request: Request,
    refresh: bool = False,
    user_id: int = Depends(extract_user_id),
    token: str = Depends(extract_token)
):
    """
    获取用户Top3推荐
    
    Args:
        refresh: 是否强制刷新缓存
        user_id: 用户ID（从token中提取）
        token: 用户认证token
    
    Returns:
        APIResponse: 包含推荐列表的响应
    """
    try:
        cache_key = f"recommendations:user:{user_id}"
        
        # 检查缓存（如果不强制刷新）
        if not refresh:
            cached_data = await cache_service.get(cache_key)
            if cached_data:
                # 标记缓存命中
                if hasattr(request, 'state'):
                    request.state.cache_hit = True
                logger.info(f"从缓存返回用户{user_id}的推荐")
                return APIResponse(
                    code=200,
                    message="success",
                    data=cached_data
                )
        
        # 生成新推荐
        logger.info(f"为用户{user_id}生成新推荐")
        recommendations = await recommendation_engine.generate_recommendations(user_id, token)
        
        # 构建响应数据
        response_data = RecommendationResponse(
            recommendations=recommendations,
            user_id=user_id,
            last_updated=datetime.now(),
            next_refresh=datetime.now() + timedelta(hours=2),
            algorithm_version="1.0"
        )
        
        # 缓存结果
        await cache_service.set(cache_key, response_data.dict(), ttl=7200)  # 2小时
        
        logger.info(f"成功为用户{user_id}生成{len(recommendations)}个推荐")
        
        return APIResponse(
            code=200,
            message="success",
            data=response_data.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取推荐失败: 用户{user_id}, 错误: {e}")
        raise HTTPException(status_code=500, detail="服务内部错误")


@router.post("/recommend/feedback")
async def submit_feedback(
    recommendation_id: str,
    feedback_type: str,  # "like", "dislike", "click", "complete"
    user_id: int = Depends(extract_user_id)
):
    """
    提交用户反馈
    
    Args:
        recommendation_id: 推荐项目ID
        feedback_type: 反馈类型
        user_id: 用户ID
    
    Returns:
        APIResponse: 反馈提交结果
    """
    try:
        # 记录用户反馈（这里简化处理，实际应该存储到数据库）
        feedback_data = {
            "user_id": user_id,
            "recommendation_id": recommendation_id,
            "feedback_type": feedback_type,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"用户{user_id}对推荐{recommendation_id}提交了{feedback_type}反馈")
        
        # 如果是完成反馈，清除用户缓存以触发新推荐
        if feedback_type == "complete":
            cache_key = f"recommendations:user:{user_id}"
            await cache_service.delete(cache_key)
            logger.info(f"用户{user_id}完成任务，已清除推荐缓存")
        
        return APIResponse(
            code=200,
            message="反馈提交成功",
            data={"feedback_recorded": True}
        )
        
    except Exception as e:
        logger.error(f"提交反馈失败: {e}")
        raise HTTPException(status_code=500, detail="反馈提交失败")


@router.get("/recommend/explain/{recommendation_id}")
async def explain_recommendation(
    recommendation_id: str,
    user_id: int = Depends(extract_user_id)
):
    """
    解释推荐原因
    
    Args:
        recommendation_id: 推荐项目ID
        user_id: 用户ID
    
    Returns:
        APIResponse: 推荐解释
    """
    try:
        # 从缓存中获取推荐详情
        cache_key = f"recommendations:user:{user_id}"
        cached_data = await cache_service.get(cache_key)
        
        if not cached_data:
            raise HTTPException(status_code=404, detail="推荐数据不存在或已过期")
        
        # 查找指定推荐
        recommendation = None
        for rec in cached_data.get("recommendations", []):
            if rec["id"] == recommendation_id:
                recommendation = rec
                break
        
        if not recommendation:
            raise HTTPException(status_code=404, detail="推荐项目不存在")
        
        # 构建解释数据
        explanation = {
            "recommendation_id": recommendation_id,
            "title": recommendation["title"],
            "total_score": recommendation["score"],
            "score_breakdown": {
                "urgency": {
                    "score": recommendation["urgency"],
                    "weight": "35%",
                    "description": "时间紧迫度：基于DDL和时间敏感性"
                },
                "importance": {
                    "score": recommendation["importance"],
                    "weight": "30%",
                    "description": "重要程度：基于任务的重要性和影响"
                },
                "personal_fit": {
                    "score": recommendation["personal_fit"],
                    "weight": "25%",
                    "description": "个人匹配度：基于技能和兴趣匹配"
                },
                "growth_value": {
                    "score": recommendation["growth_value"],
                    "weight": "10%",
                    "description": "成长价值：完成后的技能提升价值"
                }
            },
            "reasons": recommendation.get("reasons", []),
            "recommendation_type": recommendation["type"],
            "algorithm_version": cached_data.get("algorithm_version", "1.0")
        }
        
        return APIResponse(
            code=200,
            message="success",
            data=explanation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解释推荐失败: {e}")
        raise HTTPException(status_code=500, detail="获取推荐解释失败")


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "what-to-do-agent",
        "version": "1.0.0"
    }