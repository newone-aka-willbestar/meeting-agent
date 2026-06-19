"""会议相关接口：上传、列表、详情。

注意路由前缀是 /meetings（不带 /api）。前端发的是 /api/meetings，
由 Vite 开发代理把 /api 前缀剥掉再转发到这里（见 frontend/vite.config.js）。"""

import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import Extraction, Meeting, MeetingStatus
from app.queue import enqueue_transcription
from app.schemas import ExtractionOut, MeetingOut

router = APIRouter(prefix="/meetings", tags=["meetings"])
settings = get_settings()


@router.post("", response_model=MeetingOut, status_code=201)
def upload_meeting(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> Meeting:
    """上传音频：落盘 → 建 meeting(pending) → 入队 → 立刻返回（不等转写）。"""
    os.makedirs(settings.storage_dir, exist_ok=True)

    # 用随机名落盘，避免同名覆盖；保留原扩展名
    ext = os.path.splitext(file.filename or "")[1]
    saved_name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.storage_dir, saved_name)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    meeting = Meeting(
        filename=file.filename or saved_name,
        audio_path=path,
        status=MeetingStatus.pending.value,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)  # 拿回数据库生成的 id / created_at

    # 入队后由后台 worker 异步转写
    enqueue_transcription(meeting.id)
    return meeting


@router.get("", response_model=list[MeetingOut])
def list_meetings(db: Session = Depends(get_db)) -> list[Meeting]:
    """会议列表，最新的在前。"""
    return list(db.scalars(select(Meeting).order_by(Meeting.id.desc())))


@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)) -> Meeting:
    """查单场会议（前端轮询它看 status 是否变 done）。"""
    meeting = db.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="meeting not found")
    return meeting


@router.get("/{meeting_id}/extraction", response_model=ExtractionOut)
def get_extraction(meeting_id: int, db: Session = Depends(get_db)) -> Extraction:
    """查抽取结果（决策/待办/风险/待议 + 纪要 + 周报）。转写后异步生成，可能稍晚于 done。"""
    ext = db.scalar(select(Extraction).where(Extraction.meeting_id == meeting_id))
    if ext is None:
        raise HTTPException(status_code=404, detail="extraction not ready")
    return ext
