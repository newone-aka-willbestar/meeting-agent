"""LangGraph 抽取图。

把"转写 → 结构化"拆成多个节点，每个节点单一职责：
  load_skill → extract → minutes → weekly
拆图的好处：可定位（哪步错一目了然）、每步 prompt 更简单更稳、可分别调温度、
每个节点未来在 Langfuse 里是一条独立 trace。"""

import json
from functools import partial
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.agent.prompts import (
    EXTRACTION_INSTRUCTION,
    EXTRACTION_SYSTEM,
    MINUTES_INSTRUCTION,
    WEEKLY_INSTRUCTION,
    parse_json_object,
)
from app.llm.base import LLMProvider
from app.skills.loader import load_skill


class AgentState(TypedDict, total=False):
    transcript: str
    meeting_type: str
    skill_body: str
    extraction: dict
    minutes: str
    weekly_summary: str


def _detect_meeting_type(transcript: str) -> str:
    """极简会议类型判定（够 MVP）。后续可换成 LLM 分类节点。
    用较强信号判定，避免"客户反馈"这种词把站会误判成客户会。"""
    if "评审会" in transcript or "代码评审" in transcript:
        return "review"
    if "客户会" in transcript or "客户会议" in transcript:
        return "client"
    return "standup"  # 默认按站会处理（站会/周会/晨会）


def _strip_code_fence(text: str) -> str:
    """去掉 LLM 可能给纪要套的 ```markdown ... ``` 代码块外壳。"""
    t = text.strip()
    if t.startswith("```"):
        lines = t.split("\n")
        lines = lines[1:]  # 去掉 ```markdown 那行
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        t = "\n".join(lines)
    return t.strip()


def load_skill_node(state: AgentState) -> AgentState:
    meeting_type = _detect_meeting_type(state["transcript"])
    try:
        body = load_skill(meeting_type).body
    except FileNotFoundError:
        body = ""  # 没有对应 skill 就不注入专项规则，用通用抽取
    return {"meeting_type": meeting_type, "skill_body": body}


def _as_objects(items: list, key: str) -> list[dict]:
    """归一化：LLM 有时把某类返回成字符串列表，统一成 [{key: 文本}] 的对象列表。"""
    result = []
    for it in items or []:
        if isinstance(it, str):
            result.append({key: it})
        elif isinstance(it, dict):
            result.append(it)
    return result


def extract_node(state: AgentState, llm: LLMProvider) -> AgentState:
    skill_part = ""
    if state.get("skill_body"):
        skill_part = "专项规则：\n" + state["skill_body"] + "\n"
    prompt = (
        f"{EXTRACTION_INSTRUCTION}"
        f"{skill_part}"
        f"会议转写：\n{state['transcript']}"
    )
    out = llm.complete(prompt, system=EXTRACTION_SYSTEM, temperature=0.1)
    data = parse_json_object(out)
    return {
        "extraction": {
            "decisions": _as_objects(data.get("decisions"), "content"),
            "todos": _as_objects(data.get("todos"), "content"),
            "risks": _as_objects(data.get("risks"), "description"),
            "open_questions": _as_objects(data.get("open_questions"), "content"),
        }
    }


def minutes_node(state: AgentState, llm: LLMProvider) -> AgentState:
    prompt = (
        f"{MINUTES_INSTRUCTION}"
        f"抽取结果：\n{json.dumps(state['extraction'], ensure_ascii=False)}\n\n"
        f"转写：\n{state['transcript']}"
    )
    return {"minutes": _strip_code_fence(llm.complete(prompt, temperature=0.3))}


def weekly_node(state: AgentState, llm: LLMProvider) -> AgentState:
    prompt = f"{WEEKLY_INSTRUCTION}会议纪要：\n{state['minutes']}"
    return {"weekly_summary": llm.complete(prompt, temperature=0.4)}


def build_graph(llm: LLMProvider):
    """组装并编译抽取图。llm 通过 partial 绑进各节点。"""
    builder = StateGraph(AgentState)
    builder.add_node("load_skill", load_skill_node)
    builder.add_node("extract", partial(extract_node, llm=llm))
    builder.add_node("make_minutes", partial(minutes_node, llm=llm))
    builder.add_node("make_weekly", partial(weekly_node, llm=llm))

    builder.set_entry_point("load_skill")
    builder.add_edge("load_skill", "extract")
    builder.add_edge("extract", "make_minutes")
    builder.add_edge("make_minutes", "make_weekly")
    builder.add_edge("make_weekly", END)
    return builder.compile()
