"""
第二层数据源：京东轻量爬虫
- 只爬搜索结果列表页，不登录，不爬详情页
- 单次30条，2-5秒随机间隔
- 结果缓存到 data/cache/，24小时 TTL
- 爬取失败自动降级到 Mock
"""
import json
import logging
import random
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import JD_CACHE_PATH, JD_MAX_ITEMS, JD_MIN_DELAY, JD_MAX_DELAY, JD_CACHE_TTL_HOURS

logger = logging.getLogger(__name__)

# 真实 UA 列表（主流浏览器）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]


class JDLightCrawler:
    """
    京东轻量级搜索结果爬虫
    缓存机制：24小时内相同关键词直接读缓存
    """

    def __init__(self, cache_path: Optional[str] = None):
        self.cache_dir = Path(cache_path or JD_CACHE_PATH)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, keyword: str) -> str:
        """生成缓存文件名（关键词 MD5）"""
        h = hashlib.md5(keyword.encode()).hexdigest()
        return f"jd_{h}.json"

    def _read_cache(self, keyword: str) -> Optional[List[Dict[str, Any]]]:
        """读取缓存：24 小时内有效"""
        cache_file = self.cache_dir / self._cache_key(keyword)
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)

            cache_time = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
            if datetime.now() - cache_time < timedelta(hours=JD_CACHE_TTL_HOURS):
                logger.info(f"[JD] 命中缓存: {keyword} ({len(cached['data'])} 条)")
                return cached["data"]
            else:
                logger.info(f"[JD] 缓存已过期: {keyword}")
        except Exception as e:
            logger.warning(f"[JD] 缓存读取失败: {e}")

        return None

    def _write_cache(self, keyword: str, data: List[Dict[str, Any]]):
        """写入缓存"""
        cache_file = self.cache_dir / self._cache_key(keyword)
        cache_data = {
            "cached_at": datetime.now().isoformat(),
            "keyword": keyword,
            "count": len(data),
            "data": data,
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logger.info(f"[JD] 缓存写入: {keyword} ({len(data)} 条)")

    def _random_delay(self):
        """随机 2-5 秒延迟"""
        delay = random.uniform(JD_MIN_DELAY, JD_MAX_DELAY)
        time.sleep(delay)

    def _get_random_ua(self) -> str:
        return random.choice(USER_AGENTS)

    def _build_search_url(self, keyword: str, page: int = 1) -> str:
        """构建京东搜索 URL"""
        encoded = keyword.replace(" ", "+")
        return f"https://search.jd.com/Search?keyword={encoded}&page={page}&enc=utf-8"

    def _parse_search_result_html(self, html: str, keyword: str) -> List[Dict[str, Any]]:
        """
        解析京东搜索结果 HTML（正则方式，避免依赖 BeautifulSoup）
        只提取列表页基本字段：标题、价格、评论数、店铺名、链接
        """
        import re

        results = []
        # 京东列表页每个商品通常在 <li data-sku="..."> 里
        # 用正则批量匹配
        items = re.split(r'<li[^>]*data-sku', html)
        for item in items[1:JD_MAX_ITEMS + 1]:
            try:
                # 提取 SKU ID
                sku_match = re.search(r'"(\d+)"', item)
                sku_id = sku_match.group(1) if sku_match else ""

                # 提取标题
                title_match = re.search(r'<em>(.*?)</em>', item)
                title = title_match.group(1) if title_match else "未知商品"

                # 提取价格
                price_match = re.search(r'<i[^>]*>(\d+\.?\d*)</i>', item)
                price = float(price_match.group(1)) if price_match else 0.0

                # 提取评论数
                comment_match = re.search(r'(\d+)万?\+?条评价', item)
                review_count = 0
                if comment_match:
                    if "万" in comment_match.group(0):
                        review_count = int(float(comment_match.group(1)) * 10000)
                    else:
                        review_count = int(comment_match.group(1))

                # 提取店铺名
                shop_match = re.search(r'<a[^>]*class="[^"]*shopname[^"]*"[^>]*>(.*?)</a>', item, re.DOTALL)
                shop_name = shop_match.group(1).strip() if shop_match else ""

                results.append({
                    "platform": "jd",
                    "title": self._clean_html(title),
                    "price": price,
                    "sales_30d": 0,  # 列表页不可见
                    "brand": shop_name or "京东商家",
                    "sub_category": keyword,
                    "shop_type": "京东店",
                    "rating": 4.0,
                    "review_count": review_count,
                    "source_url": f"https://item.jd.com/{sku_id}.html" if sku_id else "",
                })
            except Exception as e:
                logger.debug(f"[JD] 解析单条失败: {e}")
                continue

        return results

    @staticmethod
    def _clean_html(text: str) -> str:
        """去除 HTML 标签"""
        import re
        return re.sub(r'<[^>]+>', '', text).strip()

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索京东商品（带缓存、反爬、降级）
        优先读缓存，缓存未命中则尝试爬取
        """
        # 1. 先查缓存
        cached = self._read_cache(keyword)
        if cached is not None:
            return cached

        # 2. 尝试爬取
        logger.info(f"[JD] 开始爬取: {keyword}")
        results = []

        try:
            import urllib.request
            from urllib.error import URLError

            search_url = self._build_search_url(keyword)
            req = urllib.request.Request(
                search_url,
                headers={
                    "User-Agent": self._get_random_ua(),
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                    "Referer": "https://www.jd.com/",
                }
            )

            self._random_delay()
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                results = self._parse_search_result_html(html, keyword)

            logger.info(f"[JD] 爬取成功: {keyword} ({len(results)} 条)")
        except URLError as e:
            logger.warning(f"[JD] 网络请求失败: {e}")
        except Exception as e:
            logger.warning(f"[JD] 爬取异常: {e}")

        # 3. 即使没爬到结果也缓存（避免频繁重试）
        self._write_cache(keyword, results)
        return results
