"""
模块三：用户痛点挖掘

核心逻辑：
  1. 情感分类（按 rating 自动分 negative/neutral/positive）
  2. jieba 分词 + 停用词过滤 → 提取高频负面关键词
  3. 五维痛点聚类：质量/体验/描述/售后/物流
  4. 痛点密度评分（0-100）：差评率 + 痛点集中度 → 改进空间

设计理念：
  痛点密度评分是"反向指标"——分越高说明现有产品做得越差，
  对于新入局者来说这是巨大机会。现有竞品在某个维度反复被吐槽，
  你只要做好这一点就能形成差异化优势。
  
  这个评分模型是为非品牌/小品牌商家设计的：
  大品牌可以通过广告掩盖差评，小品牌唯一能赢的方式就是
  解决现有产品没做好的真实痛点。

评分模型（面试可讲）：
  - 差评率 > 20% → 基础分 80+（市场普遍不满）
  - 痛点集中在 1-2 个维度 → +10 分（问题聚焦，容易针对性改进）
  - 痛点分散在 5 个维度 → 降分（说明产品整体不行，不是单一问题）
"""
import re
import logging
from collections import Counter
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

# ========== 停用词表 ==========
STOP_WORDS = set("""
的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你
会 着 没有 看 好 自己 这 他 她 它 们 那 些 什么 怎么 哪 这个 那个
还 可以 但 吧 啊 呢 哦 嗯 吗 了 啦 的 地 得 之 与 或 及 对 等
被 把 给 让 从 以 为 所以 因为 但是 然而 不过 虽然 如果 然后
没 太 挺 非常 很 特别 真的 觉得 感觉 知道 应该 需要 已经
能 不能 能够 可以 可 不可以 一定 必须 没 没有
个 次 年 月 日 时 分 秒 多 少 大 小 中
还是 吧 不是 不要 别 等等 都 其他 其它
""".split())

# ========== 五维痛点分类词库 ==========
# 每个维度配一组特征词，用于聚类高频负面关键词
PAIN_CATEGORIES = {
    "质量问题": {
        "keywords": ["质量", "做工", "材质", "耐用", "坏了", "裂开", "断裂", "脱线",
                     "褪色", "掉色", "掉毛", "起球", "缩水", "变形", "生锈", "粘锅",
                     "涂层脱落", "掉粉", "断连", "松动", "磨损"],
        "weight": 1.0,
    },
    "体验问题": {
        "keywords": ["不方便", "太硬", "太软", "太重", "太轻", "有异味", "气味", "不透气",
                     "闷汗", "磨脚", "烫手", "噪音", "吵", "清洗麻烦", "安装繁琐",
                     "占空间", "尺寸不对", "不太合适", "卡粉", "拔干", "搓泥", "闷痘"],
        "weight": 0.9,
    },
    "描述不符": {
        "keywords": ["不一样", "不像图片", "夸大", "虚假", "收到的是", "差别", "不一致",
                     "图片好看", "色差", "严重", "没有图上好看", "失望"],
        "weight": 0.8,
    },
    "售后问题": {
        "keywords": ["客服", "不理人", "态度差", "退货", "不退款", "退不了", "换货",
                     "不处理", "投诉", "售后太差", "没人管", "退款慢"],
        "weight": 0.7,
    },
    "物流包装": {
        "keywords": ["包装", "破损", "坏了", "物流慢", "发错", "少发", "快递", "暴力",
                     "收到就坏", "不包邮", "运费", "延迟", "派送"],
        "weight": 0.6,
    },
}


def analyze_pain_points(
    reviews: List[Dict[str, Any]],
    products: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    用户痛点挖掘

    Args:
        reviews: 评论列表，每项含 content, sentiment, rating, keywords（可选）
        products: 商品列表（仅用于计算差评率，可选）

    Returns:
        {
            "score": 0-100,
            "negative_ratio": 0-1,
            "top_pain_points": [...],
            "improvement_opportunities": [...],
            "detail": "..."
        }
    """
    if not reviews:
        return _empty_result("无评论数据")

    # ---- 1. 情感分类 ----
    negative_reviews, neutral_reviews, positive_reviews = _classify_reviews(reviews)
    total = len(reviews)
    neg_ratio = len(negative_reviews) / total

    # ---- 2. 关键词提取 ----
    neg_keywords = _extract_keywords(negative_reviews)
    top_keywords = neg_keywords.most_common(20)

    # ---- 3. 痛点聚类 ----
    clustered = _cluster_pain_points(top_keywords)
    top_pain_points = clustered[:10]  # Top10

    # ---- 4. 评分模型 ----
    score = _compute_pain_score(neg_ratio, clustered)

    # ---- 5. 改进建议生成 ----
    improvements = _generate_improvements(top_pain_points)

    # ---- 6. 描述生成 ----
    detail = _generate_detail(neg_ratio, top_pain_points, score)

    return {
        "score": score,
        "negative_ratio": round(neg_ratio, 3),
        "top_pain_points": [
            {
                "keyword": k["keyword"],
                "count": k["count"],
                "category": k["category"],
            }
            for k in top_pain_points
        ],
        "improvement_opportunities": improvements,
        "detail": detail,
    }


def _classify_reviews(reviews: List[Dict]) -> Tuple[List, List, List]:
    """按 rating 分类评论"""
    neg, neu, pos = [], [], []
    for r in reviews:
        rating = r.get("rating", 3)
        if rating <= 2:
            neg.append(r)
        elif rating == 3:
            neu.append(r)
        else:
            pos.append(r)
    return neg, neu, pos


def _extract_keywords(reviews: List[Dict]) -> Counter:
    """
    从差评中提取高频关键词
    使用 jieba 分词 + 停用词过滤
    """
    # 延迟导入 jieba（首次会自动下载词典）
    try:
        import jieba
    except ImportError:
        logger.warning("jieba 未安装，使用简易分词")
        return _simple_keyword_extract(reviews)

    counter = Counter()
    for r in reviews:
        content = r.get("content", "")
        # 去掉标点和数字
        content = re.sub(r'[^\u4e00-\u9fa5]', '', content)
        if not content:
            continue

        words = jieba.cut(content)
        for w in words:
            w = w.strip()
            if len(w) < 2 or w in STOP_WORDS:
                continue
            counter[w] += 1

    return counter


def _simple_keyword_extract(reviews: List[Dict]) -> Counter:
    """简易分词（无 jieba 时的 fallback）：按 2-3 字切分"""
    counter = Counter()
    for r in reviews:
        content = r.get("content", "")
        content = re.sub(r'[^\u4e00-\u9fa5]', '', content)
        # 2-3 字滑动窗口
        for i in range(len(content) - 1):
            bigram = content[i:i + 2]
            if bigram not in STOP_WORDS and len([c for c in bigram if '\u4e00' <= c <= '\u9fa5']) == 2:
                counter[bigram] += 1
    return counter


def _cluster_pain_points(keywords: List[Tuple[str, int]]) -> List[Dict]:
    """
    将高频关键词归类到五维痛点体系
    同时保留无法归类的关键词标记为"其他"
    """
    clustered = []
    for kw, count in keywords:
        category = "其他"
        for cat_name, cat_info in PAIN_CATEGORIES.items():
            if kw in cat_info["keywords"]:
                category = cat_name
                break

        clustered.append({
            "keyword": kw,
            "count": count,
            "category": category,
        })

    # 按 count 降序排列
    clustered.sort(key=lambda x: -x["count"])
    return clustered


def _compute_pain_score(neg_ratio: float, clustered: List[Dict]) -> int:
    """痛点密度评分（0-100）"""
    if neg_ratio == 0:
        return 0

    # 基础分：差评率线性映射
    # 差评 30% → 100分，差评 5% → 20分
    base = min(100, neg_ratio / 0.3 * 100)

    # 痛点集中度调整
    if len(clustered) > 0:
        top_categories = set(item["category"] for item in clustered[:10])
        # 集中在 1-2 个类别 → 加分（问题聚焦）
        if len(top_categories) <= 2:
            base += 10
        # 分散在 4+ 个类别 → 减分（问题分散，难解决）
        elif len(top_categories) >= 5:
            base -= 10

    return round(max(0, min(100, base)))


def _generate_improvements(top_pain_points: List[Dict]) -> List[str]:
    """根据 Top 痛点生成改进建议"""
    improvements = []
    categories_seen = set()

    for pp in top_pain_points:
        cat = pp["category"]
        if cat in categories_seen:
            continue
        categories_seen.add(cat)

        suggestions = {
            "质量问题": f"升级{pp['keyword']}的材质和做工标准，主打「经久耐用」差异化",
            "体验问题": f"优化产品{pp['keyword']}设计，提升使用体验",
            "描述不符": "实拍详情页，拒绝过度美化，用真实素材建立信任",
            "售后问题": "建立快速响应售后团队，7天无理由退换增强购买信心",
            "物流包装": "升级包装防护 + 顺丰合作，降低破损率",
            "其他": f"关注「{pp['keyword']}」相关问题，对应用户真实反馈改进",
        }
        improvements.append(suggestions.get(cat, suggestions["其他"]))

    return improvements[:5]


def _generate_detail(neg_ratio: float, top_points: List[Dict], score: int) -> str:
    parts = [f"差评率 {neg_ratio:.1%}"]

    if top_points:
        top3_kws = [p["keyword"] for p in top_points[:3]]
        parts.append(f"Top 痛点：{'、'.join(top3_kws)}")

    if score >= 70:
        parts.append("市场痛点明显且集中，存在改进切入机会")
    elif score >= 40:
        parts.append("存在一定改进空间，但差异化优势不明显")
    else:
        parts.append("市场满意度较高，从痛点切入难度大")

    return "；".join(parts)


def _empty_result(reason: str) -> Dict[str, Any]:
    return {
        "score": 0,
        "negative_ratio": 0,
        "top_pain_points": [],
        "improvement_opportunities": [],
        "detail": reason,
    }
