"""通义 Qwen（DashScope Generation）实现。返回结构待拿到 key 真机校对。"""

from app.llm.base import LLMProvider


class DashScopeLLM(LLMProvider):
    def __init__(self, api_key: str, model: str = "qwen-plus"):
        if not api_key:
            raise ValueError("DashScope LLM 需要 key（dashscope/asr/llm 任一）")
        self.api_key = api_key
        self.model = model

    def complete(self, prompt: str, system: str = "", temperature: float = 0.2) -> str:
        from dashscope import Generation

        messages = [
            {"role": "system", "content": system or "你是严谨的会议纪要助手。"},
            {"role": "user", "content": prompt},
        ]
        resp = Generation.call(
            model=self.model,
            messages=messages,
            result_format="message",
            temperature=temperature,
            api_key=self.api_key,
        )
        return resp.output.choices[0].message.content
