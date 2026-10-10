# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from main import app
from conversation.database import test_engine,get_test_db,get_db

from conversation.models import Base
import os



# TEST_DB_FILE = "test_rag.db"


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)   # 建表（如果没建）
    
    # 清空所有表的数据
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    
    yield
    # 不删除文件

@pytest.fixture
def client():
    """覆盖 get_db，让路由用测试库"""
    app.dependency_overrides[get_db] = get_test_db   # ← 关键
    yield TestClient(app)
    app.dependency_overrides.clear()   # ← 测试后清除覆盖


@pytest.fixture
def auth_client(client):
    """已登录的 client（带 Token）"""
    client.post("/auth/register", json={
        "username": "testuser",
        "password": "123456789",
    })
    res = client.post("/auth/login", data={
        "username": "testuser",
        "password": "123456789",
    })
    token = res.json()["access_token"]
    
    # 给 client 设置默认 header
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def test_session(auth_client):
    """创建一个会话，返回 session_id"""
    res = auth_client.post("/session/create")
    return res.json()["id"]


@pytest.fixture
def session_with_messages(auth_client, test_session):
    """往会话里加 3 条消息"""
    from conversation.database import TestSessionLocal
    from conversation import repository as repo
    
    db = TestSessionLocal()
    try:
        repo.add_message(db, test_session, "user", "你好")
        repo.add_message(db, test_session, "assistant", "你好，有什么可以帮你？")
        repo.add_message(db, test_session, "user", "再见")
    finally:
        db.close()
    return test_session

