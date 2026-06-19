# Phase 1 逐步学习手册 · 转写闭环

> 记录 Phase 1（转写闭环）的**每一步设计与概念**，配可问 AI 的原理清单。
> 标记说明：✅ = 已实现并验证；🚧 = 已设计、即将实现；⭐ = 初学者/面试优先级最高。
> 这份文档随 Phase 1 推进持续补充。

---

## 目录

- [0. Phase 1 是干嘛的](#0-phase-1-是干嘛的)
- [1. 整体数据流（端到端）⭐](#1-整体数据流端到端)
- [2. 配置层 config.py ✅](#2-配置层-configpy-)
- [3. ASR 供应商抽象 ✅⭐](#3-asr-供应商抽象-)
- [4. 测试替身 Mock ✅](#4-测试替身-mock-)
- [5. 异步任务队列：为什么转写要走 Redis ⭐🚧](#5-异步任务队列为什么转写要走-redis-)
- [6. 数据库建模：meeting / transcript 🚧](#6-数据库建模meeting--transcript-)
- [7. 文件上传 🚧](#7-文件上传-)
- [8. 音频预处理：ffmpeg 转码 🚧](#8-音频预处理ffmpeg-转码-)
- [9. 混合检索（护城河核心）⭐🚧](#9-混合检索护城河核心)
  - [9.1 为什么要"检索"](#91-为什么要检索)
  - [9.2 切块 chunking](#92-切块-chunking)
  - [9.3 向量检索 + Embedding（BGE-M3）](#93-向量检索--embeddingbge-m3)
  - [9.4 BM25 关键词检索](#94-bm25-关键词检索)
  - [9.5 为什么"混合"：两者互补](#95-为什么混合两者互补)
  - [9.6 重排 rerank](#96-重排-rerank)
- [全部"可问 AI"问题汇总](#全部可问-ai问题汇总)

---

## 0. Phase 1 是干嘛的

**目标（DoD）**：上传一段会议音频 → 出转写文本，**并且**能跨会检索到历史片段。

它由两块独立能力组成：

- **1-A 上传 + 异步转写**：音频 → 文字。
- **1-B 混合检索**：把转写文字变成"可被语义+关键词搜索"的知识库。

做的顺序是先 1-A 再 1-B，因为检索的输入（文本）来自转写。

> 选型已定：ASR 用**阿里云通义**（云，模型 `paraformer-realtime-v2`）；**不做说话人分离**（diarization），MVP 先出一整段文本。

---

## 1. 整体数据流（端到端）⭐

这是 Phase 1 最该先在脑子里建立的一张图：

```
[浏览器] 上传音频
   │
   ▼
[FastAPI] 落盘 + 在 Postgres 建一条 meeting(status=pending) + 往 Redis 丢一个转写任务
   │
   └─► 立刻返回 { meeting_id, status: "pending" }     ← 关键：请求不等转写跑完
                                                          
[后台 worker] 从 Redis 取任务
   │  ① ffmpeg 把音频转成 16k 单声道 wav
   │  ② 调 ASR（通义）拿到转写文本
   │  ③ 写回 Postgres：transcript + status="done"
   │  ④ 文本切块 → 向量化 → 存进 Qdrant（供日后检索）
   ▼
[浏览器] 轮询 GET /meetings/{id} → 看到 status 变 done、拿到文本
```

🔍 **可以问 AI 的问题**：
- 这条链路里，为什么"上传请求"和"真正转写"要拆开、不在一个请求里做完？
- `status` 字段（pending → done）这种"状态机"在异步系统里为什么重要？还可能有哪些状态（如 failed）？

---

## 2. 配置层 config.py ✅

- **文件**：[backend/app/config.py](../backend/app/config.py)
- **做了什么**：用 `pydantic-settings` 把 `.env` 读成一个带类型校验的 `Settings` 对象，全项目统一 `from app.config import get_settings` 取值。
- **关键设计**：
  - 只有这一处碰环境变量，别处不直接 `os.getenv`——拼错/类型错在启动时就暴露。
  - `@lru_cache` 让它成单例：整个进程只读一次 `.env`。
- 🔍 **可以问 AI 的问题**：
  - 为什么"集中式配置"比到处 `os.getenv` 好？
  - `pydantic-settings` 是怎么做类型校验和默认值的？读取优先级（环境变量 vs .env vs 默认值）是怎样的？
  - `@lru_cache` 是怎么把一个函数变成"只算一次"的？这里用它做单例有什么好处和坑？

---

## 3. ASR 供应商抽象 ✅⭐

- **文件**：[base.py](../backend/app/asr/base.py) ｜ [dashscope_asr.py](../backend/app/asr/dashscope_asr.py) ｜ [__init__.py](../backend/app/asr/__init__.py)
- **做了什么**：定义抽象接口 `ASRProvider.transcribe(path) -> str`；具体实现挂在子类上（`DashScopeASR` / `MockASR`）；用工厂函数 `get_asr_provider()` 按环境变量 `ASR_PROVIDER` 选实现。
- **关键设计（面试高频）**：业务代码只依赖**抽象**，不依赖**具体厂商**。换供应商 = 新增一个子类 + 改一个环境变量，业务零改动。这叫**面向接口编程 / 依赖倒置原则（DIP）**。
- **延迟 import 的小技巧**：`dashscope` SDK 只在真用阿里云时才 import，用 mock 时连装都不用装。
- 🔍 **可以问 AI 的问题**：
  - 什么是"依赖倒置原则"？为什么"依赖抽象、不依赖具体"能让系统更好维护？举个换供应商的例子。
  - Python 里 `ABC` + `@abstractmethod` 是怎么强制子类实现方法的？和 `Protocol`（鸭子类型）有什么区别？
  - "工厂模式"解决什么问题？为什么不在业务代码里直接 `DashScopeASR(...)`？
  - "延迟 import（lazy import）"有什么好处？什么时候该用？

---

## 4. 测试替身 Mock ✅

- **文件**：[mock.py](../backend/app/asr/mock.py) ｜ 测试 [test_asr.py](../backend/tests/test_asr.py)
- **做了什么**：`MockASR` 忽略音频、返回一段写死的假转写（内容刻意含"决策/待办/风险"，方便后续抽取阶段也能拿它练手）。
- **关键设计**：让我们**不依赖真 ASR、不花钱、不联网**就能跑通并测试整条管道；CI 里也能跑（CI 不可能去调真 ASR）。
- **名词**：这类"冒充真实依赖的假对象"统称**测试替身（test double）**，细分还有 mock / stub / fake / spy。
- 🔍 **可以问 AI 的问题**：
  - 测试替身（mock/stub/fake）各自的区别和适用场景？
  - 为什么测试里要避免真的调用外部服务（网络/数据库/付费 API）？
  - `monkeypatch.setenv` 在测试里做了什么？为什么测完要 `cache_clear()`（结合第 2 节的 lru_cache 想）？

---

## 5. 异步任务队列：为什么转写要走 Redis ✅⭐

> 已实现：[app/queue.py](../backend/app/queue.py)（生产者/消费者帮助函数）+ [app/worker.py](../backend/app/worker.py)（消费者进程）+ docker-compose 里新增的 `worker` 服务。

这是 Phase 1 最值得讲透的工程概念之一。

- **问题**：一段会议转写要几十秒甚至几分钟。如果在"上传"这个 HTTP 请求里**同步**等它跑完：
  - 用户浏览器转圈几分钟，体验极差；
  - 请求可能超时（网关/浏览器一般 30~60s 就断）；
  - 一个慢任务占住一个 web 工作进程，并发一高服务就被拖垮。
- **解法（异步解耦）**：上传接口只做"轻活"——存文件、建记录、**往 Redis 丢一个任务**，然后**立刻返回 `task_id`/`meeting_id`**。真正的"重活"（转写）由后台 **worker** 进程从 Redis 取出来慢慢做。前端拿 id 轮询或用 SSE 看进度。
- **同步 vs 异步两条时间线**：
  ```
  同步：  [上传请求]====转写 90s====>[返回]      用户干等 90s，可能超时
  异步：  [上传请求]→丢队列→[1s 返回 task_id]    用户立刻得到响应
          [后台 worker] ====转写 90s====> 更新 status=done
  ```
- **Redis 在这里的角色**：消息/任务队列（也兼做缓存）。生产者（web）push 任务，消费者（worker）pop 任务。
- 🔍 **可以问 AI 的问题**：
  - "同步"和"异步"处理一个慢请求，分别发生了什么？为什么同步会拖垮并发？
  - 为什么用 Redis 当任务队列？它和专业消息队列（RabbitMQ / Kafka）比，取舍在哪？
  - "生产者-消费者模型"是什么？worker 进程和 web 进程为什么要分开？
  - 任务失败了怎么办？什么是"重试""死信队列""幂等性"？
  - 前端怎么知道转写好了——轮询 vs SSE vs WebSocket，各自取舍？

---

## 6. 数据库建模：meeting / transcript ✅

> 已实现：[app/models.py](../backend/app/models.py)（ORM 模型）+ [app/db.py](../backend/app/db.py)（引擎/会话/建表）。

- **做了什么**：在 Postgres 建了一张 `meeting` 表，字段：id、filename（原文件名）、audio_path（落盘路径）、status（状态机 pending/processing/done/failed）、transcript（转写文本）、error（失败原因）、created_at。
- **建模决策**：MVP 先把 transcript 作为 `meeting` 的一个大字段；等 Phase 3 要做"点待办跳回原话"时，再考虑拆成带时间戳的"分段表"。**先简单、需要时再拆**。
- **用 ORM 不手写 SQL**：`class Meeting(Base)` 里每个 `mapped_column` 对应一列，SQLAlchemy 负责翻译成 SQL。`Base.metadata.create_all()` 按模型建表（MVP 做法；生产用 Alembic 迁移）。
- 🔍 **可以问 AI 的问题**：
  - 数据库表设计时，什么时候该把数据放同一张表的字段、什么时候该拆成关联表（一对多）？
  - "状态字段"用字符串还是枚举（enum）？各有什么利弊？
  - 用 ORM（如 SQLAlchemy）和手写 SQL 各有什么取舍？
  - 什么是数据库迁移（migration，如 Alembic）？为什么不直接改表？

---

## 7. 文件上传 ✅

> 已实现：[app/api/meetings.py](../backend/app/api/meetings.py) 的 `POST /meetings`。

- **做了什么**：FastAPI 接收 `multipart/form-data` 上传的音频，用随机文件名落盘到 `storage/`（避免同名覆盖），建 `meeting(pending)`、入队，立刻返回。另有 `GET /meetings`（列表）和 `GET /meetings/{id}`（详情，前端轮询它看状态）。
- 🔍 **可以问 AI 的问题**：
  - 浏览器上传文件用的 `multipart/form-data` 编码长什么样？为什么传文件不用普通 JSON？
  - 大文件上传要注意什么（大小限制、流式写盘、临时文件）？
  - FastAPI 的 `UploadFile` 和直接读 `bytes` 有什么区别？

---

## 8. 音频预处理：ffmpeg 转码 🚧

- **将做什么**：上传的音频格式/采样率五花八门（mp3/m4a/各种 Hz），ASR 对输入有要求，所以先用 **ffmpeg** 统一转成 16k 单声道 wav。
- 🔍 **可以问 AI 的问题**：
  - "采样率""声道""位深""编码格式"分别是什么？为什么 ASR 常要 16kHz 单声道？
  - ffmpeg 是什么？`ffmpeg -i in.mp3 -ar 16000 -ac 1 out.wav` 这条命令每段什么意思？
  - 有损（mp3）和无损（wav）音频的区别？转写为什么常用 wav/pcm？

---

## 9. 混合检索（护城河核心）⭐✅

> 这是 Phase 1 的"硬核"和面试深挖重点。**从零实现**，封装在 `backend/app/retrieval/`。
> 已实现：[chunking.py](../backend/app/retrieval/chunking.py)（切块）、[tokenize.py](../backend/app/retrieval/tokenize.py)（jieba 分词）、[embedder.py](../backend/app/retrieval/embedder.py)（向量化，mock/dashscope）、[vector_store.py](../backend/app/retrieval/vector_store.py)（Qdrant）、[bm25.py](../backend/app/retrieval/bm25.py)（BM25）、[fusion.py](../backend/app/retrieval/fusion.py)（RRF 融合）、[reranker.py](../backend/app/retrieval/reranker.py)（重排，mock/dashscope）、[service.py](../backend/app/retrieval/service.py)（串起 index + search）。
> 真实向量/重排选 **云 DashScope**（text-embedding + gte-rerank），mock 实现用于测试和"先跑通"。
>
> **检索流水线**：`query → 向量召回(Qdrant) + BM25 召回 → RRF 融合 → gte-rerank 重排 → Top-K`。
> 索引时机：worker 转写完成后自动切块、向量化入库。查询入口：`GET /search?q=...`。

### 9.1 为什么要"检索"

会议越开越多，用户会问"上次关于预算我们定了啥"。不可能把所有历史会议全塞进 LLM（太长、太贵）。所以先**检索**出最相关的几段历史片段，再把这几段喂给 LLM——这就是 **RAG（检索增强生成）** 的核心思路。

🔍 问 AI：什么是 RAG？为什么不能把所有资料直接塞进大模型的上下文？

### 9.2 切块 chunking

整篇转写太长，要切成一段段"块（chunk）"再分别索引。怎么切（按句子/按字数/带重叠 overlap）直接影响检索质量。

🔍 问 AI：为什么要把长文本切块？块太大/太小分别有什么问题？什么是"overlap（重叠）"、为什么需要它？

### 9.3 向量检索 + Embedding（BGE-M3）

- **Embedding（嵌入）**：把一段文字用模型（我们用 **BGE-M3**）转成一串数字（向量），**语义相近的文字，向量也相近**。
- **向量检索**：把查询也转成向量，在 Qdrant 里找"距离最近"的那些块。好处：能命中"意思相近但用词不同"（如查"预算"能找到"成本花费"）。
- 🔍 问 AI：
  - Embedding 是怎么把"语义"变成向量的？"向量相似度"（余弦相似度）怎么衡量两段话像不像？
  - 向量数据库（Qdrant）和普通数据库查询有什么本质不同？它怎么做到快速找"最近邻"？
  - BGE-M3 这种 embedding 模型有什么特点（多语言、长文本）？

### 9.4 BM25 关键词检索

BM25 是经典的**基于关键词**的检索算法（搜索引擎老牌方法）：看查询词在文档里出现的频率等。好处：**精确命中专有名词/编号/人名**（如 "PROJ-1234"、"张伟"），这正是向量检索容易"糊"掉的。

🔍 问 AI：BM25 大致怎么打分？它和老的 TF-IDF 什么关系？它擅长和不擅长什么？

### 9.5 为什么"混合"：两者互补

- **向量**：懂语义、抗换词，但对精确关键词/罕见词不敏感。
- **BM25**：精确命中关键词，但不懂"近义"。
- **混合**：两路一起检索再合并（如 RRF 融合），取长补短。**这就是"为什么混合检索"的标准答案。**

🔍 问 AI：向量和 BM25 各自的短板是什么？"混合检索"怎么把两路结果融合（什么是 RRF / 加权融合）？

### 9.6 重排 rerank

混合检索召回一批候选后，再用一个更强的 **rerank（重排）模型**对这批候选精细打分、重新排序，把最相关的顶到最前。

- **为什么要它**：第一轮检索图快、召回多但排序粗；重排图准，对小批候选精算。没有它，最相关的片段可能排在第 5 位，喂给 LLM 时被截断漏掉。
- 🔍 问 AI：
  - rerank 模型和 embedding 检索有什么不同（cross-encoder vs bi-encoder）？为什么 rerank 准但慢、只能用于小批量？
  - 没有重排会出现什么具体问题？

### 9.7 自己验证检索（可复现）
起好 docker 后，上传一段音频（mock 会给固定转写并自动索引），再搜索：
```powershell
# 上传（curl.exe，国内开代理时加 --noproxy "*" 绕过代理劫持 localhost）
curl.exe -s --noproxy "*" -X POST http://localhost:8000/meetings -F "file=@音频.mp3;type=audio/mpeg"
# 跨会检索
curl.exe -s --noproxy "*" "http://localhost:8000/search?q=支付模块联调谁负责&top_k=3"
```
返回每条带 `meeting_id`（来源会议）、`text`（原文片段）、`score`（重排分）。
**mock 局限**：mock 向量只按"词是否相同"算相似、不懂近义；且 mock 转写内容固定，
多场会议看着一样。换成 `EMBEDDING_PROVIDER=dashscope` + 真实不同会议后，语义检索效果才完整。

🔍 问 AI：为什么 mock（词袋哈希）embedding 查"成本"找不到"预算"，而真实 embedding 可以？

---

## 10. 本轮新增的工程概念（已在代码里用到）✅

跑通 1-A 时落地了几个面试常考的工程概念，单独拎出来：

### 10.1 ORM（对象关系映射）
用 Python 类（`Meeting`）映射数据库表，用对象操作数据而非手写 SQL。见 [models.py](../backend/app/models.py)。
🔍 问 AI：ORM 的好处和代价（性能、N+1 查询）？`Base.metadata.create_all` 和迁移（Alembic）的区别？

### 10.2 依赖注入（FastAPI 的 Depends）
路由函数写 `db: Session = Depends(get_db)`，框架自动在请求时创建 Session、结束时关闭。见 [meetings.py](../backend/app/api/meetings.py) + [db.py](../backend/app/db.py) 的 `get_db`。
🔍 问 AI：什么是依赖注入？`Depends` + `yield` 是怎么实现「请求级资源的自动创建与释放」的？它对写测试有什么好处？

### 10.3 表模型 vs 接口 schema 的分离
`models.py`（库里怎么存）和 `schemas.py`（接口怎么对外）分开。见 [schemas.py](../backend/app/schemas.py)。
🔍 问 AI：为什么不直接把 ORM 对象返回给前端？分层（model / schema）解决了什么？`from_attributes` 做了什么？

### 10.4 用依赖覆盖写测试（dependency_overrides）
测试里把 `get_db` 换成 SQLite 会话、把入队函数换成假的，于是无需真 Postgres/Redis 就能测接口。见 [test_meetings.py](../backend/tests/test_meetings.py)。
🔍 问 AI：`app.dependency_overrides` 的原理？为什么用 SQLite 替代 Postgres 测试是合理的、又有什么局限？

### 10.5 真实排错（面试可讲）
- **代理劫持 localhost**：开了 VPN/代理后，连本地服务都被代理拦截 → 请求用 `--noproxy "*"` 绕过。引申：`http_proxy`/`no_proxy` 环境变量、代理对 localhost 的影响。
- **`docker compose up --build` 只重建了部分镜像**：构建中途 Docker 崩溃，backend 仍跑 39 小时前的旧镜像（缺新依赖）→ 单独 `docker compose build backend` 修复。引申：镜像分层缓存、如何确认容器跑的是不是最新镜像（看 image 的 CREATED 时间）。

🔍 问 AI：`no_proxy`/`--noproxy` 怎么配？怎么判断一个运行中的容器用的是哪个镜像、镜像是什么时候构建的？

---

## 全部"可问 AI"问题汇总

**异步 / 工程**
1. 同步 vs 异步处理慢请求，分别发生什么？为什么同步拖垮并发？
2. 为什么用 Redis 当任务队列？和 RabbitMQ/Kafka 的取舍？
3. 生产者-消费者模型？worker 和 web 为什么分开？
4. 任务失败的重试 / 死信 / 幂等性？
5. 前端感知完成：轮询 vs SSE vs WebSocket？

**设计模式 / 抽象**
6. 依赖倒置原则 + 面向接口编程，举换供应商的例子。
7. `ABC`/`@abstractmethod` vs `Protocol`？
8. 工厂模式解决什么？延迟 import 的好处？
9. 测试替身 mock/stub/fake 的区别？为什么测试不碰真外部服务？

**配置 / 数据库**
10. 集中式配置 vs 到处 os.getenv？pydantic-settings 的校验与优先级？
11. `@lru_cache` 怎么实现"只算一次"？
12. 何时拆关联表（一对多）？状态字段用 enum 还是字符串？
13. ORM vs 手写 SQL？数据库迁移（Alembic）是什么？

**音频 / 上传**
14. multipart/form-data 为什么用于传文件？
15. 采样率/声道/编码？为什么 ASR 要 16k 单声道？ffmpeg 命令怎么读？

**检索（护城河）⭐**
16. 什么是 RAG？为什么不能把全部资料塞进 LLM？
17. 为什么切块？块大小与 overlap 的取舍？
18. Embedding 怎么把语义变向量？余弦相似度？向量库怎么找最近邻？
19. BM25 怎么打分？擅长什么？
20. 向量 vs BM25 的短板？混合怎么融合（RRF）？
21. rerank：cross-encoder vs bi-encoder？为什么准但慢？没它会怎样？

---

> 📌 用法：检索那一节（第 9 节）是面试深挖重灾区，建议**优先攻**。一题题问、追问例子，目标是"能在白板上给人讲明白为什么要混合检索 + 重排"。
