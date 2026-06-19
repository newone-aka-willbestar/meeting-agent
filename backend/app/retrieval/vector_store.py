"""向量库封装（Qdrant）：建集合、写入向量、按相似度搜索。

chunk.id 直接用作 Qdrant 里 point 的 id，两边对齐，搜索结果能回到 Postgres 取原文。"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import get_settings


class VectorStore:
    def __init__(self, dim: int, collection: str = "chunks"):
        self.client = QdrantClient(url=get_settings().qdrant_url)
        self.dim = dim
        self.collection = collection

    def ensure_collection(self) -> None:
        """集合不存在就建；若已存在但维度不一致（比如从 mock 256 维换成
        dashscope 1024 维），就重建——否则写入会维度冲突。"""
        names = {c.name for c in self.client.get_collections().collections}
        if self.collection in names:
            info = self.client.get_collection(self.collection)
            if info.config.params.vectors.size == self.dim:
                return
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            self.collection,
            vectors_config=VectorParams(size=self.dim, distance=Distance.COSINE),
        )

    def upsert(
        self, ids: list[int], vectors: list[list[float]], payloads: list[dict]
    ) -> None:
        points = [
            PointStruct(id=i, vector=v, payload=p)
            for i, v, p in zip(ids, vectors, payloads)
        ]
        self.client.upsert(self.collection, points=points)

    def search(self, vector: list[float], top_k: int = 20) -> list[tuple[int, float]]:
        """返回 [(chunk_id, 相似度分数)]，按相似度从高到低。"""
        hits = self.client.search(
            self.collection, query_vector=vector, limit=top_k
        )
        return [(int(h.id), h.score) for h in hits]
