/**
 * API 统一入口 — 所有 HTTP 请求和 SSE 连接从这里发出
 *
 * 环境变量：
 *   开发环境（Vite dev server）：代理 /api/v1 → http://localhost:8000
 *   生产环境：VITE_API_BASE_URL → https://brand-miner-api.onrender.com
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const api = axios.create({
  baseURL: BASE_URL + '/api/v1',
  timeout: 30000,
})

/**
 * 通用的 Server-Sent Events 连接
 * @param {string} path - SSE 路径，如 /analysis/{task_id}/stream
 * @returns {EventSource}
 */
export function createSSE(path) {
  const url = BASE_URL + '/api/v1' + path
  return new EventSource(url)
}

export default api
