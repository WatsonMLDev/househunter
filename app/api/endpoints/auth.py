from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.api.deps import get_session
from app.core.models import User, UserSettings
import os
from pydantic import BaseModel
import random
import string

router = APIRouter()

class LoginRequest(BaseModel):
    account_id: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    is_new: bool = False

@router.post("/signup", response_model=Token)
def signup(
    session: Session = Depends(get_session),
    x_signup_token: str = Header(None)
):
    # Verify Secret Token
    admin_secret = os.getenv("ADMIN_SECRET_KEY")
    if not admin_secret or x_signup_token != admin_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Signup is restricted. Invalid or missing X-Signup-Token."
        )

    # Generate 10-digit ID
    for _ in range(10): # retry logic for collision
        account_id = ''.join(random.choices(string.digits, k=10))
        existing = session.exec(select(User).where(User.account_id == account_id)).first()
        if not existing:
            user = User(account_id=account_id)
            session.add(user)
            session.commit()
            session.refresh(user)
            
            # Create default settings
            settings = UserSettings(user_id=user.id)
            session.add(settings)
            session.commit()
            
            return {
                "access_token": user.account_id, 
                "token_type": "bearer",
                "user_id": str(user.id),
                "is_new": True
            }
            
    raise HTTPException(status_code=500, detail="Could not generate unique ID")

@router.post("/login", response_model=Token)
def login(req: LoginRequest, session: Session = Depends(get_session)):
    """
    JSON Login for Frontend
    """
    user = session.exec(select(User).where(User.account_id == req.account_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Account ID")
    
    return {
        "access_token": user.account_id, 
        "token_type": "bearer",
        "user_id": str(user.id),
        "is_new": False
    }

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """
    Standard OAuth2 Token Endpoint for Swagger UI.
    User enters account_id in 'username' field. Password can be anything.
    """
    account_id = form_data.username
    user = session.exec(select(User).where(User.account_id == account_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "access_token": user.account_id, 
        "token_type": "bearer",
        "user_id": str(user.id)
    }
