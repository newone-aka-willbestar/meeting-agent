# Phase 2 逐步学习手册 · 抽取 Agent + 自写 MCP

> 标记：✅ 已实现并验证；🚧 已设计/即将写；⭐ 面试优先级最高。随进度更新。

---

## 目录
- [0. Phase 2 是干嘛的](#0-phase-2-是干嘛的)
- [1. LLM 抽象层 ✅](#1-llm-抽象层-)
- [2. LangGraph 抽取图 ✅⭐](#2-langgraph-抽取图-)
- [3. 为什么拆成图而不是一个 prompt ⭐](#3-为什么拆成图而不是一个-prompt-)
- [4. Skill 注入：会议类型驱动抽取 ✅](#4-skill-注入会议类型驱动抽取-)
- [5. 稳健解析 LLM 的 JSON 输出 ✅](#5-稳健解析-llm-的-json-输出-)
- [6. 抽取结果落库（JSON 列）✅](#6-抽取结果落库json-列-)
- [7. 自写 MCP server 🚧⭐](#7-自写-mcp-server-)
- [可问 AI 问题汇总](#可问-ai问题汇总)

---

## 0. Phase 2 是干嘛的

把"转写文本"变成"结构化会议成果"：**决策 / 待办 / 风险 / 待议**，再生成**纪要**和**周报**；
并自写一个 **MCP server**，把"创建待办/查历史/发纪要"暴露成标准工具，agent 经它调用，
还能被 Claude Desktop 直接连上。

两块：**2-A 抽取 Agent（LangGraph 图）** + **2-B 自写 MCP server**。

LLM 选型：**通义 Qwen（DashScope）**，复用百炼 key；先用 mock 跑通。

---

## 1. LLM 抽象层 ✅

> [app/llm/](../backend/app/llm/)：base（接口）/ mock / dashscope_llm（通义）/ 工厂。

和 ASR、Embedder 同一套思路：业务只依赖 `LLMProvider.complete(prompt, system, temperature)`，
背后是 mock 还是通义由 `LLM_PROVIDER` 决定。`MockLLM` 按 prompt 里的任务词（抽取/纪要/周报）
返回不同写死结果，能驱动整张图跑通、也让测试稳定。

🔍 问 AI：
- `temperature` 是什么？为什么抽取用低温度、周报可略高？
- 为什么把 LLM 也做成可替换的抽象？多家模型/降级备用有什么价值？

---

## 2. LangGraph 抽取图 ✅⭐

> [app/agent/graph.py](../backend/app/agent/graph.py)：StateGraph + 四个节点。

图结构：
```
load_skill → extract → make_minutes → make_weekly → END
```
- **State（AgentState）**：一个 TypedDict，节点间传递的"共享黑板"——transcript / meeting_type /
  skill_body / extraction / minutes / weekly_summary。每个节点读它、写回部分字段。
- **节点 = 纯函数**：输入 state，返回要更新的字段。LLM 通过 `partial(node, llm=llm)` 绑进节点。
- **边**：定义执行顺序；这里是一条直线（后续可加分支/条件边）。

🔍 问 AI：
- LangGraph 的 State 是怎么在节点间流转、合并的？为什么用 TypedDict？
- `StateGraph` / `add_node` / `add_edge` / `set_entry_point` / `compile` 各是什么？
- 节点名为什么不能和 state 的键重名？（我们踩过：node "minutes" 撞了 key "minutes"）
- 什么时候需要"条件边"（按上一步结果决定走哪个节点）？

---

## 3. 为什么拆成图而不是一个 prompt ⭐

面试核心问题。一个巨型 prompt"既抽取又写纪要又写周报"的问题：

1. **难定位**：错了不知道是抽取错还是纪要错。拆成节点后，能精确到某一步。
2. **每步更稳**：单一职责的小 prompt 比大杂烩可靠，幻觉更少。
3. **可分别调**：抽取要低温度求准；周报可高一点求顺。一个 prompt 没法分开调。
4. **可观测/可重试**：每个节点是独立单元，未来在 Langfuse 里是一条独立 trace，能单独重跑。
5. **可演进**：要加"会议分类""多轮校验"节点，往图里插一个节点即可，不动其它。

🔍 问 AI：把"抽取+纪要+周报"合成一个 prompt，可能出现哪些具体故障？拆开怎么缓解？

---

## 4. Skill 注入：会议类型驱动抽取 ✅

`load_skill` 节点先判定会议类型（站会/评审会/客户会），加载对应 [SKILL.md](../skills/standup.md)，
把其正文拼进抽取 prompt（见 Phase 0/1 的 skill 演示）。不同会议类型抽取重点不同，
用可插拔的 skill 外置规则，而不是写死成 prompt 里的一堆 if-else。

🔍 问 AI：为什么"不同会议类型用不同 rubric"，而不是一个通用抽取 prompt 走天下？

---

## 5. 稳健解析 LLM 的 JSON 输出 ✅

> [app/agent/prompts.py](../backend/app/agent/prompts.py) 的 `parse_json_object`。

LLM 偶尔会在 JSON 前后加解释、或包 ```json 代码块。我们用正则截取"第一个 { 到最后一个 }"，
再 `json.loads`，比直接 parse 整段稳。解析失败兜底返回空结构，不让一步坏掉整条流水线。

🔍 问 AI：
- 让 LLM 稳定输出 JSON 有哪些手段（prompt 约束、JSON mode、function calling、后处理）？各自取舍？
- 为什么"解析失败要兜底"而不是直接抛错？

---

## 6. 抽取结果落库（JSON 列）✅

> [models.py](../backend/app/models.py) 的 `Extraction` 表；worker 里 upsert。

决策/待办/风险/待议是"长度不定的列表"，用 **JSON 列**存最省事（一对多关系不必拆四张表）。
纪要/周报是长文本，用 Text。一场会议一条（meeting_id 唯一）。
查询接口：`GET /meetings/{id}/extraction`。

🔍 问 AI：
- 什么时候该用 JSON 列、什么时候该规范化成关联表？JSON 列的查询/索引代价？
- "一对一"关系（meeting↔extraction）在表设计上怎么体现（唯一外键）？

---

## 7. 自写 MCP server 🚧⭐

下一步 2-B。MCP（Model Context Protocol）是个**标准协议**，把能力暴露成 tools，
任何兼容的 client（你的 agent、Claude Desktop）都能发现并调用。

计划工具：`创建待办` / `查历史会议` / `发纪要`（先写本地 Postgres）。

🔍 提前可问 AI：
- MCP 是什么、解决什么问题？和"直接把函数给 agent"比强在哪？
- MCP 的 server/client 怎么握手、agent 怎么发现工具（tool discovery）？
- 为什么同一个 server 能被 Claude Desktop 这种通用 client 连上？

---

## 可问 AI 问题汇总

**LLM/Agent**
1. temperature 的作用？抽取 vs 周报怎么设？
2. 为什么 LLM 也要做可替换抽象？
3. 让 LLM 稳定输出 JSON 的几种手段与取舍？

**LangGraph**
4. State 怎么在节点间流转/合并？为什么用 TypedDict？
5. StateGraph 的核心 API？节点名为何不能撞 state 键？
6. 什么时候用条件边/循环？

**架构论证（面试重点）**
7. 为什么拆成图而不是一个 prompt？合并会有哪些故障？
8. 抽错/漏抽时怎么定位是哪个节点的问题？
9. 为什么不同会议类型用不同 skill？

**建模**
10. JSON 列 vs 关联表的取舍？一对一怎么建？

**MCP（护城河）**
11. MCP 是什么、比"直接给函数"强在哪？
12. tool discovery 和协议握手大意？
13. 为何能被 Claude Desktop 连上？
