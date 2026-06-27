/**
 * Pinia Store — 核心状态管理
 * 管理：分析任务、SSE 连接、实时结果、报告数据
 */
import { defineStore } from 'pinia'
import api, { createSSE } from '../utils/api'

export const useAnalysisStore = defineStore('analysis', {
  state: () => ({
    // 当前任务
    currentTaskId: null,
    taskStatus: null,       // pending | running | done | failed
    progress: 0,
    category: '',
    constraints: {},

    // ThinkingStream 消息
    thinkingMessages: [],

    // 细分方向结果（实时累积，按评分排序）
    subCategoryResults: [],

    // 完整报告
    fullReport: null,

    // AI 报告
    aiReport: '',           // 流式累积的报告文字
    aiReportStatus: 'idle', // idle | generating | done | fallback
    llmProvider: '',        // 'DeepSeek' 或 'template'

    // 数据源状态
    dataSourceStatus: null,

    // SSE 连接
    sseConnection: null,
  }),

  actions: {
    // ---- 启动分析 ----
    async startAnalysis(category, constraints = {}) {
      this.reset()
      const { data } = await api.post('/analysis/start', { category, constraints })
      this.currentTaskId = data.task_id
      this.taskStatus = 'pending'
      this.category = category
      this.constraints = constraints
      return data.task_id
    },

    // ---- SSE 连接 ----
    connectSSE(taskId) {
      this.disconnectSSE()
      this.currentTaskId = taskId
      this.taskStatus = 'running'

      const sse = createSSE(`/analysis/${taskId}/stream`)
      this.sseConnection = sse

      sse.addEventListener('task_start', (e) => {
        const d = JSON.parse(e.data)
        this.addThinking({ type: 'task_start', icon: '🔍', text: `开始探索「${this.category}」市场格局...`, raw: d })
        this.progress = d.progress || 5
      })

      sse.addEventListener('data_fetching', (e) => {
        const d = JSON.parse(e.data)
        const sourceLabel = { tianchi: '天池数据', jd: '京东实时', mock: '模拟数据' }[d.source] || d.source
        this.addThinking({ type: 'data_fetching', icon: '📡', text: `正在抓取市场数据 [${sourceLabel}]...`, raw: d })
        this.progress = d.progress || 10
      })

      sse.addEventListener('data_ready', (e) => {
        const d = JSON.parse(e.data)
        const subCats = (d.sub_categories || []).join('、')
        this.addThinking({ type: 'data_ready', icon: '✅', text: `获取 ${d.product_count} 条商品，识别出 ${d.sub_categories?.length || 0} 个细分方向：${subCats}`, raw: d })
        this.progress = d.progress || 30
      })

      sse.addEventListener('subcategory_done', (e) => {
        const d = JSON.parse(e.data)
        this.addThinking({ type: 'subcategory_done', icon: '📊', text: `「${d.sub_category}」分析完成 → ${d.key_insight}`, raw: d })
        this.progress = d.progress || this.progress

        // 添加或更新细分方向结果
        const idx = this.subCategoryResults.findIndex(r => r.name === d.sub_category)
        const result = {
          name: d.sub_category,
          total_score: d.score,
          recommendation: d.recommendation,
          key_insight: d.key_insight,
          message: d.message,
        }
        if (idx >= 0) {
          this.subCategoryResults[idx] = result
        } else {
          this.subCategoryResults.push(result)
        }
        // 按评分降序
        this.subCategoryResults.sort((a, b) => b.total_score - a.total_score)
      })

      sse.addEventListener('analysis_done', (e) => {
        const d = JSON.parse(e.data)
        this.addThinking({ type: 'analysis_done', icon: '🎯', text: `分析完成，最优切入方向：「${d.top_recommendation?.sub_category || ''}」`, raw: d })
        this.progress = 100
        this.taskStatus = 'ai_generating'
        // 不关闭 SSE，等待 AI 报告事件
      })

      sse.addEventListener('ai_report_start', (e) => {
        const d = JSON.parse(e.data)
        this.addThinking({ type: 'ai_report_start', icon: '🤖', text: 'AI 正在深度解读数据...', raw: d })
        this.aiReportStatus = 'generating'
        this.aiReport = ''
      })

      sse.addEventListener('ai_report_chunk', (e) => {
        const d = JSON.parse(e.data)
        this.aiReport += d.chunk
      })

      sse.addEventListener('ai_report_done', (e) => {
        const d = JSON.parse(e.data)
        this.addThinking({ type: 'ai_report_done', icon: '✅', text: '决策报告已生成，由 DeepSeek 提供支持', raw: d })
        this.aiReportStatus = 'done'
        this.llmProvider = d.provider || 'DeepSeek'
        this.taskStatus = 'done'
        this.disconnectSSE()
      })

      sse.addEventListener('ai_report_fallback', (e) => {
        const d = JSON.parse(e.data)
        this.addThinking({ type: 'ai_report_fallback', icon: '📋', text: '已生成结构化分析报告', raw: d })
        this.aiReport = d.report || ''
        this.aiReportStatus = 'fallback'
        this.llmProvider = 'template'
        this.taskStatus = 'done'
        this.disconnectSSE()
      })

      sse.addEventListener('error', (e) => {
        try {
          const d = JSON.parse(e.data)
          this.addThinking({ type: 'error', icon: '⚠️', text: d.message, raw: d })
          this.taskStatus = 'failed'
          this.disconnectSSE()
        } catch {
          // SSE 连接错误（可能是服务端未就绪）
        }
      })

      sse.addEventListener('ping', () => {
        // 心跳，忽略
      })

      // 连接异常处理
      sse.onerror = () => {
        if (this.taskStatus === 'running') {
          // 可能是网络波动，SSE 会自动重连
        }
      }
    },

    disconnectSSE() {
      if (this.sseConnection) {
        this.sseConnection.close()
        this.sseConnection = null
      }
    },

    // ---- 获取完整报告 ----
    async fetchResult(taskId) {
      const { data } = await api.get(`/analysis/${taskId}/result`)
      this.fullReport = data
      this.taskStatus = data.status
      this.progress = data.progress
      return data
    },

    // ---- 获取历史 ----
    async fetchHistory() {
      const { data } = await api.get('/analysis/history?limit=10')
      return data
    },

    // ---- 获取数据源状态 ----
    async fetchDataSourceStatus() {
      try {
        const { data } = await api.get('/data-source/status')
        this.dataSourceStatus = data
        return data
      } catch {
        return null
      }
    },

    // ---- 内部方法 ----
    addThinking(msg) {
      msg.id = Date.now() + Math.random()
      msg.time = new Date().toLocaleTimeString()
      this.thinkingMessages.push(msg)
    },

    reset() {
      this.currentTaskId = null
      this.taskStatus = null
      this.progress = 0
      this.thinkingMessages = []
      this.subCategoryResults = []
      this.fullReport = null
      this.aiReport = ''
      this.aiReportStatus = 'idle'
      this.llmProvider = ''
    },
  },
})
