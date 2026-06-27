"""
分析结果接口
- GET /api/v1/analysis/{task_id}/stream   SSE 实时推送
- GET /api/v1/analysis/{task_id}/result   结果查询
- GET /api/v1/analysis/history            历史列表
"""
import asyncio
import json
import logging
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from backend.schemas import HistoryResponse, HistoryItem
from backend.sse_manager import sse_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# ═══════════════ SSE 实时推送 ═══════════════

@router.get("/analysis/{task_id}/stream")
async def stream_analysis(task_id: str):
    """
    核心接口：Server-Sent Events 实时分析进度

    事件顺序：
    task_start → data_fetching → data_ready → subcategory_done(×N) → analysis_done

    心跳：每 15 秒发送 ping，防止连接超时
    间隔：事件间至少 0.3 秒，还原"系统正在思考"体验
    """
    queue = sse_manager.get_queue(task_id)
    if queue is None:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    async def event_generator():
        """SSE 事件生成器"""
        try:
            last_event_time = 0

            while True:
                # 从队列获取事件，最多等 1 秒就发心跳
                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    # 心跳包
                    yield {"event": "ping", "data": str(asyncio.get_event_loop().time())}
                    continue

                if event_data is None:
                    break

                event_type = event_data.get("event", "message")
                data = event_data.get("data", {})

                # 最小间隔（ai_report_chunk 更快，其他保持 0.3s）
                min_delay = 0.05 if event_type == "ai_report_chunk" else 0.3
                now = asyncio.get_event_loop().time()
                elapsed = now - last_event_time
                if elapsed < min_delay:
                    await asyncio.sleep(min_delay - elapsed)
                last_event_time = asyncio.get_event_loop().time()

                # SSE 格式输出
                yield {
                    "event": event_type,
                    "data": json.dumps(data, ensure_ascii=False),
                }

                # ai_report_done / ai_report_fallback / error 后结束流
                if event_type in ("ai_report_done", "ai_report_fallback", "error"):
                    # 再送一个关闭事件
                    yield {
                        "event": "close",
                        "data": json.dumps({"message": "SSE 流已关闭"}),
                    }
                    break

        except asyncio.CancelledError:
            logger.info(f"SSE 连接取消: {task_id}")
        except Exception as e:
            logger.error(f"SSE 异常: {task_id} — {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}),
            }
        finally:
            sse_manager.cleanup(task_id)

    return EventSourceResponse(event_generator())


# ═══════════════ 结果查询 ═══════════════

@router.get("/analysis/{task_id}/result")
async def get_analysis_result(task_id: str):
    """
    获取分析结果

    状态 pending/running → 返回已完成的部分
    状态 done → 返回完整结果
    状态 failed → 返回错误
    不存在 → 404
    """
    cached = sse_manager.get_result(task_id)
    if not cached or "status" not in cached:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")

    # 尝试从 orchestrator 内存获取完整结果
    # Phase 2 中 orchestrator 返回结果在内存中，这里先用缓存
    # Phase 4 可以从数据库读取

    status = cached.get("status", "pending")
    response = {
        "task_id": task_id,
        "status": status,
        "progress": cached.get("progress", 0),
        "category": cached.get("category", ""),
        "constraints": cached.get("constraints"),
        "sub_categories": cached.get("sub_categories", []),
        "top_recommendation": cached.get("top_recommendation"),
        "error": cached.get("error"),
        "created_at": cached.get("created_at", ""),
    }

    return response


# ═══════════════ 历史列表 ═══════════════

@router.get("/analysis/history")
async def get_analysis_history(limit: int = 10):
    """
    获取最近的分析任务历史

    Phase 4 可以从数据库读取，目前从内存
    """
    all_ids = sse_manager.get_all_task_ids()

    items = []
    for tid in reversed(all_ids):
        cached = sse_manager.get_result(tid)
        if not cached:
            continue

        top_rec = cached.get("top_recommendation", {})
        items.append(HistoryItem(
            task_id=tid,
            category=cached.get("category", ""),
            status=cached.get("status", "pending"),
            top_recommendation=top_rec.get("sub_category") if top_rec else None,
            created_at=cached.get("created_at", ""),
        ))

        if len(items) >= limit:
            break

    return HistoryResponse(tasks=items, total=len(items))
