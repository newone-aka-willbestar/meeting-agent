"""验证 ASR 抽象层：工厂能按配置返回 mock 实现，且 mock 能产出文本。
不调用真 ASR，所以 CI 里也能跑。"""

from app.asr import get_asr_provider
from app.asr.base import ASRProvider
from app.asr.mock import MockASR


def test_factory_returns_mock_by_default(monkeypatch):
    # 强制 provider=mock（不依赖外部 .env），并清掉配置缓存
    monkeypatch.setenv("ASR_PROVIDER", "mock")
    from app.config import get_settings

    get_settings.cache_clear()

    provider = get_asr_provider()
    assert isinstance(provider, ASRProvider)   # 拿到的是抽象类型
    assert isinstance(provider, MockASR)       # 具体是 mock


def test_mock_transcribe_returns_text():
    text = MockASR().transcribe("任意路径都行.wav")
    assert isinstance(text, str)
    assert len(text) > 0
