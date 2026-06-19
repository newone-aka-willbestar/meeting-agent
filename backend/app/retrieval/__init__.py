"""检索模块入口：按配置组装 Embedder / Reranker / RetrievalService。

业务代码只调 build_retrieval_service()，背后是 mock 还是 dashscope 由环境变量决定。"""

from functools import lru_cache

from app.config import get_settings
from app.retrieval.embedder import DashScopeEmbedder, Embedder, MockEmbedder
from app.retrieval.reranker import DashScopeReranker, MockReranker, Reranker
from app.retrieval.service import RetrievalService


def _dashscope_key() -> str:
    s = get_settings()
    # embedding/rerank 的 key 优先用 dashscope_api_key，没填就退回 asr_api_key（同一个百炼 key）
    return s.dashscope_api_key or s.asr_api_key


def get_embedder() -> Embedder:
    provider = get_settings().embedding_provider.lower()
    if provider == "mock":
        return MockEmbedder()
    if provider == "dashscope":
        return DashScopeEmbedder(_dashscope_key())
    raise ValueError(f"未知 EMBEDDING_PROVIDER: {provider}（可选 mock / dashscope）")


def get_reranker() -> Reranker:
    provider = get_settings().rerank_provider.lower()
    if provider == "mock":
        return MockReranker()
    if provider == "dashscope":
        return DashScopeReranker(_dashscope_key())
    raise ValueError(f"未知 RERANK_PROVIDER: {provider}（可选 mock / dashscope）")


@lru_cache
def build_retrieval_service() -> RetrievalService:
    """进程内单例：避免每次请求都重建 Qdrant 连接、重复 ensure_collection。"""
    return RetrievalService(embedder=get_embedder(), reranker=get_reranker())
