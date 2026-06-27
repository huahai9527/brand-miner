"""
AI 模块 — LLM 客户端 + 报告生成
"""
from backend.ai.llm_client import LLMClient, llm_client
from backend.ai.report_generator import ReportGenerator

__all__ = ["LLMClient", "llm_client", "ReportGenerator"]
