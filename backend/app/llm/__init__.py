"""LLM 模块入口：按配置返回实现。"""

from app.config import get_settings
from app.llm.base import LLMProvider
from app.llm.mock import MockLLM


def get_llm() -> LLMProvider:
    s = get_settings()
    provider = s.llm_provider.lower()
    if provider == "mock":
        return MockLLM()
    if provider == "dashscope":
        from app.llm.dashscope_llm import DashScopeLLM

        # key 优先级：llm_api_key > dashscope_api_key > asr_api_key（都是百炼 key）
        key = s.llm_api_key or s.dashscope_api_key or s.asr_api_key
        return DashScopeLLM(api_key=key, model=s.llm_model)
    raise ValueError(f"未知 LLM_PROVIDER: {provider}（可选 mock / dashscope）")
