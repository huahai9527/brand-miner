"""
第一层数据源：阿里天池电商数据集
- 读取标准 CSV 格式
- 字段映射为统一 Product 格式
- 文件不存在时自动降级到 Mock
"""
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import TIANCHI_DATA_PATH

logger = logging.getLogger(__name__)

# 天池标准字段 -> 统一 Product 格式的映射
TIANCHI_FIELD_MAP = {
    "item_id": "source_id",
    "cate_id": "category_id",
    "cate_name": "sub_category",
    "brand": "brand",
    "price": "price",
    "sales": "sales_30d",
    "comment_num": "review_count",
    "shop_name": "shop_name",
}

TIANCHI_REQUIRED_FIELDS = {"item_id", "cate_id", "cate_name", "price"}


class TianchiDataLoader:
    """
    天池数据加载器
    读取 data/real/ 下的 CSV，输出统一 Product 字典列表
    """

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = Path(data_path or TIANCHI_DATA_PATH)

    def list_csv_files(self) -> List[Path]:
        """列出 data/real/ 下所有 CSV 文件"""
        if not self.data_path.exists():
            return []
        return sorted(self.data_path.glob("*.csv"))

    def validate_fields(self, headers: List[str]) -> bool:
        """验证 CSV 是否包含必要字段"""
        header_set = set(headers)
        return TIANCHI_REQUIRED_FIELDS.issubset(header_set)

    def map_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """将天池行数据映射为统一 Product 格式"""
        product = {
            "platform": "tianchi",
            "title": row.get("item_id", ""),
            "price": self._safe_float(row.get("price", 0)),
            "sales_30d": self._safe_int(row.get("sales", 0)),
            "brand": row.get("brand", "未知品牌"),
            "sub_category": row.get("cate_name", ""),
            "shop_type": "普通店",
            "rating": 4.0,  # 天池不提供评分
            "review_count": self._safe_int(row.get("comment_num", 0)),
            "source_url": "",
        }
        return product

    def load(self, category: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
        """
        加载天池数据
        category: 可选按大类过滤
        limit: 最大返回条数
        """
        csv_files = self.list_csv_files()
        if not csv_files:
            logger.warning("[Tianchi] data/real/ 目录无可用的 CSV 文件，降级到 Mock")
            return []

        results = []
        for csv_file in csv_files:
            try:
                with open(csv_file, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames or []
                    if not self.validate_fields(headers):
                        logger.warning(f"[Tianchi] {csv_file.name} 缺少必要字段 {TIANCHI_REQUIRED_FIELDS}，跳过")
                        continue

                    for row in reader:
                        product = self.map_row(row)
                        if category and category not in product.get("sub_category", "") and category not in product.get("title", ""):
                            continue
                        results.append(product)
                        if len(results) >= limit:
                            break
            except Exception as e:
                logger.error(f"[Tianchi] 读取 {csv_file.name} 失败: {e}")
                continue

            if len(results) >= limit:
                break

        logger.info(f"[Tianchi] 成功加载 {len(results)} 条数据")
        return results

    def check_available(self) -> bool:
        """检查天池数据是否可用"""
        csv_files = self.list_csv_files()
        if not csv_files:
            return False
        # 快速检查第一个文件是否有数据
        try:
            with open(csv_files[0], "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames and self.validate_fields(reader.fieldnames):
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def _safe_float(val) -> float:
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _safe_int(val) -> int:
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0
