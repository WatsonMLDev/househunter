from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from app.core.models import User
from app.core.database import engine

# OAuth2 Scheme - Points to the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_session():
    with Session(engine) as session:
        yield session

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """
    Standard OAuth2 dependency. 
    The 'token' is simply the account_id in our simplified password-less flow.
    """
    # In a full auth system, we would decode a JWT here. 
    # For this password-less system, the token IS the account_id.
    account_id = token
    
    user = session.exec(select(User).where(User.account_id == account_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authentication Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
