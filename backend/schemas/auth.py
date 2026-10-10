from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class RegisterRequest(BaseModel):
    """注册请求体"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., description="密码")
  
    
    # confirm_password: str = Field(..., min_length=8,max_length=128, description="确认密码")



class LoginRequest (BaseModel):
    """登录请求体"""
    username: str 
    password: str
    


class TokenResponse (BaseModel):
    """登录成功返回"""
    access_token: str
    token_type: str = Field(..., description="Bearer")

class UserResponse (BaseModel):
    """用户信息"""
    user_id: int
    username: str

    class Config:
         from_attributes = True
   


class RegisterResponse (BaseModel):
    """注册成功返回"""
    message: str = Field(..., description="注册成功")
    user: UserResponse = Field(..., description="用户信息")
