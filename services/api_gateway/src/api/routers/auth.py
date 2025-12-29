from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.database.connection import get_db
from src.auth import service
from src.database.models import User

router = APIRouter(
    tags=["Auth"]
)

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: str
    password: str

@router.post("/register", response_model=Token)
async def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = service.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )
    user = service.create_user(db, email=user_in.email, password=user_in.password)
    
    # Auto login after register
    access_token = service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = service.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def read_users_me(current_user: User = Depends(service.get_current_active_user)):
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active
    }
