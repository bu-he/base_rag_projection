from conversation.database import get_db
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from schemas.chat import SessionTitleUpdateRequest,SessionResponse,SessionListResponse,SessionTitleUpdateResponse
from auth.dependencies import get_current_user
from conversation.service import ConversationService

conversation_service=ConversationService()


router=APIRouter( prefix="/session",tags=["session"])


@router.post("/create",response_model=SessionResponse)
def create_session(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
     
        session=conversation_service.create_session(db,current_user.id,"默认会话")
        return session


@router.get("/list",response_model=SessionListResponse)
def list_sessions(db: Session = Depends(get_db),current_user=Depends(get_current_user)):
    
        sessions=conversation_service.get_session_by_user(db,current_user.id)
        return {"sessions":sessions}

@router.patch("/{session_id}",response_model=SessionTitleUpdateResponse)
def update_session_title(session_id:int,request:SessionTitleUpdateRequest,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
     
       conversation_service.update_session_title(db,session_id=session_id,user_id=current_user.id,title=request.title)
       return {"message":"会话标题更新成功"}


@router.delete("/{session_id}")
def delete_session(session_id:int,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
   
        conversation_service.delete_session(db,session_id=session_id,user_id=current_user.id)
        return {"message":"会话删除成功"}
