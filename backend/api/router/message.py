from fastapi import Depends
from fastapi import APIRouter
from conversation.service import ConversationService
from sqlalchemy.orm import Session
from conversation.database import get_db
from schemas.chat import MessageResponse
from auth.dependencies import get_current_user

conversation_service=ConversationService()


router=APIRouter(prefix="/message",tags=["message"])


@router.get("/{session_id}",response_model=list[MessageResponse])
def get_messages(session_id:int,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    
        messages=conversation_service.get_messages(db,user_id=current_user.id,session_id=session_id)
   
        return messages


@router.delete("/{message_id}")
def delete_message(message_id:int,db:Session=Depends(get_db),current_user=Depends(get_current_user)):

        result=conversation_service.delete_message(db,user_id=current_user.id,message_id=message_id)
        if result:
            return {"message":"消息删除成功"}
    
