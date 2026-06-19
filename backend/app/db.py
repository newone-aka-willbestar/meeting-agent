"""数据库连接层：引擎、会话工厂、依赖注入、建表。

用 SQLAlchemy（ORM）——让我们用 Python 类操作数据库表，
而不必手写 SQL 字符串。"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

# 引擎：数据库连接池的总入口。pool_pre_ping 在借连接前先 ping 一下，
# 避免拿到一个已被数据库单方面断开的死连接。
engine = create_engine(settings.database_url, pool_pre_ping=True)

# 会话工厂：每次请求/任务都用它 new 一个独立的 Session 来读写数据库。
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# 所有 ORM 模型的基类（models.py 里的表都继承它）
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：每个请求开一个 Session，请求结束自动关闭。
    用 yield 实现『进入时建、退出时关』，即使处理中报错也会走 finally。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """建表。MVP 阶段直接按模型建；生产项目应改用数据库迁移工具（如 Alembic）。"""
    # 必须先 import models，Base 才知道有哪些表要建
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
