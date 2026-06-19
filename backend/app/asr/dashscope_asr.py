"""阿里云通义 ASR 实现（DashScope SDK）。

用「实时识别」模型 paraformer-realtime-v2 的同步调用：直接喂本地文件路径，
返回整段文本——适合我们「本地上传一个音频文件」的场景，
不必像「录音文件识别」那样先把文件传到公网 URL。

注意：dashscope 是可选依赖，只有真用阿里云时才会被 import；
具体的返回结构会在拿到 key、真机联调时核对调整（见 transcribe 内注释）。"""

from app.asr.base import ASRProvider


class DashScopeASR(ASRProvider):
    def __init__(self, api_key: str, model: str = "paraformer-realtime-v2"):
        if not api_key:
            raise ValueError("DashScope ASR 需要 ASR_API_KEY，请在 .env 中配置")
        self.api_key = api_key
        self.model = model

    def transcribe(self, audio_path: str) -> str:
        # 延迟 import：没装 dashscope 时，只要不真正调用就不报错
        import dashscope
        from dashscope.audio.asr import Recognition

        dashscope.api_key = self.api_key

        recognition = Recognition(
            model=self.model,
            format="wav",        # 调用前会把音频统一转成 16k 单声道 wav
            sample_rate=16000,
            language_hints=["zh"],
            callback=None,       # 同步模式不需要回调
        )
        result = recognition.call(audio_path)

        # 同步模式下把所有句子的 text 拼起来。
        # 真机联调时按实际返回结构微调这里的解析。
        sentences = result.get_sentence() or []
        return "".join(s.get("text", "") for s in sentences)
