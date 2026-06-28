# Brand Miner — 技术栈详解

> 面试时别说"用了这些技术"——要说"每个技术解决什么问题，为什么选它"

---

## 一、后端 Python 技术栈

### FastAPI 0.115.6 — Web 框架

**解决什么问题**：REST API 开发框架

**为什么选它**：
- 原生 async/await 支持——和本项目全链路异步的设计天然契合
- 自动生成 OpenAPI 文档（访问 `/docs` 就能看到完整的 Swagger UI）
- 类型提示驱动——Pydantic 模型自动做参数校验，少写一堆 if-else
- 生态成熟——Starlette 底层，CORS/中间件/TesClient 开箱即用

**项目中用在哪**：
```python
# 路由注册（main.py）
app.include_router(search_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")

# 类型校验（schemas.py）
class AnalysisRequest(BaseModel):
    category: str = Field(..., min_length=1, max_length=50)
    constraints: Optional[Dict[str, Any]] = None
```

---

### uvicorn 0.34.0 — ASGI 服务器

**解决什么问题**：把 FastAPI 应用跑起来

**为什么选它**：FastAPI 官方推荐，支持热重载（`reload=True`）、多 worker 模式。比 Gunicorn 更适合 async 场景。

---

### SQLAlchemy 2.0.36 + aiosqlite — 异步 ORM + 数据库

**解决什么问题**：数据持久化——Report 表存分析报告，AnalysisTask 表存任务状态

**为什么选这两个组合**：
- SQLAlchemy 2.0 原生支持 async mode（`select()` 风格的 ORM 查询）
- aiosqlite 是 SQLite 的异步驱动——不需要安装 MySQL/PostgreSQL，单文件数据库零配置部署
- 适合演示和个人项目——不需要额外数据库服务

**项目中用在哪**：
```python
# models.py — 表结构
class Report(Base):
    __tablename__ = "reports"
    task_id = Column(Integer, ForeignKey("analysis_tasks.id"))
    content = Column(JSON)  # 存完整的分析报告（含 AI 文字）
    top_direction = Column(String)  # 推荐品类
    pricing_suggestion = Column(String)  # 定价建议

# session.py — 异步会话
async_session = async_sessionmaker(engine, class_=AsyncSession)

# 查询示例
async with async_session() as session:
    stmt = select(Report).where(Report.task_id == task.id)
    report = (await session.execute(stmt)).scalar_one_or_none()
```

---

### python-dotenv 1.0.1 — 环境变量管理

**解决什么问题**：`.env` 文件→系统环境变量的桥梁

**为什么需要它**：DEEPSEEK_API_KEY 不能写代码里，又不想每次手动 `export`。`load_dotenv()` 自动加载根目录 `.env` 文件，开发环境配置零摩擦。

---

### jieba 0.42.1 — 中文分词

**解决什么问题**：用户痛点挖掘——从评论中提取高频关键词

**为什么选它**：
- 中文 NLP 领域最成熟的轻量分词库
- 零配置，不需要下载模型文件（内置词典 349,046 个词）
- 在这个项目里够用——只需要从几千条评论中提取 TOP10 痛点关键词

**项目中用在哪**：
```python
# pain_point.py — 痛点提取
import jieba
# 对差评文本分词，统计词频，过滤停用词
words = jieba.lcut(review_text)
word_freq = Counter(w for w in words if w not in STOPWORDS)
top_pains = word_freq.most_common(10)
```

---

### sse-starlette 1.8.2 — 服务端推送事件

**解决什么问题**：SSE Stream 的标准实现——asyncio.Queue → EventSourceResponse

**为什么选它**：
- FastAPI/Starlette 官方推荐的 SSE 库
- 单行代码：`return EventSourceResponse(event_generator())`
- 自动处理 Content-Type: text/event-stream 和连接管理

**项目中用在哪**：
```python
# routes/analysis.py
async def event_generator():
    while True:
        event = await queue.get()
        yield {"event": event["type"], "data": json.dumps(event["data"])}
        if event["type"] in ("ai_report_done", "ai_report_fallback", "error"):
            break

return EventSourceResponse(event_generator())
```

---

### httpx — HTTP 客户端（隐式依赖）

**解决什么问题**：调用 DeepSeek API

**为什么用它**：Python 生态最成熟的 async HTTP 客户端。支持 `client.stream()` 做 SSE 接收（AI 流式输出），超时控制、自动重定向。FastAPI 的 TestClient 底层也是 httpx。

---

## 二、前端 Vue 3 技术栈

### Vue 3.5.13 — 渐进式前端框架

**解决什么问题**：构建单页面应用（SPA）

**为什么选它**：
- Composition API（`<script setup>`）语法——比 Options API 更简洁，逻辑复用更方便
- 响应式系统（`ref`/`reactive`）——数据变化自动更新 DOM
- 生态系统——Vue Router、Pinia、Vite 官方维护，不需要自己拼装

**项目中用在哪**：7 个组件（Analyzing/Report/Home 页面 + ScoreCard/ThinkingStream/Chart 等子组件）通过 SFC（`.vue` 单文件组件）组织。

---

### Vue Router 4.5.0 — 路由管理

**解决什么问题**：页面导航（`/ → /analyzing/{id} → /report/{id}`）

**为什么选它**：Vue 3 官方路由，支持动态路由、导航守卫、懒加载。

**项目路由结构**：
```js
/                    → Home.vue       (输入品类)
/analyzing/:taskId   → Analyzing.vue  (实时分析)
/report/:taskId      → Report.vue     (完整报告)
```

---

### Pinia 2.3.0 — 状态管理

**解决什么问题**：跨组件共享分析任务状态（进度、结果、SSE 连接）

**为什么选它**（相比 Vuex）：
- 更简洁的 API——no mutations，直接 `store.progress = 50`
- TypeScript 友好
- Vue 3 官方推荐，替代 Vuex

**项目中用在哪**：`useAnalysisStore` 管理全局分析状态：
```js
state: {
  currentTaskId,    // 当前分析任务 ID
  taskStatus,       // pending/running/ai_generating/done/failed
  progress,         // 0-100
  thinkingMessages, // ThinkingStream 消息列表
  subCategoryResults, // 细分方向评分结果
  aiReport,         // AI 报告文字（流式累积）
  aiReportStatus,   // idle/generating/done/fallback
}
```

---

### axios 1.7.9 — HTTP 请求

**解决什么问题**：前端调用后端 API

**为什么选它**：拦截器、超时控制、自动 JSON 解析。统一配置：
```js
// utils/api.js
const api = axios.create({
  baseURL: (import.meta.env.VITE_API_BASE_URL || '') + '/api/v1',
  timeout: 30000,
})
```

---

### ECharts 5.5.1 — 数据可视化

**解决什么问题**：报告页的雷达图、柱状图、折线图、词云

**为什么选它**：
- 效果好——渲染 Canvas，支持动画、主题、交互
- 中文文档全——比 D3.js 上手快 10 倍
- 图表种类够用——雷达图（四维对比）、柱状图（品牌真空/增长信号）、词云（痛点关键词）

**项目中用了 4 种图表**：
```
BrandVacuumChart.vue → 横向柱状图（品牌真空度对比）
GrowthChart.vue      → 柱状图+折线（增长率对比）
PriceRangeChart.vue  → 柱状+折线（价格带分布图）
PainPointCloud.vue   → 词云（差评关键词）
RadarChart（内嵌在 Report.vue） → 雷达图（TOP3 四维对比）
```

---

### TailwindCSS 3.4.17 — 原子化 CSS

**解决什么问题**：样式开发——不用写 CSS 文件

**为什么选它**：
- 原子化——`flex items-center gap-3` 比单写一个 `.header` class 快
- 深色主题——CSS 变量 `var(--bg-primary)` 配合 Tailwind 的 `bg-[var(--bg-card)]` 语法
- 减少样式冲突——没有全局 CSS 污染

**项目中用在哪**：所有组件的样式都是 Tailwind utility classes，只有 `main.css` 里有动画和 CSS 变量定义。

---

### Autoprefixer 10.4.20 — CSS 前缀补充

**解决什么问题**：自动加浏览器前缀（`-webkit-`、`-moz-`）

**为什么需要**：部分 CSS 属性在不同浏览器需要前缀（如 `backdrop-filter`），Autoprefixer 根据 Can I Use 数据自动补充。

---

### Vite 6.0.7 — 构建工具

**解决什么问题**：开发服务器 + 生产构建

**为什么选它**（相比 Webpack）：
- 开发启动快——ESM 原生模块，秒开
- HMR 热更新快——改一个组件不需要重编译整个项目
- 构建快——Rollup 底层，生产打包优化

**vite.config.js 关键配置**：
```js
server: {
  port: 5173,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // 开发环境代理到后端
      changeOrigin: true,
    }
  }
}
```

---

### @headlessui/vue 1.7.22 — 无样式 UI 组件

**解决什么问题**：可访问性交互组件（下拉菜单、对话框等）

**为什么选它**：提供交互逻辑但不限制样式——完全用 Tailwind 自定义外观。项目中用于输入表单的下拉选择器。

---

## 三、部署 & DevOps

### Railway — 后端托管

**特点**：自动从 GitHub 拉取代码，识别 Python 项目（`requirements.txt`），自动 `pip install` 然后跑 `python -m backend.main`。

**配置**（通过 render.yaml 或 Railway Dashboard）：
```yaml
buildCommand: pip install -r requirements.txt
startCommand: python -m backend.main
envVars:
  DEEPSEEK_API_KEY: (sync: false)  # 手动在 Dashboard 配置，不存代码
  DATA_SOURCE: mock
```

---

### Cloudflare Pages — 前端托管

**特点**：GitHub 推送后自动 `npm run build`，全球 CDN 分发。SPA 重写规则用 `vercel.json`。

**为什么选它**：免费、快、自动部署。

---

### GitHub — 版本控制 + CI/CD 触发器

**为什么用它**：Railway 和 Cloudflare Pages 都支持 GitHub 自动部署，推送即上线。

---

## 四、技术栈总结（面试一句话版）

"后端用 FastAPI + asyncio 实现全链路异步，前端用 Vue 3 + Pinia + ECharts，数据可视化用雷达图和柱状图对比四维评分，SSE 实时推送还原 Deep Research 体验，AI 报告部分接 DeepSeek 流式输出，部署在 Railway + Cloudflare Pages 公网可访问。"

## 五、每个技术解决什么问题的速查表

| 技术 | 类别 | 解决的问题 |
|------|------|-----------|
| FastAPI | 后端框架 | REST API + 自动参数校验 + 异步支持 |
| SQLAlchemy 2.0 async | ORM | Report 表持久化，异步查询不阻塞 |
| aiosqlite | 数据库驱动 | SQLite 零配置部署，单文件数据库 |
| jieba | NLP | 从评论中提取高频痛点关键词 |
| sse-starlette | SSE | asyncio.Queue → EventSource 标准推送 |
| httpx | HTTP 客户端 | 调用 DeepSeek API + 流式接收 |
| python-dotenv | 配置管理 | .env 文件加载 API Key |
| Vue 3 Composition API | 前端框架 | SPA 单页应用，响应式渲染 |
| Pinia | 状态管理 | 跨组件共享分析进度和结果 |
| ECharts | 数据可视化 | 雷达图/柱状图/词云 |
| TailwindCSS | CSS | 原子化样式，深色主题 |
| Vite | 构建工具 | 秒级开发启动 + 生产打包 |
| axios | HTTP 请求 | 前端调用后端 API |
| Vue Router | 路由 | 三页面导航 |
