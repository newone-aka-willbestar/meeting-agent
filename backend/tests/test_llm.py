"""测试 LLM 抽象 + Mock：工厂返回 mock，mock 能按任务返回不同内容。"""

import json

from app.llm import get_llm
from app.llm.base import LLMProvider
from app.llm.mock import MockLLM


def test_factory_returns_mock(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    from app.config import get_settings

    get_settings.cache_clear()
    llm = get_llm()
    assert isinstance(llm, LLMProvider)
    assert isinstance(llm, MockLLM)


def test_mock_extraction_returns_valid_json():
    out = MockLLM().complete("请抽取 决策/待办/风险/待议：……")
    data = json.loads(out)
    assert "todos" in data
    assert data["todos"][0]["assignee"] == "张伟"


def test_mock_routes_by_task_keyword():
    llm = MockLLM()
    assert "纪要" in llm.complete("请生成会议纪要：……")
    assert llm.complete("请生成本周周报：……").startswith("本周")
