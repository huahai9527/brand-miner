"""
模块五：综合评分与选品决策引擎

核心逻辑：
  1. 加权综合评分公式
  2. 根据用户约束动态调整权重
  3. 推荐等级判定
  4. 核心洞察 & 切入建议生成

评分公式（面试时可讲的核心方法论）：
  综合评分 = 
    品牌真空度得分  × 0.35
    + 增长信号得分  × 0.30
    + 痛点密度得分  × 0.20
    + 价格利润得分  × 0.15

权重设计理念：
  - 品牌真空度最重（35%）：对于非品牌商家，最大的机会在于市场没有品牌壁垒
  - 增长信号次之（30%）：选品最终要看是否在上升期
  - 痛点密度（20%）：差异化切入的抓手
  - 价格利润（15%）：利润是结果，前三个维度决定利润空间

动态权重调整（根据用户约束）：
  - "白牌优先" → 品牌真空度 +5%，利润 -5%
  - "快速起量" → 增长信号 +5%，痛点 -5%
  - "差异化/品质" → 痛点 +5%，增长 -5%
"""
from typing import Dict, List, Any, Optional


# 基础权重（总和 = 1.0）
BASE_WEIGHTS = {
    "brand_vacuum": 0.35,
    "growth_signal": 0.30,
    "pain_point": 0.20,
    "price_profit": 0.15,
}

# 推荐等级阈值
RECOMMENDATION_THRESHOLDS = {
    "recommended": 70,
    "neutral": 50,
    # < 50 → not_recommended
}


def compute_overall_score(
    brand_vacuum_result: Dict[str, Any],
    growth_signal_result: Dict[str, Any],
    pain_point_result: Dict[str, Any],
    price_profit_result: Dict[str, Any],
    constraints: Optional[Dict[str, Any]] = None,
    sub_category: str = "",
) -> Dict[str, Any]:
    """
    综合评分计算

    Args:
        brand_vacuum_result: 品牌真空度分析结果
        growth_signal_result: 增长信号分析结果
        pain_point_result: 用户痛点分析结果
        price_profit_result: 价格利润分析结果
        constraints: 用户约束条件，影响权重调整
        sub_category: 细分品类名称

    Returns:
        {
            "sub_category": str,
            "total_score": float,
            "recommendation": "recommended/neutral/not_recommended",
            "score_breakdown": {...},
            "key_insight": "一句话核心洞察",
            "entry_suggestion": "切入策略建议"
        }
    """
    constraints = constraints or {}

    # ---- 1. 获取各模块分数 ----
    raw_scores = {
        "brand_vacuum": brand_vacuum_result.get("score", 0),
        "growth_signal": growth_signal_result.get("score", 0),
        "pain_point": pain_point_result.get("score", 0),
        "price_profit": price_profit_result.get("score", 0),
    }

    # ---- 2. 动态权重调整 ----
    weights = _adjust_weights(constraints)

    # ---- 3. 加权计算 ----
    total_score = 0
    score_breakdown = {}
    for key, w in weights.items():
        weighted = raw_scores[key] * w
        total_score += weighted
        score_breakdown[key] = {
            "score": raw_scores[key],
            "weight": w,
            "weighted": round(weighted, 2),
        }

    total_score = round(total_score, 1)

    # ---- 4. 推荐等级 ----
    recommendation = _classify_recommendation(total_score)

    # ---- 5. 核心洞察 ----
    key_insight = _generate_key_insight(
        sub_category, total_score, recommendation, score_breakdown
    )

    # ---- 6. 切入建议 ----
    entry_suggestion = _generate_entry_suggestion(
        recommendation, brand_vacuum_result, growth_signal_result,
        pain_point_result, price_profit_result, constraints,
    )

    return {
        "sub_category": sub_category,
        "total_score": total_score,
        "recommendation": recommendation,
        "score_breakdown": score_breakdown,
        "key_insight": key_insight,
        "entry_suggestion": entry_suggestion,
    }


def _adjust_weights(constraints: Dict[str, Any]) -> Dict[str, float]:
    """
    根据用户约束条件动态调整权重

    规则：
    - prefer_white_label → 品牌真空 +0.05, 利润 -0.05
    - prefer_quick_scale → 增长 +0.05, 痛点 -0.05
    - prefer_quality → 痛点 +0.05, 增长 -0.05

    确保权重总和始终 = 1.0
    """
    weights = dict(BASE_WEIGHTS)

    if constraints.get("prefer_white_label"):
        weights["brand_vacuum"] += 0.05
        weights["price_profit"] -= 0.05

    if constraints.get("prefer_quick_scale"):
        weights["growth_signal"] += 0.05
        weights["pain_point"] -= 0.05

    if constraints.get("prefer_quality"):
        weights["pain_point"] += 0.05
        weights["growth_signal"] -= 0.05

    # 防止负值
    for k in weights:
        weights[k] = max(0.05, min(0.50, weights[k]))

    # 归一化
    total = sum(weights.values())
    if total > 0:
        weights = {k: round(v / total, 4) for k, v in weights.items()}

    return weights


def _classify_recommendation(total_score: float) -> str:
    if total_score >= RECOMMENDATION_THRESHOLDS["recommended"]:
        return "recommended"
    elif total_score >= RECOMMENDATION_THRESHOLDS["neutral"]:
        return "neutral"
    else:
        return "not_recommended"


def _generate_key_insight(
    sub_category: str,
    total_score: float,
    recommendation: str,
    score_breakdown: Dict[str, Any],
) -> str:
    """生成一句话核心洞察 — 基于四维数据差异化"""

    scores = {k: v["score"] for k, v in score_breakdown.items()}
    best_dim_key = max(scores, key=scores.get)
    best_score = scores[best_dim_key]

    dim_labels = {
        "brand_vacuum": "品牌真空度",
        "growth_signal": "增长信号",
        "pain_point": "痛点机会",
        "price_profit": "利润空间",
    }

    # 分数偏低 → 谨慎建议
    if total_score < 65:
        return (
            f"「{sub_category}」竞争较激烈（{total_score}分），"
            f"建议充分调研后谨慎入场"
        )

    # 品牌真空度最高（>75）→ 强调品牌集中度低
    if best_dim_key == "brand_vacuum" and best_score > 75:
        return (
            f"「{sub_category}」品牌集中度低，白牌占比高，"
            f"非品牌商家切入阻力小（品牌真空度{best_score:.0f}分）"
        )

    # 增长信号最高（>75）→ 强调市场上升期
    if best_dim_key == "growth_signal" and best_score > 75:
        return (
            f"「{sub_category}」市场处于上升期，新品活跃度高，"
            f"需求增长明显（增长信号{best_score:.0f}分）"
        )

    # 痛点密度最高（>75）→ 强调品质升级机会
    if best_dim_key == "pain_point" and best_score > 75:
        return (
            f"「{sub_category}」用户差评集中，"
            f"存在明显品质升级机会（痛点机会{best_score:.0f}分）"
        )

    # 价格利润最高（>75）→ 强调利润空间
    if best_dim_key == "price_profit" and best_score > 75:
        return (
            f"「{sub_category}」价格带分散，部分区间竞争较少，"
            f"利润空间可观（利润空间{best_score:.0f}分）"
        )

    # 综合分数高但无明显单项突出 → 均衡型
    if total_score >= 70:
        return (
            f"「{sub_category}」四维表现均衡（{total_score}分），"
            f"适合稳健型商家切入"
        )

    # 中等分数 → 一般性描述
    best_label = dim_labels.get(best_dim_key, "")
    return (
        f"「{sub_category}」{best_label}相对突出（{best_score:.0f}分），"
        f"综合评分{total_score}分，可考虑试水"
    )


def _generate_entry_suggestion(
    recommendation: str,
    brand: Dict,
    growth: Dict,
    pain: Dict,
    price: Dict,
    constraints: Dict,
) -> str:
    """生成差异化切入策略建议"""
    parts = []

    if recommendation == "recommended":
        parts.append("策略建议：强势切入")

        # 根据最强维度给出不同建议
        scores = {
            "brand": brand.get("score", 0),
            "growth": growth.get("score", 0),
            "pain": pain.get("score", 0),
            "price": price.get("score", 0),
        }
        best_dim = max(scores, key=scores.get)

        if best_dim == "brand":
            parts.append("利用品牌真空红利，以性价比策略快速入场")
        elif best_dim == "growth":
            parts.append("抓住上升期窗口，扩大曝光抢占增量用户")
        elif best_dim == "pain":
            if pain.get("top_pain_points"):
                top_pain = pain["top_pain_points"][0]["keyword"]
                parts.append(f"针对「{top_pain}」痛点做差异化升级，以品质溢价切入")
            else:
                parts.append("针对用户痛点做品质升级，以差异化切入")
        else:
            parts.append(
                f"入场价 ¥{price.get('suggested_price_entry', 0)} 起量，"
                f"溢价线 ¥{price.get('suggested_price_premium', 0)} 提利润"
            )

    elif recommendation == "neutral":
        parts.append("策略建议：谨慎试探")
        parts.append("建议先用少量 SKU 测试市场反馈，验证数据后再扩大投入")
    else:
        parts.append("策略建议：暂时观望")
        parts.append("建议关注市场变化，等待竞争格局改善后入局")

    return "；".join(parts)
