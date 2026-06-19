"""抽取 Agent 各节点的 prompt 模板与 JSON 解析工具。

把 prompt 单独放，便于调优、也便于 eval 对照。"""

import json
import re

EXTRACTION_SYSTEM = "你是严谨的会议信息抽取助手，只输出 JSON，不要多余解释。"

EXTRACTION_INSTRUCTION = (
    "请从会议转写中抽取四类信息，输出严格的 JSON，键为："
    "decisions（决策）、todos（待办，每项含 assignee/content/ddl）、"
    "risks（风险，每项含 description/owner）、open_questions（待议）。"
    "找不到的类别给空数组，不要编造。\n"
)

MINUTES_INSTRUCTION = (
    "请根据下面的抽取结果和转写，生成一份结构清晰的中文【会议纪要】（markdown），"
    "分『决策 / 待办 / 风险』小节。\n"
)

WEEKLY_INSTRUCTION = (
    "请把这场会议浓缩成一段不超过 80 字的【周报】摘要，"
    "突出关键决策、主要待办负责人、需关注的风险。\n"
)


def parse_json_object(text: str) -> dict:
    """从 LLM 输出里稳健地取出 JSON 对象：截取第一个 { 到最后一个 }。
    兼容模型偶尔包 ```json 代码块或加前后缀的情况。"""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {"decisions": [], "todos": [], "risks": [], "open_questions": []}
    return json.loads(match.group(0))
