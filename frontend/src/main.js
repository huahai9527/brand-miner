/**
 * Brand Miner — 前端入口
 * 初始化 Vue 3 + Pinia + Router + ECharts
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
