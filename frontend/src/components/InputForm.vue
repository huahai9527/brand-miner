<!--
  InputForm.vue — 分析输入表单
  Props: (none)
  Emits: submit(category, constraints)
-->
<template>
  <div class="w-full">
    <!-- 大类关键词输入 -->
    <div class="relative">
      <input
        ref="inputRef"
        v-model="category"
        type="text"
        placeholder="输入任意品类方向，如：宠物、家居、户外..."
        class="w-full px-4 py-3.5 rounded-xl text-base
               bg-[var(--bg-card)] border border-[var(--border-subtle)]
               text-[var(--text-primary)] placeholder-[var(--text-muted)]
               focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]/30
               transition-all duration-200"
        :disabled="loading"
        @keydown.enter="handleSubmit"
      />
    </div>

    <!-- 可选约束条件 -->
    <div class="mt-3">
      <button
        @click="showAdvanced = !showAdvanced"
        class="flex items-center gap-1.5 text-sm text-[var(--text-secondary)] hover:text-[var(--accent-light)] transition-colors"
      >
        <span class="transition-transform duration-200" :class="{ 'rotate-90': showAdvanced }">▸</span>
        高级筛选
      </button>

      <div v-if="showAdvanced" class="mt-3 space-y-3 p-4 rounded-xl bg-[var(--bg-card)] border border-[var(--border-subtle)] animate-fade-in-up">
        <!-- 价格区间 -->
        <div>
          <label class="block text-xs text-[var(--text-secondary)] mb-1.5">价格区间 (元)</label>
          <div class="flex items-center gap-2">
            <input v-model.number="priceMin" type="number" min="0" placeholder="最低价"
              class="w-1/2 px-3 py-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]/50" />
            <span class="text-[var(--text-muted)]">—</span>
            <input v-model.number="priceMax" type="number" min="0" placeholder="最高价"
              class="w-1/2 px-3 py-2 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)]/50" />
          </div>
        </div>

        <!-- 目标客群 -->
        <div>
          <label class="block text-xs text-[var(--text-secondary)] mb-1.5">目标客群</label>
          <div class="flex flex-wrap gap-1.5">
            <button v-for="opt in audienceOptions" :key="opt.value"
              @click="audience = audience === opt.value ? '' : opt.value"
              :class="[
                'px-3 py-1.5 rounded-full text-xs transition-all',
                audience === opt.value
                  ? 'bg-[var(--accent)]/20 text-[var(--accent-light)] border border-[var(--accent)]/30'
                  : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:border-[var(--accent)]/30'
              ]">
              {{ opt.label }}
            </button>
          </div>
        </div>

        <!-- 品牌策略 -->
        <div>
          <label class="block text-xs text-[var(--text-secondary)] mb-1.5">品牌策略</label>
          <div class="flex flex-wrap gap-1.5">
            <button v-for="opt in brandOptions" :key="opt.value"
              @click="brandStrategy = brandStrategy === opt.value ? '' : opt.value"
              :class="[
                'px-3 py-1.5 rounded-full text-xs transition-all',
                brandStrategy === opt.value
                  ? 'bg-[var(--accent)]/20 text-[var(--accent-light)] border border-[var(--accent)]/30'
                  : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:border-[var(--accent)]/30'
              ]">
              {{ opt.label }}
            </button>
          </div>
        </div>

        <!-- 优先策略 -->
        <div>
          <label class="block text-xs text-[var(--text-secondary)] mb-1.5">优先策略</label>
          <div class="flex flex-wrap gap-1.5">
            <button v-for="opt in priorityOptions" :key="opt.value"
              @click="priority = priority === opt.value ? '' : opt.value"
              :class="[
                'px-3 py-1.5 rounded-full text-xs transition-all',
                priority === opt.value
                  ? 'bg-[var(--accent)]/20 text-[var(--accent-light)] border border-[var(--accent)]/30'
                  : 'bg-[var(--bg-primary)] text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:border-[var(--accent)]/30'
              ]">
              {{ opt.label }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 提交按钮 -->
    <button
      @click="handleSubmit"
      :disabled="!canSubmit || loading"
      class="mt-4 w-full py-3 rounded-xl font-semibold text-white transition-all duration-300
             disabled:opacity-40 disabled:cursor-not-allowed"
      :class="canSubmit && !loading
        ? 'bg-gradient-to-r from-[var(--accent)] to-[var(--accent-light)] hover:shadow-lg hover:shadow-[var(--accent)]/20'
        : 'bg-[var(--bg-card)]'"
    >
      <span v-if="loading" class="inline-flex items-center gap-2">
        <span class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
        分析准备中...
      </span>
      <span v-else>开始分析</span>
    </button>

    <p class="mt-2 text-xs text-center text-[var(--text-muted)]">
      系统将自动探索市场数据，识别细分方向，输出选品决策建议
    </p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const emit = defineEmits(['submit'])

const category = ref('')
const showAdvanced = ref(false)
const priceMin = ref(null)
const priceMax = ref(null)
const audience = ref('')
const brandStrategy = ref('')
const priority = ref('')
const loading = ref(false)
const inputRef = ref(null)

const audienceOptions = [
  { label: '年轻人', value: 'young' },
  { label: '宝妈', value: 'mom' },
  { label: '老年人', value: 'elderly' },
  { label: '通用', value: 'general' },
]
const brandOptions = [
  { label: '白牌切入', value: 'white_label' },
  { label: '轻品牌', value: 'light_brand' },
  { label: '品质升级', value: 'quality_up' },
]
const priorityOptions = [
  { label: '快速起量', value: 'volume' },
  { label: '利润优先', value: 'margin' },
  { label: '差异化竞争', value: 'differentiation' },
]

const canSubmit = computed(() => category.value.trim().length > 0)

const handleSubmit = async () => {
  if (!canSubmit.value || loading.value) return

  const constraints = {}
  if (priceMin.value != null) constraints.price_min = priceMin.value
  if (priceMax.value != null) constraints.price_max = priceMax.value
  if (audience.value) constraints.target_audience = audience.value
  if (brandStrategy.value) constraints.brand_strategy = brandStrategy.value
  if (priority.value) constraints.priority = priority.value

  loading.value = true
  emit('submit', category.value.trim(), constraints)
}
</script>
