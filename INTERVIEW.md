# 品牌矿工 Brand Miner — 面试深度拆解

> 面试官不可能挨个问，但你必须全部能答。每个问题都在问你的理解深度。

---

## 1. 这个项目是做什么的？为什么做？

**一句话**：非品牌电商商家的智能选品决策引擎——输入品类，AI 自动分析市场，输出可执行的选品建议。

**为什么做（背景故事）**：
公司想做产品方向调研，需要一个低成本验证选品假设的工具。传统方式：运营团队手工翻淘宝京东评论、列 Excel 对比价格、凭经验判断——效率低、主观性强、无法规模化。我的思路参照了 Deep Research 的产品理念：给系统一个问题，它自己探索、分析、给出建议，而不是让用户自己翻数据做决策。

**解决的痛点**：非品牌商家（白牌卖家）没有数据团队，不知道什么品类好做、什么价格带有机会、用户痛点在哪里。这个工具替他们做完了数据收集→分析→决策的全链路。

---

## 2. 三层数据源怎么设计的？每一层什么情况下降级？

```
Python
DATA_SOURCE 环境变量: "tianchi" → "jd" → "mock"（逐层降级）

DataSourceAdapter 封装了统一接口 fetch(keyword, constraints)
  ├── Layer 1: TianchiDataLoader
  │   阿里天池开放数据集（约10GB CSV），最接近真实市场
  │   降级条件：CSV 文件不存在 / 品类不匹配 / 数据不足
  │
  ├── Layer 2: JDLightCrawler
  │   轻量爬虫，搜索京东列表页（30条/次），带24h缓存
  │   降级条件：网络超时 / 反爬拦截 / 返回空列表
  │
  └── Layer 3: MockDataEngine（终极兜底）
      内置40+品类知识库，结构化模拟数据
      绝不可能失败——即使前两层全挂，系统也能正常工作
```

**设计原则**：对上层（AnalysisOrchestrator）完全透明。不管走到哪一层，返回的数据结构一模一样（platform/price/sales_30d/brand/sub_category...）。上层代码不需要知道数据从哪来的。

---

## 3. 评分引擎的四个维度是什么？权重怎么定的？

```
综合评分 = 品牌真空度×0.35 + 增长信号×0.30 + 痛点密度×0.20 + 价格利润×0.15
```

| 维度 | 权重 | 衡量什么 | 为什么这个权重 |
|------|------|---------|---------------|
| 品牌真空度 | 35% | 白牌占比、头部品牌集中度 | 非品牌商家最大的机会在于市场没有品牌壁垒 |
| 增长信号 | 30% | 新品上架频率、月增长率、是否"自然增长" | 选品最终要看是否在上升期（排除广告驱动的伪增长） |
| 痛点密度 | 20% | 差评关键词密度、差评率 | 差异化切入的抓手——用户抱怨最多的就是机会 |
| 价格利润 | 15% | 价格带分布、机会价格带、建议入场价 | 利润是结果不是原因，前三个维度决定了利润空间 |

**动态权重**：用户选"白牌优先"→品牌真空+5%利润-5%；选"快速起量"→增长+5%痛点-5%；选"差异化竞争"→痛点+5%增长-5%。所有权重归一化到1.0。

**面试时能多说一句**：每个维度的评分算法也有细节——品牌真空度用基尼系数衡量集中度，增长用90天内新品占比排除季节性波动，痛点用jieba分词+TF-IDF提取，价格用直方图找稀疏区间。

---

## 4. SSE怎么实现的？和WebSocket区别？

**SSE实现链路**：
```
AnalysisOrchestrator（后台任务）
  → push_sse("subcategory_done", {...})  回调解耦
  → SSEManager.push_event(task_id, event, data)
  → asyncio.Queue(maxsize=500)  异步事件队列
  → FastAPI EventSourceResponse  SSE Stream
  → 前端 EventSource API 消费
```

**核心代码（简化）**：
```python
# 后端：asyncio.Queue 作为事件总线
queues[task_id] = asyncio.Queue(500)
queues[task_id].put_nowait({"event": "subcategory_done", "data": {...}})

# 前端：原生 API，自带重连
const sse = new EventSource(`/api/v1/analysis/${taskId}/stream`)
sse.addEventListener('subcategory_done', (e) => {...})
```

**为什么选SSE而不是WebSocket**：

| | SSE | WebSocket |
|---|-----|-----------|
| 通信方向 | 单向（服务端→客户端） | 双向 |
| 协议 | HTTP（长连接） | 独立协议 ws:// |
| 重连 | 浏览器自带 | 需要手动实现 |
| 实现复杂度 | 低（FastAPI一行代码） | 中（需要心跳、重连逻辑） |
| 适合场景 | 实时推送、通知、进度条 | 聊天、协作编辑、游戏 |

**面试加分点**："这个场景天然是单向的——前端只需要消费分析进度，不需要向服务端发送命令。SSE轻量且自带重连，实现成本比WebSocket低一个数量级。"

---

## 5. asyncio.gather怎么用的？为什么用这个？

**两层并行**：
```python
# 第一层：8个细分方向彼此独立 → 并行执行
analysis_tasks = [analyze_one_direction(sc) for sc in sub_categories]
raw_results = await asyncio.gather(*analysis_tasks)

# 第二层：单个方向内部的4个分析模块 → 并行执行
brand_task = asyncio.to_thread(analyze_brand_vacuum, products)
growth_task = asyncio.to_thread(analyze_growth_signal, products, reviews)
pain_task = asyncio.to_thread(analyze_pain_points, reviews, products)
price_task = asyncio.to_thread(analyze_price, products, constraints)

brand_result, growth_result, pain_result, price_result = await asyncio.gather(
    brand_task, growth_task, pain_task, price_task,
)
```

**为什么用 asyncio.gather 而不是 for 循环**：
- 8个细分方向 × 4个分析模块 = 32个独立任务，串行需要3-5秒
- `asyncio.gather` 并行后只需要1-1.5秒（取决于最慢的那个）
- `asyncio.to_thread` 将 CPU密集型 NLP 分析（jieba分词、直方图计算）放到线程池，不阻塞事件循环

**面试时强调**："全链路异步——从FastAPI请求→数据获取→NLP分析→评分计算→SSE推送，整个链路没有一个同步阻塞点。"

---

## 6. DeepSeek调用失败怎么办？（降级机制）

**三层防御**：
```
L1: 环境变量检查
    DEEPSEEK_API_KEY 不存在 → 直接走 Fallback，不发请求

L2: 请求层容错
    超时（30s）、429限流、网络异常 → return None，不抛异常

L3: 业务层兜底
    _fallback_report() → 7个区块的结构化模板报告
    基于真实评分数据填充（不是硬编码的假数据）
```

**核心代码**：
```python
# llm_client.py：所有异常静默捕获，永不抛异常
try:
    response = await client.post(...)
except Exception as e:
    logger.warning(f"[LLM] call failed: {e}")
    return None  # 不抛异常，上层Fallback接管

# report_generator.py：Fallback模板是必选方案，不是备选
ai_report = await self.llm.chat(messages)
if ai_report:
    return ai_report
return self._fallback_report(task_data, analysis_summary)  # 必然可达
```

**设计哲学**："LLM 不可靠是常态，不是异常。Fallback 不是备选方案，是必选方案——它是演示时的最后防线，绝不能让屏幕空白。"

---

## 7. 部署在哪？遇到过什么问题？

**部署架构**：
- 后端：Railway（Python 3.11 + FastAPI + uvicorn，自动从 GitHub 拉取）
- 前端：Cloudflare Pages（Vue 3 静态构建，全球 CDN）
- 环境变量：DEEPSEEK_API_KEY 通过 Railway Dashboard 注入，不写代码

**遇到并解决的问题**：
1. **SQLite 路径问题**：Railway 容器没有预设 data/ 目录 → 启动时用 `os.makedirs(exist_ok=True)` 自动创建
2. **CORS 跨域**：OPTIONS 预检 400 → CORS_ORIGINS 白名单需要精确到生产域名（`*.pages.dev`）
3. **.env 泄露风险**：确认 .gitignore 拦截，API Key 仅在 Railway Dashboard 配置

---

## 8. 最大的困难是什么？怎么解决的？

**最大困难：SSE 事件流的完整链路调试**

问题场景：从 orchestrator → asyncio.Queue → FastAPI SSE → 前端 EventSource，四个环节任何一个出问题都表现为"前端没收到数据"，排查极难。

具体坑：
1. **队列溢出**：AI 报告流式输出时，每 1-2 个 token 就发一个事件，500 容量队列瞬间被填满，后续事件（包括 `ai_report_done`）被丢弃，前端永远停在"生成中"
2. **stream close 时机**：原来 `analysis_done` 就关流，但新增 AI 报告阶段后还有更多事件，导致前端连接提前中断

解决方法：
- 将 chunk 事件改为批量推送（每 50 字一发），队列压力降为原来的 1/50
- 将关闭条件改为 `ai_report_done` / `ai_report_fallback`
- 加日志记录每个事件的推送状态，发现 `队列已满` 警告立刻定位

**第二个困难：前端图表全部显示为 0**

根因：SSE 缓存只存了 4 个字段（name/score/recommendation/key_insight），图表需要的 score_breakdown/growth_rate/avg_price 全都没有。

解决方法：逐层追踪数据流——orchestrator 有完整数据但只推了摘要 → 改 SSE 事件推全部字段 → 改 SSE Manager 缓存全字段 → 前端重新绑定数据

**面试时这样说**："最有价值的困难不是技术本身，而是调试数据流时建立的'端到端思维'——从前端报错反推，一层层追踪数据在哪丢的，这是全栈工程师的核心能力。"

---

## 9. 补充问题：面试官还可能问什么

### Q：为什么不用数据库存分析结果？全是内存？
A：Phase 1-4 确实是纯内存，但 Phase 5 加了 SQLite 持久化。Report 表存完整的分析报告（含 AI 生成的文字 + 评分数据），支持历史回溯。内存缓存（SSE Manager）处理实时分析期间的状态，完成后写库。

### Q：Mock 数据的市场规律是什么？
A：品牌分布=二八定律（20%知名品牌占80%销量），价格=正态分布（均值±2σ截断），销量=指数衰减（销售额排名靠前的占绝大多数），增长趋势=品类特定（新兴品类高增长、传统品类平缓）。这些规律参考了电商行业公开统计指标。

### Q：SEO/产品关键词怎么处理的？
A：品类映射 → 模糊匹配 → 别名表 → 动态生成。40+品类知识库覆盖主流电商品类，"蓝牙耳机"会精确匹配到蓝牙耳机的 7 个细分子品类而非整个"耳机音频"大类。完全匹配不到时用"品类+通用后缀"动态构建（不会报错也不会返回空）。

### Q：前端图表如果数据为空怎么处理？
A：每个图表组件都有 `v-if` 守卫——数据为空时不初始化 ECharts，显示骨架占位。watch 用 `{deep: true}` 监听数据变化，数据就绪后自动渲染。

### Q：怎么保证 8 个细分方向的结果是有序的？
A：`asyncio.gather` 保持顺序——返回顺序和传参顺序一致，即使某些方向先完成。最终结果再按 total_score 降序排列。

### Q：代码质量怎么保证的？
A：模块化设计（Backend 分 6 层：api/routes → orchestrator → analyzers → data_sources → ai → database）、单一职责（每个分析模块只做一件事）、类型注释（虽然 Python 不强制，但关键接口都有类型提示）。

### Q：你在这个项目里最大的技术成长是什么？
A：三个收获：1）async/await 全链路异步在 Python 中的落地——从 FastAPI → SQLAlchemy 2.0 async → asyncio.gather，全程无同步阻塞；2）SSE 在生产环境下的实践——队列管理、心跳保活、连接清理；3）LLM 接入的工程化思维——任何 AI 服务都是不可靠的，Fallback 不是可选项而是必需项。

### Q：如果要重构，你会改什么？
A：1）前端状态管理——目前 Pinia Store 有点臃肿（200+行），应该拆成独立的 analysisStore / reportStore / uiStore；2）ECharts 按需引入——现在全量引入，体积约 1MB，改为按需引入可压缩到 300KB；3）Python 类型安全——加 mypy 静态检查，目前只有注释型的类型提示；4）添加 pytest 测试覆盖——目前只有手动验证。
