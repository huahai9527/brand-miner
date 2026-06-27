"""
应用配置模块
统一管理环境变量和应用设置
"""
import os
from pathlib import Path

# 项目根目录 (brand-miner/)
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 .env 文件（本地开发）
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# --- 数据源配置 ---
DATA_SOURCE = os.getenv("DATA_SOURCE", "mock")  # tianchi / jd / mock
TIANCHI_DATA_PATH = os.getenv("TIANCHI_DATA_PATH", str(BASE_DIR / "data" / "real"))
JD_CACHE_PATH = os.getenv("JD_CACHE_PATH", str(BASE_DIR / "data" / "cache"))
USE_MOCK_FALLBACK = os.getenv("USE_MOCK_FALLBACK", "true").lower() == "true"

# --- 数据库配置 ---
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'brand_miner.db'}"
)

# --- 服务配置 ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# --- CORS ---
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://brand-miner.pages.dev",
    "https://*.pages.dev",
]

# --- JD 爬虫配置 ---
JD_MAX_ITEMS = 30
JD_MIN_DELAY = 2
JD_MAX_DELAY = 5
JD_CACHE_TTL_HOURS = 24

# --- LLM 配置 (DeepSeek) ---
# API Key 只从环境变量读取，不硬编码
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY", os.getenv("LLM_API_KEY", ""))
LLM_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1"))
LLM_MODEL = os.getenv("DEEPSEEK_MODEL", os.getenv("LLM_MODEL", "deepseek-chat"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
