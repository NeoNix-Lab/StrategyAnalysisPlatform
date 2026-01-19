from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from quant_shared.models.connection import get_db
from src.auth import service
from quant_shared.models.models import User, ApiKey, Role

router = APIRouter(
    tags=["Auth"]
)

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: str
    password: str

class ApiKeyCreate(BaseModel):
    label: str | None = None
    expires_utc: datetime | None = None
    scopes: list[str] | None = None

class ApiKeyResponse(BaseModel):
    key_id: str
    label: str | None = None
    expires_utc: datetime | None = None
    api_key: str | None = None
    scopes: list[str] | None = None

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
@router.get("/me")
async def read_users_me(current_user: User = Depends(service.get_current_active_user)):
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active
    }

@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    payload: ApiKeyCreate,
    current_user: User = Depends(service.get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        api_key, raw_key = service.create_api_key(
            db,
            user_id=current_user.user_id,
            label=payload.label,
            expires_utc=payload.expires_utc,
            scopes=payload.scopes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "key_id": api_key.key_id,
        "label": api_key.label,
        "expires_utc": api_key.expires_utc,
        "api_key": raw_key,
        "scopes": api_key.scopes_json,
    }

@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(service.get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(ApiKey)
    if current_user.role != Role.ADMIN:
        query = query.filter(ApiKey.user_id == current_user.user_id)
    keys = query.all()
    return [
        {
            "key_id": key.key_id,
            "label": key.label,
            "expires_utc": key.expires_utc,
            "scopes": key.scopes_json,
        }
        for key in keys
    ]

@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(service.get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(ApiKey).filter(ApiKey.key_id == key_id)
    if current_user.role != Role.ADMIN:
        query = query.filter(ApiKey.user_id == current_user.user_id)
    key = query.first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    db.delete(key)
    db.commit()
    return {"status": "ok"}
