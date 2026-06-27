<!--
  PainPointCloud.vue — 痛点关键词云（CSS 模拟）
  Props: painPoints: Array of { keyword, count, category }
-->
<template>
  <div class="flex flex-wrap justify-center items-center gap-2 p-4 min-h-[180px]">
    <span
      v-for="point in sizedPoints"
      :key="point.keyword"
      class="inline-block px-2 py-0.5 rounded-full transition-all hover:scale-110"
      :style="{
        fontSize: point.size + 'px',
        color: point.color,
        backgroundColor: point.bgColor,
        fontWeight: point.size > 16 ? '600' : '400',
      }"
      :title="`${point.category} · 出现${point.count}次`"
    >
      {{ point.keyword }}
    </span>

    <div v-if="sizedPoints.length === 0" class="text-sm text-[var(--text-muted)]">
      暂无痛点数据
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  painPoints: { type: Array, default: () => [] },
})

const categoryColors = {
  '质量问题': { color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
  '体验问题': { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
  '描述不符': { color: '#8b5cf6', bg: 'rgba(139,92,246,0.1)' },
  '售后问题': { color: '#ec4899', bg: 'rgba(236,72,153,0.1)' },
  '物流包装': { color: '#06b6d4', bg: 'rgba(6,182,212,0.1)' },
  '其他': { color: '#6b7280', bg: 'rgba(107,114,128,0.1)' },
}

const sizedPoints = computed(() => {
  if (!props.painPoints || props.painPoints.length === 0) return []

  const maxCount = Math.max(...props.painPoints.map(p => p.count), 1)
  const minSize = 13
  const maxSize = 26

  return props.painPoints
    .filter(p => p.count > 0)
    .slice(0, 20)
    .map(p => {
      const ratio = p.count / maxCount
      const size = Math.round(minSize + ratio * (maxSize - minSize))
      const catColors = categoryColors[p.category] || categoryColors['其他']
      return { ...p, size, color: catColors.color, bgColor: catColors.bg }
    })
})
</script>
