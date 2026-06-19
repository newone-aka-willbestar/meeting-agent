"""Embedder（向量化器）：把文本变成向量，语义相近的文本向量也相近。

和 ASR 一样做成抽象接口 + 多实现：
- MockEmbedder：纯 Python 哈希词袋，确定性、轻量，给测试/CI 和"先跑通"用；
- DashScopeEmbedder：阿里云 text-embedding，真实语义向量（需 key、联网）。
collection 的维度要和 embedder.dim 一致，所以每个实现都声明自己的 dim。"""

import hashlib
import math
from abc import ABC, abstractmethod

from app.retrieval.tokenize import tokenize


class Embedder(ABC):
    dim: int  # 向量维度，子类声明

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量把文本转成向量。"""
        raise NotImplementedError

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


class MockEmbedder(Embedder):
    """把分词后的词哈希到固定维度的"词袋"向量，再做 L2 归一化。
    共享词越多，向量越接近——足够让检索管道和测试跑出合理结果。
    它不懂真正的语义（近义词不算相近），真语义留给 DashScope。"""

    dim = 256

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(t) for t in texts]

    def _vectorize(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in tokenize(text):
            # 用 md5 把词稳定地映射到某一维上（同一个词永远落同一维）
            bucket = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self.dim
            vec[bucket] += 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]


class DashScopeEmbedder(Embedder):
    """阿里云通义 text-embedding。返回结构待拿到 key 后真机校对。"""

    dim = 1024  # text-embedding-v3 的维度

    def __init__(self, api_key: str, model: str = "text-embedding-v3"):
        if not api_key:
            raise ValueError("DashScope embedding 需要 dashscope_api_key")
        self.api_key = api_key
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        from dashscope import TextEmbedding

        resp = TextEmbedding.call(model=self.model, input=texts, api_key=self.api_key)
        # output.embeddings 里每项带 text_index，按它排回原顺序
        items = sorted(resp.output["embeddings"], key=lambda e: e["text_index"])
        return [item["embedding"] for item in items]
