<!--
  ThinkingStream.vue — AI 思考过程实时展示
  消费 Pinia store 中的 thinkingMessages + aiReport
  每条消息从下方淡入，自动滚到底部，底部闪烁光标
  AI 报告流式内容在独立的卡片区域显示
-->
<template>
  <div class="flex flex-col h-full">
    <!-- 进度条 -->
    <div class="mb-4">
      <div class="flex justify-between text-xs text-[var(--text-secondary)] mb-1.5">
        <span>{{ statusLabel }}</span>
        <span>{{ store.progress }}%</span>
      </div>
      <div class="h-1.5 bg-[var(--bg-primary)] rounded-full overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-700 ease-out"
          :class="progressGradient"
          :style="{ width: store.progress + '%' }"
        ></div>
      </div>
    </div>

    <!-- 思考消息列表 -->
    <div ref="listRef" class="flex-1 overflow-y-auto space-y-3 pr-1">
      <div
        v-for="(msg, i) in store.thinkingMessages"
        :key="msg.id"
        class="animate-fade-in-up text-sm leading-relaxed"
        :class="i === store.thinkingMessages.length - 1
          ? 'text-[var(--text-primary)]'
          : 'text-[var(--text-secondary)] opacity-80'"
      >
        <span class="mr-1.5">{{ msg.icon }}</span>
        <span>{{ msg.text }}</span>
      </div>

      <!-- AI 报告流式内容 -->
      <div
        v-if="store.aiReportStatus === 'generating' || store.aiReportStatus === 'done'"
        class="mt-4 p-3 rounded-lg border border-l-2 bg-[var(--bg-primary)] animate-fade-in-up"
        :class="store.aiReportStatus === 'done'
          ? 'border-[var(--green)]/30 border-l-[var(--green)]'
          : 'border-[var(--accent)]/20 border-l-[var(--accent)]'"
      >
        <div class="text-xs text-[var(--text-muted)] mb-2 flex items-center gap-1.5">
          <span v-if="store.aiReportStatus === 'generating'" class="w-1.5 h-1.5 bg-[var(--accent)] rounded-full animate-pulse"></span>
          {{ store.aiReportStatus === 'generating' ? 'AI 正在生成报告...' : `由 ${store.llmProvider || 'DeepSeek'} 提供支持` }}
        </div>
        <div class="text-xs leading-relaxed text-[var(--text-secondary)] whitespace-pre-wrap font-mono max-h-48 overflow-y-auto report-preview">{{ formatReport(store.aiReport) }}</div>
        <div
          v-if="store.aiReportStatus === 'generating'"
          class="text-xs text-[var(--accent)] mt-1 cursor-blink inline-block"
        ></div>
      </div>

      <!-- 闪烁光标 -->
      <div
        v-if="store.taskStatus === 'running' || store.taskStatus === 'ai_generating'"
        class="text-sm text-[var(--accent)] cursor-blink ml-5"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useAnalysisStore } from '../stores/analysis'

const store = useAnalysisStore()
const listRef = ref(null)

const statusLabel = computed(() => {
  const map = { pending: '准备中...', running: '分析中', ai_generating: 'AI 报告中', done: '完成', failed: '失败' }
  return map[store.taskStatus] || '等待中'
})

const progressGradient = computed(() => {
  if (store.taskStatus === 'done') return 'bg-gradient-to-r from-[var(--green)] to-[var(--accent)]'
  if (store.taskStatus === 'failed') return 'bg-[var(--red)]'
  return 'bg-gradient-to-r from-[var(--accent)] to-[var(--accent-light)]'
})

// 格式化为可读文本（去掉 markdown 标记的简化显示）
const formatReport = (text) => {
  if (!text) return ''
  return text
    .replace(/^##\s+(.+)$/gm, '▸ $1')
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/^- /gm, '• ')
    .substring(0, 2000)
}

// 自动滚到底部
watch(() => store.thinkingMessages.length, () => {
  nextTick(() => {
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight
    }
  })
})

watch(() => store.aiReport.length, () => {
  nextTick(() => {
    if (listRef.value) {
      listRef.value.scrollTop = listRef.value.scrollHeight
    }
  })
})
</script>

<style scoped>
.report-preview {
  word-break: break-word;
  overflow-wrap: break-word;
}
</style>
