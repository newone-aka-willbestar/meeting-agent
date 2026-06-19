"""转写 worker：独立进程，循环从 Redis 取任务并转写。

跑法：python -m app.worker （docker-compose 里单独起一个 worker 服务）
它和 web 进程分开，正是异步解耦的关键：慢转写不占用处理 HTTP 的进程。"""

import logging

from app.asr import get_asr_provider
from app.db import SessionLocal, init_db
from app.models import Meeting, MeetingStatus
from app.queue import dequeue_transcription
from app.retrieval import build_retrieval_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [worker] %(message)s")
log = logging.getLogger("worker")


def process_one(meeting_id: int) -> None:
    """处理一个会议的转写。任何一步出错都把状态置为 failed 并记录原因。"""
    db = SessionLocal()
    try:
        meeting = db.get(Meeting, meeting_id)
        if meeting is None:
            log.warning("meeting %s 不存在，跳过", meeting_id)
            return

        meeting.status = MeetingStatus.processing.value
        db.commit()

        asr = get_asr_provider()
        text = asr.transcribe(meeting.audio_path)

        meeting.transcript = text
        meeting.status = MeetingStatus.done.value
        db.commit()
        log.info("meeting %s 转写完成（%d 字）", meeting_id, len(text))

        # 转写成功后再做检索索引。索引失败不应回退转写状态（转写本身已成功），
        # 所以单独 try、只记日志。
        try:
            n = build_retrieval_service().index_meeting(db, meeting_id, text)
            log.info("meeting %s 已索引 %d 个块", meeting_id, n)
        except Exception:
            log.exception("meeting %s 索引失败（转写仍保留）", meeting_id)
    except Exception as exc:  # noqa: BLE001  这里就是要兜住一切异常、落库
        db.rollback()
        meeting = db.get(Meeting, meeting_id)
        if meeting is not None:
            meeting.status = MeetingStatus.failed.value
            meeting.error = str(exc)
            db.commit()
        log.exception("meeting %s 转写失败", meeting_id)
    finally:
        db.close()


def main() -> None:
    init_db()  # 保证表存在（worker 可能先于 web 启动）
    log.info("worker 启动，等待任务……")
    while True:
        meeting_id = dequeue_transcription(timeout=5)
        if meeting_id is not None:
            process_one(meeting_id)


if __name__ == "__main__":
    main()
