"""RetrievalService：把切块/向量/BM25/RRF/重排串成两个动作。

- index_meeting：转写完成后，把文本切块、入库(Postgres)、向量化(Qdrant)。
- search：一次查询走完 向量+BM25 → RRF 融合 → 重排 → Top-K。

BM25 语料每次查询从 Postgres 现加载（MVP 规模够用）。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Chunk
from app.retrieval.bm25 import BM25Index
from app.retrieval.chunking import chunk_text
from app.retrieval.embedder import Embedder
from app.retrieval.fusion import rrf_fuse
from app.retrieval.reranker import Reranker
from app.retrieval.vector_store import VectorStore


class RetrievalService:
    def __init__(self, embedder: Embedder, reranker: Reranker):
        self.embedder = embedder
        self.reranker = reranker
        self.vector_store = VectorStore(dim=embedder.dim)
        self.vector_store.ensure_collection()

    def index_meeting(self, db: Session, meeting_id: int, transcript: str) -> int:
        """切块 → 存 Postgres → 向量化 → 写 Qdrant。返回切了多少块。"""
        texts = chunk_text(transcript)
        if not texts:
            return 0

        chunks = [Chunk(meeting_id=meeting_id, seq=i, text=t) for i, t in enumerate(texts)]
        db.add_all(chunks)
        db.commit()
        for c in chunks:
            db.refresh(c)  # 拿回数据库生成的 id

        vectors = self.embedder.embed([c.text for c in chunks])
        self.vector_store.upsert(
            ids=[c.id for c in chunks],
            vectors=vectors,
            payloads=[{"meeting_id": meeting_id, "text": c.text} for c in chunks],
        )
        return len(chunks)

    def search(
        self, db: Session, query: str, top_k: int = 5, candidates: int = 20
    ) -> list[dict]:
        """混合检索：向量 + BM25 → RRF → 重排 → Top-K。"""
        # 1) 向量召回
        qvec = self.embedder.embed_one(query)
        vec_ids = [cid for cid, _ in self.vector_store.search(qvec, top_k=candidates)]

        # 2) BM25 召回（语料从库里现加载）
        all_chunks = list(db.scalars(select(Chunk)))
        bm25 = BM25Index([c.id for c in all_chunks], [c.text for c in all_chunks])
        bm_ids = [cid for cid, _ in bm25.search(query, top_k=candidates)]

        # 3) RRF 融合两路
        fused_ids = rrf_fuse([vec_ids, bm_ids], top_k=candidates)

        # 4) 重排（对融合后的候选精排）
        id2chunk = {c.id: c for c in all_chunks}
        docs = [(cid, id2chunk[cid].text) for cid in fused_ids if cid in id2chunk]
        reranked = self.reranker.rerank(query, docs, top_k=top_k)

        # 5) 组装结果（带来源会议 id，支持跨会检索）
        results = []
        for chunk_id, score in reranked:
            c = id2chunk[chunk_id]
            results.append(
                {
                    "chunk_id": chunk_id,
                    "meeting_id": c.meeting_id,
                    "text": c.text,
                    "score": score,
                }
            )
        return results
