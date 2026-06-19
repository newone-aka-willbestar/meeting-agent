"""Reranker（重排器）：对候选段做精细打分、重新排序。

第一轮混合检索图快、召回多但排序粗；重排对这一小批候选用更强的模型精算，
把最相关的顶到最前。没有它，最相关的片段可能排在第 5 位、被 Top-K 截断漏掉。

- MockReranker：用 query 和候选的"词重叠率"近似相关度，轻量、给测试/先跑通用；
- DashScopeReranker：阿里云 gte-rerank，真正的 cross-encoder 重排（需 key）。"""

from abc import ABC, abstractmethod

from app.retrieval.tokenize import tokenize


class Reranker(ABC):
    @abstractmethod
    def rerank(
        self, query: str, docs: list[tuple[int, str]], top_k: int
    ) -> list[tuple[int, float]]:
        """docs：[(chunk_id, 文本)]；返回 [(chunk_id, 相关度分)]，按分从高到低，截断到 top_k。"""
        raise NotImplementedError


class MockReranker(Reranker):
    def rerank(
        self, query: str, docs: list[tuple[int, str]], top_k: int
    ) -> list[tuple[int, float]]:
        q = set(tokenize(query))
        scored: list[tuple[int, float]] = []
        for chunk_id, text in docs:
            t = set(tokenize(text))
            # Jaccard 相似度：交集 / 并集
            overlap = len(q & t) / (len(q | t) or 1)
            scored.append((chunk_id, overlap))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


class DashScopeReranker(Reranker):
    def __init__(self, api_key: str, model: str = "gte-rerank"):
        if not api_key:
            raise ValueError("DashScope rerank 需要 dashscope_api_key")
        self.api_key = api_key
        self.model = model

    def rerank(
        self, query: str, docs: list[tuple[int, str]], top_k: int
    ) -> list[tuple[int, float]]:
        from dashscope import TextReRank

        resp = TextReRank.call(
            model=self.model,
            query=query,
            documents=[d[1] for d in docs],
            top_n=top_k,
            return_documents=False,
            api_key=self.api_key,
        )
        # results 每项含原 documents 里的 index 和 relevance_score
        return [
            (docs[r["index"]][0], float(r["relevance_score"]))
            for r in resp.output["results"]
        ]
