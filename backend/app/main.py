"""FastAPI 应用入口。

挂载：健康检查 + 会议相关路由（上传/列表/详情）。
启动时建表（MVP 做法；生产用 Alembic 迁移）。"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import meetings, search
from app.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时执行一次：确保数据库表已建好
    init_db()
    yield
    # 这里可放关闭时的清理逻辑（目前无）


app = FastAPI(title="Meeting Intelligence Agent", version="0.1.0", lifespan=lifespan)

# 挂载路由：会议（/meetings/...）+ 检索（/search）
app.include_router(meetings.router)
app.include_router(search.router)


@app.get("/health")
def health() -> dict:
    """健康检查：编排靠它判断服务是否就绪。保持极简——不查数据库、不依赖外部服务。"""
    return {"status": "ok"}


@app.get("/")
def root() -> dict:
    """根路由，方便手动验证时一眼看到服务名。"""
    return {"service": "meeting-agent-backend", "docs": "/docs"}
