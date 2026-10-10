

def test_register(client):
      res=client.post("/auth/register",json={"username":"test1","password":"123456789"})
      assert res.status_code==200
      assert res.json()["message"]=="注册成功"
 
def test_login(client):
      client.post("/auth/register",json={"username":"test2","password":"123456789"})
      res=client.post("/auth/login",data={"username":"test2","password":"123456789"})
      assert res.status_code==200
      # assert res.json()["message"]=="登录成功"
      assert "access_token" in res.json()
     


def test_register_duplicate(client):
      client.post("/auth/register",json={"username":"dup_test","password":"123456789"})
      res=client.post("/auth/register",json={"username":"dup_test","password":"123456789"})
      assert res.status_code==400
      assert res.json()["detail"]=="用户名已存在"

def test_short_password(client):
      res=client.post("/auth/register",json={"username":"test3","password":"123"})
      assert res.status_code==400
      assert res.json()["detail"]=="密码长度必须大于等于6位且小于等于64位"

def test_error_password_login(client):
      client.post("/auth/register",json={"username":"passworderror_test","password":"123456789"})
      res=client.post("/auth/login",data={"username":"passworderror_test","password":"123456"})
      assert res.status_code==401
      assert res.json()["detail"]=="用户名或密码错误"

def test_error_username_login(client):
      client.post("/auth/register",json={"username":"usernameerror_test","password":"123456789"})
      res=client.post("/auth/login",data={"username":"error_test","password":"123456789"})
      assert res.status_code==401
      assert res.json()["detail"]=="用户名或密码错误"
      res=client.post("/auth/login",data={"username":"nonexist_test","password":"123456"})
      assert res.status_code==401
      assert res.json()["detail"]=="用户名或密码错误"