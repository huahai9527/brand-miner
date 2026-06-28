"""
第三层数据源：Mock 数据引擎（Demo 主力，稳定可控）
- 内置 40+ 大品类知识库，覆盖主流电商分类
- 支持知识库外任意关键词动态生成
- 100-200 条模拟商品数据，遵循真实市场规律
- 约束条件影响数据生成
"""
import random
import logging
import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CategoryKnowledge:
    name: str
    sub_directions: List[str]
    known_brands: List[str]
    pain_points: List[str]
    price_range: tuple  # (min, max, mean)
    growth_scenarios: List[Dict[str, Any]]


# ===================== 电商品类映射表 =====================

BUILTIN_KNOWLEDGE = {
    # ── 食品饮料 ──
    "水饮": CategoryKnowledge(
        name="水饮/饮料",
        sub_directions=["碳酸饮料", "无糖茶饮", "电解质水", "矿泉水", "果汁", "功能饮料", "咖啡饮料", "植物蛋白饮料"],
        known_brands=["农夫山泉", "元气森林", "康师傅", "统一", "三得利", "雀巢", "脉动", "红牛", "东鹏", "怡宝", "东方树叶", "百岁山"],
        pain_points=["太甜", "口感差", "包装破损", "量太少", "气不足", "味道怪", "瓶盖漏", "不符描述"],
        price_range=(2, 80, 15),
        growth_scenarios=[{"name": "无糖茶饮", "rate": 0.65}, {"name": "电解质水", "rate": 0.72}, {"name": "功能饮料", "rate": 0.40}, {"name": "果汁", "rate": 0.20}, {"name": "矿泉水", "rate": 0.10}, {"name": "碳酸饮料", "rate": -0.05}],
    ),
    "零食": CategoryKnowledge(
        name="零食/休闲食品",
        sub_directions=["坚果炒货", "薯片膨化食品", "饼干糕点", "糖果巧克力", "肉类零食", "果干蜜饯", "海苔紫菜", "辣条"],
        known_brands=["良品铺子", "三只松鼠", "百草味", "乐事", "奥利奥", "德芙", "卫龙", "徐福记", "沃隆", "恰恰", "百醇", "旺旺"],
        pain_points=["量少", "不新鲜", "太甜腻", "有哈味", "碎末多", "口味不正", "包装难撕", "发货慢"],
        price_range=(3, 120, 25),
        growth_scenarios=[{"name": "肉类零食", "rate": 0.55}, {"name": "坚果炒货", "rate": 0.30}, {"name": "辣条", "rate": 0.40}, {"name": "糖果巧克力", "rate": 0.10}, {"name": "饼干糕点", "rate": 0.05}],
    ),
    "速食": CategoryKnowledge(
        name="速食/方便食品",
        sub_directions=["方便面", "自热火锅", "螺蛳粉", "自热米饭", "速冻水饺", "即食罐头", "冲泡粥", "代餐棒"],
        known_brands=["康师傅", "统一", "海底捞", "自嗨锅", "三全", "思念", "好欢螺", "李子柒", "白象", "五谷道场", "莫小仙", "拉面说"],
        pain_points=["量太少", "口味不正宗", "包装破损", "不够辣", "太咸", "配料少", "不新鲜", "吃不完浪费"],
        price_range=(3, 100, 25),
        growth_scenarios=[{"name": "自热火锅", "rate": 0.60}, {"name": "螺蛳粉", "rate": 0.75}, {"name": "速冻水饺", "rate": 0.30}, {"name": "方便面", "rate": 0.05}, {"name": "代餐棒", "rate": 0.50}],
    ),
    "生鲜": CategoryKnowledge(
        name="生鲜/食材",
        sub_directions=["新鲜水果", "蔬菜", "猪牛羊肉", "鸡鸭禽类", "海鲜水产", "鸡蛋豆制品", "米面粮油", "调味品"],
        known_brands=["恒都", "正大", "国联水产", "科尔沁", "十月稻田", "海天", "李锦记", "金龙鱼", "福临门", "大希地", "圣农", "壹号土猪"],
        pain_points=["不新鲜", "分量少", "解冻出水", "腥味重", "破损坏", "口感差", "运输慢", "大小不均"],
        price_range=(5, 300, 40),
        growth_scenarios=[{"name": "海鲜水产", "rate": 0.35}, {"name": "预包装食材", "rate": 0.50}, {"name": "调味品", "rate": 0.15}, {"name": "米面粮油", "rate": 0.05}, {"name": "新鲜水果", "rate": 0.20}],
    ),
    "保健食品": CategoryKnowledge(
        name="保健食品",
        sub_directions=["维生素矿物质", "蛋白粉", "益生菌", "鱼油", "胶原蛋白", "减肥代餐", "儿童营养品", "中老年保健"],
        known_brands=["Swisse", "汤臣倍健", "康恩贝", "善存", "GNC", "纽崔莱", "健康元", "MoveFree", "养生堂", "百合康", "生命阳光", "惠氏"],
        pain_points=["效果不明显", "有异味", "颗粒太大难吞咽", "包装漏", "吃了不舒服", "分量少", "味道怪", "瓶子难开"],
        price_range=(30, 500, 120),
        growth_scenarios=[{"name": "益生菌", "rate": 0.65}, {"name": "胶原蛋白", "rate": 0.55}, {"name": "减肥代餐", "rate": 0.45}, {"name": "蛋白粉", "rate": 0.25}, {"name": "维生素矿物质", "rate": 0.10}],
    ),
    # ── 美妆个护 ──
    "护肤品": CategoryKnowledge(
        name="护肤品",
        sub_directions=["洁面产品", "水乳精华", "面霜防晒", "眼霜", "面膜", "化妆水", "精华油", "男士护肤"],
        known_brands=["雅诗兰黛", "兰蔻", "SK-II", "资生堂", "薇诺娜", "珀莱雅", "欧莱雅", "OLAY", "修丽可", "理肤泉", "自然堂", "百雀羚"],
        pain_points=["过敏刺痛", "闷痘", "太油腻", "效果不明显", "搓泥", "有酒精味", "瓶口坏", "量少"],
        price_range=(30, 1000, 180),
        growth_scenarios=[{"name": "精华油", "rate": 0.55}, {"name": "男士护肤", "rate": 0.60}, {"name": "面膜", "rate": 0.20}, {"name": "洁面产品", "rate": 0.10}, {"name": "水乳精华", "rate": 0.15}],
    ),
    "彩妆": CategoryKnowledge(
        name="彩妆",
        sub_directions=["口红唇釉", "粉底液气垫", "眼影盘", "睫毛膏", "腮红高光", "眉笔眼线", "散粉定妆", "卸妆产品"],
        known_brands=["MAC", "花西子", "完美日记", "兰蔻", "雅诗兰黛", "YSL", "迪奥", "阿玛尼", "3CE", "Colorkey", "橘朵", "INTO YOU"],
        pain_points=["拔干", "卡粉", "脱妆", "不显色", "氧化快", "晕染", "持妆短", "碎盘"],
        price_range=(19, 600, 100),
        growth_scenarios=[{"name": "散粉定妆", "rate": 0.40}, {"name": "粉底液气垫", "rate": 0.35}, {"name": "腮红高光", "rate": 0.30}, {"name": "口红唇釉", "rate": 0.05}, {"name": "卸妆产品", "rate": 0.15}],
    ),
    "洗护": CategoryKnowledge(
        name="洗护/个护",
        sub_directions=["洗发水", "护发素发膜", "沐浴露", "香皂洗手液", "牙膏牙刷", "剃须产品", "电吹风", "卷直发器"],
        known_brands=["海飞丝", "飘柔", "潘婷", "清扬", "多芬", "力士", "舒肤佳", "佳洁士", "飞利浦", "飞科", "戴森", "欧乐B"],
        pain_points=["不起泡", "油腻", "有头屑", "味道刺鼻", "漏液", "掉毛", "噪音大", "不耐用"],
        price_range=(5, 500, 40),
        growth_scenarios=[{"name": "电吹风", "rate": 0.35}, {"name": "卷直发器", "rate": 0.30}, {"name": "护发素发膜", "rate": 0.25}, {"name": "洗发水", "rate": 0.05}, {"name": "剃须产品", "rate": 0.10}],
    ),
    "香水": CategoryKnowledge(
        name="香水/香氛",
        sub_directions=["女士香水", "男士香水", "香薰蜡烛", "车载香薰", "扩香器", "身体喷雾"],
        known_brands=["祖玛珑", "迪奥", "香奈儿", "芦丹氏", "名创优品", "气味图书馆", "冰希黎", "观夏", "野兽派", "Le Labo", "Byredo", "Diptyque"],
        pain_points=["留香短", "味道太浓", "不符描述", "盖子松", "漏液", "瓶子碎"],
        price_range=(10, 1500, 200),
        growth_scenarios=[{"name": "香薰蜡烛", "rate": 0.55}, {"name": "车载香薰", "rate": 0.40}, {"name": "身体喷雾", "rate": 0.30}, {"name": "女士香水", "rate": 0.10}, {"name": "男士香水", "rate": 0.20}],
    ),
    # ── 服装鞋包 ──
    "女装": CategoryKnowledge(
        name="女装",
        sub_directions=["连衣裙", "T恤上衣", "休闲裤", "卫衣外套", "内衣睡衣", "针织衫", "风衣大衣", "运动套装"],
        known_brands=["优衣库", "Zara", "UR", "太平鸟", "蕉下", "内外", "Ubras", "伊芙丽", "欧时力", "Lily", "Only", "乐町"],
        pain_points=["缩水", "掉色", "起球", "尺寸不准", "不透气", "线头多", "扣子松", "偏硬磨皮肤"],
        price_range=(19, 800, 120),
        growth_scenarios=[{"name": "运动套装", "rate": 0.45}, {"name": "内衣睡衣", "rate": 0.30}, {"name": "连衣裙", "rate": 0.15}, {"name": "T恤上衣", "rate": 0.05}, {"name": "风衣大衣", "rate": 0.10}],
    ),
    "男装": CategoryKnowledge(
        name="男装",
        sub_directions=["T恤Polo衫", "休闲裤牛仔裤", "卫衣套卫裤", "商务衬衫", "运动服", "夹克外套", "羽绒服", "内裤袜子"],
        known_brands=["GXG", "海澜之家", "优衣库", "太平鸟", "马克华菲", "杰克琼斯", "森马", "H&M", "七匹狼", "罗蒙", "Anta", "特步"],
        pain_points=["脱线", "掉色", "起球", "版型差", "不透气", "拉链坏", "尺寸偏大", "缩水"],
        price_range=(15, 1200, 100),
        growth_scenarios=[{"name": "运动服", "rate": 0.35}, {"name": "卫衣套卫裤", "rate": 0.30}, {"name": "内裤袜子", "rate": 0.25}, {"name": "商务衬衫", "rate": 0.05}, {"name": "休闲裤牛仔裤", "rate": 0.10}],
    ),
    "鞋靴": CategoryKnowledge(
        name="鞋靴",
        sub_directions=["运动鞋", "休闲板鞋", "凉鞋拖鞋", "靴子", "商务皮鞋", "帆布鞋", "老爹鞋", "跑步鞋"],
        known_brands=["Nike", "Adidas", "安踏", "李宁", "斯凯奇", "回力", "匡威", "Vans", "Clarks", "百丽", "红蜻蜓", "奥康"],
        pain_points=["磨脚", "偏小偏大", "不透气", "开胶", "鞋底硬", "有异味", "掉色", "鞋带易断"],
        price_range=(30, 1500, 200),
        growth_scenarios=[{"name": "老爹鞋", "rate": 0.45}, {"name": "跑步鞋", "rate": 0.40}, {"name": "帆布鞋", "rate": 0.20}, {"name": "商务皮鞋", "rate": 0.05}, {"name": "凉鞋拖鞋", "rate": 0.25}],
    ),
    "箱包": CategoryKnowledge(
        name="箱包",
        sub_directions=["双肩包", "单肩斜挎包", "手提包", "钱包卡包", "行李箱", "腰包", "帆布袋", "化妆包"],
        known_brands=["小米", "网易严选", "无印良品", "稻草人", "七匹狼", "Herschel", "Jansport", "Targus", "外交官", "九牧王", "哥伦比亚", "太平洋"],
        pain_points=["拉链坏", "脱线", "褪色", "有异味", "缝线不牢", "容量小", "带子易断", "扣子松"],
        price_range=(15, 800, 100),
        growth_scenarios=[{"name": "化妆包", "rate": 0.40}, {"name": "腰包", "rate": 0.35}, {"name": "帆布袋", "rate": 0.30}, {"name": "双肩包", "rate": 0.10}, {"name": "行李箱", "rate": 0.15}],
    ),
    "配饰": CategoryKnowledge(
        name="配饰",
        sub_directions=["项链手链", "耳环耳钉", "戒指", "手表", "帽子", "围巾", "腰带", "眼镜"],
        known_brands=["潘多拉", "施华洛世奇", "卡西欧", "浪琴", "天王", "飞亚达", "蕉下", "普拉达", "Gucci", "巴宝莉", "Coach", "Michael Kors"],
        pain_points=["掉色", "过敏", "尺寸不合适", "有瑕疵", "搭扣坏", "玻璃不清晰", "链子断", "掉钻"],
        price_range=(5, 3000, 150),
        growth_scenarios=[{"name": "手表", "rate": 0.25}, {"name": "眼镜", "rate": 0.35}, {"name": "项链手链", "rate": 0.20}, {"name": "帽子", "rate": 0.30}, {"name": "腰带", "rate": 0.10}],
    ),
    # ── 数码3C ──
    "手机配件": CategoryKnowledge(
        name="手机配件",
        sub_directions=["手机壳", "钢化膜水凝膜", "充电器插头", "数据线", "充电宝", "手机支架", "散热背夹", "镜头贴"],
        known_brands=["倍思", "绿联", "Anker", "小米", "品胜", "罗马仕", "华为", "紫米", "飞利浦", "公牛", "摩米士", "酷态科"],
        pain_points=["发烫", "断连", "不耐用", "充电慢", "尺寸不符", "褪色", "线短", "接口松动", "起泡", "信号差"],
        price_range=(3, 300, 35),
        growth_scenarios=[{"name": "充电器插头", "rate": 0.50}, {"name": "散热背夹", "rate": 0.60}, {"name": "钢化膜", "rate": 0.20}, {"name": "手机壳", "rate": -0.05}, {"name": "数据线", "rate": 0.05}],
    ),
    "耳机音频": CategoryKnowledge(
        name="耳机音频",
        sub_directions=["真无线耳机", "头戴耳机", "有线耳机", "骨传导耳机", "蓝牙音箱", "降噪耳机"],
        known_brands=["Sony", "Bose", "Apple", "森海塞尔", "漫步者", "Anker Soundcore", "小米", "华为", "Beats", "JBL", "万魔", "QCY"],
        pain_points=["断连", "音质差", "佩戴不舒服", "续航短", "降噪效果差", "底噪大", "配对难", "外壳划痕"],
        price_range=(30, 2500, 250),
        growth_scenarios=[{"name": "骨传导耳机", "rate": 0.70}, {"name": "降噪耳机", "rate": 0.50}, {"name": "蓝牙音箱", "rate": 0.30}, {"name": "真无线耳机", "rate": 0.15}, {"name": "有线耳机", "rate": -0.10}],
    ),
    "电脑配件": CategoryKnowledge(
        name="电脑配件",
        sub_directions=["机械键盘", "游戏鼠标", "鼠标垫", "笔记本支架", "显示器", "摄像头", "耳机麦克风", "U盘硬盘"],
        known_brands=["罗技", "雷蛇", "Cherry", "海盗船", "Acer", "Samsung", "西部数据", "金士顿", "闪迪", "HyperX", "Dell", "联想"],
        pain_points=["双击", "飘移", "噪音大", "不兼容", "掉漆", "连接不稳", "线太短", "发热严重"],
        price_range=(20, 5000, 200),
        growth_scenarios=[{"name": "机械键盘", "rate": 0.45}, {"name": "笔记本支架", "rate": 0.55}, {"name": "游戏鼠标", "rate": 0.30}, {"name": "U盘硬盘", "rate": 0.10}, {"name": "鼠标垫", "rate": 0.05}],
    ),
    "智能设备": CategoryKnowledge(
        name="智能设备",
        sub_directions=["智能手表手环", "蓝牙耳机", "扫地机器人", "智能音箱", "行车记录仪", "运动相机", "电子书阅读器"],
        known_brands=["Apple", "华为", "小米", "三星", "Amazfit", "Insta360", "GoPro", "科沃斯", "石头", "追觅", "小度", "天猫精灵"],
        pain_points=["续航短", "APP不稳定", "连接失败", "不防水", "升级变卡", "触控失灵", "发烫", "划花屏幕"],
        price_range=(50, 5000, 500),
        growth_scenarios=[{"name": "扫地机器人", "rate": 0.55}, {"name": "运动相机", "rate": 0.60}, {"name": "行车记录仪", "rate": 0.40}, {"name": "智能手表", "rate": 0.20}, {"name": "电子书阅读器", "rate": 0.15}],
    ),
    "摄影器材": CategoryKnowledge(
        name="摄影器材",
        sub_directions=["相机镜头", "三脚架", "摄影灯", "存储卡", "相机包", "滤镜", "无人机", "手持稳定器"],
        known_brands=["佳能", "尼康", "Sony", "富士", "大疆", "智云", "JOBY", "Sandisk", "腾龙", "适马", "保富图", "耐司"],
        pain_points=["对焦慢", "体积大", "太重", "电池不耐用", "遥控失灵", "画面抖动", "发热", "兼容性差"],
        price_range=(20, 10000, 600),
        growth_scenarios=[{"name": "无人机", "rate": 0.65}, {"name": "手持稳定器", "rate": 0.55}, {"name": "滤镜", "rate": 0.30}, {"name": "三脚架", "rate": 0.10}, {"name": "存储卡", "rate": 0.05}],
    ),
    # ── 家居家装 ──
    "家居收纳": CategoryKnowledge(
        name="家居收纳",
        sub_directions=["收纳箱抽屉柜", "衣柜收纳", "厨房收纳", "浴室收纳", "桌面收纳", "鞋架鞋柜", "挂钩挂件", "真空压缩袋"],
        known_brands=["宜家", "无印良品", "网易严选", "名创优品", "爱丽思", "妙洁", "禧天龙", "百露", "家乐", "Lazy Corner", "太空喵", "DFVS"],
        pain_points=["占空间", "易变形", "有异味", "不耐用", "关不严", "掉色", "拉手坏", "尺寸不符"],
        price_range=(5, 300, 40),
        growth_scenarios=[{"name": "真空压缩袋", "rate": 0.55}, {"name": "衣柜收纳", "rate": 0.40}, {"name": "桌面收纳", "rate": 0.30}, {"name": "收纳箱", "rate": 0.10}, {"name": "挂钩挂件", "rate": 0.05}],
    ),
    "床上用品": CategoryKnowledge(
        name="床上用品",
        sub_directions=["被子被芯", "枕头枕芯", "床单被套", "床垫保护垫", "毛毯毛巾被", "蚕丝被", "儿童床品套件"],
        known_brands=["水星家纺", "罗莱", "梦洁", "富安娜", "恒源祥", "博洋", "南极人", "慕思", "网易严选", "尚朵", "恩兴", "雅兰"],
        pain_points=["掉毛", "缩水", "不透气", "有气味", "褪色", "起球", "尺寸偏小", "商家发错"],
        price_range=(30, 2000, 200),
        growth_scenarios=[{"name": "蚕丝被", "rate": 0.45}, {"name": "儿童床品套件", "rate": 0.55}, {"name": "毛毯毛巾被", "rate": 0.20}, {"name": "床单被套", "rate": 0.10}, {"name": "枕头枕芯", "rate": 0.15}],
    ),
    "厨房用品": CategoryKnowledge(
        name="厨房用品",
        sub_directions=["锅具炊具", "刀具砧板", "厨房小工具", "烘焙模具", "保鲜盒饭盒", "水杯保温杯", "餐具碗筷"],
        known_brands=["苏泊尔", "双立人", "九阳", "美的", "张小泉", "康宁", "WMF", "爱仕达", "利仁", "摩飞", "小熊", "米家"],
        pain_points=["粘锅", "生锈", "太沉", "烫手", "不耐刮", "漏气", "清洗困难", "涂层脱落"],
        price_range=(5, 1500, 80),
        growth_scenarios=[{"name": "烘焙模具", "rate": 0.50}, {"name": "水杯保温杯", "rate": 0.35}, {"name": "厨房小工具", "rate": 0.25}, {"name": "锅具炊具", "rate": 0.05}, {"name": "餐具碗筷", "rate": 0.10}],
    ),
    "灯具照明": CategoryKnowledge(
        name="灯具照明",
        sub_directions=["吸顶灯", "台灯", "落地灯", "LED灯带", "小夜灯", "射灯筒灯", "户外庭院灯"],
        known_brands=["欧普照明", "雷士", "松下", "Philips", "Yeelight", "公牛", "明基", "米家", "TCL", "海尔", "佛山照明", "三雄极光"],
        pain_points=["太暗", "频闪", "发烫", "遥控失灵", "安装麻烦", "色差", "寿命短", "噪音"],
        price_range=(10, 1000, 100),
        growth_scenarios=[{"name": "LED灯带", "rate": 0.60}, {"name": "小夜灯", "rate": 0.45}, {"name": "台灯", "rate": 0.25}, {"name": "吸顶灯", "rate": 0.10}, {"name": "户外庭院灯", "rate": 0.35}],
    ),
    "清洁用品": CategoryKnowledge(
        name="清洁用品",
        sub_directions=["洗衣液洗衣粉", "洗洁精", "消毒液84", "清洁剂去污粉", "纸巾湿巾", "垃圾袋", "拖把扫把", "清洁刷海绵"],
        known_brands=["蓝月亮", "威露士", "滴露", "好爸爸", "花王", "维达", "清风", "洁柔", "3M", "妙洁", "宝家洁", "佳帮手"],
        pain_points=["去污力差", "刺激皮肤", "香味刺鼻", "包装漏", "量太少", "喷嘴坏", "留水渍", "不禁用"],
        price_range=(2, 150, 25),
        growth_scenarios=[{"name": "消毒液84", "rate": 0.35}, {"name": "清洁剂去污粉", "rate": 0.30}, {"name": "纸巾湿巾", "rate": 0.20}, {"name": "洗衣液", "rate": 0.10}, {"name": "垃圾袋", "rate": 0.05}],
    ),
    "家纺软装": CategoryKnowledge(
        name="家纺软装",
        sub_directions=["窗帘", "地毯", "抱枕靠垫", "桌布餐垫", "浴巾毛巾", "门垫脚垫", "壁挂装饰"],
        known_brands=["宜家", "罗莱", "无印良品", "网易严选", "摩力克", "苏雅", "美居乐", "恒源祥", "南极人", "紫罗兰", "家乐", "雨竹"],
        pain_points=["掉色", "缩水", "起球", "尺寸不准", "异味重", "掉毛", "缝线歪", "遮光差"],
        price_range=(5, 500, 60),
        growth_scenarios=[{"name": "壁挂装饰", "rate": 0.45}, {"name": "抱枕靠垫", "rate": 0.35}, {"name": "门垫脚垫", "rate": 0.20}, {"name": "窗帘", "rate": 0.10}, {"name": "桌布餐垫", "rate": 0.15}],
    ),
    # ── 母婴 ──
    "婴儿用品": CategoryKnowledge(
        name="婴儿用品",
        sub_directions=["纸尿裤", "湿巾", "婴儿洗护", "婴儿辅食", "奶瓶奶嘴", "安抚奶嘴", "婴儿床品", "婴儿监护器"],
        known_brands=["贝亲", "babycare", "好孩子", "全棉时代", "好奇", "帮宝适", "花王", "小白熊", "博朗", "新安怡", "可优比", "英氏"],
        pain_points=["红屁股", "漏尿", "起泡", "太硬", "有BPA", "掉色过敏", "不耐用", "刻度不准"],
        price_range=(10, 2000, 80),
        growth_scenarios=[{"name": "婴儿辅食", "rate": 0.50}, {"name": "婴儿监护器", "rate": 0.60}, {"name": "婴儿洗护", "rate": 0.30}, {"name": "纸尿裤", "rate": 0.05}, {"name": "奶瓶奶嘴", "rate": 0.15}],
    ),
    "儿童玩具": CategoryKnowledge(
        name="儿童玩具",
        sub_directions=["积木拼装", "遥控车", "毛绒玩具", "益智早教", "过家家玩具", "户外玩具", "桌游卡牌", "模型手办"],
        known_brands=["乐高", "万代", "孩之宝", "泡泡玛特", "奥迪双钻", "费雪", "伟易达", "变形金刚", "HAPE", "B.Toys", "星辉", "银辉"],
        pain_points=["掉零件", "容易坏", "有毛刺", "声音太大", "电池不耐用", "味道刺鼻", "遥控不灵", "不防水"],
        price_range=(10, 800, 60),
        growth_scenarios=[{"name": "积木拼装", "rate": 0.50}, {"name": "模型手办", "rate": 0.55}, {"name": "益智早教", "rate": 0.40}, {"name": "毛绒玩具", "rate": 0.10}, {"name": "遥控车", "rate": 0.20}],
    ),
    "儿童服装": CategoryKnowledge(
        name="儿童服装",
        sub_directions=["儿童T恤外套", "儿童裤子", "儿童鞋", "儿童内衣", "儿童睡衣", "儿童运动服", "儿童帽子"],
        known_brands=["巴拉巴拉", "安奈儿", "英氏", "Mini Peace", "优衣库", "GAP", "HM", "ZARA", "B.Duck", "马拉丁", "小猪班纳", "安踏儿童"],
        pain_points=["缩水严重", "起球", "面料偏硬", "掉色", "偏小偏大", "扣子松", "有异味", "不透气"],
        price_range=(15, 500, 80),
        growth_scenarios=[{"name": "儿童运动服", "rate": 0.45}, {"name": "儿童内衣", "rate": 0.30}, {"name": "儿童帽子", "rate": 0.25}, {"name": "儿童T恤", "rate": 0.10}, {"name": "儿童鞋", "rate": 0.15}],
    ),
    "孕产妇": CategoryKnowledge(
        name="孕产妇",
        sub_directions=["孕妇装", "哺乳文胸", "月子服", "孕妇枕", "待产包", "产后修复", "孕妇营养品"],
        known_brands=["babycare", "十月结晶", "美德乐", "嫚熙", "全棉时代", "贝亲", "子初", "婧麒", "娇韵诗", "海氏海诺", "袋鼠妈妈", "belli"],
        pain_points=["不透气", "弹性差", "勒肚子", "面料硬", "有异味", "脱线", "洗后变薄", "开线"],
        price_range=(20, 600, 100),
        growth_scenarios=[{"name": "产后修复", "rate": 0.55}, {"name": "孕妇枕", "rate": 0.45}, {"name": "待产包", "rate": 0.35}, {"name": "哺乳文胸", "rate": 0.20}, {"name": "孕妇装", "rate": 0.10}],
    ),
    # ── 运动户外 ──
    "健身器材": CategoryKnowledge(
        name="健身器材",
        sub_directions=["哑铃杠铃", "瑜伽垫", "弹力带拉力绳", "跳绳", "健腹轮", "泡沫轴", "健身手套", "护具护腕"],
        known_brands=["Keep", "迪卡侬", "小米有品", "Lululemon", "麦瑞克", "亿健", "Prosource", "TMT", "Yottoy", "多德士", "铁人", "悦动"],
        pain_points=["有异味", "开胶", "太硬", "使用不方便", "不耐用", "打滑", "掉渣", "太占地方"],
        price_range=(5, 2000, 120),
        growth_scenarios=[{"name": "瑜伽垫", "rate": 0.50}, {"name": "弹力带", "rate": 0.55}, {"name": "护具护腕", "rate": 0.35}, {"name": "哑铃杠铃", "rate": 0.15}, {"name": "跳绳", "rate": 0.25}],
    ),
    "运动服饰": CategoryKnowledge(
        name="运动服饰",
        sub_directions=["运动T恤", "运动裤", "运动内衣", "瑜伽服", "跑步鞋", "运动袜", "骑行服", "游泳衣"],
        known_brands=["Nike", "Adidas", "Lululemon", "Under Armour", "李宁", "安踏", "Keep", "迪卡侬", "亚瑟士", "斯凯奇", "特步", "361°"],
        pain_points=["闷汗", "掉色", "磨脚", "弹性差", "不透气", "线头多", "起球", "缩水"],
        price_range=(15, 1500, 150),
        growth_scenarios=[{"name": "瑜伽服", "rate": 0.55}, {"name": "骑行服", "rate": 0.45}, {"name": "运动内衣", "rate": 0.35}, {"name": "跑步鞋", "rate": 0.15}, {"name": "运动T恤", "rate": 0.05}],
    ),
    "户外装备": CategoryKnowledge(
        name="户外装备",
        sub_directions=["帐篷", "睡袋", "登山包", "户外灯", "防晒衣", "冲锋衣", "登山鞋", "野营炊具"],
        known_brands=["探路者", "牧高笛", "骆驼", "挪客", "迪卡侬", "Naturehike", "北面", "Osprey", "黑鹿", "火枫", "龙牙", "凯乐石"],
        pain_points=["太重", "不防水", "褪色", "拉链坏", "支撑力不足", "有异味", "体积大", "不耐脏", "断线破洞", "锁定不牢"],
        price_range=(20, 3000, 200),
        growth_scenarios=[{"name": "帐篷", "rate": 0.60}, {"name": "野营炊具", "rate": 0.50}, {"name": "户外灯", "rate": 0.40}, {"name": "登山鞋", "rate": 0.20}, {"name": "睡袋", "rate": 0.15}],
    ),
    "球类运动": CategoryKnowledge(
        name="球类运动",
        sub_directions=["篮球足球", "羽毛球网球", "乒乓球", "高尔夫", "台球", "飞盘", "排球"],
        known_brands=["Wilson", "Spalding", "李宁", "红双喜", "Yonex", "HEAD", "史莱辛格", "胜利", "Butterfly", "Callaway", "Frisbee", "Mikasa"],
        pain_points=["漏气", "不耐打", "手感差", "掉色", "弹性差", "线断", "网不结实", "磨损快"],
        price_range=(10, 2000, 100),
        growth_scenarios=[{"name": "飞盘", "rate": 0.65}, {"name": "高尔夫", "rate": 0.30}, {"name": "羽毛球", "rate": 0.25}, {"name": "篮球足球", "rate": 0.10}, {"name": "乒乓球", "rate": 0.15}],
    ),
    # ── 宠物 ──
    "猫咪用品": CategoryKnowledge(
        name="猫咪用品",
        sub_directions=["猫粮猫零食", "猫砂猫厕所", "猫抓板猫爬架", "猫玩具", "猫咪洗护", "猫窝猫垫", "猫咪服装", "猫咪营养品"],
        known_brands=["皇家", "冠能", "麦富迪", "网易严选", "卫仕", "小佩", "有陪", "CATLINK", "铂钻", "尾巴生活", "爱肯拿", "素力高"],
        pain_points=["适口性差", "结团差", "异味重", "掉毛严重", "成分不清晰", "不倒翁", "不耐玩", "清洗麻烦"],
        price_range=(5, 500, 50),
        growth_scenarios=[{"name": "猫咪营养品", "rate": 0.60}, {"name": "智能猫砂盆", "rate": 0.75}, {"name": "猫玩具", "rate": 0.35}, {"name": "猫粮", "rate": 0.15}, {"name": "猫咪服装", "rate": 0.25}],
    ),
    "狗狗用品": CategoryKnowledge(
        name="狗狗用品",
        sub_directions=["狗粮狗零食", "狗狗牵引绳", "狗狗玩具", "狗狗洗护", "狗窝狗垫", "狗狗服装", "狗狗营养品", "训狗用品"],
        known_brands=["皇家", "比瑞吉", "伯纳天纯", "疯狂小狗", "麦富迪", "冠能", "耐威克", "信元发育宝", "海洋之星", "欧帝亿", "多格漫", "PETKIT"],
        pain_points=["适口性差", "咬坏", "异味重", "掉色", "不耐玩", "弹性差", "有化学味", "尺寸不符"],
        price_range=(10, 600, 60),
        growth_scenarios=[{"name": "训狗用品", "rate": 0.50}, {"name": "狗狗营养品", "rate": 0.55}, {"name": "狗狗玩具", "rate": 0.30}, {"name": "狗粮", "rate": 0.10}, {"name": "狗狗服装", "rate": 0.35}],
    ),
    "水族用品": CategoryKnowledge(
        name="水族用品",
        sub_directions=["鱼缸水族箱", "鱼粮", "过滤器水泵", "水草造景", "灯具加热棒", "龟缸爬宠"],
        known_brands=["森森", "佳宝", "创新", "EHEIM", "Tetra", "日生", "JBL", "博宇", "闽江", "海之蓝", "宠物石头", "千寻"],
        pain_points=["漏水", "噪音大", "过滤效果差", "灯不亮", "水泵坏", "玻璃质量差", "温度不准", "有异味"],
        price_range=(10, 3000, 200),
        growth_scenarios=[{"name": "水草造景", "rate": 0.55}, {"name": "龟缸爬宠", "rate": 0.50}, {"name": "灯具加热棒", "rate": 0.30}, {"name": "鱼缸水族箱", "rate": 0.15}, {"name": "鱼粮", "rate": 0.10}],
    ),
    # ── 汽车用品 ──
    "车内用品": CategoryKnowledge(
        name="车内用品",
        sub_directions=["车载充电器", "车载香薰", "座椅垫坐垫", "车载收纳", "车载手机支架", "方向盘套", "脚垫"],
        known_brands=["倍思", "小米", "3M", "固特异", "五福金牛", "乔氏", "指南车", "卡斯兰", "宝克", "车玛仕", "AutoPro", "致橡树"],
        pain_points=["有异味", "不匹配车型", "不耐用", "褪色", "滑移", "粘性不好", "质量差", "太厚影响驾驶"],
        price_range=(10, 500, 60),
        growth_scenarios=[{"name": "车载手机支架", "rate": 0.35}, {"name": "车载香薰", "rate": 0.45}, {"name": "车载收纳", "rate": 0.30}, {"name": "方向盘套", "rate": 0.10}, {"name": "座椅垫", "rate": 0.15}],
    ),
    "车外用品": CategoryKnowledge(
        name="车外用品",
        sub_directions=["行车记录仪", "倒车影像", "车贴改装", "车衣车罩", "洗车工具", "补漆笔", "汽车蜡"],
        known_brands=["盯盯拍", "360", "Papago", "VANTRUE", "凌度", "龟牌", "索纳克斯", "维麦通", "米其林", "洗车王国", "车仆", "宜丽客"],
        pain_points=["画质模糊", "安装复杂", "夜视差", "不防水", "发烫", "漏录", "太大影响视线", "信号不稳定"],
        price_range=(30, 2000, 200),
        growth_scenarios=[{"name": "行车记录仪", "rate": 0.45}, {"name": "车衣车罩", "rate": 0.35}, {"name": "洗车工具", "rate": 0.25}, {"name": "车贴改装", "rate": 0.20}, {"name": "倒车影像", "rate": 0.15}],
    ),
    # ── 文具办公 ──
    "学生文具": CategoryKnowledge(
        name="学生文具",
        sub_directions=["中性笔圆珠笔", "笔记本作业本", "铅笔橡皮", "尺子圆规", "彩笔水彩", "书包", "文具盒"],
        known_brands=["得力", "晨光", "齐心", "国誉", "百乐", "三菱", "真彩", "樱花", "马利", "孔庙祈福", "KACO", "慕那美"],
        pain_points=["断墨", "出水不顺", "纸张薄透", "橡皮容易断", "褪色", "书包线头多", "文具盒坏掉", "尺子不直"],
        price_range=(1, 300, 20),
        growth_scenarios=[{"name": "彩笔水彩", "rate": 0.35}, {"name": "书包", "rate": 0.25}, {"name": "笔记本", "rate": 0.15}, {"name": "中性笔", "rate": 0.05}, {"name": "文具盒", "rate": 0.20}],
    ),
    "办公用品": CategoryKnowledge(
        name="办公用品",
        sub_directions=["打印纸", "文件夹档案盒", "便利贴", "订书机打孔器", "白板笔", "名片夹", "办公桌垫"],
        known_brands=["得力", "晨光", "齐心", "AP", "国际纸业", "金得利", "三木", "汇金", "天章", "科密", "索尼", "益而高"],
        pain_points=["纸张泛黄", "有异味", "卡纸", "夹子坏", "尺寸不对", "粘性不好", "褪色", "生锈"],
        price_range=(2, 500, 30),
        growth_scenarios=[{"name": "办公桌垫", "rate": 0.40}, {"name": "打印纸", "rate": 0.10}, {"name": "便利贴", "rate": 0.20}, {"name": "文件夹", "rate": 0.05}, {"name": "订书机打孔器", "rate": 0.15}],
    ),
}


# ===================== 别名映射（模糊匹配用） =====================

ALIAS_MAP = {
    # 水饮
    "水": "水饮", "饮料": "水饮", "饮品": "水饮", "喝的": "水饮",
    "茶": "水饮", "咖啡": "水饮", "汽水": "水饮", "矿泉水": "水饮",
    # 零食
    "零食": "零食", "休闲食品": "零食", "坚果": "零食", "薯片": "零食",
    "饼干": "零食", "糖果": "零食", "巧克力": "零食", "辣条": "零食",
    "吃的": "零食", "小吃": "零食", "零嘴": "零食",
    # 速食
    "方便面": "速食", "泡面": "速食", "自热": "速食", "螺蛳粉": "速食",
    "速冻": "速食", "冷冻食品": "速食", "罐头": "速食", "代餐": "速食",
    "冲泡": "速食", "即食": "速食",
    # 生鲜
    "水果": "生鲜", "蔬菜": "生鲜", "肉": "生鲜", "海鲜": "生鲜",
    "鸡蛋": "生鲜", "米面": "生鲜", "粮油": "生鲜", "调味": "生鲜",
    "食材": "生鲜", "生鲜": "生鲜",
    # 保健
    "保健": "保健食品", "维生素": "保健食品", "蛋白粉": "保健食品",
    "保健品": "保健食品", "营养品": "保健食品", "补品": "保健食品",
    # 美妆
    "护肤": "护肤品", "洗面奶": "护肤品", "精华": "护肤品",
    "面膜": "护肤品", "面霜": "护肤品", "爽肤水": "护肤品",
    "彩妆": "彩妆", "口红": "彩妆", "粉底": "彩妆", "眼影": "彩妆",
    "化妆品": "彩妆", "化妆": "彩妆", "眉笔": "彩妆",
    "洗护": "洗护", "洗发": "洗护", "沐浴": "洗护", "牙膏": "洗护",
    "牙刷": "洗护", "个护": "洗护", "吹风机": "洗护",
    "香水": "香水", "香薰": "香水", "香氛": "香水", "蜡烛": "香水",
    # 服装
    "女装": "女装", "连衣裙": "女装", "内衣": "女装", "睡衣": "女装",
    "男装": "男装", "T恤": "男装", "衬衫": "男装", "POLO": "男装",
    "男士": "男装",
    "鞋": "鞋靴", "运动鞋": "鞋靴", "板鞋": "鞋靴", "靴子": "鞋靴",
    "皮鞋": "鞋靴", "帆布鞋": "鞋靴",
    "箱包": "箱包", "背包": "箱包", "包包": "箱包", "行李箱": "箱包",
    "配饰": "配饰", "项链": "配饰", "耳环": "配饰", "手表": "配饰",
    "帽子": "配饰", "眼镜": "配饰",
    # 数码
    "手机壳": "手机配件", "手机膜": "手机配件", "充电器": "手机配件",
    "充电宝": "手机配件", "数据线": "手机配件", "手机支架": "手机配件",
    "手机": "手机配件", "充电": "手机配件",
    "耳机": "耳机音频", "音箱": "耳机音频", "蓝牙耳机": "耳机音频",
    "音频": "耳机音频",
    "键盘": "电脑配件", "鼠标": "电脑配件", "显示器": "电脑配件",
    "笔记本": "电脑配件", "U盘": "电脑配件", "硬盘": "电脑配件",
    "电脑": "电脑配件", "PC": "电脑配件",
    "智能": "智能设备", "手表": "智能设备", "扫地机": "智能设备",
    "机器人": "智能设备", "无人机": "摄影器材", "相机": "摄影器材",
    "摄影": "摄影器材", "镜头": "摄影器材",
    # 家居
    "收纳": "家居收纳", "抽屉柜": "家居收纳", "整理": "家居收纳",
    "床上": "床上用品", "被子": "床上用品", "枕头": "床上用品",
    "床单": "床上用品", "四件套": "床上用品",
    "厨房": "厨房用品", "锅": "厨房用品", "厨具": "厨房用品",
    "刀具": "厨房用品", "炊具": "厨房用品", "餐具": "厨房用品",
    "灯": "灯具照明", "台灯": "灯具照明", "吸顶灯": "灯具照明",
    "清洁": "清洁用品", "洗衣": "清洁用品", "纸巾": "清洁用品",
    "湿巾": "清洁用品", "垃圾袋": "清洁用品", "拖把": "清洁用品",
    "家纺": "家纺软装", "窗帘": "家纺软装", "地毯": "家纺软装",
    "抱枕": "家纺软装", "软装": "家纺软装",
    # 母婴
    "婴儿": "婴儿用品", "纸尿裤": "婴儿用品", "奶瓶": "婴儿用品",
    "宝宝": "婴儿用品", "奶粉": "婴儿用品", "尿不湿": "婴儿用品",
    "玩具": "儿童玩具", "乐高": "儿童玩具", "积木": "儿童玩具",
    "多美卡": "儿童玩具", "毛绒": "儿童玩具",
    "儿童服装": "儿童服装", "童装": "儿童服装", "宝宝衣服": "儿童服装",
    "孕产妇": "孕产妇", "孕妇": "孕产妇", "待产": "孕产妇",
    "月子": "孕产妇", "哺乳": "孕产妇",
    # 运动
    "健身": "健身器材", "瑜伽": "健身器材", "哑铃": "健身器材",
    "器材": "健身器材", "锻炼": "健身器材",
    "运动服": "运动服饰", "运动装": "运动服饰", "跑步": "运动服饰",
    "骑行": "运动服饰", "游泳": "运动服饰",
    "户外": "户外装备", "露营": "户外装备", "登山": "户外装备",
    "帐篷": "户外装备", "冲锋衣": "户外装备",
    "篮球": "球类运动", "足球": "球类运动", "羽毛球": "球类运动",
    "球类": "球类运动", "运动": "运动服饰",
    # 宠物
    "猫": "猫咪用品", "猫咪": "猫咪用品", "喵": "猫咪用品",
    "猫粮": "猫咪用品", "猫砂": "猫咪用品",
    "狗": "狗狗用品", "狗狗": "狗狗用品", "汪": "狗狗用品",
    "狗粮": "狗狗用品",
    "宠物": "猫咪用品", "水族": "水族用品", "鱼缸": "水族用品",
    "鱼": "水族用品", "爬宠": "水族用品",
    # 汽车
    "车载": "车内用品", "车用": "车内用品", "车内": "车内用品",
    "车": "车外用品", "汽车": "车外用品", "行车记录仪": "车外用品",
    # 办公
    "文具": "学生文具", "笔": "学生文具", "笔记本本子": "学生文具",
    "书包": "学生文具",
    "办公": "办公用品", "打印": "办公用品", "文件夹": "办公用品",
    # 工业
    "自动化": "自动化设备", "工业": "自动化设备", "工控": "自动化设备",
    "设备": "自动化设备", "传感器": "自动化设备",
}


class MockDataEngine:
    """Mock 数据引擎 — 支持 40+ 品类"""

    def __init__(self):
        self.knowledge = BUILTIN_KNOWLEDGE

    def get_knowledge(self, keyword: str) -> Optional[CategoryKnowledge]:
        """精确匹配知识库大类"""
        return self.knowledge.get(keyword)

    def fuzzy_match(self, keyword: str) -> Optional[CategoryKnowledge]:
        """模糊匹配：别名映射 → 精确匹配 → 子串包含 → 细分方向匹配"""
        kw_lower = keyword.lower()

        # 1. 别名映射
        for alias, cat_name in ALIAS_MAP.items():
            if alias in kw_lower or kw_lower in alias:
                if found := self.knowledge.get(cat_name):
                    return found

        # 2. 精确匹配
        if found := self.knowledge.get(keyword):
            return found

        # 3. 大类名称包含关系
        for cat_name, knowledge in self.knowledge.items():
            if kw_lower in cat_name.lower() or cat_name.lower() in kw_lower:
                return knowledge

        # 4. 细分方向匹配
        for knowledge in self.knowledge.values():
            for sd in knowledge.sub_directions:
                if kw_lower in sd.lower() or sd.lower() in kw_lower:
                    return knowledge

        return None

    def _build_dynamic_knowledge(self, keyword: str, constraints: Dict[str, Any]) -> CategoryKnowledge:
        """为未知品类动态构建知识结构"""
        price_min = constraints.get("price_min", 5)
        price_max = constraints.get("price_max", 500)
        price_mean = (price_min + price_max) / 2

        suffixes = ["基础款", "升级款", "家用款", "商用款", "高端款", "便携款"]
        generic_directions = [f"{keyword}{s}" for s in suffixes]

        generic_brands = [f"{keyword[:2]}品牌{k}" for k in "ABCDEF"] + ["白牌"]
        generic_pain_points = ["质量不稳定", "性价比低", "使用不方便", "外观一般",
                               "售后服务差", "功能少", "尺寸不合适", "有异味"]

        return CategoryKnowledge(
            name=keyword,
            sub_directions=generic_directions,
            known_brands=generic_brands,
            pain_points=generic_pain_points,
            price_range=(price_min, price_max, price_mean),
            growth_scenarios=[{"name": d, "rate": round(random.uniform(-0.15, 0.75), 2)} for d in generic_directions],
        )

    def generate(self, keyword, constraints=None, count=150):
        """生成模拟商品数据"""
        constraints = constraints or {}
        count = max(100, min(200, count))

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

        brand_dist = {"known": 0.05, "small": 0.15, "white": 0.80} if prefer_white_label \
            else {"known": 0.15, "small": 0.25, "white": 0.60}

        sales_ranks = list(range(count))
        random.shuffle(sales_ranks)
        growth_map = {s["name"]: s["rate"] for s in knowledge.growth_scenarios}

        for i in range(count):
            sub_dir = self._pick_sub_direction(knowledge, target_audience)
            brand_type = self._weighted_choice(["known", "small", "white"],
                                               [brand_dist["known"], brand_dist["small"], brand_dist["white"]])
            brand = self._pick_brand(knowledge, brand_type)
            price = self._normal_price(price_mean, price_min, price_max)
            rank_pct = sales_ranks[i] / count
            base_sales = int(10000 * math.exp(-3 * rank_pct))
            sales = max(1, int(base_sales * random.uniform(0.7, 1.3)))
            rating = max(1.0, min(5.0, round(random.gauss(4.3, 0.4), 1)))
            review_count = int(sales * random.uniform(0.02, 0.15))
            title = self._generate_title(keyword, sub_dir, brand, i)
            shop_type = "旗舰店" if brand_type == "known" else random.choice(["专营店", "普通店", "普通店"])
            growth_rate = growth_map.get(sub_dir, round(random.uniform(-0.10, 0.55), 2))

            products.append({
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
            })

        products.sort(key=lambda x: -x["sales_30d"])
        logger.info(f"[Mock] 生成完成: {len(products)} 条")
        return products

    def generate_reviews(self, products, knowledge=None, keyword=""):
        """为商品列表生成评论数据"""
        if not knowledge:
            knowledge = self.get_knowledge(keyword) or self.fuzzy_match(keyword)
        if not knowledge:
            knowledge = self._build_dynamic_knowledge(keyword, {})
        reviews = []
        for product in products:
            neg_ratio = (5.0 - product["rating"]) / 10.0
            total_reviews = min(20, max(3, int(product["review_count"] * 0.05)))
            for _ in range(total_reviews):
                is_negative = random.random() < neg_ratio
                rev_rating = random.randint(1, 3) if is_negative else random.randint(4, 5)
                if is_negative:
                    keywords = random.sample(knowledge.pain_points, k=min(3, len(knowledge.pain_points)))
                    content = f"{'、'.join(keywords)}，{'不太满意' if rev_rating == 2 else '很失望'}"
                else:
                    keywords = random.sample(["好用", "性价比高", "发货快", "质感好", "推荐"], k=min(2, 5))
                    content = f"{'、'.join(keywords)}，{'不错' if rev_rating == 4 else '非常满意'}"
                reviews.append({"content": content, "sentiment": "negative" if is_negative else "positive",
                                "keywords": keywords, "rating": rev_rating})
        return reviews

    def _pick_sub_direction(self, knowledge, audience):
        directions = knowledge.sub_directions.copy() or [knowledge.name]
        weights = [1.0] * len(directions)
        if "年轻人" in audience:
            for i, d in enumerate(directions):
                if any(w in d for w in ["智能", "便携", "潮", "新"]):
                    weights[i] *= 1.5
        if "宝妈" in audience or "母婴" in audience:
            for i, d in enumerate(directions):
                if any(w in d for w in ["安全", "婴儿", "孕", "母婴", "儿童", "宝宝"]):
                    weights[i] *= 1.8
        return self._weighted_choice(directions, weights)

    def _pick_brand(self, knowledge, brand_type):
        if brand_type == "white":
            return "白牌"
        if brand_type == "known" and knowledge.known_brands:
            return random.choice(knowledge.known_brands[:8])
        return f"{knowledge.name[:2]}{random.choice(['之', '优', '良', '品', '佳', '尚'])}{random.choice(['选', '作', '坊', '造'])}"

    def _normal_price(self, mean, lo, hi):
        std = (hi - lo) / 4
        return max(lo, min(hi, random.gauss(mean, std)))

    def _generate_title(self, keyword, sub_dir, brand, idx):
        templates = [
            f"{brand} {sub_dir} {keyword}{random.randint(1, 999)}",
            f"{brand} {random.choice(['新款', '升级', '便携'])}{sub_dir}",
            f"{sub_dir} {random.choice(['套装', '组合', '礼盒'])} {brand}",
            f"{brand} {keyword}专用 {sub_dir}",
        ]
        return random.choice(templates)

    @staticmethod
    def _weighted_choice(items, weights):
        total = sum(weights)
        r = random.random() * total
        cumulative = 0
        for item, w in zip(items, weights):
            cumulative += w
            if r <= cumulative:
                return item
        return items[-1]
