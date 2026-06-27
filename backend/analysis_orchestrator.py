"""
分析任务编排器 — 调度中心

职责：
  1. 接收用户输入（category + constraints）
  2. 调用 DataSourceAdapter 获取数据
  3. 从商品数据中自动聚类细分方向（sub_category）
  4. 对每个细分方向并行执行四大分析 + 综合评分
  5. 实时更新任务进度（0→20→30→...→100）
  6. 结果写入数据库（SubCategoryAnalysis + Report）

并发策略：
  - 细分方向间：asyncio.gather 并行
  - 单方向内四个模块：asyncio.gather 并行
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Callable, Optional
from collections import Counter
from datetime import datetime, timezone

from backend.data_sources.adapter import DataSourceAdapter
from backend.analyzers.brand_vacuum import analyze_brand_vacuum
from backend.analyzers.growth_signal import analyze_growth_signal
from backend.analyzers.pain_point import analyze_pain_points
from backend.analyzers.price_analysis import analyze_price
from backend.analyzers.scoring import compute_overall_score

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """
    分析任务编排器
    把所有模块串起来的调度中心
    """

    def __init__(self, adapter: Optional[DataSourceAdapter] = None):
        self.adapter = adapter or DataSourceAdapter()

    async def run(
        self,
        category: str,
        constraints: Optional[Dict[str, Any]] = None,
        on_progress: Optional[Callable[[int, str], None]] = None,
        on_sse_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        sse_task_id: str = "",
    ) -> Dict[str, Any]:
        """
        执行完整分析流程

        Args:
            category: 品类关键词（如 "宠物"）
            constraints: 用户约束条件
            on_progress: 进度回调 (progress_pct, message) -> None
            on_sse_event: SSE 事件回调 (event_type, data_dict) -> None

        Returns:
            完整的分析结果字典，含所有细分方向的排序结果
        """
        constraints = constraints or {}

        def update_progress(pct: int, msg: str):
            logger.info(f"[Progress {pct}%] {msg}")
            if on_progress:
                on_progress(pct, msg)

        def push_sse(event: str, data: dict):
            """同时推送 SSE 事件和日志"""
            if on_sse_event:
                try:
                    on_sse_event(event, data)
                except Exception:
                    pass

        # ---- Step 1: 获取数据 ----
        push_sse("task_start", {
            "task_id": "",  # 由调用方注入
            "category": category,
            "message": f"开始分析「{category}」市场...",
            "progress": 5,
        })

        data_source = self.adapter.current_source
        push_sse("data_fetching", {
            "progress": 10,
            "source": data_source,
            "message": f"正在从{data_source}获取市场数据...",
        })
        result = self.adapter.fetch_with_reviews(category, constraints, count=150)
        products = result["products"]
        reviews_by_product = result.get("reviews", [])

        if not products:
            push_sse("error", {
                "progress": 100,
                "message": "无可用数据",
            })
            return {"category": category, "error": "无可用数据", "results": []}

        update_progress(20, f"数据获取完成，共 {len(products)} 条商品")

        # ---- Step 2: 细分方向聚类 ----
        sub_categories = self._cluster_sub_categories(products)
        update_progress(30, f"识别到 {len(sub_categories)} 个细分方向")

        push_sse("data_ready", {
            "progress": 30,
            "product_count": len(products),
            "sub_categories": sub_categories,
            "message": f"已获取 {len(products)} 条商品数据，识别出 {len(sub_categories)} 个细分方向",
        })

        if not sub_categories:
            sub_categories = [category]  # fallback: 用大类本身

        # ---- Step 3: 为每个细分方向准备数据和评论 ----
        sub_products_map = {}
        sub_reviews_map = {}
        for sc in sub_categories:
            sc_products = [p for p in products if p.get("sub_category") == sc]
            sub_products_map[sc] = sc_products
            # 为这个细分方向重新生成评论（确保数据对应）
            sc_reviews = self.adapter.mock.generate_reviews(
                sc_products, keyword=category
            )
            sub_reviews_map[sc] = sc_reviews

        # ---- Step 4: 并行分析所有细分方向 ----
        total_dirs = len(sub_categories)
        completed = 0
        results_lock = asyncio.Lock()
        all_results = []

        async def analyze_one_direction(sc_name: str):
            nonlocal completed
            sc_products = sub_products_map[sc_name]
            sc_reviews = sub_reviews_map[sc_name]

            if len(sc_products) < 3:
                logger.warning(f"[{sc_name}] 商品数据不足 ({len(sc_products)} 条)，跳过")
                async with results_lock:
                    completed += 1
                return None

            # 四模块并行分析
            brand_task = asyncio.to_thread(analyze_brand_vacuum, sc_products)
            growth_task = asyncio.to_thread(analyze_growth_signal, sc_products, sc_reviews)
            pain_task = asyncio.to_thread(analyze_pain_points, sc_reviews, sc_products)
            price_task = asyncio.to_thread(analyze_price, sc_products, constraints)

            brand_result, growth_result, pain_result, price_result = await asyncio.gather(
                brand_task, growth_task, pain_task, price_task,
            )

            # 综合评分
            overall = compute_overall_score(
                brand_vacuum_result=brand_result,
                growth_signal_result=growth_result,
                pain_point_result=pain_result,
                price_profit_result=price_result,
                constraints=constraints,
                sub_category=sc_name,
            )

            async with results_lock:
                completed += 1
                progress = 30 + int(completed / total_dirs * 60)
                update_progress(progress, f"完成 {sc_name} 分析 ({completed}/{total_dirs})")

                # SSE: 细分方向分析完成（含完整数据）
                push_sse("subcategory_done", {
                    "progress": progress,
                    "sub_category": sc_name,
                    "score": overall["total_score"],
                    "recommendation": overall["recommendation"],
                    "key_insight": overall["key_insight"],
                    "entry_suggestion": overall.get("entry_suggestion", ""),
                    "score_breakdown": overall.get("score_breakdown", {}),
                    "white_brand_ratio": brand_result.get("white_brand_ratio", 0),
                    "growth_rate": growth_result.get("growth_rate", 0),
                    "avg_price": price_result.get("avg_price", 0),
                    "suggested_price_entry": price_result.get("suggested_price_entry", 0),
                    "suggested_price_premium": price_result.get("suggested_price_premium", 0),
                    "price_distribution": price_result.get("price_distribution", []),
                    "top_pain_points": pain_result.get("top_pain_points", []),
                    "message": f"「{sc_name}」分析完成，综合评分 {overall['total_score']}",
                })

            return {
                "sub_category": sc_name,
                "product_count": len(sc_products),
                "brand_vacuum": brand_result,
                "growth_signal": growth_result,
                "pain_point": pain_result,
                "price_profit": price_result,
                "overall": overall,
            }

        # 并行启动所有细分方向的分析
        analysis_tasks = [analyze_one_direction(sc) for sc in sub_categories]
        raw_results = await asyncio.gather(*analysis_tasks)

        all_results = [r for r in raw_results if r is not None]

        # ---- Step 5: 按综合得分降序排列 ----
        all_results.sort(key=lambda x: -x["overall"]["total_score"])

        update_progress(95, "正在生成最终报告...")

        # SSE: 全部分析完成
        top_direction = all_results[0] if all_results else None
        push_sse("analysis_done", {
            "progress": 100,
            "top_recommendation": {
                "sub_category": top_direction["sub_category"] if top_direction else "",
                "score": top_direction["overall"]["total_score"] if top_direction else 0,
                "entry_suggestion": top_direction["overall"]["entry_suggestion"] if top_direction else "",
            } if top_direction else {},
            "message": f"分析完成，推荐切入方向：{top_direction['sub_category'] if top_direction else '无'}",
        })

        update_progress(100, "分析完成")

        # ---- Step 6: 生成简单的汇总报告 ----
        top_direction = all_results[0] if all_results else None
        report = {
            "category": category,
            "constraints": constraints,
            "data_source": self.adapter.current_source,
            "total_products_analyzed": len(products),
            "sub_categories_found": len(sub_categories),
            "top_pick": (
                {
                    "sub_category": top_direction["sub_category"],
                    "total_score": top_direction["overall"]["total_score"],
                    "recommendation": top_direction["overall"]["recommendation"],
                    "key_insight": top_direction["overall"]["key_insight"],
                }
                if top_direction else None
            ),
            "rankings": [
                {
                    "rank": i + 1,
                    "sub_category": r["sub_category"],
                    "total_score": r["overall"]["total_score"],
                    "recommendation": r["overall"]["recommendation"],
                }
                for i, r in enumerate(all_results)
            ],
        }

        update_progress(100, "分析完成")

        # ---- Step 6: AI 报告生成 ----
        task_data = {
            "category": category,
            "report": report,
            "detailed_results": all_results,
        }

        push_sse("ai_report_start", {
            "progress": 100,
            "message": "AI 正在深度解读数据...",
        })

        ai_report = None
        try:
            from backend.ai.report_generator import ReportGenerator
            gen = ReportGenerator()

            if gen.llm.is_available():
                # LLM 可用 → 流式输出
                analysis_summary = _build_analysis_summary(category, report, all_results)

                from backend.ai.report_generator import FULL_REPORT_PROMPT
                prompt = FULL_REPORT_PROMPT.format(
                    category=category,
                    analysis_data=json.dumps(analysis_summary, ensure_ascii=False, indent=2),
                )

                messages = [
                    {"role": "system", "content": "你是一个专业的电商选品策略顾问，基于数据生成决策报告。只输出报告正文，不要添加额外说明。"},
                    {"role": "user", "content": prompt},
                ]

                full_report = ""
                batch = ""
                async for chunk in gen.llm.chat_stream(messages):
                    if chunk:
                        full_report += chunk
                        batch += chunk
                        # 每 50 个字符发一次，减少队列压力
                        if len(batch) >= 50:
                            push_sse("ai_report_chunk", {"chunk": batch})
                            batch = ""
                # 推送剩余内容
                if batch:
                    push_sse("ai_report_chunk", {"chunk": batch})

                if full_report.strip():
                    ai_report = full_report
                    push_sse("ai_report_done", {
                        "message": "报告生成完成",
                        "provider": "DeepSeek",
                    })
            else:
                # LLM 不可用 → Fallback
                ai_report = gen._fallback_report(task_data, {})
                if on_sse_event:
                    push_sse("ai_report_fallback", {
                        "message": "已生成结构化报告",
                        "report": ai_report,
                    })
        except Exception as e:
            logger.warning(f"AI 报告生成失败: {e}")
            # 最终 fallback
            try:
                from backend.ai.report_generator import ReportGenerator
                gen = ReportGenerator()
                ai_report = gen._fallback_report(task_data, {})
            except Exception:
                ai_report = ""
            push_sse("ai_report_fallback", {
                "message": "已生成结构化报告",
                "report": ai_report,
            })

        # ---- Step 7: 写入 Report 表 ----
        try:
            await self._save_report(task_data, ai_report or "", sse_task_id)
        except Exception as e:
            logger.warning(f"Report 写库失败: {e}")

        return {
            "category": category,
            "report": report,
            "detailed_results": all_results,
            "ai_report": ai_report,
        }

    async def _save_report(self, task_data: dict, ai_report: str, sse_task_id: str):
        """将报告持久化到 Report 表"""
        from backend.database.session import async_session
        from backend.database.models import Report, AnalysisTask

        report_data = task_data.get("report", {})
        top_pick = report_data.get("top_pick", {})

        # 获取定价信息
        detailed = task_data.get("detailed_results", [])
        pricing = ""
        if detailed and detailed[0].get("price_profit"):
            p = detailed[0]["price_profit"]
            entry = p.get("suggested_price_entry", 0)
            premium = p.get("suggested_price_premium", 0)
            pricing = f"建议入场定价 ¥{entry}，品质升级定价 ¥{premium}"

        content = {
            "category": task_data.get("category", ""),
            "data_source": report_data.get("data_source", "mock"),
            "ai_report": ai_report,
            "rankings": report_data.get("rankings", []),
            "detailed_results": [
                {
                    "sub_category": r["sub_category"],
                    "total_score": r["overall"]["total_score"],
                    "recommendation": r["overall"]["recommendation"],
                    "key_insight": r["overall"]["key_insight"],
                }
                for r in detailed
            ],
        }

        async with async_session() as session:
            # 创建新的分析任务记录（使用 SSE 的 task_id UUID）
            task = AnalysisTask(
                task_id=sse_task_id,
                category=task_data.get("category", ""),
                status="done",
                progress=100,
            )
            session.add(task)
            await session.flush()  # 获取 task.id
            
            report = Report(
                task_id=task.id,
                content=content,
                top_direction=top_pick.get("sub_category", ""),
                pricing_suggestion=pricing,
                entry_strategy=top_pick.get("key_insight", ""),
            )
            session.add(report)
            await session.commit()
            logger.info(f"[Orchestrator] Report 写入成功: {top_pick.get('sub_category', '')} (task.id={task.id})")

    def _cluster_sub_categories(self, products: List[Dict]) -> List[str]:
        """
        从商品数据中自动聚类细分方向
        统计 sub_category 出现频次，过滤低频方向
        """
        counter = Counter()
        for p in products:
            sc = p.get("sub_category", "")
            if sc:
                counter[sc] += 1

        total = sum(counter.values())
        # 保留出现频率 > 3% 的细分方向
        return [sc for sc, cnt in counter.most_common()
                if cnt / total > 0.03]


# ===================== 辅助函数 =====================

def _build_analysis_summary(category: str, report: dict, detailed_results: list) -> dict:
    """构建 LLM prompt 用的分析数据摘要"""
    summary = {
        "品类": category,
        "数据来源": report.get("data_source", "mock"),
        "分析商品数": report.get("total_products_analyzed", 0),
        "识别细分方向数": report.get("sub_categories_found", 0),
    }
    if report.get("top_pick"):
        summary["首选推荐"] = {
            "方向": report["top_pick"]["sub_category"],
            "得分": report["top_pick"]["total_score"],
            "洞察": report["top_pick"]["key_insight"],
        }
    sub_details = []
    for r in detailed_results:
        overall = r.get("overall", {})
        brand = r.get("brand_vacuum", {})
        growth = r.get("growth_signal", {})
        pain = r.get("pain_point", {})
        price = r.get("price_profit", {})
        sub_details.append({
            "细分方向": r.get("sub_category", ""),
            "综合评分": overall.get("total_score", 0),
            "推荐等级": overall.get("recommendation", ""),
            "品牌真空度得分": brand.get("score", 0),
            "白牌占比": brand.get("white_brand_ratio", 0),
            "增长率": growth.get("growth_rate", 0),
            "自然增长": growth.get("is_natural_growth", False),
            "差评率": pain.get("negative_ratio", 0),
            "TOP痛点": [p["keyword"] for p in pain.get("top_pain_points", [])[:5]],
            "均价": price.get("avg_price", 0),
            "建议入场价": price.get("suggested_price_entry", 0),
            "核心洞察": overall.get("key_insight", ""),
        })
    summary["细分方向明细"] = sub_details
    return summary


# ===================== 便捷函数（用于直接调用） =====================
async def run_analysis(
    category: str,
    constraints: Optional[Dict] = None,
) -> Dict[str, Any]:
    """一键运行完整分析流程"""
    orch = AnalysisOrchestrator()
    return await orch.run(category, constraints)
