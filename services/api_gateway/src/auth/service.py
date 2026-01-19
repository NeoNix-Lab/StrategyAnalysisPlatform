from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
import hashlib
import os
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import uuid

from quant_shared.models.connection import get_db
from quant_shared.models.models import User, Role, ApiKey
from .crypto import PasswordHasherService

# Configuration (Should be in env)
SECRET_KEY = "CHANGE_THIS_IN_PRODUCTION_SECRET_KEY" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 3  # 3 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
hasher = PasswordHasherService()

ALLOW_API_KEY_AUTH = os.getenv("ALLOW_API_KEY_AUTH", "false").lower() in ("1", "true", "yes")

API_KEY_SCOPE_CONNECTIONS_READ = "connections:read"
API_KEY_SCOPE_CONNECTIONS_WRITE = "connections:write"
API_KEY_SCOPE_INGEST_WRITE = "ingest:write"
API_KEY_SCOPE_TRADING_READ = "trading:read"
API_KEY_SCOPE_TRADING_WRITE = "trading:write"

ALLOWED_API_KEY_SCOPES = {
    API_KEY_SCOPE_CONNECTIONS_READ,
    API_KEY_SCOPE_CONNECTIONS_WRITE,
    API_KEY_SCOPE_INGEST_WRITE,
    API_KEY_SCOPE_TRADING_READ,
    API_KEY_SCOPE_TRADING_WRITE,
}

DEFAULT_API_KEY_SCOPES = {
    API_KEY_SCOPE_CONNECTIONS_READ,
    API_KEY_SCOPE_CONNECTIONS_WRITE,
}

@dataclass
class AuthContext:
    user: User
    scopes: set[str]
    auth_type: str  # jwt or api_key

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, password: str, role: Role = Role.USER):
    hashed_password = hasher.hash_password(password)
    new_user = User(
        user_id=str(uuid.uuid4()),
        email=email,
        hashed_password=hashed_password,
        role=role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not hasher.verify_password(password, user.hashed_password):
        return False
    return user

def _hash_api_key_secret(secret: str) -> str:
    pepper = os.getenv("API_KEY_PEPPER", "")
    return hashlib.sha256((secret + pepper).encode()).hexdigest()

def normalize_api_key_scopes(scopes: Optional[list[str]]) -> list[str]:
    if scopes is None:
        return sorted(DEFAULT_API_KEY_SCOPES)
    normalized = sorted(set(scopes))
    unknown = set(normalized) - ALLOWED_API_KEY_SCOPES
    if unknown:
        raise ValueError(f"Unknown scopes: {', '.join(sorted(unknown))}")
    return normalized

def create_api_key(
    db: Session,
    user_id: str,
    label: Optional[str] = None,
    expires_utc: Optional[datetime] = None,
    scopes: Optional[list[str]] = None,
):
    key_id = str(uuid.uuid4())
    secret = secrets.token_urlsafe(32)
    raw_key = f"{key_id}.{secret}"
    key_hash = _hash_api_key_secret(secret)
    scopes_json = normalize_api_key_scopes(scopes)

    api_key = ApiKey(
        key_id=key_id,
        user_id=user_id,
        key_hash=key_hash,
        label=label,
        expires_utc=expires_utc,
        scopes_json=scopes_json,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key, raw_key

def get_api_key_context(db: Session, api_key: str) -> Optional[AuthContext]:
    if not api_key or "." not in api_key:
        return None

    key_id, secret = api_key.split(".", 1)
    record = db.query(ApiKey).filter(ApiKey.key_id == key_id).first()
    if not record:
        return None

    if record.expires_utc and record.expires_utc < datetime.utcnow():
        return None

    if record.key_hash != _hash_api_key_secret(secret):
        return None

    user = db.query(User).filter(User.user_id == record.user_id).first()
    if not user:
        return None

    scopes = set(record.scopes_json or DEFAULT_API_KEY_SCOPES)
    return AuthContext(user=user, scopes=scopes, auth_type="api_key")

def _get_user_from_token(db: Session, token: Optional[str]) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None
    return get_user_by_email(db, email=email)

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = _get_user_from_token(db, token)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_user_or_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    context = None
    if ALLOW_API_KEY_AUTH and api_key:
        context = get_api_key_context(db, api_key)
    if context is None and token:
        user = _get_user_from_token(db, token)
        if user:
            context = AuthContext(user=user, scopes=set(), auth_type="jwt")
    if context is None:
        raise credentials_exception
    if not context.user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return context

def require_scopes(*required_scopes: str):
    async def _dependency(context: AuthContext = Depends(get_current_active_user_or_api_key)):
        if context.auth_type == "api_key":
            missing = set(required_scopes) - context.scopes
            if missing:
                raise HTTPException(status_code=403, detail="Insufficient scope")
        return context.user
    return _dependency
