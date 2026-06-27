"""
数据源适配器 — 统一入口 + 自动降级
- 根据 DATA_SOURCE 环境变量选择数据源
- 降级链：tianchi → jd → mock
- 自动记录日志，对上层透明
"""
import logging
from typing import List, Dict, Any, Optional

from backend.config import DATA_SOURCE, USE_MOCK_FALLBACK
from backend.data_sources.tianchi import TianchiDataLoader
from backend.data_sources.jd_crawler import JDLightCrawler
from backend.data_sources.mock_engine import MockDataEngine

logger = logging.getLogger(__name__)


class DataSourceAdapter:
    """
    数据源适配器
    统一接口，自动降级，保证演示永不中断
    """

    def __init__(self):
        self.tianchi = TianchiDataLoader()
        self.jd = JDLightCrawler()
        self.mock = MockDataEngine()
        self.current_source = DATA_SOURCE

    def get_status(self) -> Dict[str, Any]:
        """获取三层数据源状态（用于 /api/v1/data-source/status）"""
        tianchi_available = self.tianchi.check_available()
        # JD 总是 available=True（因为爬取失败只是返回空列表）
        jd_available = True
        mock_available = True

        return {
            "current_source": self.current_source,
            "sources": {
                "tianchi": {
                    "available": tianchi_available,
                    "description": "阿里天池电商数据集",
                    "csv_files": len(self.tianchi.list_csv_files()),
                },
                "jd": {
                    "available": jd_available,
                    "description": "京东搜索结果爬虫（单次≤30条）",
                },
                "mock": {
                    "available": mock_available,
                    "description": "智能 Mock 数据引擎（10大类知识库+动态生成）",
                },
            },
        }

    def fetch(
        self,
        keyword: str,
        constraints: Optional[Dict[str, Any]] = None,
        count: int = 150,
    ) -> List[Dict[str, Any]]:
        """
        统一数据获取入口
        按降级链自动尝试，保证返回数据不为空
        """
        source = self.current_source
        logger.info(f"[Adapter] 当前数据源: {source}, 关键词: {keyword}")

        # ---- 第1层：天池 ----
        if source == "tianchi":
            data = self.tianchi.load(category=keyword, limit=count)
            if data:
                logger.info(f"[Adapter] 天池数据成功: {len(data)} 条")
                return data
            logger.warning(f"[Adapter] 天池数据不可用，降级到 JD")
            data = self._try_jd(keyword, count)
            if data:
                return data
            logger.warning(f"[Adapter] JD 数据不可用，降级到 Mock")
            return self.mock.generate(keyword, constraints, count)

        # ---- 第2层：京东 ----
        if source == "jd":
            data = self._try_jd(keyword, count)
            if data:
                logger.info(f"[Adapter] JD 数据成功: {len(data)} 条")
                return data
            logger.warning(f"[Adapter] JD 数据不可用，降级到 Mock")
            return self.mock.generate(keyword, constraints, count)

        # ---- 第3层：Mock（默认）----
        return self.mock.generate(keyword, constraints, count)

    def fetch_with_reviews(
        self,
        keyword: str,
        constraints: Optional[Dict[str, Any]] = None,
        count: int = 150,
    ) -> Dict[str, Any]:
        """
        获取商品 + 评论数据
        返回: {"products": [...], "reviews": [...]}
        """
        products = self.fetch(keyword, constraints, count)
        reviews = self.mock.generate_reviews(products, keyword=keyword)
        return {"products": products, "reviews": reviews}

    def _try_jd(self, keyword: str, count: int) -> List[Dict[str, Any]]:
        """尝试 JD 爬虫，异常安全"""
        try:
            results = self.jd.search(keyword)
            # 爬不到也不要紧，返回空列表触发降级
            if results:
                return results[:count]
        except Exception as e:
            logger.warning(f"[Adapter] JD 异常: {e}")
        return []
