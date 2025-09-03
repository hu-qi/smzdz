from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict

from app.models.schemas import APIResponse
from app.services.performance import performance_monitor

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/performance", response_model=APIResponse)
async def get_performance_stats():
    """
    获取性能统计
    
    Returns:
        APIResponse: 性能统计数据
    """
    try:
        stats = await performance_monitor.get_performance_stats()
        
        return APIResponse(
            code=200,
            message="success",
            data={
                "performance_stats": stats,
                "timestamp": datetime.now().isoformat(),
                "service": "what-to-do-agent"
            }
        )
        
    except Exception as e:
        return APIResponse(
            code=500,
            message=f"获取性能统计失败: {e}",
            data=None
        )


@router.post("/performance/reset", response_model=APIResponse)
async def reset_performance_stats():
    """
    重置性能统计
    
    Returns:
        APIResponse: 重置结果
    """
    try:
        await performance_monitor.reset_metrics()
        
        return APIResponse(
            code=200,
            message="性能统计已重置",
            data={"reset_timestamp": datetime.now().isoformat()}
        )
        
    except Exception as e:
        return APIResponse(
            code=500,
            message=f"重置性能统计失败: {e}",
            data=None
        )


@router.get("/system/status", response_model=APIResponse)
async def get_system_status():
    """
    获取系统状态
    
    Returns:
        APIResponse: 系统状态信息
    """
    try:
        # 获取性能统计
        performance_stats = await performance_monitor.get_performance_stats()
        
        # 系统状态信息
        system_info = {
            "service_name": "什么值得做智能体",
            "version": "1.0.0",
            "status": "running",
            "uptime": "计算中...",  # 实际应用中计算服务运行时间
            "performance": performance_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        return APIResponse(
            code=200,
            message="success",
            data=system_info
        )
        
    except Exception as e:
        return APIResponse(
            code=500,
            message=f"获取系统状态失败: {e}",
            data=None
        )