<!--
  App.vue — 根组件（深色主题）
  顶部导航含标题 + DataSourceBadge
-->
<template>
  <div class="min-h-screen bg-[var(--bg-primary)] text-[var(--text-primary)]">
    <!-- Top Nav -->
    <header class="border-b border-[var(--border-subtle)] px-6 py-3 flex items-center justify-between">
      <RouterLink to="/" class="flex items-center gap-2 hover:opacity-80 transition-opacity">
        <span class="text-lg font-bold gradient-text">Brand Miner</span>
        <span class="text-xs text-[var(--text-muted)] hidden sm:inline">智能选品决策</span>
      </RouterLink>
      <DataSourceBadge />
    </header>

    <!-- Main -->
    <main class="min-h-[calc(100vh-100px)]">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="text-center text-xs text-[var(--text-muted)] py-4 border-t border-[var(--border-subtle)]">
      Brand Miner v1.0 · 演示环境基于真实市场规律构建的模拟数据
    </footer>
  </div>
</template>

<script setup>
import DataSourceBadge from './components/DataSourceBadge.vue'
</script>
