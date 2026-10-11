from langchain.agents import create_agent
from factory.model_factory import get_model
from config.rag import Settings
from agent.tool import search_knowledge_base
from utils.prompt_loader import load_prompt
from sqlalchemy.orm import Session
from conversation.service import ConversationService
from config.logger import logger
from langchain_core.messages import AIMessage,ToolMessage


settings=Settings()



class AgentService:
  def __init__(self):
    self.agent_system_prompt=load_prompt("agent_system_prompt_path")
    self.conversation_service=ConversationService()
    self.llm=get_model()
    self.agent=create_agent(
      model=self.llm,
      tools=[search_knowledge_base],
      system_prompt=self.agent_system_prompt
    )


  
# 同步调用
  def run(self,db:Session,query:str,session_id:str,user_id:str):
     
     history=self.conversation_service.get_chat_history(db,session_id=session_id,user_id=user_id)
     messages=history+[{ "role":"user","content":query}]
     
     # 先把用户问题存入
     self.conversation_service.add_message(db,session_id=session_id,user_id=user_id,role="user",content=query)
     
     
     
     result=self.agent.invoke({"messages":messages})
     self.conversation_service.add_message(db,session_id=session_id,user_id=user_id,role="assistant",content=result["messages"][-1].content)
    
    # 工具调用链路日志：决策（带参数）+ 结果
     for msg in result["messages"]:
         if isinstance(msg, AIMessage) and msg.tool_calls:
             for tc in msg.tool_calls:
                 logger.info(f"Agent 决定调用工具：{tc['name']}，参数：{tc['args']}")
         elif isinstance(msg, ToolMessage):
             preview = str(msg.content).replace("\n", " ")[:120]
             logger.info(f"工具 {msg.name} 执行完成，返回 {len(str(msg.content))} 字符：{preview}...")



     return result["messages"][-1].content
  
    


  def stream(self,db:Session,query:str,session_id:str,user_id:str):
    
     history=self.conversation_service.get_chat_history(db,session_id=session_id,user_id=user_id)
     messages=history+[{ "role":"user","content":query}]
     
     # 先把用户问题存入
     self.conversation_service.add_message(db,session_id=session_id,user_id=user_id,role="user",content=query)

    
     
     content=""
     completed=False
     try:
        for chunk ,metadata in self.agent.stream({"messages":messages},stream_mode="messages"):
             if isinstance(chunk, ToolMessage):   # 工具结果，一次一条
                 preview = str(chunk.content).replace("\n", " ")[:120]
                 logger.info(f"工具 {chunk.name} 执行完成，返回 {len(str(chunk.content))} 字符：{preview}...")
             elif chunk.content and metadata.get("langgraph_node") == "model":
                  content += chunk.content
                  yield chunk
        completed=True
     finally:
        if completed and content:
            self.conversation_service.add_message(db,
            session_id=session_id,
            user_id=user_id,role="assistant",
            content=content)
        
   
import threading

_agent_service = None
_lock = threading.Lock()
def get_agent_service():
   global _agent_service
   if _agent_service is None:
      with _lock:
         if _agent_service is None:
            _agent_service = AgentService()
   return _agent_service



if __name__=="__main__":
    agent_service=AgentService()
    # # messages={
    # #    "messages":[{"role":"user","content":"这里主要卖什么产品？"}]
    # # }
    # res=agent_service.run("首次使用扫地机器人需要做什么？")
    # print(res)

    res=agent_service.stream("首次使用扫地机器人需要做什么？")
    for chunk in res:
        print(chunk)
        
        
