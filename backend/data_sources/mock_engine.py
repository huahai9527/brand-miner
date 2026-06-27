"""
第三层数据源：Mock 数据引擎（Demo 主力，稳定可控）
- 内置 10 大类知识库
- 支持知识库外任意关键词动态生成
- 100-200 条模拟商品数据，遵循真实市场规律
- 约束条件影响数据生成
"""
import random
import logging
import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ===================== 十类知识库 =====================
# 每个大类包含：细分方向、知名品牌、常见痛点词库、价格区间、增长趋势

@dataclass
class CategoryKnowledge:
    name: str
    sub_directions: List[str]
    known_brands: List[str]
    pain_points: List[str]
    price_range: tuple  # (min, max, mean)
    growth_scenarios: List[Dict[str, Any]]  # [{name, rate}] 不同增速的场景


BUILTIN_KNOWLEDGE = {
    "宠物": CategoryKnowledge(
        name="宠物",
        sub_directions=["宠物食品", "宠物玩具", "宠物保健品", "猫砂", "宠物洗护", "宠物服饰", "宠物窝垫", "智能宠物用品"],
        known_brands=["皇家", "冠能", "麦富迪", "伯纳天纯", "伟嘉", "比瑞吉", "疯狂小狗", "网易严选", "卫仕", "小佩", "有陪", "CATLINK"],
        pain_points=["掉毛严重", "成分不清晰", "适口性差", "异味重", "结团差", "过敏", "不耐用", "噪音大", "清洗麻烦", "闷热不透气"],
        price_range=(3, 500, 60),
        growth_scenarios=[
            {"name": "宠物保健品", "rate": 0.68},
            {"name": "智能宠物用品", "rate": 0.85},
            {"name": "宠物食品", "rate": 0.25},
            {"name": "宠物服饰", "rate": -0.05},
            {"name": "宠物洗护", "rate": 0.15},
            {"name": "猫砂", "rate": 0.10},
            {"name": "宠物窝垫", "rate": 0.05},
        ],
    ),
    "家居": CategoryKnowledge(
        name="家居",
        sub_directions=["收纳用品", "厨房用品", "清洁工具", "家纺", "装饰摆件", "灯具", "家具配件", "浴室用品"],
        known_brands=["宜家", "无印良品", "网易严选", "名创优品", "家乐福", "苏泊尔", "双立人", "爱丽思", "得力", "全棉时代", "维达"],
        pain_points=["占空间", "易变形", "有异味", "不耐用", "清洗困难", "掉色", "功能单一", "安装繁琐", "褪色", "不防滑"],
        price_range=(5, 500, 50),
        growth_scenarios=[
            {"name": "收纳用品", "rate": 0.55},
            {"name": "智能灯具", "rate": 0.60},
            {"name": "清洁工具", "rate": 0.30},
            {"name": "家纺", "rate": -0.10},
            {"name": "装饰摆件", "rate": 0.20},
        ],
    ),
    "办公": CategoryKnowledge(
        name="办公",
        sub_directions=["文具", "桌面收纳", "人体工学椅", "显示器支架", "键盘鼠标", "台灯", "白板贴纸", "会议设备"],
        known_brands=["得力", "晨光", "齐心", "联想", "罗技", "小米", "华为", "网易严选", "西昊", "乐歌", "明基", "倍思"],
        pain_points=["发货慢", "色差严重", "不透气", "容易脏", "手感差", "支撑不够", "噪音大", "续航短", "配对困难", "夹手"],
        price_range=(2, 3000, 80),
        growth_scenarios=[
            {"name": "人体工学椅", "rate": 0.70},
            {"name": "显示器支架", "rate": 0.50},
            {"name": "台灯", "rate": 0.20},
            {"name": "文具", "rate": -0.05},
            {"name": "桌面收纳", "rate": 0.15},
        ],
    ),
    "母婴": CategoryKnowledge(
        name="母婴",
        sub_directions=["婴儿食品", "纸尿裤", "奶瓶", "婴儿推车", "安全座椅", "婴儿洗护", "早教玩具", "孕妇装"],
        known_brands=["贝亲", "飞利浦新安怡", "好孩子", "babycare", "全棉时代", "好奇", "帮宝适", "惠氏", "美赞臣", "合生元", "小白熊", "博朗"],
        pain_points=["红屁股", "漏尿", "起泡", "太硬", "有BPA", "掉色过敏", "拼装复杂", "承重差", "有气味", "刻度不准"],
        price_range=(15, 2000, 100),
        growth_scenarios=[
            {"name": "安全座椅", "rate": 0.45},
            {"name": "早教玩具", "rate": 0.55},
            {"name": "婴儿洗护", "rate": 0.30},
            {"name": "纸尿裤", "rate": 0.05},
            {"name": "孕妇装", "rate": -0.10},
        ],
    ),
    "运动": CategoryKnowledge(
        name="运动",
        sub_directions=["瑜伽装备", "跑步装备", "户外装备", "游泳装备", "健身器材", "运动护具", "运动服饰", "骑行装备"],
        known_brands=["Nike", "Adidas", "Lululemon", "Under Armour", "李宁", "安踏", "Keep", "迪卡侬", "亚瑟士", "斯凯奇", "特步", "361°"],
        pain_points=["闷汗", "掉色", "磨脚", "弹性差", "不防滑", "太硬", "有异味", "掉粉", "松动", "不好收纳"],
        price_range=(10, 1500, 120),
        growth_scenarios=[
            {"name": "瑜伽装备", "rate": 0.60},
            {"name": "骑行装备", "rate": 0.75},
            {"name": "健身器材", "rate": 0.35},
            {"name": "跑步装备", "rate": 0.10},
            {"name": "游泳装备", "rate": -0.15},
        ],
    ),
    "美妆": CategoryKnowledge(
        name="美妆",
        sub_directions=["口红唇釉", "粉底液", "眼影盘", "护肤套装", "面膜", "卸妆产品", "美妆工具", "美容仪"],
        known_brands=["雅诗兰黛", "兰蔻", "MAC", "花西子", "完美日记", "薇诺娜", "珀莱雅", "欧莱雅", "OLAY", "韩束", "百雀羚", "自然堂"],
        pain_points=["拔干", "卡粉", "脱妆", "闷痘", "过敏刺痛", "不显色", "氧化快", "搓泥", "晕染", "用量太少"],
        price_range=(19, 800, 120),
        growth_scenarios=[
            {"name": "美容仪", "rate": 0.80},
            {"name": "护肤套装", "rate": 0.35},
            {"name": "面膜", "rate": 0.20},
            {"name": "口红唇釉", "rate": 0.05},
            {"name": "美妆工具", "rate": 0.10},
        ],
    ),
    "数码配件": CategoryKnowledge(
        name="数码配件",
        sub_directions=["手机壳", "充电器", "数据线", "蓝牙耳机", "手机支架", "屏幕保护膜", "移动电源", "车载充电器"],
        known_brands=["倍思", "绿联", "Anker", "小米", "品胜", "罗马仕", "华为", "紫米", "飞利浦", "公牛", "摩米士", "酷态科"],
        pain_points=["发烫", "断连", "不耐用", "充电慢", "尺寸不符", "褪色", "线短", "接口松动", "起泡", "信号差"],
        price_range=(5, 500, 40),
        growth_scenarios=[
            {"name": "蓝牙耳机", "rate": 0.40},
            {"name": "氮化镓充电器", "rate": 0.85},
            {"name": "移动电源", "rate": 0.15},
            {"name": "手机壳", "rate": -0.05},
            {"name": "数据线", "rate": 0.05},
        ],
    ),
    "厨房": CategoryKnowledge(
        name="厨房",
        sub_directions=["锅具", "刀具", "餐具", "厨房小电器", "调味品瓶罐", "砧板", "保鲜收纳", "烘焙工具"],
        known_brands=["苏泊尔", "双立人", "九阳", "美的", "张小泉", "康宁", "WMF", "爱仕达", "利仁", "摩飞", "小熊", "米家"],
        pain_points=["粘锅", "生锈", "太沉", "烫手", "不耐刮", "漏气", "清洗困难", "占台面", "噪音大", "涂层脱落"],
        price_range=(3, 800, 70),
        growth_scenarios=[
            {"name": "空气炸锅", "rate": 0.70},
            {"name": "烘焙工具", "rate": 0.50},
            {"name": "保鲜收纳", "rate": 0.25},
            {"name": "锅具", "rate": 0.05},
            {"name": "调味品瓶罐", "rate": -0.05},
        ],
    ),
    "户外": CategoryKnowledge(
        name="户外",
        sub_directions=["露营装备", "登山装备", "垂钓装备", "烧烤用具", "户外照明", "水壶水袋", "防晒用品", "户外服饰"],
        known_brands=["探路者", "牧高笛", "骆驼", "挪客", "迪卡侬", "Naturehike", "北极狐", "Osprey", "黑鹿", "火枫", "龙牙", "凯乐石"],
        pain_points=["太重", "不防水", "褪色", "拉链坏", "支撑力不足", "有异味", "体积大", "不耐脏", "断线破洞", "锁定不牢"],
        price_range=(15, 2000, 150),
        growth_scenarios=[
            {"name": "露营装备", "rate": 0.90},
            {"name": "烧烤用具", "rate": 0.40},
            {"name": "户外照明", "rate": 0.55},
            {"name": "登山装备", "rate": 0.20},
            {"name": "垂钓装备", "rate": -0.05},
        ],
    ),
    "服装": CategoryKnowledge(
        name="服装",
        sub_directions=["女装上衣", "男装上衣", "裤装", "裙装", "内衣", "袜子", "配饰", "儿童服装"],
        known_brands=["优衣库", "Zara", "H&M", "太平鸟", "森马", "蕉下", "内外", "Ubras", "海澜之家", "太平鸟", "马克华菲", "GXG"],
        pain_points=["缩水", "掉色", "起球", "掉毛", "不透气", "尺寸不准", "线头多", "扣子松", "褪色严重", "偏硬磨皮肤"],
        price_range=(9, 600, 80),
        growth_scenarios=[
            {"name": "内衣", "rate": 0.30},
            {"name": "运动服饰", "rate": 0.45},
            {"name": "配饰", "rate": 0.20},
            {"name": "女装上衣", "rate": 0.05},
            {"name": "男装上衣", "rate": -0.05},
        ],
    ),
}


class MockDataEngine:
    """
    Mock 数据引擎
    支持知识库内外的任意品类关键词动态生成商品数据
    所有数据遵循真实市场分布规律
    """

    def __init__(self):
        self.knowledge = BUILTIN_KNOWLEDGE

    # ----- 品类匹配 -----
    def get_knowledge(self, keyword: str) -> Optional[CategoryKnowledge]:
        """精确匹配知识库大类"""
        return self.knowledge.get(keyword)

    def fuzzy_match(self, keyword: str) -> Optional[CategoryKnowledge]:
        """模糊匹配：看 keyword 是否包含在知识库大类的 sub_directions 或 name 中"""
        for cat_name, knowledge in self.knowledge.items():
            if keyword in cat_name or cat_name in keyword:
                return knowledge
            for sd in knowledge.sub_directions:
                if keyword in sd or sd in keyword:
                    return knowledge
        return None

    # ----- 动态生成（知识库外关键词）-----
    def _build_dynamic_knowledge(self, keyword: str, constraints: Dict[str, Any]) -> CategoryKnowledge:
        """
        为知识库外的任意关键词动态构建知识结构
        基于通用模板生成细分方向、品牌、痛点，绝不报错
        """
        price_min = constraints.get("price_min", 5)
        price_max = constraints.get("price_max", 500)
        price_mean = (price_min + price_max) / 2

        # 通用细分方向模板（任何品类都适用）
        generic_directions = [
            f"入门级{keyword}", f"中级{keyword}", f"高端{keyword}",
            f"便携{keyword}", f"专业级{keyword}", f"{keyword}配件",
            f"{keyword}套装", f"{keyword}耗材",
        ]

        # 通用品牌
        generic_brands = [f"品牌{k}" for k in "ABCDEFGH"] + ["白牌"]

        # 通用痛点
        generic_pain_points = [
            "质量不稳定", "性价比低", "使用不方便", "外观一般",
            "售后服务差", "功能少", "尺寸不合适", "有异味",
        ]

        return CategoryKnowledge(
            name=keyword,
            sub_directions=generic_directions,
            known_brands=generic_brands,
            pain_points=generic_pain_points,
            price_range=(price_min, price_max, price_mean),
            growth_scenarios=[{"name": d, "rate": round(random.uniform(-0.15, 0.75), 2)}
                              for d in generic_directions],
        )

    # ----- 核心生成逻辑 -----
    def generate(
        self,
        keyword: str,
        constraints: Optional[Dict[str, Any]] = None,
        count: int = 150,
    ) -> List[Dict[str, Any]]:
        """
        生成模拟商品数据
        keyword: 大类关键词（任意开放，知识库内外均可）
        constraints: {"price_min", "price_max", "target_audience", "prefer_white_label"}
        count: 生成数量（100-200）
        """
        constraints = constraints or {}
        count = max(100, min(200, count))

        # 匹配知识
        knowledge = self.get_knowledge(keyword) or self.fuzzy_match(keyword)
        is_dynamic = False
        if not knowledge:
            logger.info(f"[Mock] '{keyword}' 不在知识库中，启用动态生成")
            knowledge = self._build_dynamic_knowledge(keyword, constraints)
            is_dynamic = True

        logger.info(f"[Mock] 生成 '{keyword}' 商品数据 {'(动态)' if is_dynamic else ''}，目标 {count} 条")

        products = []
        price_min, price_max = constraints.get("price_min", knowledge.price_range[0]), \
                               constraints.get("price_max", knowledge.price_range[1])
        price_mean = (price_min + price_max) / 2
        prefer_white_label = constraints.get("prefer_white_label", False)
        target_audience = constraints.get("target_audience", "")

        # 品牌比例调整
        if prefer_white_label:
            brand_dist = {"known": 0.05, "small": 0.15, "white": 0.80}  # 白牌优先
        else:
            brand_dist = {"known": 0.15, "small": 0.25, "white": 0.60}  # 正常市场分布

        # 销量排名（用于二八定律）
        sales_ranks = list(range(count))
        random.shuffle(sales_ranks)

        # 获取增长场景
        growth_map = {s["name"]: s["rate"] for s in knowledge.growth_scenarios}

        for i in range(count):
            # 细分方向（有权重：受众影响）
            sub_dir = self._pick_sub_direction(knowledge, target_audience)

            # 品牌
            brand_type = self._weighted_choice(["known", "small", "white"],
                                               [brand_dist["known"], brand_dist["small"], brand_dist["white"]])
            brand = self._pick_brand(knowledge, brand_type)

            # 价格：正态分布
            price = self._normal_price(price_mean, price_min, price_max)

            # 销量：二八定律
            rank_pct = sales_ranks[i] / count
            base_sales = int(10000 * math.exp(-3 * rank_pct))  # 指数衰减
            sales = max(1, int(base_sales * random.uniform(0.7, 1.3)))

            # 评分
            rating = round(random.gauss(4.3, 0.4), 1)
            rating = max(1.0, min(5.0, rating))

            # 评论数
            review_count = int(sales * random.uniform(0.02, 0.15))

            # 标题
            title = self._generate_title(keyword, sub_dir, brand, i)

            # 店铺类型
            shop_type = "旗舰店" if brand_type == "known" else random.choice(["专营店", "普通店", "普通店"])

            # 增长率
            growth_rate = growth_map.get(sub_dir, round(random.uniform(-0.10, 0.55), 2))

            product = {
                "platform": "mock",
                "title": title,
                "price": round(price, 2),
                "sales_30d": sales,
                "brand": brand,
                "sub_category": sub_dir,
                "shop_type": shop_type,
                "rating": rating,
                "review_count": review_count,
                "source_url": "",
                "growth_rate": growth_rate,
            }
            products.append(product)

        # 按销量降序排列
        products.sort(key=lambda x: -x["sales_30d"])
        logger.info(f"[Mock] 生成完成: {len(products)} 条")
        return products

    def generate_reviews(self, products: List[Dict[str, Any]],
                         knowledge: Optional[CategoryKnowledge] = None,
                         keyword: str = "") -> List[Dict[str, Any]]:
        """
        为商品列表生成评论数据
        差评率与评分成反比，差评关键词从痛点词库随机组合
        """
        if not knowledge:
            knowledge = self.get_knowledge(keyword) or self.fuzzy_match(keyword)
        if not knowledge:
            knowledge = self._build_dynamic_knowledge(keyword, {})

        reviews = []
        for product in products:
            # 差评率 ≈ (5 - rating) / 10，评分越低差评越多
            neg_ratio = (5.0 - product["rating"]) / 10.0
            total_reviews = min(20, max(3, int(product["review_count"] * 0.05)))

            for _ in range(total_reviews):
                is_negative = random.random() < neg_ratio
                rev_rating = random.randint(1, 3) if is_negative else random.randint(4, 5)
                sentiment = "negative" if is_negative else "positive"

                if is_negative:
                    keywords = random.sample(knowledge.pain_points,
                                             k=min(3, len(knowledge.pain_points)))
                    content = f"{'、'.join(keywords)}，{'不太满意' if rev_rating == 2 else '很失望'}"
                else:
                    keywords = random.sample(["好用", "性价比高", "发货快", "质感好", "推荐"],
                                             k=min(2, 5))
                    content = f"{'、'.join(keywords)}，{'不错' if rev_rating == 4 else '非常满意'}"

                reviews.append({
                    "content": content,
                    "sentiment": sentiment,
                    "keywords": keywords,
                    "rating": rev_rating,
                })

        return reviews

    # ----- 内部辅助方法 -----
    def _pick_sub_direction(self, knowledge: CategoryKnowledge, audience: str) -> str:
        """选择细分方向（受众影响权重）"""
        directions = knowledge.sub_directions.copy()
        if not directions:
            directions = [knowledge.name]

        # 简单受众权重
        weights = [1.0] * len(directions)
        if "年轻人" in audience:
            # 年轻人偏好新潮方向
            for i, d in enumerate(directions):
                if any(w in d for w in ["智能", "便携", "新", "美", "炫"]):
                    weights[i] *= 1.5
        if "宝妈" in audience or "母婴" in audience:
            for i, d in enumerate(directions):
                if any(w in d for w in ["安全", "婴儿", "孕", "母婴", "儿童"]):
                    weights[i] *= 1.8

        return self._weighted_choice(directions, weights)

    def _pick_brand(self, knowledge: CategoryKnowledge, brand_type: str) -> str:
        if brand_type == "white":
            return "白牌"
        if brand_type == "known" and knowledge.known_brands:
            return random.choice(knowledge.known_brands[:8])
        # 小品牌：虚构
        return f"{knowledge.name[:2]}{random.choice(['之', '优', '良', '品', '佳', '尚'])}{random.choice(['选', '作', '坊', '造'])}"

    def _normal_price(self, mean: float, lo: float, hi: float) -> float:
        """截断正态分布价格"""
        std = (hi - lo) / 4
        price = random.gauss(mean, std)
        return max(lo, min(hi, price))

    def _generate_title(self, keyword: str, sub_dir: str, brand: str, idx: int) -> str:
        """生成商品标题"""
        templates = [
            f"{brand} {sub_dir} {keyword}{random.randint(1, 999)}",
            f"{brand} {random.choice(['新款', '升级', '便携'])}{sub_dir}",
            f"{sub_dir} {random.choice(['套装', '组合', '礼盒'])} {brand}",
            f"{brand} {keyword}专用 {sub_dir}",
        ]
        return random.choice(templates)

    @staticmethod
    def _weighted_choice(items: List[str], weights: List[float]) -> str:
        total = sum(weights)
        r = random.random() * total
        cumulative = 0
        for item, w in zip(items, weights):
            cumulative += w
            if r <= cumulative:
                return item
        return items[-1]
