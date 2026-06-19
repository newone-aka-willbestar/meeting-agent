"""RRF（Reciprocal Rank Fusion，倒数排名融合）。

把多路检索（向量、BM25）的排名合并成一个。核心思想：只看"名次"不看各自的
原始分数（两路分数量纲不同，没法直接相加），某文档在各路里名次越靠前，
贡献的分越高：score += 1 / (k + rank)。k 是平滑常数，常取 60。

好处：简单、稳健、不需要调权重，是混合检索里最常用的融合法之一。"""


def rrf_fuse(
    rankings: list[list[int]], k: int = 60, top_k: int = 20
) -> list[int]:
    """rankings：每一路的 chunk_id 有序列表（已按相关度从高到低）。
    返回融合后的 chunk_id 列表。"""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(ranking):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [chunk_id for chunk_id, _ in fused[:top_k]]
