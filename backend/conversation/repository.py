# 数据库操作类
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select,delete
from .models import User, ChatSession, Message
 
# ============ 用户 ============




def create_user(db: Session, username: str,password_hash:str) -> User:
    """创建用户"""
    user = User(username=username,password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_id(db:Session,user_id:int)->User|None:
      """根据ID获取用户,
      如果用户不存在,返回None"""
      return db.get(User,user_id)

def get_user_by_username(db:Session,username:str)->User|None:
      """根据用户名获取用户,
      如果用户不存在,返回None"""
      stmt=select(User).where(User.username==username)
      return db.execute(stmt).scalars().first()

def list_users(db:Session)->list[User]:
      """获取所有用户"""
      stmt=select(User).order_by(User.id)
      result = list(db.execute(stmt).scalars().all())
      return result


# ============ 会话 ============

def create_session(db: Session, user_id: int, title: str | None = None) -> ChatSession:
    session = ChatSession(user_id=user_id, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_by_id(db: Session, session_id: int) -> ChatSession | None:
    return db.get(ChatSession, session_id)


def get_sessions_by_user(db: Session, user_id: int) -> list[ChatSession]:
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    )
    return list(db.execute(stmt).scalars().all())

def get_session_by_id_and_user(db:Session,session_id:int,user_id:int)->ChatSession | None:
    """根据会话ID和用户ID获取会话,
    """
    stmt=select(ChatSession).where(ChatSession.id==session_id,
         ChatSession.user_id==user_id)
    return db.execute(stmt).scalars().first()



def update_session_title(db: Session, session_id: int,user_id:int, title: str) -> ChatSession | None:
    session = get_session_by_id_and_user(db,session_id,user_id)
    if session is None:
        return None
    session.title = title
    db.commit()
    db.refresh(session)
    return session


def touch_session(db: Session, session_id: int,user_id:int) -> bool:
    session = get_session_by_id_and_user(db,session_id,user_id)
    if session is None:
        return False
    session.updated_at = datetime.now()
    db.commit()
    return True


def delete_session(db: Session, session_id: int,user_id:int) -> bool:
    
    session=get_session_by_id_and_user(db,session_id,user_id)
    if session is None:
        return False

   
    db.execute(delete(Message).where(Message.session_id == session_id))
    db.delete(session)
    db.commit()
    return True


# ============ 消息 ============

def get_message_by_id_and_user(db:Session,message_id:int,user_id:int):
     stmt=select(Message).join(
         ChatSession,Message.session_id==ChatSession.id
     ).where(
         Message.id==message_id,
         ChatSession.user_id==user_id
     )
     return db.execute(stmt).scalars().first()



def add_message(db: Session, session_id: int, role: str, content: str) -> Message:
    msg = Message(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_messages(db: Session, session_id: int) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())




def get_recent_messages(db: Session, session_id: int, limit: int = 20) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return list(reversed(list(db.execute(stmt).scalars().all())))


def delete_message(db:Session,message_id:int,user_id:int):
     """删除消息"""
     message=get_message_by_id_and_user(db,message_id,user_id)
     if message is None:
        return False
     db.delete(message)
     db.commit()
     
     return True



if __name__ == "__main__":
      from .database import SessionLocal
      from config.logger import logger
      from sqlalchemy.orm import Session
      db=SessionLocal()
    #   create_user(db,"test6")
    #   logger.info("创建用户成功")
    #   user=get_user_by_id(db,1)
    #   logger.info(f"根据ID获取用户：{user}")
    #   users=list_users(db)
    #   logger.info(f"获取所有用户：{users}")
      bool=delete_message(db,5)
      if bool:
        logger.info("删除消息成功")
      else:
        logger.error("删除消息失败")
        