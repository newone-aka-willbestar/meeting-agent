"""数据库表模型（ORM）。

Phase 1 只有一张 meeting 表：存一场会议的元数据、状态、转写结果。
（待办/决策/风险等抽取结果是 Phase 2 的事，到时再加表。）"""

import datetime
import enum

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class MeetingStatus(str, enum.Enum):
    """会议处理状态机：上传后在这几个状态间流转。"""

    pending = "pending"        # 已上传，排队等转写
    processing = "processing"  # worker 正在转写
    done = "done"              # 转写完成
    failed = "failed"          # 转写出错


class Meeting(Base):
    __tablename__ = "meeting"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 用户上传时的原始文件名（仅展示用）
    filename: Mapped[str] = mapped_column(String(255))
    # 落盘后的实际路径（worker 据此读音频）
    audio_path: Mapped[str] = mapped_column(String(512))
    # 状态：存字符串，默认 pending
    status: Mapped[str] = mapped_column(String(20), default=MeetingStatus.pending.value)
    # 转写文本：转写完成前为空
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 出错信息：失败时记录原因，方便排查
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 创建时间：用数据库的 now() 自动填
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Chunk(Base):
    """转写文本切块后的一段。BM25 语料来自这张表；同一段也会向量化进 Qdrant。
    chunk.id 同时作为 Qdrant 里向量的 point id，两边对齐。"""

    __tablename__ = "chunk"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 属于哪场会议（跨会检索时用它定位来源）
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meeting.id"), index=True)
    # 在该会议里的第几段（保留顺序，便于"点回原话上下文"）
    seq: Mapped[int] = mapped_column()
    text: Mapped[str] = mapped_column(Text)


class Extraction(Base):
    """抽取 Agent 的产出：一场会议一条。结构化结果用 JSON 列存。"""

    __tablename__ = "extraction"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meeting.id"), unique=True, index=True
    )
    meeting_type: Mapped[str] = mapped_column(String(32), default="")
    # 四类抽取结果，各是一个列表（每项是 dict）
    decisions: Mapped[list] = mapped_column(JSON, default=list)
    todos: Mapped[list] = mapped_column(JSON, default=list)
    risks: Mapped[list] = mapped_column(JSON, default=list)
    open_questions: Mapped[list] = mapped_column(JSON, default=list)
    # 生成式产出
    minutes: Mapped[str | None] = mapped_column(Text, nullable=True)
    weekly_summary: Mapped[str | None] = mapped_column(Text, nullable=True)


class Todo(Base):
    """待办（即"任务系统"，本地版）。抽取 Agent 自动落库，MCP create_todo 也写这里。"""

    __tablename__ = "todo"

    id: Mapped[int] = mapped_column(primary_key=True)
    # 来源会议（手动/外部创建的可为空）
    meeting_id: Mapped[int | None] = mapped_column(
        ForeignKey("meeting.id"), nullable=True, index=True
    )
    assignee: Mapped[str] = mapped_column(String(64))
    content: Mapped[str] = mapped_column(Text)
    ddl: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="open")   # open / done
    source: Mapped[str] = mapped_column(String(16), default="manual")  # agent / mcp / manual
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
