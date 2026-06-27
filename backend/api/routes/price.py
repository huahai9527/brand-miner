"""
比价查询接口
POST /api/v1/price/compare — 快速比价，不创建完整分析任务
"""
import logging
from fastapi import APIRouter

from backend.schemas import PriceCompareRequest
from backend.data_sources.adapter import DataSourceAdapter
from backend.analyzers.price_analysis import analyze_price
from backend.analyzers.brand_vacuum import analyze_brand_vacuum

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/price/compare")
async def compare_price(request: PriceCompareRequest):
    """
    快速比价查询
    直接调用数据源 + 价格分析模块，无需创建完整分析任务
    适用于用户想快速了解某个品类的价格现状
    """
    adapter = DataSourceAdapter()

    # 获取商品数据
    products = adapter.fetch(keyword=request.category, count=100)

    # 按细分方向过滤（如果指定）
    if request.sub_category:
        products = [p for p in products
                    if p.get("sub_category", "") == request.sub_category]

    if not products:
        return {
            "category": request.category,
            "error": "无可用数据",
        }

    # 价格分析
    price_result = analyze_price(products)

    # 竞品分析
    brand_result = analyze_brand_vacuum(products)

    # TOP3 品牌
    brand_sales = {}
    for p in products:
        b = p.get("brand", "白牌")
        brand_sales[b] = brand_sales.get(b, 0) + max(0, p.get("sales_30d", 0))

    total_sales = sum(brand_sales.values()) or 1
    top3 = sorted(brand_sales.items(), key=lambda x: -x[1])[:3]

    return {
        "category": request.category,
        "price_analysis": {
            "avg_price": price_result["avg_price"],
            "min_price": min(p.get("price", 0) for p in products),
            "max_price": max(p.get("price", 0) for p in products),
            "price_distribution": price_result["price_distribution"],
            "opportunity_range": price_result["opportunity_price_range"],
            "suggested_entry_price": price_result["suggested_price_entry"],
            "suggested_premium_price": price_result["suggested_price_premium"],
            "profit_rate": price_result["profit_rate"],
        },
        "competitor_summary": {
            "total_products": len(products),
            "white_brand_ratio": brand_result["white_brand_ratio"],
            "top3_brands": [
                {"brand": b, "market_share": round(s / total_sales, 3)}
                for b, s in top3
            ],
        },
    }
