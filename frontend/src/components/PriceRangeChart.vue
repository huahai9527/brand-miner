<!--
  PriceRangeChart.vue — 价格带分布图
  Props: distribution: Array of { range, count, sales_ratio }
         opportunityRange: { low, high }
         mainRange: { low, high }
         suggestedEntry: number
         suggestedPremium: number
-->
<template>
  <div ref="chartRef" class="w-full h-64"></div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  distribution: { type: Array, default: () => [] },
  opportunityRange: { type: Object, default: () => ({}) },
  mainRange: { type: Object, default: () => ({}) },
  suggestedEntry: { type: Number, default: 0 },
  suggestedPremium: { type: Number, default: 0 },
})

const chartRef = ref(null)
let chart = null

const render = () => {
  if (!chartRef.value || props.distribution.length === 0) return
  if (!chart) chart = echarts.init(chartRef.value, null, { renderer: 'canvas' })

  const ranges = props.distribution.map(d => d.range)
  const counts = props.distribution.map(d => d.count)
  const salesRatios = props.distribution.map(d => d.sales_ratio * 100)

  chart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: { data: ['商品数', '销量占比'], textStyle: { color: '#8b8fa8', fontSize: 11 }, bottom: 0 },
    grid: { left: 10, right: 40, top: 10, bottom: 30 },
    xAxis: { type: 'category', data: ranges, axisLabel: { color: '#8b8fa8', fontSize: 10 }, axisLine: { show: false } },
    yAxis: [
      { type: 'value', name: '商品数', nameTextStyle: { color: '#515470', fontSize: 10 }, axisLabel: { color: '#515470' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } } },
      { type: 'value', name: '占比%', nameTextStyle: { color: '#515470', fontSize: 10 }, axisLabel: { color: '#515470' }, splitLine: { show: false } },
    ],
    series: [
      { name: '商品数', type: 'bar', data: counts, barWidth: 16, yAxisIndex: 0, itemStyle: { color: '#6366f1', borderRadius: [4, 4, 0, 0] } },
      { name: '销量占比', type: 'line', data: salesRatios, yAxisIndex: 1, smooth: true, lineStyle: { color: '#10b981' }, itemStyle: { color: '#10b981' }, symbol: 'circle', symbolSize: 6 },
    ],
  })
}

onMounted(render)
watch(() => props.distribution, render, { deep: true })
</script>
