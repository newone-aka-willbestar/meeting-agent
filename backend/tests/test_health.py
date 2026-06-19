"""最小测试：验证 /health 路由可用。
TestClient 会在内存里跑起整个 FastAPI 应用，不需要真启动服务器，
所以 CI 里跑得很快，也不依赖 docker。"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
