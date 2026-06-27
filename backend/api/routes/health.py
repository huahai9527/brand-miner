"""
Health & Data Source Status 路由
"""
from fastapi import APIRouter
from pathlib import Path

from backend.data_sources.adapter import DataSourceAdapter
from backend.config import TIANCHI_DATA_PATH, JD_CACHE_PATH

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "version": "1.0.0"}


@router.get("/data-source/status")
async def data_source_status():
    """三层数据源状态查询（含详细文件/缓存计数）"""
    adapter = DataSourceAdapter()

    # 基础状态
    status = adapter.get_status()

    # 补充详细统计
    tianchi_dir = Path(TIANCHI_DATA_PATH)
    cache_dir = Path(JD_CACHE_PATH)

    # 天池 CSV 文件数
    csv_count = len(list(tianchi_dir.glob("*.csv"))) if tianchi_dir.exists() else 0
    status["sources"]["tianchi"]["file_count"] = csv_count
    status["sources"]["tianchi"]["description"] = "阿里天池脱敏数据集"

    # JD 缓存文件数
    cache_count = len(list(cache_dir.glob("jd_*.json"))) if cache_dir.exists() else 0
    status["sources"]["jd"]["cache_count"] = cache_count
    status["sources"]["jd"]["description"] = "京东轻量爬虫（30条/次，24h缓存）"

    # Mock 知识库覆盖数
    status["sources"]["mock"]["category_count"] = 10
    status["sources"]["mock"]["description"] = "结构化模拟数据（基于真实市场规律，10大类知识库）"

    return status
