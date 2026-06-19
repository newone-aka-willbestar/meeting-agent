"""LLM 统一接口。和 ASR/Embedder 一样：业务只依赖抽象，不绑死某家模型。"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, system: str = "", temperature: float = 0.2) -> str:
        """给定 system + user prompt，返回模型生成的文本。
        temperature 低=更确定（抽取用），高=更发散（周报可略高）。"""
        raise NotImplementedError
