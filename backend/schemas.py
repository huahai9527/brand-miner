"""
Pydantic 请求/响应模型 — 所有 API 接口的类型定义
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


# ═══════════════ POST /api/v1/analysis/start ═══════════════

class Constraints(BaseModel):
    """用户约束条件"""
    price_min: Optional[float] = Field(None, ge=0, description="价格下限")
    price_max: Optional[float] = Field(None, ge=0, description="价格上限")
    target_audience: Optional[str] = Field(None, description="目标客群：年轻人/宝妈/老年人/通用")
    brand_strategy: Optional[str] = Field(
        None,
        description="品牌策略：white_label（白牌）/ light_brand（轻品牌）/ quality_up（品质升级）"
    )
    priority: Optional[str] = Field(
        None,
        description="优先策略：volume（起量）/ margin（利润）/ differentiation（差异化）"
    )

    @model_validator(mode="after")
    def validate_price_range(self):
        if self.price_min is not None and self.price_max is not None:
            if self.price_min > self.price_max:
                raise ValueError("price_min 不能大于 price_max")
        return self


class StartAnalysisRequest(BaseModel):
    """启动分析任务请求"""
    category: str = Field(..., min_length=1, max_length=128, description="大类关键词")
    constraints: Optional[Constraints] = Field(default_factory=Constraints)


class StartAnalysisResponse(BaseModel):
    """启动分析任务响应"""
    task_id: str
    status: str = "pending"
    message: str = "分析任务已创建，请通过 SSE 接口监听进度"


# ═══════════════ SSE 事件类型 ═══════════════

class SSEEvent(BaseModel):
    """SSE 事件基类"""
    event: str
    data: Dict[str, Any]


# ═══════════════ GET /api/v1/analysis/{task_id}/result ═══════════════

class ScoreBreakdownItem(BaseModel):
    score: float
    weight: float


class SubCategoryResult(BaseModel):
    """单个细分方向的结果"""
    name: str
    total_score: float
    recommendation: str
    score_breakdown: Dict[str, ScoreBreakdownItem]
    white_brand_ratio: float
    growth_rate: float
    avg_price: float
    suggested_price_entry: float
    top_pain_points: List[Dict[str, Any]]
    key_insight: str
    entry_suggestion: str


class TopRecommendation(BaseModel):
    sub_category: str
    score: float
    reason: str


class AnalysisResultResponse(BaseModel):
    """分析结果响应"""
    task_id: str
    status: str
    progress: int
    category: str
    constraints: Optional[Dict[str, Any]] = None
    sub_categories: List[SubCategoryResult] = []
    top_recommendation: Optional[TopRecommendation] = None
    error: Optional[str] = None
    created_at: Optional[str] = None


# ═══════════════ GET /api/v1/analysis/history ═══════════════

class HistoryItem(BaseModel):
    task_id: str
    category: str
    status: str
    top_recommendation: Optional[str] = None
    created_at: str


class HistoryResponse(BaseModel):
    tasks: List[HistoryItem]
    total: int


# ═══════════════ POST /api/v1/price/compare ═══════════════

class PriceCompareRequest(BaseModel):
    category: str = Field(..., min_length=1, max_length=128)
    sub_category: Optional[str] = Field(None)


class PriceDistributionItem(BaseModel):
    range: str
    count: int
    sales_ratio: float


class CompetitorSummary(BaseModel):
    total_products: int
    white_brand_ratio: float
    top3_brands: List[Dict[str, Any]]


class PriceCompareResponse(BaseModel):
    category: str
    price_analysis: Dict[str, Any]
    competitor_summary: CompetitorSummary
