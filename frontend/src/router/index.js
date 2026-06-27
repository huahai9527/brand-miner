/**
 * Vue Router — 路由配置
 * /                    → Home.vue（输入页）
 * /analyzing/:taskId   → Analyzing.vue（分析过程）
 * /report/:taskId      → Report.vue（决策报告）
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAnalysisStore } from '../stores/analysis'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/analyzing/:taskId',
    name: 'Analyzing',
    component: () => import('../views/Analyzing.vue'),
    props: true,
    beforeEnter: (to, from, next) => {
      const store = useAnalysisStore()
      if (!to.params.taskId && !store.currentTaskId) {
        next('/')
      } else {
        next()
      }
    },
  },
  {
    path: '/report/:taskId',
    name: 'Report',
    component: () => import('../views/Report.vue'),
    props: true,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
