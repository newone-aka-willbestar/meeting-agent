"""测试 LangGraph 抽取图：用 MockLLM 跑完整图，验证四类抽取 + 纪要 + 周报。"""

from app.agent import run_extraction_agent
from app.agent.graph import _detect_meeting_type
from app.llm.mock import MockLLM

TRANSCRIPT = (
    "大家好，今天的周会开始。我们决定推迟新版本到下周三。"
    "张伟负责周五前完成支付模块联调。第三方接口稳定性有风险。"
)


def test_detect_meeting_type_defaults_standup():
    assert _detect_meeting_type("今天的周会") == "standup"
    assert _detect_meeting_type("本次代码评审会") == "review"


def test_graph_produces_all_outputs():
    result = run_extraction_agent(TRANSCRIPT, llm=MockLLM())

    # 会议类型识别 + skill 加载
    assert result["meeting_type"] == "standup"
    # 四类抽取齐全
    ext = result["extraction"]
    assert set(ext) == {"decisions", "todos", "risks", "open_questions"}
    assert ext["todos"][0]["assignee"] == "张伟"
    # 生成式产出
    assert "纪要" in result["minutes"]
    assert result["weekly_summary"].startswith("本周")
