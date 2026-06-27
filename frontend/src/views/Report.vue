<!--
  Report.vue — 决策报告页（7个区块）
  从 /api/v1/analysis/{taskId}/result 获取完整数据
-->
<template>
  <div v-if="loading" class="flex items-center justify-center h-64">
    <span class="text-sm text-[var(--text-muted)]">加载报告中...</span>
  </div>

  <div v-else-if="!report" class="flex flex-col items-center justify-center h-64 gap-3">
    <span class="text-2xl">📋</span>
    <span class="text-sm text-[var(--text-muted)]">报告数据不可用</span>
    <RouterLink to="/" class="text-[var(--accent-light)] text-sm">返回首页</RouterLink>
  </div>

  <template v-else>
    <div class="max-w-6xl mx-auto px-4 pt-4 pb-8 space-y-10">
      <!-- 返回导航 -->
      <div class="flex items-center gap-4 text-sm">
        <RouterLink to="/" class="text-[var(--text-muted)] hover:text-white transition-colors">
          ← 返回首页
        </RouterLink>
        <RouterLink :to="`/analyzing/${report.task_id || store.currentTaskId}`" class="text-[var(--text-muted)] hover:text-white transition-colors">
          ← 返回分析
        </RouterLink>
      </div>

      <!-- === 区块一：报告头部 === -->
      <section>
        <div class="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 class="text-2xl font-bold">
              选品决策报告：
              <span class="gradient-text">{{ report.category || '-' }}</span>
            </h1>
            <p class="text-xs text-[var(--text-muted)] mt-1">
              {{ formatDate(report.created_at) }}
            </p>
          </div>
          <div class="flex items-center gap-3">
            <DataSourceBadge />
          </div>
        </div>

        <!-- 约束标签 -->
        <div v-if="constraintTags.length > 0" class="flex flex-wrap gap-1.5 mt-3">
          <span v-for="tag in constraintTags" :key="tag"
            class="px-2 py-0.5 rounded-full text-xs bg-[var(--bg-card)] border border-[var(--border-subtle)] text-[var(--text-secondary)]">
            {{ tag }}
          </span>
        </div>
      </section>

      <!-- === 区块二：核心推荐 === -->
      <section v-if="report.top_recommendation" class="rounded-2xl p-6 bg-gradient-to-br from-[var(--accent)]/10 to-[var(--accent-light)]/5 border border-[var(--accent)]/20">
        <p class="text-xs text-[var(--text-muted)] mb-2">推荐切入方向</p>
        <h2 class="text-3xl font-bold gradient-text">{{ report.top_recommendation.sub_category }}</h2>
        <p class="mt-1 text-sm text-[var(--text-secondary)]">综合评分：{{ report.top_recommendation.score }} 分</p>
        <p v-if="report.top_recommendation.reason" class="mt-3 text-sm text-[var(--text-primary)] leading-relaxed">
          {{ report.top_recommendation.reason }}
        </p>

        <!-- 定价建议（从第一个subcategory获取） -->
        <div v-if="firstSubCategory" class="mt-4 flex gap-4 text-xs">
          <span class="px-3 py-1.5 rounded-lg bg-[var(--accent)]/10 text-[var(--accent-light)]">
            低价切入：¥{{ firstSubCategory.suggested_price_entry }}
          </span>
          <span class="px-3 py-1.5 rounded-lg bg-[var(--green)]/10 text-[var(--green)]">
            品质溢价：¥{{ firstSubCategory.suggested_price_premium ?? '—' }}
          </span>
        </div>
      </section>

      <!-- === AI 市场洞察（LLM 生成或 Fallback 模板）=== -->
      <section v-if="store.aiReport || store.aiReportStatus === 'generating'" class="mb-8">
        <div
          class="rounded-xl bg-[var(--bg-card)] border overflow-hidden"
          :class="store.aiReportStatus === 'done'
            ? 'border-[var(--accent)]/20 border-l-2 border-l-[var(--accent)]'
            : 'border-[var(--border-subtle)] border-l-2 border-l-[var(--text-muted)]'"
        >
          <div class="px-4 py-3 border-b border-[var(--border-subtle)] flex items-center justify-between">
            <h2 class="text-sm font-medium text-[var(--text-secondary)]">
              AI 市场洞察
            </h2>
            <span
              class="text-xs px-2 py-0.5 rounded-full"
              :class="store.aiReportStatus === 'done'
                ? 'bg-[var(--accent)]/10 text-[var(--accent-light)]'
                : 'bg-[var(--text-muted)]/10 text-[var(--text-muted)]'"
            >
              {{ store.aiReportStatus === 'done' && store.llmProvider === 'DeepSeek'
                ? `由 ${store.llmProvider} 提供支持`
                : store.aiReportStatus === 'fallback' ? '结构化模板报告' : '生成中...' }}
            </span>
          </div>
          <div class="p-4 text-sm leading-relaxed text-[var(--text-secondary)] ai-report-content" v-html="renderedReport"></div>
        </div>
      </section>

      <!-- === 区块三：细分方向全览 + 图表 === -->
      <section>
        <h2 class="text-lg font-semibold mb-4">细分方向全览</h2>

        <!-- 雷达图 -->
        <div class="rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] p-4 mb-6">
          <h3 class="text-sm font-medium text-[var(--text-secondary)] mb-3">TOP3 细分方向四维对比</h3>
          <div ref="radarRef" class="w-full h-80"></div>
        </div>

        <!-- 品牌真空 + 增长信号 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          <div class="rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] p-4">
            <h3 class="text-sm font-medium text-[var(--text-secondary)] mb-3">品牌真空度对比</h3>
            <BrandVacuumChart :data="brandVacuumData" />
          </div>
          <div class="rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] p-4">
            <h3 class="text-sm font-medium text-[var(--text-secondary)] mb-3">增长趋势对比</h3>
            <GrowthChart :data="growthData" />
          </div>
        </div>
      </section>

      <!-- === 区块四：价格市场地图 === -->
      <section v-if="firstSubCategory">
        <h2 class="text-lg font-semibold mb-4">价格市场地图</h2>
        <div class="rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] p-4">
          <h3 class="text-sm font-medium text-[var(--text-secondary)] mb-3">
            均价 ¥{{ firstSubCategory.avg_price }}
            · 建义入场 ¥{{ firstSubCategory.suggested_price_entry }}
          </h3>
          <PriceRangeChart
            :distribution="priceDistribution"
            :suggestedEntry="firstSubCategory.suggested_price_entry"
          />
        </div>
      </section>

      <!-- === 区块五：用户痛点词云 === -->
      <section>
        <h2 class="text-lg font-semibold mb-4">用户痛点关键词</h2>
        <div class="rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] p-4">
          <PainPointCloud :painPoints="allPainPoints" />
        </div>
      </section>

      <!-- === 区块六：所有细分方向评分卡 === -->
      <section>
        <h2 class="text-lg font-semibold mb-4">所有细分方向评分（{{ sortedResults.length }}）</h2>
        <div class="space-y-3">
          <ScoreCard
            v-for="r in sortedResults"
            :key="r.name"
            :result="r"
          />
        </div>
      </section>

      <!-- === 区块七：报告底部 === -->
      <section class="border-t border-[var(--border-subtle)] pt-8 space-y-4 text-xs text-[var(--text-muted)] leading-relaxed">
        <div>
          <strong class="text-[var(--text-secondary)]">评分方法论：</strong>
          综合评分 = 品牌真空度(35%) + 增长信号(30%) + 痛点密度(20%) + 价格利润(15%)。
          品牌真空度衡量市场是否存在品牌垄断；增长信号识别自然增长 vs 广告驱动的虚假繁荣；
          痛点密度分析现有产品的用户不满集中度；价格利润评估机会价格带和利润空间。
        </div>
        <div>
          <strong class="text-[var(--text-secondary)]">数据来源说明：</strong>
          演示环境数据基于真实市场规律构建的结构化模拟数据（品牌分布、销量分布、价格分布均参考电商行业公开统计指标）。
          真实数据集和京东实时搜索模块可供切换使用。
        </div>
        <div class="border-t border-[var(--border-subtle)] pt-4 text-center">
          Brand Miner v1.0 · 智能选品比价引擎
        </div>
      </section>

    </div>
  </template>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { useAnalysisStore } from '../stores/analysis'
import DataSourceBadge from '../components/DataSourceBadge.vue'
import ScoreCard from '../components/ScoreCard.vue'
import BrandVacuumChart from '../components/BrandVacuumChart.vue'
import GrowthChart from '../components/GrowthChart.vue'
import PriceRangeChart from '../components/PriceRangeChart.vue'
import PainPointCloud from '../components/PainPointCloud.vue'

const route = useRoute()
const store = useAnalysisStore()
const loading = ref(true)
const report = ref(null)
const radarRef = ref(null)

onMounted(async () => {
  const taskId = route.params.taskId || store.currentTaskId
  if (!taskId) return

  try {
    const data = await store.fetchResult(taskId)
    report.value = data
  } catch (e) {
    console.error('加载报告失败:', e)
  } finally {
    loading.value = false
  }
})

// ---- Computed data for charts ----

const sortedResults = computed(() => {
  if (!report.value?.sub_categories) return []
  return [...report.value.sub_categories].sort((a, b) => b.total_score - a.total_score)
})

const firstSubCategory = computed(() => sortedResults.value[0] || null)

const brandVacuumData = computed(() => {
  return sortedResults.value.map(r => ({
    name: r.name,
    score: r.score_breakdown?.brand_vacuum?.score ?? 0,
  }))
})

const growthData = computed(() => {
  return sortedResults.value.map(r => ({
    name: r.name,
    growth_rate: r.growth_rate ?? 0,
    score: r.score_breakdown?.growth_signal?.score ?? 0,
  }))
})

const priceDistribution = computed(() => {
  // Use the first subcategory's full data; Report API returns summary only
  return report.value?.price_distribution || []
})

const allPainPoints = computed(() => {
  return sortedResults.value
    .flatMap(r => r.top_pain_points || [])
    .reduce((acc, p) => {
      const existing = acc.find(x => x.keyword === p.keyword)
      if (existing) { existing.count += p.count; return acc }
      acc.push({ ...p })
      return acc
    }, [])
    .sort((a, b) => b.count - a.count)
})

const constraintTags = computed(() => {
  const c = report.value?.constraints
  if (!c) return []
  const tags = []
  if (c.price_min != null) tags.push(`最低 ¥${c.price_min}`)
  if (c.price_max != null) tags.push(`最高 ¥${c.price_max}`)
  if (c.target_audience) tags.push(c.target_audience)
  if (c.brand_strategy) {
    const m = { white_label: '白牌切入', light_brand: '轻品牌', quality_up: '品质升级' }
    tags.push(m[c.brand_strategy] || c.brand_strategy)
  }
  if (c.priority) tags.push(c.priority)
  return tags
})

// ---- AI 报告渲染 ----
const renderedReport = computed(() => {
  const text = store.aiReport || '等待报告生成...'
  // 简易 Markdown → HTML
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/^## (.+)$/gm, '<h3 class="text-base font-semibold text-[var(--text-primary)] mt-4 mb-2">$1</h3>')
    .replace(/^### (.+)$/gm, '<h4 class="text-sm font-semibold text-[var(--text-primary)] mt-3 mb-1">$1</h4>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-[var(--text-primary)]">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li class="ml-4 text-[var(--text-secondary)]">• $1</li>')
    .replace(/(\d+)\. (.+)/g, '<li class="ml-4 text-[var(--text-secondary)]">$1. $2</li>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>')
})

const formatDate = (d) => {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN')
}

// ---- Radar Chart ----
let radarChart = null

watch(sortedResults, () => {
  nextTick(() => renderRadar())
}, { deep: true })

onMounted(() => {
  nextTick(() => renderRadar())
})

const radarDimensions = [
  { name: '品牌真空', key: 'brand_vacuum' },
  { name: '增长信号', key: 'growth_signal' },
  { name: '痛点密度', key: 'pain_point' },
  { name: '利润空间', key: 'price_profit' },
]

const renderRadar = () => {
  if (!radarRef.value) return
  if (!radarChart) {
    radarChart = echarts.init(radarRef.value, null, { renderer: 'canvas' })
  }

  const top3 = sortedResults.value.slice(0, 3)
  const colors = ['#6366f1', '#10b981', '#f59e0b']

  radarChart.setOption({
    backgroundColor: 'transparent',
    legend: { data: top3.map(r => r.name), bottom: 0, textStyle: { color: '#8b8fa8', fontSize: 11 } },
    radar: {
      center: ['50%', '45%'],
      radius: '65%',
      indicator: radarDimensions.map(d => ({ name: d.name, max: 100 })),
      axisName: { color: '#8b8fa8', fontSize: 11 },
      splitArea: { areaStyle: { color: ['rgba(99,102,241,0.02)', 'rgba(99,102,241,0.04)'] } },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
    },
    series: [{
      type: 'radar',
      data: top3.map((r, i) => ({
        name: r.name,
        value: radarDimensions.map(d => r.score_breakdown?.[d.key]?.score ?? 0),
        lineStyle: { color: colors[i] },
        areaStyle: { color: colors[i], opacity: 0.1 },
        itemStyle: { color: colors[i] },
      })),
    }],
  })
}
</script>
