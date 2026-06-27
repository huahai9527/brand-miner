<!--
  BrandVacuumChart.vue — 品牌真空度横向柱状图
  Props: data: Array of { name, score } — 各细分方向品牌真空度得分
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
  if (!chart) {
    chart = echarts.init(chartRef.value, null, { renderer: 'canvas' })
  }

  const sorted = [...props.data].sort((a, b) => b.score - a.score)

  chart.setOption({
    backgroundColor: 'transparent',
    grid: { left: 120, right: 40, top: 10, bottom: 10 },
    xAxis: { max: 100, axisLine: { show: false }, axisTick: { show: false }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, axisLabel: { color: '#515470', fontSize: 11 } },
    yAxis: { type: 'category', data: sorted.map(d => d.name), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: '#8b8fa8', fontSize: 11 } },
    series: [{
      type: 'bar', data: sorted.map(d => d.score),
      barWidth: 10,
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#8b5cf6' }, { offset: 1, color: '#6366f1' }
        ]),
      },
      label: { show: true, position: 'right', color: '#8b8fa8', fontSize: 10, formatter: p => p.value },
    }],
  })
}

onMounted(render)
watch(() => props.data, render, { deep: true })
</script>
