<!--
  DataSourceBadge.vue — 数据来源标注（所有页面可见）
  Props: (none) — 从 store 自动获取状态
-->
<template>
  <div class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full
              bg-[var(--bg-card)] border border-[var(--border-subtle)] text-xs">
    <span class="w-2 h-2 rounded-full" :class="dotClass"></span>
    <span :class="textClass">{{ label }}</span>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAnalysisStore } from '../stores/analysis'

const store = useAnalysisStore()

onMounted(() => {
  if (!store.dataSourceStatus) {
    store.fetchDataSourceStatus()
  }
})

const currentSource = computed(() => store.dataSourceStatus?.current_source || 'mock')

const config = computed(() => ({
  tianchi: { label: '天池数据', dot: 'bg-green-500', text: 'text-green-400' },
  jd: { label: '京东实时', dot: 'bg-yellow-500', text: 'text-yellow-400' },
  mock: { label: '模拟数据', dot: 'bg-blue-500', text: 'text-blue-400' },
}))

const label = computed(() => config.value[currentSource.value]?.label || '模拟数据')
const dotClass = computed(() => config.value[currentSource.value]?.dot || 'bg-blue-500')
const textClass = computed(() => config.value[currentSource.value]?.text || 'text-blue-400')
</script>
