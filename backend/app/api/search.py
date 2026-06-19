"""跨会检索接口：GET /search?q=...

前端发 /api/search，经 Vite 代理剥掉 /api 到这里。
返回 Top-K 相关片段，每条带来源会议 id，实现"上次关于 X 我们定了啥"。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.retrieval import build_retrieval_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(
    q: str = Query(..., min_length=1, description="查询词"),
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> dict:
    service = build_retrieval_service()
    results = service.search(db, q, top_k=top_k)
    return {"query": q, "results": results}
