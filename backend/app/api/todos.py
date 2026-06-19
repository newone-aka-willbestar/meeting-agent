"""待办接口：创建 + 列表。这就是项目里的"任务系统"（本地 Postgres 版）。
MCP server 的 create_todo 工具最终调到这里的 POST /todos。"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Todo
from app.schemas import TodoIn, TodoOut

router = APIRouter(prefix="/todos", tags=["todos"])


@router.post("", response_model=TodoOut, status_code=201)
def create_todo(body: TodoIn, db: Session = Depends(get_db)) -> Todo:
    todo = Todo(**body.model_dump())
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@router.get("", response_model=list[TodoOut])
def list_todos(
    meeting_id: int | None = None, db: Session = Depends(get_db)
) -> list[Todo]:
    """列出待办；可按 meeting_id 过滤。"""
    stmt = select(Todo).order_by(Todo.id.desc())
    if meeting_id is not None:
        stmt = stmt.where(Todo.meeting_id == meeting_id)
    return list(db.scalars(stmt))
