"""测试切块 / 分词 / mock embedding（都不依赖外部服务）。"""

import math

from app.retrieval.chunking import chunk_text, split_sentences
from app.retrieval.embedder import MockEmbedder
from app.retrieval.tokenize import tokenize


def test_split_sentences_by_chinese_punctuation():
    sents = split_sentences("第一句。第二句！第三句？")
    assert sents == ["第一句。", "第二句！", "第三句？"]


def test_chunk_text_respects_max_chars_and_overlaps():
    text = "。".join(f"句子{i}" for i in range(1, 30)) + "。"
    chunks = chunk_text(text, max_chars=20, overlap=5)
    assert len(chunks) > 1                       # 长文本被切成多块
    assert all(len(c) <= 20 + 20 for c in chunks)  # 每块大致不超长（含 overlap 余量）


def test_tokenize_chinese():
    tokens = tokenize("支付模块的联调")
    assert isinstance(tokens, list)
    assert len(tokens) >= 2          # 至少被切成几个词


def test_mock_embedder_dim_and_normalized():
    emb = MockEmbedder()
    vecs = emb.embed(["支付模块联调", "新版本上线时间"])
    assert len(vecs) == 2
    assert all(len(v) == emb.dim for v in vecs)
    # L2 归一化后模长应约等于 1
    norm = math.sqrt(sum(x * x for x in vecs[0]))
    assert abs(norm - 1.0) < 1e-6


def test_mock_embedder_similar_text_closer():
    """共享词多的两段，余弦相似度应更高——证明 mock 向量有区分力。"""
    emb = MockEmbedder()
    base = emb.embed_one("支付模块的联调工作")
    similar = emb.embed_one("支付模块联调")
    different = emb.embed_one("天气预报明天下雨")

    def cosine(a, b):
        return sum(x * y for x, y in zip(a, b))  # 已归一化，点积即余弦

    assert cosine(base, similar) > cosine(base, different)
