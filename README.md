# 品牌矿工 Brand Miner

> 非品牌商家的智能选品决策引擎

## 项目简介

输入任意品类方向，系统自动分析市场数据，输出可执行的选品决策报告。
类似 Deep Research 的选品垂直版：给一个问题，系统自己分析，最后给决策建议。

## 核心功能

- **四大分析维度**：品牌真空度 / 自然增长信号 / 用户痛点挖掘 / 价格利润分析
- **三层数据源架构**：天池数据集 / 京东轻量爬虫 / 结构化模拟数据，降级链永不中断
- **SSE 实时推送**：还原 Deep Research "系统正在思考" 的体验
- **AI 决策报告**：接入 DeepSeek API，量化数据转化为可读决策建议

## 技术栈

- 后端：Python 3.11 + FastAPI + SQLite + SQLAlchemy（async）
- 前端：Vue 3 + Vite + Pinia + ECharts + TailwindCSS
- AI：DeepSeek API（deepseek-chat），支持流式输出
- 部署：Railway（后端）+ Vercel（前端）

## 系统架构

```
用户输入品类关键词
       ↓
DataSourceAdapter（三层数据源自动切换）
       ↓
AnalysisOrchestrator（asyncio.gather 并行分析）
       ↓
四大分析模块（品牌真空 / 增长信号 / 痛点挖掘 / 价格利润）
       ↓
ScoringEngine（加权评分 + 动态权重调整）
       ↓
SSE 实时推送 → Vue 3 前端实时渲染
       ↓
DeepSeek AI 生成决策报告
```

## 本地运行

```bash
# 后端
cp .env.example .env
# 填入 DEEPSEEK_API_KEY
pip install -r requirements.txt
python -m backend.main

# 前端
cd frontend
npm install
npm run dev
```

## 在线演示

- 前端：（Vercel 部署后填入）
- 后端：https://brand-miner-api-production-4dd8.up.railway.app/docs

## License

MIT
