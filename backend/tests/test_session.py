from conversation import repository as repo


def test_create_session(auth_client):
     res=auth_client.post("/session/create")
     assert res.status_code==200
     assert "id" in  res.json()

def test_list_sessions(auth_client,session_with_messages):
    res=auth_client.get("/session/list")
    assert res.status_code==200
    assert "sessions" in res.json()
    assert len(res.json()["sessions"][0])==4
    assert len(res.json()["sessions"])>=1
    assert res.json()["sessions"][0]["id"]==session_with_messages


def test_delete_session(auth_client,session_with_messages):
     res=auth_client.delete(f"/session/{session_with_messages}")
     assert res.status_code==200
     assert res.json()["message"]=="会话删除成功"
   


def test_delete_session_not_exist(auth_client):
     res=auth_client.delete("/session/999")
     assert res.status_code==404
     assert res.json()["detail"]=="会话不存在或无权删除"

def test_delete_other_user_session(client,session_with_messages):
     client.post("/auth/register",json={"username":"testdelete_otheruser","password":"123456789"})
     login=client.post("/auth/login",data={"username":"testdelete_otheruser","password":"123456789"})
     other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

     res=client.delete(f"/session/{session_with_messages}",headers=other_headers)
     assert res.status_code==404
     assert res.json()["detail"]=="会话不存在或无权删除"

def test_update_session_title(auth_client,session_with_messages):
     res=auth_client.patch(f"/session/{session_with_messages}",json={"title":"new_title"})
     assert res.status_code==200
     assert res.json()["message"]=="会话标题更新成功"

def test_update_session_title_not_exist(auth_client):
     res=auth_client.patch("/session/999",json={"title":"new_title"})
     assert res.status_code==404
     assert res.json()["detail"]=="会话不存在或无权更新标题"

def test_update_session_title_other_user(client,session_with_messages):
     client.post("/auth/register",json={"username":"testupdate_otheruser","password":"123456789"})
     login=client.post("/auth/login",data={"username":"testupdate_otheruser","password":"123456789"})
     other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

     res=client.patch(f"/session/{session_with_messages}",headers=other_headers,json={"title":"new_title"})
     assert res.status_code==404
     assert res.json()["detail"]=="会话不存在或无权更新标题"
