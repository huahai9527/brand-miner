"""
Brand Miner — FastAPI 主入口
启动：python -m backend.main (从 brand-miner/ 目录)
"""
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import HOST, PORT, CORS_ORIGINS
from backend.database.session import init_db
from backend.api.routes.health import router as health_router
from backend.api.routes.search import router as search_router
from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.price import router as price_router
from backend.api.routes.report import router as report_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s — %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时建表"""
    logger.info("Brand Miner 启动中...")
    await init_db()
    logger.info("数据库表已就绪")
    yield
    logger.info("Brand Miner 已关闭")


app = FastAPI(
    title="Brand Miner — 智能选品比价引擎",
    description="帮助非品牌/小品牌商家，输入大类方向和约束条件，输出可执行的选品决策报告",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — 允许前端 localhost:5173 访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册 — /api/v1 前缀
app.include_router(health_router, prefix="/api/v1", tags=["System"])
app.include_router(search_router, prefix="/api/v1", tags=["Analysis"])
app.include_router(analysis_router, prefix="/api/v1", tags=["Analysis"])
app.include_router(price_router, prefix="/api/v1", tags=["Price"])
app.include_router(report_router, prefix="/api/v1", tags=["Report"])


# ===================== 直接运行 =====================
if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=True,
    )
