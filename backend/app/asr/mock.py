"""Mock ASR：返回一段写死的假转写。

用途：CI / 单元测试 / 没有 API key 时跑通整条流水线。
它不读音频内容，只证明「上传→转写→入库→检索」的管道是通的。"""

from app.asr.base import ASRProvider

# 一段假的会议转写，内容刻意包含「决策/待办/风险」字样，方便后续抽取阶段也能用它练手
_FAKE_TRANSCRIPT = (
    "大家好，今天的周会开始。第一项，关于新版本上线时间，"
    "我们决定推迟到下周三发布。第二项，张伟负责在周五前完成支付模块的联调。"
    "另外有个风险，第三方接口的稳定性还没验证，可能影响进度，需要持续关注。"
)


class MockASR(ASRProvider):
    def transcribe(self, audio_path: str) -> str:
        # 故意忽略 audio_path，直接返回假数据
        return _FAKE_TRANSCRIPT
