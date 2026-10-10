from auth.security import get_hash_password, verify_password, create_access_token, decode_token
from sqlalchemy.orm import Session
from conversation import repository as repo
from core.exceptions import AuthError,BusinessError

class AuthService:
    

    def register(self,db:Session,username:str,password:str):
        # 注册用户 
        existing_user=repo.get_user_by_username(db,username)
        if existing_user is not  None:
            raise BusinessError("用户名已存在")
        if len(password)<6 or len(password)>64:
            raise BusinessError("密码长度必须大于等于6位且小于等于64位")
        password_hash=get_hash_password(password)
        return repo.create_user(db,username,password_hash)
    
    def login(self,db:Session,username:str,password:str):
        # 登录用户 
        user=repo.get_user_by_username(db,username)
        if user is None or user.password_hash is None :
           raise AuthError( "用户名或密码错误" ) 
        if not verify_password(password, user.password_hash): 
           raise AuthError( "用户名或密码错误" ) 
        return create_access_token(user.id)
    