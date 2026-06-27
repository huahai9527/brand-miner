"""
SSE 事件管理器 — 管理每个分析任务的 SSE 事件队列
用于 AnalysisOrchestrator → SSE Stream 的桥接
"""
import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SSEManager:
    """
    单例模式的 SSE 事件分发器
    每个 task_id 对应一个 asyncio.Queue，生产者推送事件，消费者（SSE Stream）获取事件
    """

    _instance: "SSEManager" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._queues: Dict[str, asyncio.Queue] = {}
            cls._instance._results: Dict[str, Dict[str, Any]] = {}
        return cls._instance

    def create_task(self, task_id: str):
        """为新任务创建事件队列"""
        self._queues[task_id] = asyncio.Queue(maxsize=500)
        self._results[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0,
            "sub_categories": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(f"[SSE] 创建任务队列: {task_id}")

    def push_event(self, task_id: str, event_type: str, data: Dict[str, Any]):
        """推送一个 SSE 事件到指定任务的队列"""
        queue = self._queues.get(task_id)
        if queue is None:
            logger.warning(f"[SSE] 任务 {task_id} 不存在")
            return

        payload = {"event": event_type, "data": data}

        try:
            queue.put_nowait(payload)
        except asyncio.QueueFull:
            logger.warning(f"[SSE] 任务 {task_id} 事件队列已满，丢弃事件 {event_type}")

        # 同步更新结果缓存
        self._update_result_cache(task_id, event_type, data)

    def get_queue(self, task_id: str) -> asyncio.Queue:
        """获取任务的事件队列（消费者使用）"""
        return self._queues.get(task_id)

    def get_result(self, task_id: str) -> Dict[str, Any]:
        """获取任务的当前结果缓存"""
        return self._results.get(task_id, {})

    def cleanup(self, task_id: str):
        """清理任务资源"""
        self._queues.pop(task_id, None)
        # 保留 results 30分钟用于查询
        logger.info(f"[SSE] 清理任务队列: {task_id}")

    def _update_result_cache(self, task_id: str, event_type: str, data: Dict[str, Any]):
        """根据事件类型更新结果缓存"""
        cache = self._results.get(task_id)
        if cache is None:
            return

        cache["progress"] = data.get("progress", cache.get("progress", 0))

        if event_type == "task_start":
            cache["status"] = "running"
            cache["category"] = data.get("category", "")

        elif event_type == "data_ready":
            cache["product_count"] = data.get("product_count", 0)

        elif event_type == "subcategory_done":
            sub = {
                "name": data["sub_category"],
                "total_score": data["score"],
                "recommendation": data["recommendation"],
                "key_insight": data.get("key_insight", ""),
            }
            cache["sub_categories"].append(sub)

        elif event_type == "analysis_done":
            cache["status"] = "ai_generating"
            cache["progress"] = 100
            top = data.get("top_recommendation", {})
            if top:
                cache["top_recommendation"] = {
                    "sub_category": top.get("sub_category", ""),
                    "score": top.get("score", 0),
                    "reason": top.get("entry_suggestion", ""),
                }

        elif event_type == "ai_report_done":
            cache["status"] = "done"
            cache["ai_provider"] = data.get("provider", "")

        elif event_type == "ai_report_fallback":
            cache["status"] = "done"
            cache["ai_report"] = data.get("report", "")
            cache["ai_provider"] = "fallback"

        elif event_type == "error":
            cache["status"] = "failed"
            cache["error"] = data.get("message", "")

    def get_all_task_ids(self) -> list:
        """获取所有任务 ID"""
        return list(self._results.keys())


# 全局单例
sse_manager = SSEManager()
