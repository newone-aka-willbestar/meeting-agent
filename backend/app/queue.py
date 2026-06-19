"""转写任务队列（基于 Redis 列表的最简实现）。

刻意手写而不用 Celery/RQ，是为了把『生产者-消费者』看得最清楚：
- 生产者（上传接口）：LPUSH 把 meeting_id 推进列表左端
- 消费者（worker）：    BRPOP 从右端阻塞取出，没任务就挂起等待
这就是一个 FIFO 队列。生产环境会换成 Celery/RQ/arq 拿到重试、
定时、监控等能力——这点在面试里要能说清取舍。"""

import redis

from app.config import get_settings

settings = get_settings()

# decode_responses=True：取出来直接是 str，不用手动 .decode()
_redis = redis.from_url(settings.redis_url, decode_responses=True)

QUEUE_KEY = "transcribe:queue"


def enqueue_transcription(meeting_id: int) -> None:
    """把一个待转写的会议 id 入队。"""
    _redis.lpush(QUEUE_KEY, str(meeting_id))


def dequeue_transcription(timeout: int = 5) -> int | None:
    """阻塞地取一个任务；timeout 秒内没有就返回 None（好让 worker 有机会响应退出）。"""
    item = _redis.brpop(QUEUE_KEY, timeout=timeout)
    if item is None:
        return None
    # brpop 返回 (队列名, 值)
    return int(item[1])
