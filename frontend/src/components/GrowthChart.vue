<!--
  GrowthChart.vue — 增长信号柱状图
  Props: data: Array of { name, growth_rate, score } — 各细分方向增长数据
-->
<template>
  <div ref="chartRef" class="w-full h-64"></div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let chart = null

const render = () => {
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value, null, { renderer: 'canvas' })

  const sorted = [...props.data].sort((a, b) => b.growth_rate - a.growth_rate)

  chart.setOption({
    backgroundColor: 'transparent',
    grid: { left: 10, right: 40, top: 10, bottom: 30 },
    xAxis: { type: 'category', data: sorted.map(d => d.name), axisLabel: { color: '#8b8fa8', fontSize: 10, rotate: 30 }, axisLine: { show: false } },
    yAxis: { axisLabel: { color: '#515470', fontSize: 11, formatter: v => (v * 100).toFixed(0) + '%' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } } },
    series: [{
      type: 'bar', data: sorted.map(d => ({ value: d.growth_rate, itemStyle: { color: d.growth_rate > 0.15 ? '#10b981' : d.growth_rate > 0 ? '#f59e0b' : '#ef4444' } })),
      barWidth: 16,
    }],
  })
}

onMounted(render)
watch(() => props.data, render, { deep: true })
</script>
