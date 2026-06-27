<!--
  ScoreCard.vue — 细分方向评分卡片
  Props:
    result: { name, total_score, recommendation, key_insight, ... }
    compact: Boolean (compact mode for report list)
    dimmed: Boolean (dimmed state when another card is loading)
-->
<template>
  <div
    class="relative rounded-xl bg-[var(--bg-card)] border transition-all duration-200 ease-out animate-slide-in-right cursor-pointer
           hover:border-[var(--accent)] hover:-translate-y-1 hover:shadow-[0_0_20px_rgba(99,102,241,0.3)]"
    :class="[
      compact ? 'p-3' : 'p-4',
      recommendation === 'recommended'
        ? 'border-l-2 border-l-[var(--green)] border-[var(--border-subtle)]'
        : 'border-[var(--border-subtle)]',
      dimmed ? 'opacity-50' : ''
    ]"
  >
    <!-- 加载遮罩 -->
    <div v-if="dimmed" class="absolute inset-0 bg-black/40 rounded-xl flex items-center justify-center z-10">
      <div class="spinner"></div>
    </div>

    <div class="flex items-start justify-between gap-3">
      <div class="flex-1 min-w-0">
        <!-- 名称 + 标签 -->
        <div class="flex items-center gap-2 flex-wrap">
          <h4 class="font-semibold truncate" :class="compact ? 'text-sm' : 'text-base'">
            {{ result.name }}
          </h4>
          <span
            class="px-2 py-0.5 rounded-full text-xs font-medium"
            :class="recBadgeClass"
          >
            {{ recLabel }}
          </span>
        </div>

        <!-- 一句话洞察 -->
        <p v-if="result.key_insight" class="mt-1.5 text-xs italic text-[var(--accent-light)] opacity-80 line-clamp-2">
          {{ result.key_insight }}
        </p>
      </div>

      <!-- 评分圆环 -->
      <div class="relative flex-shrink-0" :class="compact ? 'w-12 h-12' : 'w-16 h-16'">
        <svg viewBox="0 0 36 36" class="w-full h-full -rotate-90">
          <circle cx="18" cy="18" r="15.5" fill="none" stroke="var(--bg-primary)" stroke-width="2.5" />
          <circle
            cx="18" cy="18" r="15.5" fill="none"
            :stroke="scoreColor"
            stroke-width="2.5"
            stroke-linecap="round"
            :stroke-dasharray="circumference"
            :stroke-dashoffset="dashOffset"
            class="transition-all duration-1000 ease-out"
          />
        </svg>
        <span class="absolute inset-0 flex items-center justify-center text-sm font-bold" :class="compact ? 'text-xs' : 'text-sm'">
          {{ result.total_score ?? '—' }}
        </span>
      </div>
    </div>

    <!-- 四维小条 (非compact模式) -->
    <div v-if="!compact && result.score_breakdown" class="mt-3 grid grid-cols-4 gap-2">
      <div v-for="bar in miniBars" :key="bar.key" class="flex flex-col gap-0.5">
        <div class="flex justify-between text-[10px]">
          <span class="text-[var(--text-muted)]">{{ bar.label }}</span>
          <span class="text-[var(--text-secondary)]">{{ bar.score }}</span>
        </div>
        <div class="h-1 bg-[var(--bg-primary)] rounded-full">
          <div class="h-full rounded-full transition-all duration-700" :style="{ width: bar.pct + '%', background: bar.color }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: { type: Object, required: true },
  compact: { type: Boolean, default: false },
  dimmed: { type: Boolean, default: false },
})

const circumference = 2 * Math.PI * 15.5

const dashOffset = computed(() => {
  const score = props.result.total_score || 0
  return circumference - (score / 100) * circumference
})

const scoreColor = computed(() => {
  const s = props.result.total_score || 0
  if (s >= 70) return 'var(--green)'
  if (s >= 50) return 'var(--yellow)'
  return 'var(--red)'
})

const recommendation = computed(() => props.result.recommendation)

const recLabel = computed(() => {
  const map = { recommended: '强烈推荐', neutral: '可考虑', not_recommended: '暂不推荐' }
  return map[recommendation.value] || '待分析'
})

const recBadgeClass = computed(() => {
  const map = {
    recommended: 'bg-green-500/10 text-green-400',
    neutral: 'bg-yellow-500/10 text-yellow-400',
    not_recommended: 'bg-red-500/10 text-red-400',
  }
  return map[recommendation.value] || 'bg-[var(--bg-primary)] text-[var(--text-muted)]'
})

const miniBars = computed(() => {
  const bd = props.result.score_breakdown || {}
  return [
    { key: 'brand_vacuum', label: '真空', score: bd.brand_vacuum?.score ?? 0, pct: bd.brand_vacuum?.score ?? 0, color: '#8b5cf6' },
    { key: 'growth_signal', label: '增长', score: bd.growth_signal?.score ?? 0, pct: bd.growth_signal?.score ?? 0, color: '#10b981' },
    { key: 'pain_point', label: '痛点', score: bd.pain_point?.score ?? 0, pct: bd.pain_point?.score ?? 0, color: '#ef4444' },
    { key: 'price_profit', label: '利润', score: bd.price_profit?.score ?? 0, pct: bd.price_profit?.score ?? 0, color: '#3b82f6' },
  ]
})
</script>
