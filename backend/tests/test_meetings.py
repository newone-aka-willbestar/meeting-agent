"""上传接口测试：不依赖真 Postgres / Redis。

手法（都是面试可讲的测试技巧）：
1. 用 SQLite 文件库替代 Postgres；
2. 用 FastAPI 的 dependency_overrides 把 get_db 换成测试会话；
3. monkeypatch 掉 enqueue_transcription，避免真连 Redis（只记录被入队的 id）。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.api.meetings as meetings_mod
from app.db import Base, get_db
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # 1) 独立的 SQLite 文件库 + 建表
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}")
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # 2) 上传文件落到临时目录，别污染项目
    monkeypatch.setattr(meetings_mod.settings, "storage_dir", str(tmp_path / "storage"))

    # 3) 拦截入队：只记录，不真连 Redis
    enqueued: list[int] = []
    monkeypatch.setattr(meetings_mod, "enqueue_transcription", enqueued.append)

    # 不用 with TestClient(...)，避免触发 lifespan 去连真 Postgres 建表
    test_client = TestClient(app)
    test_client.enqueued = enqueued  # 把记录挂上去，测试里能断言
    yield test_client

    app.dependency_overrides.clear()


def test_upload_creates_pending_meeting_and_enqueues(client):
    resp = client.post(
        "/meetings",
        files={"file": ("会议录音.mp3", b"fake-audio-bytes", "audio/mpeg")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["filename"] == "会议录音.mp3"
    assert body["status"] == "pending"      # 上传后是 pending，转写还没跑
    assert body["transcript"] is None
    # 确认任务被入队了（且就是这条 meeting）
    assert client.enqueued == [body["id"]]


def test_get_meeting_404_when_missing(client):
    assert client.get("/meetings/99999").status_code == 404


def test_list_meetings_newest_first(client):
    id1 = client.post("/meetings", files={"file": ("a.wav", b"x", "audio/wav")}).json()["id"]
    id2 = client.post("/meetings", files={"file": ("b.wav", b"y", "audio/wav")}).json()["id"]
    ids = [m["id"] for m in client.get("/meetings").json()]
    assert ids == [id2, id1]   # 最新的在前
