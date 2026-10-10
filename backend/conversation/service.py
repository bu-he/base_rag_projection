# 服务类

from sqlalchemy.orm import Session
from conversation import repository as repo
from config.logger import logger
from core.exceptions import NotFoundError,BusinessError


# 
class ConversationService:
      
     
      


      def create_session(self,db:Session,user_id:int,title:str):
            """创建会话"""
            user=repo.get_user_by_id(db,user_id)
            if user is None:
                  raise NotFoundError("用户不存在")
            session = repo.create_session(db, user_id, title)
          
            logger.info(f"创建会话成功，会话ID：{session.id}")
            return session
      

      def get_or_create_session(self,db:Session,session_id:int|None,user_id:int):
            if session_id is not None:
                  session=repo.get_session_by_id_and_user(db, session_id,user_id)
                  if session is None:
                        raise NotFoundError("会话不存在或无权访问")              
                  return session
                  
            # 没有会话id，创建默认会话
            
            return self.create_session(db,user_id,"默认会话")
            
      

      def get_session_by_user(self,db:Session,user_id:int)->list:
            sessions = repo.get_sessions_by_user(db, user_id)
           
            logger.info(f"获取用户会话成功，用户ID：{user_id},会话数量：{len(sessions)}")
            return sessions
      
      def update_session_title(self,db:Session,user_id:int,session_id:int,title:str):
            """更新会话标题"""
            title=title.strip()
            if not title:
                  raise BusinessError("会话标题不能为空")
            if len(title)>100:
                  raise BusinessError("会话标题长度不能超过100个字符")
            session=repo.update_session_title(db,session_id,user_id,title)
            if session is None:
                  raise NotFoundError("会话不存在或无权更新标题")
            logger.info(f"更新会话标题成功,会话ID：{session_id},新标题：{title}")
            return session

      

      def delete_session(self,db:Session,user_id:int,session_id:int):
           

            if not repo.delete_session(db, session_id,user_id):
                  raise NotFoundError("会话不存在或无权删除")
            logger.info(f"删除会话成功，会话ID：{session_id}")
            return True
      
      
      def add_message(self,db:Session,user_id:int,session_id:int,role:str,content:str):
            chat_session=repo.get_session_by_id_and_user(db, session_id,user_id)
            if chat_session is None:
                  raise NotFoundError("会话不存在或无权访问")
            if role not in {"user","assistant"}:
                  raise NotFoundError(f"未知角色：{role}")
            if not content or not content.strip():
                  raise BusinessError("消息内容不能为空")
            msg = repo.add_message(db, session_id, role, content)
            if msg is None:
                  raise NotFoundError("添加消息失败")
            
            logger.info(f"添加消息成功,会话ID：{session_id},角色：{role}")
            
            return msg
      


      def get_messages(self,db:Session,user_id:int,session_id:int)->list:
            session=repo.get_session_by_id_and_user(db, session_id,user_id)
            if session is None:
                  raise NotFoundError("会话不存在或无权访问")
            messages = repo.get_messages(db, session_id)
            if messages is None:
                  raise BusinessError("获取消息失败")
           
            return messages
      
      def delete_message(self,db:Session,user_id:int,message_id:int):
            if not repo.delete_message(db, message_id,user_id):
                  raise NotFoundError("消息不存在或无权删除")
            logger.info(f"删除消息成功，消息ID：{message_id}")
            return True



      def get_chat_history(self,db:Session,user_id:int,session_id:int|None)->list:
            session=repo.get_session_by_id_and_user(db, session_id,user_id)
            if session is None:
                  raise NotFoundError("会话不存在或无权访问")
            messages = repo.get_recent_messages(db, session_id)
           
            chat_history=[]
            from langchain_core.messages import HumanMessage,AIMessage
            for msg in messages:
                  if msg.role=="user":
                        chat_history.append(HumanMessage(content=msg.content))
                  elif msg.role=="assistant":
                        chat_history.append(AIMessage(content=msg.content))
                  else:
                        raise BusinessError(f"未知角色：{msg.role}")
            
            logger.info(f"获取会话{session_id}的聊天记录成功，共{len(chat_history)}条消息")
            return chat_history
      
      


if __name__ == "__main__":
    service = ConversationService()
    from conversation.database import SessionLocal 
    db=SessionLocal()
#     service.create_user(db,"guest")
#     service.add_message(db,1 , "user", "你好,你是谁?")
#     service.add_message(db, 1, "assistant", "你好，我是AI助手,我叫小没")
#     service.delete_message(db, 6)
#     service.delete_session(db, 2)
#     msg=service.get_chat_history(db, 3)
#     print(msg)


# 测试获取会话
    session=service.get_or_create_session(db,None)
    logger.info(f"获取会话成功，会话ID：{session.id}")
    print(session)    
