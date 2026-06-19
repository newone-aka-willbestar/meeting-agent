"""测试 BM25 / RRF / MockReranker（纯算法，不依赖 Qdrant 或网络）。"""

from app.retrieval.bm25 import BM25Index
from app.retrieval.fusion import rrf_fuse
from app.retrieval.reranker import MockReranker

CORPUS = {
    1: "我们决定推迟新版本上线到下周三",
    2: "张伟负责支付模块的联调工作",
    3: "第三方接口稳定性存在风险",
    4: "明天天气晴朗适合出游",
}


def test_bm25_hits_keyword():
    idx = BM25Index(list(CORPUS), list(CORPUS.values()))
    hits = idx.search("支付模块", top_k=3)
    assert hits  # 有结果
    assert hits[0][0] == 2  # 命中"支付模块的联调"那段排第一


def test_bm25_empty_corpus():
    assert BM25Index([], []).search("任何词") == []


def test_rrf_prefers_items_ranked_high_in_both():
    # chunk 7 在两路里都靠前 → 融合后应排第一
    vec_ranking = [7, 3, 1]
    bm_ranking = [7, 1, 9]
    fused = rrf_fuse([vec_ranking, bm_ranking], top_k=5)
    assert fused[0] == 7


def test_mock_reranker_orders_by_overlap():
    docs = [(c_id, text) for c_id, text in CORPUS.items()]
    ranked = MockReranker().rerank("支付模块联调", docs, top_k=2)
    assert ranked[0][0] == 2          # 词重叠最高的排第一
    assert len(ranked) == 2           # 截断到 top_k
    assert ranked[0][1] >= ranked[1][1]  # 分数降序
