from fastapi import APIRouter, Depends
from conversation.database import get_db
from auth.service import AuthService
from schemas.auth import RegisterRequest, TokenResponse, UserResponse, RegisterResponse
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm


router=APIRouter(prefix="/auth",tags=["auth"])

auth_service = AuthService()

@router.post("/register", response_model=RegisterResponse)
def register(request:RegisterRequest, db: Session = Depends(get_db)):
    """注册"""
    
    user = auth_service.register(db, request.username, request.password)
    return RegisterResponse(message="注册成功", user=UserResponse(user_id=user.id, username=request.username))
  
    
@router.post("/login", response_model=TokenResponse)
def login( db: Session = Depends(get_db),  form: OAuth2PasswordRequestForm = Depends(),):
    """登录"""
    
    token = auth_service.login(db, form.username, form.password)
    return TokenResponse(access_token=token,token_type="Bearer")
   


