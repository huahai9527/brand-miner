"""
报告查询接口
GET /api/v1/report/{task_id} — 返回 Report 表完整数据
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from backend.database.session import async_session
from backend.database.models import Report, AnalysisTask

router = APIRouter()


@router.get("/report/{task_id}")
async def get_report(task_id: str):
    """
    获取完整的分析报告数据（通过 SSE task_id UUID 查询）
    """
    async with async_session() as session:
        # 先通过 UUID task_id 查找 AnalysisTask，再关联 Report
        stmt = select(AnalysisTask).where(AnalysisTask.task_id == task_id)
        result = await session.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        report_stmt = select(Report).where(Report.task_id == task.id)
        report_result = await session.execute(report_stmt)
        report = report_result.scalar_one_or_none()

        if not report:
            raise HTTPException(status_code=404, detail="报告不存在")

        return {
            "id": report.id,
            "task_id": task.task_id,
            "content": report.content,
            "top_direction": report.top_direction,
            "pricing_suggestion": report.pricing_suggestion,
            "entry_strategy": report.entry_strategy,
            "created_at": report.created_at.isoformat() if report.created_at else None,
        }
