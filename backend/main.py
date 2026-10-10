from fastapi import FastAPI
from config.rag import Settings 
from config.logger import logger
from api.router import document,auth,session,message,health,agent
from contextlib import asynccontextmanager   # ① 导入装饰器
from conversation.init_db import init_db

# CORS 跨域配置
from fastapi.middleware.cors import CORSMiddleware
from core.handlers import register_exception_handlers
import threading

settings=Settings()


def _preload():
    from rag.retriever import get_retriever_service
    from agent.agent_service import get_agent_service
    import time
    start = time.perf_counter()

    get_retriever_service()
    get_agent_service()
    
    logger.info(f"RetrieverService与AgentService 预热完成，耗时 {time.perf_counter() - start:.2f} 秒")
    

    
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    
    import time
    start = time.perf_counter()
    threading.Thread(target=_preload, daemon=True).start()   # ← 后台加载
    logger.info( f"启动初始化完成，耗时 {time.perf_counter() - start:.2f} 秒" ) # ✅ 启动完成 yield
    yield


app=FastAPI(lifespan=lifespan)
register_exception_handlers(app)

@app.get("/")
def hello():
     return {"message":"Hello World"}




origins = [
    "http://localhost",
    "http://localhost:3000",       # python -m http.server 3000
    "http://localhost:5173",       # vite
    "http://localhost:8080",       # 其他
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5500",       # VS Code Live Server
    "http://127.0.0.1:8080",
]

app.add_middleware(
      CORSMiddleware,
      allow_origins=origins,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],

)

app.include_router(health.router)
app.include_router(document.router)
app.include_router(auth.router)
app.include_router(session.router)
app.include_router(message.router)
app.include_router(agent.router)


