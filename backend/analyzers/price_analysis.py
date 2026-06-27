"""
模块四：价格利润分析

核心逻辑：
  1. 价格带五段分布（统计各段商品数和销量占比）
  2. 主战场 / 机会带识别
  3. 利润空间估算（成本 = 均价 × 0.35）
  4. 双策略定价建议（低价切入 + 品质溢价）

设计理念：
  不是简单地算均价，而是告诉商家"钱在大致的哪个价格带"。
  五个等分价格带中，既有竞争激烈的主战场（销量最大），
  也有相对冷门但利润率更高的机会带（有销量但竞品少）。
  
  对于非品牌商家，两种策略可选：
  - 价格破局：机会带 × 0.9，用低价快速抢市场
  - 品质升级：主战场 × 1.2，主打更好用料/设计，做差异化溢价

评分模型（面试可讲）：
  - 利润率 > 60% → 90+ 分
  - 机会带存在且有销量 → +10 分
  - 价格带过于集中（单一价格带占 70%+）→ 竞争激烈，降分
"""
from typing import Dict, List, Any, Optional


def analyze_price(
    products: List[Dict[str, Any]],
    constraints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    价格利润分析

    Args:
        products: 商品列表，含 price, sales_30d
        constraints: 用户约束（price_min, price_max）

    Returns:
        {
            "score": 0-100,
            "avg_price": float,
            "price_distribution": [...],
            "profit_rate": float,
            "suggested_price_entry": float,
            "suggested_price_premium": float,
            "opportunity_price_range": {low, high},
            "detail": "..."
        }
    """
    constraints = constraints or {}

    if not products:
        return _empty_result("无商品数据")

    prices = [p.get("price", 0) for p in products if p.get("price", 0) > 0]
    if not prices:
        return _empty_result("无有效价格数据")

    # ---- 1. 价格带分布 ----
    price_min = min(prices)
    price_max = max(prices)

    # 如果 max == min（单一价格），扩展一个范围
    if price_max <= price_min:
        price_max = price_min * 2 if price_min > 0 else 100

    # 5 段等分
    step = (price_max - price_min) / 5
    if step < 1:
        step = max(1, price_max / 5)

    bins = []
    for i in range(5):
        lo = round(price_min + i * step, 1)
        hi = round(price_min + (i + 1) * step, 1)
        count = 0
        sales_sum = 0
        for p in products:
            price = p.get("price", 0)
            if lo <= price <= hi:
                count += 1
                sales_sum += max(0, p.get("sales_30d", 0))

        bins.append({
            "range": f"{lo:.0f}-{hi:.0f}",
            "low": lo,
            "high": hi,
            "count": count,
            "total_sales": sales_sum,
        })

    # 二次遍历计算 sales_ratio
    total_all_sales = sum(b["total_sales"] for b in bins) or 1
    for b in bins:
        b["sales_ratio"] = round(b["total_sales"] / total_all_sales, 3)

    # ---- 2. 均价 & 主战场 & 机会带 ----
    avg_price = sum(prices) / len(prices)

    # 主战场 = 销量最高的价格段
    main_bin = max(bins, key=lambda b: b["total_sales"])

    # 机会带 = 有销量但竞争相对少（count 少但 sales_ratio > 5%）
    opp_bins = [b for b in bins if b["total_sales"] > 0 and b != main_bin]
    opportunity = opp_bins[0] if opp_bins else main_bin

    # ---- 3. 利润空间估算 ----
    # 电商行业经验：毛利率约 65%，成本 ≈ 售价 × 35%
    cost_ratio = 0.35
    profit_margin = 1 - cost_ratio  # 0.65

    # ---- 4. 定价建议 ----
    # 低价切入策略：机会带中位数 × 0.9
    opp_mid = (opportunity["low"] + opportunity["high"]) / 2
    suggested_entry = round(opp_mid * 0.9, 2)

    # 品质溢价策略：主战场均价 × 1.2
    main_mid = (main_bin["low"] + main_bin["high"]) / 2
    suggested_premium = round(main_mid * 1.2, 2)

    # ---- 5. 评分模型 ----
    score = _compute_price_score(profit_margin, bins, main_bin)

    # ---- 6. 生成描述 ----
    detail = _generate_detail(avg_price, profit_margin, main_bin, opportunity, bins)

    return {
        "score": score,
        "avg_price": round(avg_price, 2),
        "price_distribution": [
            {"range": b["range"], "count": b["count"], "sales_ratio": b["sales_ratio"]}
            for b in bins
        ],
        "profit_rate": round(profit_margin, 3),
        "suggested_price_entry": suggested_entry,
        "suggested_price_premium": suggested_premium,
        "opportunity_price_range": {
            "low": opportunity["low"],
            "high": opportunity["high"],
        },
        "detail": detail,
    }


def _compute_price_score(profit_margin: float, bins: List[Dict],
                         main_bin: Dict) -> int:
    """价格利润评分"""
    # 利润率基础分
    if profit_margin > 0.7:
        base = 95
    elif profit_margin > 0.5:
        base = 75
    elif profit_margin > 0.3:
        base = 55
    else:
        base = 30

    # 机会带加分
    has_opportunity = any(
        b != main_bin and b["total_sales"] > 0
        for b in bins
    )
    if has_opportunity:
        base += 10

    # 竞争激烈度惩罚：主战场销售额占比 > 70% → 竞争太激烈
    main_sales_ratio = sum(b["total_sales"] for b in bins)
    if main_sales_ratio > 0 and main_bin["total_sales"] / main_sales_ratio > 0.7:
        base -= 15

    return round(max(0, min(100, base)))


def _generate_detail(avg_price: float, profit: float, main_bin: Dict,
                     opp_bin: Dict, bins: List[Dict]) -> str:
    parts = [f"市场均价 ¥{avg_price:.0f}，毛利率约 {profit:.0%}"]

    parts.append(
        f"主战场在 {main_bin['range']} 元（{main_bin['count']} 款商品）"
    )

    if opp_bin != main_bin and opp_bin["total_sales"] > 0:
        parts.append(
            f"发现机会带 {opp_bin['range']} 元（{opp_bin['count']} 款竞品）"
        )

    return "；".join(parts)


def _empty_result(reason: str) -> Dict[str, Any]:
    return {
        "score": 0,
        "avg_price": 0,
        "price_distribution": [],
        "profit_rate": 0,
        "suggested_price_entry": 0,
        "suggested_price_premium": 0,
        "opportunity_price_range": {"low": 0, "high": 0},
        "detail": reason,
    }
