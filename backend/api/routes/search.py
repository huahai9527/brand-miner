"""
分析启动接口
POST /api/v1/analysis/start — 创建并启动分析任务
"""
import logging
import uuid
from fastapi import APIRouter, BackgroundTasks

from backend.schemas import StartAnalysisRequest, StartAnalysisResponse
from backend.sse_manager import sse_manager
from backend.analysis_orchestrator import AnalysisOrchestrator
from backend.data_sources.adapter import DataSourceAdapter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analysis/start", response_model=StartAnalysisResponse)
async def start_analysis(
    request: StartAnalysisRequest,
    background_tasks: BackgroundTasks,
):
    """
    启动一个新的分析任务

    1. 参数校验（由 Pydantic 自动完成）
    2. 创建 SSE 事件队列
    3. 后台异步启动 AnalysisOrchestrator
    4. 立即返回 task_id
    """
    task_id = str(uuid.uuid4())
    category = request.category

    # 构建约束条件字典（供 orchestrator 使用）
    constraints = {}
    if request.constraints:
        c = request.constraints
        if c.price_min is not None:
            constraints["price_min"] = c.price_min
        if c.price_max is not None:
            constraints["price_max"] = c.price_max
        if c.target_audience:
            constraints["target_audience"] = c.target_audience
        if c.brand_strategy:
            constraints["brand_strategy"] = c.brand_strategy
            if c.brand_strategy == "white_label":
                constraints["prefer_white_label"] = True
            elif c.brand_strategy == "light_brand":
                constraints["prefer_quality"] = True
        if c.priority:
            constraints["priority"] = c.priority
            if c.priority == "volume":
                constraints["prefer_quick_scale"] = True
            elif c.priority == "differentiation":
                constraints["prefer_quality"] = True

    # 创建 SSE 事件队列
    sse_manager.create_task(task_id)

    # 定义 SSE 回调（桥接 orchestrator → SSE）
    def sse_callback(event_type: str, data: dict):
        data["task_id"] = task_id
        sse_manager.push_event(task_id, event_type, data)

    # 后台运行分析
    async def run_task():
        try:
            orch = AnalysisOrchestrator(adapter=DataSourceAdapter())
            await orch.run(
                category=category,
                constraints=constraints,
                on_sse_event=sse_callback,
                sse_task_id=task_id,
            )
        except Exception as e:
            logger.error(f"任务 {task_id} 执行失败: {e}", exc_info=True)
            sse_manager.push_event(task_id, "error", {
                "progress": 100,
                "message": str(e),
            })

    background_tasks.add_task(run_task)

    logger.info(f"创建分析任务: {task_id} — {category}")
    return StartAnalysisResponse(task_id=task_id)
