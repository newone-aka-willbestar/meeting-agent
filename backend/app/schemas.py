"""API 的出入参模型（Pydantic schema）。

和 models.py（数据库表）分开：表是『库里怎么存』，schema 是『接口怎么对外』。
两者解耦后，能自由控制对外暴露哪些字段、字段叫什么，而不被表结构绑死。"""

import datetime

from pydantic import BaseModel, ConfigDict


class MeetingOut(BaseModel):
    """返回给前端的会议信息。"""

    # from_attributes 让 Pydantic 能直接从 ORM 对象（属性）读数据
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: str
    transcript: str | None = None
    created_at: datetime.datetime


class ExtractionOut(BaseModel):
    """抽取 Agent 的结构化产出。"""

    model_config = ConfigDict(from_attributes=True)

    meeting_id: int
    meeting_type: str
    decisions: list
    todos: list
    risks: list
    open_questions: list
    minutes: str | None = None
    weekly_summary: str | None = None
