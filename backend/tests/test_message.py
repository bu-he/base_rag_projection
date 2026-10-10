# tests/test_message.py — 消息接口测试
# 契约（来自 api/router/message.py）：
#   GET    /message/{session_id}   → 200，裸数组 [{"id","role","content","created_at"}, ...]
#   DELETE /message/{message_id}   → 200 {"message":"消息删除成功"}；不存在/无权访问 → 404
# 依赖 conftest 的夹具（惰性，写进参数才执行）：
#   test_session          建好一个空会话，返回 session_id
#   session_with_messages 建好会话并直插 3 条消息（2 user + 1 assistant），返回 session_id


def test_get_history(session_with_messages, auth_client):
    """正常路径：3 条消息能按会话完整拉回来"""
    res = auth_client.get(f"/message/{session_with_messages}")
    assert res.status_code == 200
    messages = res.json()                     # 裸数组（response_model=list[MessageResponse]）
    assert len(messages) == 3
    # 不赌返回顺序，只验证角色构成：2 条 user + 1 条 assistant
    roles = [m["role"] for m in messages]
    assert roles.count("user") == 2
    assert roles.count("assistant") == 1


def test_get_history_empty(test_session, auth_client):
    """空会话的历史应该是空数组（200 + []，而不是 404 或 null）"""
    res = auth_client.get(f"/message/{test_session}")
    assert res.status_code == 200
    assert res.json() == []


def test_get_history_unauthorized(client):
    """不带 token 拉历史 → 401
    注意：这里必须用裸 client 而不是 auth_client——
    auth_client 的默认头里已经带 token 了，永远测不出 401"""
    res = client.get("/message/1")
    assert res.status_code == 401


def test_delete_message(session_with_messages, auth_client):
    """正常路径：删一条 → 返回成功文案 → 历史真的少了一条"""
    # Arrange：先拉历史，拿到第一条消息的 id
    msg_id = auth_client.get(f"/message/{session_with_messages}").json()[0]["id"]

    # Act：删除它
    res = auth_client.delete(f"/message/{msg_id}")
    assert res.status_code == 200
    assert res.json()["message"] == "消息删除成功"

    # Assert：再拉历史，只剩 2 条，且删掉的那条不在了
    messages = auth_client.get(f"/message/{session_with_messages}").json()
    assert len(messages) == 2
    assert all(m["id"] != msg_id for m in messages)


def test_delete_nonexistent_message(auth_client):
    """删一条不存在的消息 → 404（NotFoundError 走全局异常处理器）"""
    res = auth_client.delete("/message/99999")
    assert res.status_code == 404


def test_delete_other_users_message(client, session_with_messages):
    """水平越权：intruder 删 testuser 的消息 → 404，且原消息安然无恙

    返回 404 而不是 403 是刻意设计：对陌生请求隐藏「这条消息存在」的信息，
    让越权者和访问不存在资源的人拿到同一种响应，探测不到任何区别。

    前置说明：申请了 session_with_messages，依赖链会把 client 的默认头
    设置成 testuser 的 token——所以下面不带 headers 的请求都是 testuser 身份。
    """
    # Arrange：注册并登录第二个用户 intruder
    client.post("/auth/register", json={"username": "intruder", "password": "123456789"})
    login = client.post("/auth/login", data={"username": "intruder", "password": "123456789"})
    intruder_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # 拿到 testuser 会话里第一条消息的 id（默认头 = testuser）
    msg_id = client.get(f"/message/{session_with_messages}").json()[0]["id"]

    # Act：intruder 带自己的 token 尝试删（显式 headers 会覆盖默认的 testuser token）
    res = client.delete(f"/message/{msg_id}", headers=intruder_headers)
    assert res.status_code == 404

    # Assert：testuser 再看，3 条一条没少——删除被正确拒绝了
    messages = client.get(f"/message/{session_with_messages}").json()
    assert len(messages) == 3
