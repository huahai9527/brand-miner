"""
模块一：品牌真空度分析

核心逻辑：
  1. 统计品牌分布 —— 知名品牌 / 小品牌 / 白牌占比
  2. 计算 TOP3 品牌销量集中度
  3. 综合评分（0-100）：白牌占比越高、集中度越低 → 越适合新品牌切入

设计理念：
  品牌真空度越高，大品牌没有形成垄断，小品牌甚至白牌占主导，
  意味着市场没有"品牌溢价壁垒"，新入局者不需要巨额广告费就能杀进去。
  
评分模型（面试可讲）：
  - 白牌占比 60% 以上 → 基础分 70+（市场没有品牌忠诚度）
  - TOP3 集中度 < 30% → 极度分散，大机会
  - 知名品牌集中度 > 60% → 惩罚 -20 分（巨头垄断，不建议硬刚）
"""
from typing import Dict, List, Any


# 知名品牌名单（与 mock_engine 知识库对齐，用于品牌类型判定）
KNOWN_BRANDS = {
    "皇家", "冠能", "麦富迪", "伯纳天纯", "伟嘉", "比瑞吉", "疯狂小狗",
    "网易严选", "卫仕", "小佩", "有陪", "CATLINK",
    "宜家", "无印良品", "名创优品", "苏泊尔", "双立人", "爱丽思", "得力", "全棉时代", "维达",
    "晨光", "齐心", "联想", "罗技", "小米", "华为", "西昊", "乐歌", "明基", "倍思", "绿联", "Anker", "品胜", "罗马仕",
    "贝亲", "飞利浦新安怡", "好孩子", "babycare", "好奇", "帮宝适", "惠氏", "美赞臣", "合生元",
    "Nike", "Adidas", "Lululemon", "Under Armour", "李宁", "安踏", "Keep", "迪卡侬", "亚瑟士", "斯凯奇",
    "雅诗兰黛", "兰蔻", "MAC", "花西子", "完美日记", "薇诺娜", "珀莱雅", "欧莱雅", "OLAY",
    "九阳", "美的", "张小泉", "康宁", "WMF", "爱仕达",
    "探路者", "牧高笛", "骆驼", "挪客", "Naturehike", "北极狐", "Osprey",
    "优衣库", "Zara", "H&M", "太平鸟", "森马", "蕉下", "海澜之家",
}


def analyze_brand_vacuum(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    品牌真空度分析

    Args:
        products: 某细分品类下的商品列表，每项含 brand, sales_30d 字段

    Returns:
        {
            "score": 0-100,
            "white_brand_ratio": 0-1,
            "top3_concentration": 0-1,
            "known_brand_count": int,
            "detail": "..."
        }
    """
    if not products:
        return _empty_result("无商品数据")

    # ---- 1. 品牌分类统计 ----
    brand_sales: Dict[str, int] = {}        # 品牌 → 总销量
    brand_type_count = {"known": 0, "small": 0, "white": 0}

    for p in products:
        brand = p.get("brand", "白牌")
        sales = max(0, p.get("sales_30d", 0))
        brand_sales[brand] = brand_sales.get(brand, 0) + sales

        if brand == "白牌":
            brand_type_count["white"] += 1
        elif brand in KNOWN_BRANDS:
            brand_type_count["known"] += 1
        else:
            brand_type_count["small"] += 1

    total = len(products)
    total_sales = sum(brand_sales.values()) or 1

    # ---- 2. 占比计算 ----
    white_ratio = brand_type_count["white"] / total

    # TOP3 品牌销量集中度
    sorted_brands = sorted(brand_sales.items(), key=lambda x: -x[1])[:3]
    top3_sales = sum(s for _, s in sorted_brands)
    top3_concentration = top3_sales / total_sales

    # 知名品牌集中度（仅考察 TOP3 中是否包含知名品牌）
    known_in_top3 = sum(s for b, s in sorted_brands if b in KNOWN_BRANDS)
    known_concentration = known_in_top3 / total_sales

    # ---- 3. 评分模型 ----
    # 基础分来自白牌占比：白牌 60% → 70 分，线性映射
    base_score = min(100, white_ratio * 100 / 0.85 * 70)

    # 集中度调整：越分散分越高
    concentration_bonus = (1 - top3_concentration) * 20

    # 知名品牌惩罚
    known_penalty = 20 if known_concentration > 0.6 else 0

    score = round(max(0, min(100, base_score + concentration_bonus - known_penalty)))

    # ---- 4. 生成描述 ----
    detail = _generate_detail(white_ratio, top3_concentration, known_concentration, score, sorted_brands)

    return {
        "score": score,
        "white_brand_ratio": round(white_ratio, 3),
        "top3_concentration": round(top3_concentration, 3),
        "known_brand_count": brand_type_count["known"],
        "detail": detail,
    }


def _generate_detail(white_ratio: float, top3_c: float, known_c: float,
                     score: int, top3: list) -> str:
    """生成可读的分析描述"""
    parts = []
    if white_ratio > 0.6:
        parts.append(f"白牌占比高达 {white_ratio:.0%}，市场品牌真空度极高")
    elif white_ratio > 0.3:
        parts.append(f"白牌占比 {white_ratio:.0%}，有一定品牌真空空间")
    else:
        parts.append(f"白牌占比仅 {white_ratio:.0%}，品牌市场较成熟")

    if top3_c < 0.3:
        parts.append("头部品牌集中度低，市场极度分散，新品牌有机会")
    elif top3_c < 0.5:
        parts.append("头部品牌有一定份额但未垄断")
    else:
        top_name = top3[0][0] if top3 else "?"
        parts.append(f"头部品牌 {top_name} 占据主导，集中度 {top3_c:.0%}")

    if known_c > 0.6:
        parts.append("⚠️ 知名品牌强势垄断，切入难度较大")
    elif known_c > 0.3:
        parts.append("知名品牌有一定存在感，建议差异化避开正面竞争")

    return "；".join(parts)


def _empty_result(reason: str) -> Dict[str, Any]:
    return {
        "score": 0,
        "white_brand_ratio": 0,
        "top3_concentration": 0,
        "known_brand_count": 0,
        "detail": reason,
    }
