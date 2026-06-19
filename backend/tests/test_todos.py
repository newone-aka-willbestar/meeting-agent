"""待办接口测试：创建 + 列表 + 按会议过滤（SQLite，无需 Postgres）。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.main import app


@pytest.fixture
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'t.db'}")
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_and_list_todo(client):
    resp = client.post(
        "/todos",
        json={"assignee": "张伟", "content": "周五前联调支付模块", "ddl": "周五"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["assignee"] == "张伟"
    assert body["status"] == "open"
    assert body["source"] == "mcp"   # 默认来源

    todos = client.get("/todos").json()
    assert len(todos) == 1


def test_filter_by_meeting(client):
    client.post("/todos", json={"assignee": "A", "content": "x", "meeting_id": 1})
    client.post("/todos", json={"assignee": "B", "content": "y", "meeting_id": 2})
    only1 = client.get("/todos?meeting_id=1").json()
    assert len(only1) == 1
    assert only1[0]["assignee"] == "A"
