# api/schemas/chat.py
from pydantic import BaseModel, Field
from datetime import datetime


class SessionCreateRequest(BaseModel):
    """创建会话的请求体"""
    user_id: int = Field(..., description="用户 ID")
    title: str | None = Field(None, max_length=200, description="会话标题")


class MessageCreateRequest(BaseModel):
    """发消息的请求体"""
    role: str = Field(..., description="角色：user / assistant")
    content: str = Field(..., min_length=1, description="消息内容")


class ChatRequest(BaseModel):
    """聊天请求体"""
    query: str = Field(..., min_length=1, description="用户问题")
    session_id: int | None = Field(None, description="会话 ID，不传则新建")

# 会话响应类
class SessionResponse(BaseModel):
    """会话响应"""
    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True   # ← 允许从 ORM 对象转换



class SessionTitleUpdateRequest(BaseModel):
    """更新会话标题的请求体"""
    title: str = Field(..., max_length=200, description="新标题")
class SessionTitleUpdateResponse(BaseModel):
   """更新会话标题的响应"""
   message: str = Field(..., description="更新结果")


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: list[SessionResponse] = Field(..., description="会话列表")


# 消息响应类
class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
