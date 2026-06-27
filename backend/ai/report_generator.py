"""
AI 报告生成器 — 将量化评分数据转化为可读的决策报告

调用链：
  AnalysisOrchestrator → 评分数据
  ReportGenerator.generate_full_report() → DeepSeek LLM → Markdown 格式报告
  LLM 不可用 → Fallback 结构化模板（演示永不中断）
"""
import json
import logging
from typing import Optional

from backend.ai.llm_client import llm_client

logger = logging.getLogger(__name__)

# ── Full Report Prompt ──
# 设计意图：
#   角色限定为电商选品顾问 → 确保输出语言专业、面向商业决策者
#   强制基于数据分析 → 禁止编造数据，提示词中注入完整分析 JSON
#   7 区块结构 → 控制输出长度和质量，防止 AI 发散

FULL_REPORT_PROMPT = """你是一位专注于电商非品牌市场的选品策略顾问。
你的客户是准备进入{category}市场的非品牌商家。

以下是基于真实市场数据的量化分析结果：
{analysis_data}

请基于以上数据（不要编造任何数据），生成一份选品决策报告，严格按照以下结构输出：

## 市场概况
（2-3句话描述该大类市场整体格局）

## 核心推荐方向
（推荐切入的细分方向及理由，200字以内）

## 竞争机会分析
（品牌真空度数据的商业解读，100字以内）

## 用户需求洞察
（痛点数据背后的用户需求解读，100字以内）

## 定价策略建议
（结合价格分析数据给出具体定价建议）

## 风险提示
（1-2条客观风险，不要过度乐观）

## 行动建议
（3条可立即执行的具体建议）

要求：语言简洁专业，面向商业决策者，中文输出。"""


class ReportGenerator:
    """AI 报告生成器 — LLM 不可用时自动降级到 Fallback 模板"""

    def __init__(self):
        self.llm = llm_client

    async def generate_full_report(self, task_data: dict) -> str:
        """
        使用 LLM 生成完整选品决策报告

        Args:
            task_data: 包含 category、report、detailed_results 的完整任务数据

        Returns:
            Markdown 格式的决策报告；LLM 不可用时返回 Fallback 模板报告
        """
        category = task_data.get("category", "未指定")
        report = task_data.get("report", {})
        detailed_results = task_data.get("detailed_results", [])

        # ── 构建分析数据摘要（注入 prompt）──
        analysis_summary = {
            "品类": category,
            "数据来源": report.get("data_source", "mock"),
            "分析商品数": report.get("total_products_analyzed", 0),
            "识别细分方向数": report.get("sub_categories_found", 0),
        }

        if report.get("top_pick"):
            analysis_summary["首选推荐"] = {
                "方向": report["top_pick"]["sub_category"],
                "得分": report["top_pick"]["total_score"],
                "洞察": report["top_pick"]["key_insight"],
            }

        # 细分方向明细
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
                "白牌占比": f"{brand.get('white_brand_ratio', 0):.0%}",
                "增长率": f"{growth.get('growth_rate', 0):.0%}",
                "自然增长": growth.get("is_natural_growth", False),
                "差评率": f"{pain.get('negative_ratio', 0):.0%}",
                "TOP痛点": [p["keyword"] for p in pain.get("top_pain_points", [])[:5]],
                "均价": price.get("avg_price", 0),
                "建议入场价": price.get("suggested_price_entry", 0),
                "建议溢价": price.get("suggested_price_premium", 0),
                "核心洞察": overall.get("key_insight", ""),
            })

        analysis_summary["细分方向明细"] = sub_details

        # ── 调用 LLM ──
        prompt = FULL_REPORT_PROMPT.format(
            category=category,
            analysis_data=json.dumps(analysis_summary, ensure_ascii=False, indent=2),
        )

        logger.info(f"[ReportGen] 请求 LLM 生成报告 — {category}（{len(sub_details)} 个细分方向）")
        ai_report = await self.llm.chat([
            {"role": "system", "content": "你是一个专业的电商选品策略顾问，基于数据生成决策报告。只输出报告正文，不要添加额外说明。"},
            {"role": "user", "content": prompt},
        ])

        if ai_report:
            logger.info(f"[ReportGen] ✓ AI 报告生成成功 ({len(ai_report)} 字)")
            return ai_report

        # ── LLM 不可用 → Fallback ──
        logger.warning("[ReportGen] LLM 不可用，使用 Fallback 模板")
        return self._fallback_report(task_data, analysis_summary)

    # ── Fallback 模板报告 ──
    # 设计意图：
    #   当 LLM 不可用时，用预定义模板 + 实际数据填充
    #   保证演示永不中断，且输出仍包含核心数据洞察

    def _fallback_report(self, task_data: dict, summary: dict) -> str:
        """Fallback 结构化的模板报告 — LLM 不可用时的降级输出"""
        category = summary.get("品类", "")
        top = task_data.get("report", {}).get("top_pick", {})
        rankings = task_data.get("report", {}).get("rankings", [])
        details = summary.get("细分方向明细", [])

        # 取 TOP3 和首推
        top1 = details[0] if len(details) > 0 else {}
        top2 = details[1] if len(details) > 1 else {}
        top3 = details[2] if len(details) > 2 else {}

        # 统计推荐和中性方向
        recommended = [d for d in details if d["推荐等级"] == "recommended"]
        neutral = [d for d in details if d["推荐等级"] == "neutral"]

        lines = []
        lines.append(f"# {category}市场选品决策报告\n")

        # 1. 市场概况
        lines.append("## 市场概况")
        lines.append(f"本次分析覆盖了{category}市场的 {summary.get('识别细分方向数', 0)} 个细分方向，"
                     f"基于 {summary.get('分析商品数', 0)} 条商品数据进行量化评估。")
        lines.append(f"从市场结构看，白牌占比普遍较高，品牌集中度较低，为非品牌商家提供了切入机会。\n")

        # 2. 核心推荐方向
        lines.append("## 核心推荐方向")
        if top:
            lines.append(f"综合评分最高的细分方向是 **{top.get('sub_category', '')}**"
                        f"（{top.get('total_score', '—')} 分）。")
            lines.append(f"{top.get('key_insight', '')}\n")
        if recommended:
            lines.append(f"共有 {len(recommended)} 个细分方向获得「强烈推荐」评级："
                        f"{'、'.join(r['细分方向'] for r in recommended)}。\n")

        # 3. 竞争机会分析
        lines.append("## 竞争机会分析")
        if top1:
            lines.append(f"当前 {category} 市场品牌真空度显著，白牌占比 {top1.get('白牌占比', '—')}，"
                        f"品牌真空度评分 {top1.get('品牌真空度得分', '—')}/100，头部品牌尚未形成垄断。")
        lines.append("这意味着新品牌不需要大量广告投入即可获得市场份额，适合以性价比或差异化策略切入。\n")

        # 4. 用户需求洞察
        lines.append("## 用户需求洞察")
        if top1 and top1.get("TOP痛点"):
            pain_kws = "、".join(top1["TOP痛点"][:5])
            lines.append(f"用户反馈中高频出现的痛点关键词包括：**{pain_kws}**。")
            lines.append(f"现有产品在{top1['TOP痛点'][0] if top1['TOP痛点'] else '质量'}方面存在明显短板，"
                        f"这为新品牌提供了差异化的切入点——只需做好这一点即可在用户口碑上拉开差距。\n")

        # 5. 定价策略建议
        lines.append("## 定价策略建议")
        if top1:
            lines.append(f"当前市场均价为 ¥{top1.get('均价', '—')}，建议采取双线定价策略：")
            lines.append(f"- **快速起量线**：定价约 ¥{top1.get('建议入场价', '—')}，"
                        f"低于市场均价 10%，快速获取初始用户和评价")
            lines.append(f"- **品质升级线**：定价约 ¥{top1.get('建议溢价', '—')}，"
                        f"主打更好的用料和设计，建立品牌溢价能力\n")

        # 6. 风险提示
        lines.append("## 风险提示")
        lines.append(f"1. {category}市场竞争可能加剧，随着更多商家进入，利润空间可能被压缩")
        if neutral:
            lines.append(f"2. {neutral[0]['细分方向'] if neutral else '部分方向'}等方向评分中等，"
                       f"需谨慎评估后再投入\n")

        # 7. 行动建议
        lines.append("## 行动建议")
        lines.append(f"1. **优先切入 {top1.get('细分方向', '') if top1 else rankings[0].get('sub_category', '') if rankings else ''}**"
                    f"—— 综合评分最高，品牌真空度和增长信号均表现突出")
        if top2:
            lines.append(f"2. **同步测试 {top2.get('细分方向', '')}**"
                        f"—— 作为第二备选方向，用少量 SKU 验证市场反馈")
        lines.append("3. **关注差评中高频提到的痛点** —— 针对性改进产品，用差异化打开市场")

        # 底部声明
        lines.append("\n---\n*本报告由 Brand Miner 自动生成，数据基于真实市场规律构建的结构化模拟数据。*")

        return "\n".join(lines)
