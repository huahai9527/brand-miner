"""
数据库模型层 — 5 张核心表（async SQLAlchemy 2.0 风格）
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Text, JSON, DateTime, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


# ===================== 表1: AnalysisTask =====================
# 记录每次分析任务的核心元数据
class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(64), default=generate_uuid, unique=True, index=True,
                     comment="UUID 任务标识")
    category = Column(String(128), nullable=False, index=True,
                      comment="分析的大类方向，如 '宠物'、'家居'")
    constraints = Column(JSON, default=dict,
                         comment="约束条件 JSON: {price_range, target_audience, prefer_white_label, ...}")
    status = Column(String(32), default="pending",
                    comment="pending / running / completed / failed")
    progress = Column(Integer, default=0,
                      comment="进度百分比 0-100")
    created_at = Column(DateTime, default=utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, comment="更新时间")

    # 关联
    products = relationship("Product", back_populates="task", cascade="all, delete-orphan")
    sub_category_analyses = relationship("SubCategoryAnalysis", back_populates="task", cascade="all, delete-orphan")
    report = relationship("Report", back_populates="task", uselist=False, cascade="all, delete-orphan")


# ===================== 表2: Product =====================
# 统一商品数据模型 — 所有数据源适配后统一为此格式
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("analysis_tasks.id"), nullable=False, index=True)

    platform = Column(String(32), default="mock", comment="数据来源平台: tianchi/jd/mock")
    title = Column(String(512), nullable=False, comment="商品标题")
    price = Column(Float, nullable=False, comment="商品价格（元）")
    sales_30d = Column(Integer, default=0, comment="近30天销量")
    brand = Column(String(128), default="白牌", comment="品牌名")
    sub_category = Column(String(128), index=True, comment="细分品类")
    shop_type = Column(String(32), default="普通店", comment="店铺类型: 旗舰店/专营店/普通店")
    rating = Column(Float, default=4.0, comment="评分 1-5")
    review_count = Column(Integer, default=0, comment="评论总数")
    source_url = Column(String(1024), default="", comment="原始链接")

    created_at = Column(DateTime, default=utcnow)

    task = relationship("AnalysisTask", back_populates="products")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")


# ===================== 表3: Review =====================
# 商品评论数据
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    content = Column(Text, comment="评论内容")
    sentiment = Column(String(16), comment="情感极性: positive/neutral/negative")
    keywords = Column(JSON, default=list, comment="关键词列表")
    rating = Column(Integer, comment="评论星级 1-5")

    created_at = Column(DateTime, default=utcnow)

    product = relationship("Product", back_populates="reviews")


# ===================== 表4: SubCategoryAnalysis =====================
# 细分品类分析结果 — 4 维度评分模型
class SubCategoryAnalysis(Base):
    __tablename__ = "sub_category_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("analysis_tasks.id"), nullable=False, index=True)
    sub_category = Column(String(128), nullable=False, comment="细分品类名称")

    # 四大评分维度（0-100 分制）
    brand_vacuum_score = Column(Integer, default=0, comment="品牌真空度得分（白牌占比越高分越高）")
    growth_signal_score = Column(Integer, default=0, comment="增长信号得分（销量增速）")
    pain_point_score = Column(Integer, default=0, comment="痛点得分（差评关键词密度）")
    price_profit_score = Column(Integer, default=0, comment="价格利润空间得分")
    total_score = Column(Integer, default=0, comment="综合加权总分")

    # 分析详情
    market_size = Column(Integer, default=0, comment="市场体量（近30天总销量）")
    avg_price = Column(Float, default=0, comment="均价")
    brand_count = Column(Integer, default=0, comment="品牌数量")
    growth_rate = Column(Float, default=0, comment="季度增长率")
    analysis_detail = Column(JSON, default=dict, comment="详细分析数据 JSON")

    created_at = Column(DateTime, default=utcnow)

    task = relationship("AnalysisTask", back_populates="sub_category_analyses")


# ===================== 表5: Report =====================
# 最终决策报告
class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("analysis_tasks.id"), nullable=False, unique=True, index=True)

    content = Column(JSON, default=dict, comment="完整报告 JSON")
    top_direction = Column(String(128), comment="推荐首选细分方向")
    pricing_suggestion = Column(String(256), comment="定价建议")
    entry_strategy = Column(Text, comment="切入策略描述")

    created_at = Column(DateTime, default=utcnow)

    task = relationship("AnalysisTask", back_populates="report")
