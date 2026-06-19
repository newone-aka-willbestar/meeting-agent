"""ASR 模块入口：一个工厂函数，按配置返回对应的 ASR 实现。

业务代码只调 get_asr_provider()，拿到的是 ASRProvider 抽象类型，
完全不知道背后是 mock 还是 dashscope——这就是抽象层的价值。"""

from app.asr.base import ASRProvider
from app.asr.mock import MockASR
from app.config import get_settings


def get_asr_provider() -> ASRProvider:
    settings = get_settings()
    provider = settings.asr_provider.lower()

    if provider == "mock":
        return MockASR()
    if provider == "dashscope":
        # 延迟 import：用 mock 时不必依赖 dashscope SDK
        from app.asr.dashscope_asr import DashScopeASR

        return DashScopeASR(api_key=settings.asr_api_key)

    raise ValueError(f"未知的 ASR_PROVIDER: {settings.asr_provider}（可选 mock / dashscope）")
