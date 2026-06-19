"""BM25 关键词检索。

BM25 是经典的基于词频的打分算法：一个词在某段里出现得多、但在所有段里又不
常见，那它对这段就更有区分度。擅长精确命中专有名词/人名/编号——这是向量检索
容易"糊"掉的地方。

实现上用 rank_bm25 在内存里现建索引：MVP 规模（几百上千段）够用；
规模大了应换持久化倒排索引（Elasticsearch / Qdrant 稀疏向量）。这点面试要会讲。"""

from rank_bm25 import BM25Okapi

from app.retrieval.tokenize import tokenize


class BM25Index:
    def __init__(self, ids: list[int], texts: list[str]):
        self.ids = ids
        # 每段先分词，BM25Okapi 在分好词的语料上建索引
        self._bm25 = BM25Okapi([tokenize(t) for t in texts]) if texts else None

    def search(self, query: str, top_k: int = 20) -> list[tuple[int, float]]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self.ids, scores), key=lambda x: x[1], reverse=True)
        # 只保留有正分的（BM25 里 0 分表示没匹配上）
        return [(cid, float(s)) for cid, s in ranked[:top_k] if s > 0]
