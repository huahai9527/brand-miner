<!--
  Home.vue — 输入页
  品类输入 + 约束条件 + 提交 + 历史列表
-->
<template>
  <div class="max-w-[720px] mx-auto px-4 py-16">
    <!-- 标题 -->
    <div class="text-center mb-10">
      <h1 class="text-4xl font-bold tracking-tight">
        <span class="gradient-text">品牌矿工</span>
        <span class="text-[var(--text-primary)] ml-2">Brand Miner</span>
      </h1>
      <p class="mt-3 text-[var(--text-secondary)] text-sm">
        非品牌商家的智能选品决策引擎 — 输入品类，系统自主探索市场，输出可执行的选品建议
      </p>
    </div>

    <!-- 输入表单 -->
    <InputForm @submit="handleStart" />

    <!-- 历史记录 -->
    <div v-if="history.length > 0" class="mt-10">
      <h3 class="text-sm font-medium text-[var(--text-secondary)] mb-3">最近分析</h3>
      <div class="space-y-2">
        <RouterLink
          v-for="item in history.slice(0, 3)"
          :key="item.task_id"
          :to="item.status === 'done' ? `/report/${item.task_id}` : `/analyzing/${item.task_id}`"
          class="block px-4 py-3 rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)]
                 hover:border-[var(--accent)]/30 transition-all group"
        >
          <div class="flex items-center justify-between">
            <div>
              <span class="text-sm font-medium text-[var(--text-primary)]">{{ item.category }}</span>
              <span v-if="item.top_recommendation" class="ml-2 text-xs text-[var(--green)]">
                推荐：{{ item.top_recommendation }}
              </span>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-xs text-[var(--text-muted)]">{{ formatDate(item.created_at) }}</span>
              <span class="text-xs opacity-0 group-hover:opacity-100 transition-opacity text-[var(--accent-light)]">
                查看 →
              </span>
            </div>
          </div>
        </RouterLink>
      </div>
    </div>

    <!-- DataSourceBadge -->
    <div class="fixed bottom-4 right-4 z-10">
      <DataSourceBadge />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAnalysisStore } from '../stores/analysis'
import InputForm from '../components/InputForm.vue'
import DataSourceBadge from '../components/DataSourceBadge.vue'

const router = useRouter()
const store = useAnalysisStore()
const history = ref([])

onMounted(async () => {
  try {
    const data = await store.fetchHistory()
    if (data?.tasks) history.value = data.tasks
  } catch { /* ignore */ }
})

const handleStart = async (category, constraints) => {
  try {
    const taskId = await store.startAnalysis(category, constraints)
    router.push(`/analyzing/${taskId}`)
  } catch (e) {
    console.error('启动分析失败:', e)
  }
}

const formatDate = (d) => {
  if (!d) return ''
  return new Date(d).toLocaleDateString('zh-CN')
}
</script>
