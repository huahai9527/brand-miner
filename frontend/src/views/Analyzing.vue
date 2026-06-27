<!--
  Analyzing.vue — 实时分析页（核心页面）
  左侧：ThinkingStream（思考流）
  右侧：实时结果卡片（每完成一个细分方向出现一张）
  顶部：进度条 + 完成后「查看报告」按钮
-->
<template>
  <div class="h-[calc(100vh-56px)] flex flex-col">
    <!-- 顶部状态栏 -->
    <div class="px-6 py-3 border-b border-[var(--border-subtle)] flex items-center justify-between">
      <div class="flex items-center gap-3">
        <RouterLink to="/" class="text-sm text-[var(--text-muted)] hover:text-white transition-colors">
          ← 返回首页
        </RouterLink>
        <h2 class="text-sm font-semibold">
          分析中：<span class="gradient-text">{{ store.category }}</span>
        </h2>
        <span v-if="store.taskStatus === 'running'" class="w-2 h-2 bg-[var(--accent)] rounded-full animate-pulse"></span>
      </div>
      <RouterLink
        v-if="store.taskStatus === 'done'"
        :to="`/report/${store.currentTaskId}`"
        class="px-4 py-1.5 rounded-lg bg-gradient-to-r from-[var(--accent)] to-[var(--accent-light)]
               text-white text-sm font-medium hover:shadow-lg hover:shadow-[var(--accent)]/20
               transition-all btn-glow"
      >
        查看完整报告 →
      </RouterLink>
    </div>

    <!-- 主要内容区 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 左侧：ThinkingStream -->
      <div class="w-[40%] min-w-[300px] border-r border-[var(--border-subtle)] p-4 overflow-hidden">
        <ThinkingStream />
      </div>

      <!-- 右侧：实时结果卡片 -->
      <div class="flex-1 p-4 overflow-y-auto">
        <div class="space-y-3">
          <ScoreCard
            v-for="(result, i) in store.subCategoryResults"
            :key="result.name"
            :result="result"
            :style="{ animationDelay: i * 0.08 + 's' }"
          />
        </div>

        <!-- 空状态 -->
        <div v-if="store.subCategoryResults.length === 0 && store.taskStatus === 'running'"
             class="flex items-center justify-center h-64 text-sm text-[var(--text-muted)]">
          等待分析结果...
        </div>

        <!-- 失败状态 -->
        <div v-if="store.taskStatus === 'failed'"
             class="flex flex-col items-center justify-center h-64 gap-3">
          <span class="text-3xl">⚠️</span>
          <span class="text-sm text-[var(--text-secondary)]">分析过程中出现问题</span>
          <RouterLink to="/" class="text-sm text-[var(--accent-light)] hover:underline">
            返回首页重试
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAnalysisStore } from '../stores/analysis'
import ThinkingStream from '../components/ThinkingStream.vue'
import ScoreCard from '../components/ScoreCard.vue'

const route = useRoute()
const store = useAnalysisStore()

onMounted(() => {
  const taskId = route.params.taskId || store.currentTaskId
  if (taskId) {
    store.connectSSE(taskId)
  }
})

onUnmounted(() => {
  if (store.taskStatus === 'running') {
    store.disconnectSSE()
  }
})
</script>
