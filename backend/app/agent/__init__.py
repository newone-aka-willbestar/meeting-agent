"""抽取 Agent 入口。worker 转写完成后调 run_extraction_agent。"""

from app.agent.graph import build_graph
from app.llm import get_llm
from app.llm.base import LLMProvider


def run_extraction_agent(transcript: str, llm: LLMProvider | None = None) -> dict:
    """跑完整张图，返回 {meeting_type, extraction, minutes, weekly_summary}。"""
    graph = build_graph(llm or get_llm())
    return graph.invoke({"transcript": transcript})
