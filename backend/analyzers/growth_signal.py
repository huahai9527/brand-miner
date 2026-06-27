"""
模块二：自然增长信号分析

核心逻辑：
  1. 计算细分品类整体增速（近30天销量相对于市场体量的比例）
  2. 识别自然增长 vs 广告刷单（销量增速 vs 评论增速协调性判定）
  3. 综合评分（0-100）

设计理念：
  我们关注的是"真实的、可持续的市场需求增长"，而非短期广告投放砸出来的虚假繁荣。
  销量涨但评论不涨 → 可能是刷单/SKU合并操作，降权。
  销量和评论同步增长 → 真实用户购买行为，加权。
  
评分模型（面试可讲）：
  - 增速 > 50% → 90+ 分（爆发品类）
  - 增速 0-30% → 60-80 分（稳健增长）
  - 负增长 → < 30 分（衰退市场，避开）
  - 自然增长判定成功 → +10 分奖励
"""
from typing import Dict, List, Any


def analyze_growth_signal(
    products: List[Dict[str, Any]],
    reviews: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    增长信号分析

    Args:
        products: 商品列表，含 sales_30d, review_count, growth_rate（可选）
        reviews: 评论列表（可选，用于自然增长判定）

    Returns:
        {
            "score": 0-100,
            "growth_rate": float,
            "is_natural_growth": bool,
            "trend": "rising/stable/declining",
            "detail": "..."
        }
    """
    if not products:
        return _empty_result("无商品数据")

    # ---- 1. 汇总数据 ----
    total_sales_30d = sum(max(0, p.get("sales_30d", 0)) for p in products)
    total_reviews = sum(max(0, p.get("review_count", 0)) for p in products)

    # 从商品数据中提取预置的 growth_rate（Mock 引擎已计算）
    growth_rates = [p.get("growth_rate", 0) for p in products if p.get("growth_rate") is not None]
    if growth_rates:
        avg_growth = sum(growth_rates) / len(growth_rates)
    else:
        # 没有预设增长率时，用销量/评论比推算
        avg_growth = _estimate_growth(total_sales_30d, total_reviews)

    # ---- 2. 自然增长判定 ----
    is_natural = _detect_natural_growth(products, reviews or [])

    # ---- 3. 评分模型 ----
    score = _compute_score(avg_growth, is_natural)

    # ---- 4. 趋势判定 ----
    trend = _classify_trend(avg_growth)

    # ---- 5. 生成描述 ----
    detail = _generate_detail(avg_growth, is_natural, score, total_sales_30d, total_reviews)

    return {
        "score": score,
        "growth_rate": round(avg_growth, 3),
        "is_natural_growth": is_natural,
        "trend": trend,
        "detail": detail,
    }


def _estimate_growth(total_sales: int, total_reviews: int) -> float:
    """
    根据销量与评论的比例推算增速
    电商经验：月销/累计评论 ≈ 30-60 说明活跃；<10 说明疲软
    """
    if total_reviews == 0:
        return 0.1  # 谨慎乐观

    ratio = total_sales / total_reviews
    if ratio > 40:
        return 0.60  # 爆发
    elif ratio > 20:
        return 0.30
    elif ratio > 10:
        return 0.10
    else:
        return -0.05


def _detect_natural_growth(products: List[Dict], reviews: List[Dict]) -> bool:
    """
    自然增长判定算法：
    1. 取销量 TOP 20% 的商品作为样本（主力SKU）
    2. 计算这些商品的"评销比"（review_count / sales_30d）
    3. 如果评销比正常（> 1%），说明评论和销量同步，自然增长
    4. 如果评销比异常低（< 0.5%），疑似刷单
    """
    if not reviews:
        # 无评论数据 → 保守判定为非自然增长
        return False

    # 取 TOP20% 商品
    sorted_products = sorted(products, key=lambda p: p.get("sales_30d", 0), reverse=True)
    top_n = max(3, len(sorted_products) // 5)
    top_products = sorted_products[:top_n]

    natural_count = 0
    for p in top_products:
        sales = max(1, p.get("sales_30d", 0))
        reviews_count = max(0, p.get("review_count", 0))
        ratio = reviews_count / sales
        if ratio > 0.01:  # 评销比 > 1%
            natural_count += 1

    # 超过 60% 的TOP商品评销比正常 → 判定为自然增长
    return natural_count / len(top_products) > 0.6


def _compute_score(growth_rate: float, is_natural: bool) -> int:
    """将增长率映射为 0-100 分"""
    if growth_rate > 0.5:
        base = 90
    elif growth_rate > 0.3:
        base = 80
    elif growth_rate > 0.1:
        base = 65
    elif growth_rate > 0:
        base = 50
    elif growth_rate > -0.1:
        base = 30
    else:
        base = 10

    # 自然增长加分
    if is_natural:
        base += 10

    return round(min(100, max(0, base)))


def _classify_trend(growth_rate: float) -> str:
    if growth_rate > 0.15:
        return "rising"
    elif growth_rate > -0.05:
        return "stable"
    else:
        return "declining"


def _generate_detail(growth_rate: float, is_natural: bool, score: int,
                     total_sales: int, total_reviews: int) -> str:
    parts = [f"近30天总销量 {total_sales}，总评论 {total_reviews}"]

    if growth_rate > 0.3:
        parts.append(f"增长率 {growth_rate:.0%}，呈强上升趋势")
    elif growth_rate > 0:
        parts.append(f"增长率 {growth_rate:.0%}，平稳增长")
    else:
        parts.append(f"增长率 {growth_rate:.0%}，市场可能萎缩")

    if is_natural:
        parts.append("判定为自然增长（销量与评论同步），非广告驱动")
    else:
        parts.append("增长信号中存在异常模式，需警惕刷单可能")

    return "；".join(parts)


def _empty_result(reason: str) -> Dict[str, Any]:
    return {
        "score": 0,
        "growth_rate": 0,
        "is_natural_growth": False,
        "trend": "stable",
        "detail": reason,
    }
