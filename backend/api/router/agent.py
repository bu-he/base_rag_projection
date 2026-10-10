from fastapi import APIRouter
from agent.agent_service import get_agent_service
from schemas.agent import QueryRequest,QueryResponse
from fastapi import Depends
from conversation.database import get_db
from conversation.service import ConversationService
from auth.dependencies import get_current_user
from core.exceptions import BusinessError
import json
from fastapi.responses import StreamingResponse
from config.logger import logger



conversation_service=ConversationService()
from sqlalchemy.orm import Session
router=APIRouter(prefix="/agent",tags=["agent"])

@router.post("/ask",response_model=QueryResponse)
def ask(request:QueryRequest,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    agent_service=get_agent_service()
    if not request.query.strip():
        raise BusinessError("查询不能为空")
    session=conversation_service.get_or_create_session(db,session_id=request.session_id,user_id=current_user.id)
    response=agent_service.run(db,query=request.query,session_id=session.id,user_id=session.user_id)
    return QueryResponse(response=response)



@router.post("/stream")   # ← ① 没有 response_model！
def stream(request: QueryRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    agent_service = get_agent_service()
    if not request.query.strip():
        raise BusinessError("查询不能为空")

    session = conversation_service.get_or_create_session(
        db, session_id=request.session_id, user_id=current_user.id
    )

    def event_generator():   # ← ② yield 必须收进内部函数（你 README 踩坑第一条）
        try:
            yield f"data: {json.dumps({'session_id': session.id}, ensure_ascii=False)}\n\n"
            for chunk in agent_service.stream(
                db, query=request.query, session_id=session.id, user_id=current_user.id
            ):
                if chunk.content:
                    yield f"data: {json.dumps({'content': chunk.content}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.exception(f"Agent SSE 流异常：{e}")
            yield f"data: {json.dumps({'error': '服务器内部错误'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")   # ← ③