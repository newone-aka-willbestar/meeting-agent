"""数据库表模型（ORM）。

Phase 1 只有一张 meeting 表：存一场会议的元数据、状态、转写结果。
（待办/决策/风险等抽取结果是 Phase 2 的事，到时再加表。）"""

import datetime
import enum

from sqlalchemy import DateTime, String, Text, func
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
