from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from conversation.database import get_db
from conversation import repository as repo
from auth.security import decode_token     

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        
        user_id =decode_token(token)
        if user_id is None:
            raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
        user = repo.get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="用户不存在")
        return user