"""Mock LLM：不调真模型，按 prompt 里的任务关键词返回写死结果。

它能区分三种任务（抽取 / 纪要 / 周报），所以能驱动整张 LangGraph 图跑通、
也能让测试稳定。返回的抽取 JSON 刻意和 mock 转写内容对齐，演示才连贯。"""

import json

from app.llm.base import LLMProvider

# 和 MockASR 的假转写内容对齐
_FAKE_EXTRACTION = {
    "decisions": [{"content": "新版本上线时间推迟到下周三发布"}],
    "todos": [
        {"assignee": "张伟", "content": "在周五前完成支付模块的联调", "ddl": "周五"}
    ],
    "risks": [
        {"description": "第三方接口稳定性还未验证，可能影响进度", "owner": None}
    ],
    "open_questions": [],
}

_FAKE_MINUTES = (
    "# 会议纪要\n\n"
    "## 决策\n- 新版本上线推迟到下周三发布\n\n"
    "## 待办\n- 张伟：周五前完成支付模块联调\n\n"
    "## 风险\n- 第三方接口稳定性未验证，需持续关注\n"
)

_FAKE_WEEKLY = "本周周会决定新版本推迟到下周三上线；支付模块联调由张伟周五前完成；需关注第三方接口稳定性风险。"


class MockLLM(LLMProvider):
    def complete(self, prompt: str, system: str = "", temperature: float = 0.2) -> str:
        text = prompt + system
        if "周报" in text:
            return _FAKE_WEEKLY
        if "纪要" in text:
            return _FAKE_MINUTES
        # 默认当作抽取任务，返回 JSON 字符串
        return json.dumps(_FAKE_EXTRACTION, ensure_ascii=False)
