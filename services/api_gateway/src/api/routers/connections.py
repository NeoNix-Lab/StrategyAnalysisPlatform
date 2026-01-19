from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid
import json

from quant_shared.models.connection import get_db
from quant_shared.models.models import Connection, Role, User
from quant_shared.schemas.schemas import (
    ConnectionCreate,
    ConnectionUpdate,
    ConnectionHeartbeat,
    ConnectionResponse,
    ConnectionStatus,
)
from src.auth.crypto import FernetService
from src.auth.service import (
    require_scopes,
    API_KEY_SCOPE_CONNECTIONS_READ,
    API_KEY_SCOPE_CONNECTIONS_WRITE,
)

router = APIRouter()
fernet = FernetService()


def _encrypt_secrets(secrets_json: Optional[dict]) -> Optional[str]:
    if secrets_json is None:
        return None
    payload = json.dumps(secrets_json, sort_keys=True, separators=(",", ":"))
    return fernet.encrypt(payload)


@router.post("/", response_model=ConnectionResponse)
def create_connection(
    data: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scopes(API_KEY_SCOPE_CONNECTIONS_WRITE)),
):
    connection_id = data.connection_id or str(uuid.uuid4())

    existing = db.query(Connection).filter(Connection.connection_id == connection_id).first()
    if existing:
        if existing.user_id and existing.user_id != current_user.user_id and current_user.role != Role.ADMIN:
            raise HTTPException(status_code=403, detail="Not allowed")
        payload = data.model_dump(exclude_unset=True)
        if "name" in payload:
            existing.name = payload["name"]
        if "platform" in payload:
            existing.platform = payload["platform"]
        if "mode" in payload:
            existing.mode = payload["mode"]
        if "status" in payload:
            existing.status = payload["status"]
        if "account_id" in payload:
            existing.account_id = payload["account_id"]
        if "capabilities_json" in payload:
            existing.capabilities_json = payload["capabilities_json"]
        if "config_json" in payload:
            existing.config_json = payload["config_json"]
        if "meta_json" in payload:
            existing.meta_json = payload["meta_json"]
        if "secrets_json" in payload:
            existing.secrets_json = _encrypt_secrets(payload["secrets_json"])
        if current_user.role == Role.ADMIN and data.user_id:
            existing.user_id = data.user_id
        elif not existing.user_id:
            existing.user_id = current_user.user_id
        existing.updated_utc = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    if current_user.role == Role.ADMIN and data.user_id:
        user_id = data.user_id
    else:
        user_id = current_user.user_id

    connection = Connection(
        connection_id=connection_id,
        user_id=user_id,
        name=data.name,
        platform=data.platform,
        mode=data.mode,
        status=data.status,
        account_id=data.account_id,
        capabilities_json=data.capabilities_json,
        config_json=data.config_json,
        secrets_json=_encrypt_secrets(data.secrets_json),
        meta_json=data.meta_json,
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection


@router.get("/", response_model=List[ConnectionResponse])
def list_connections(
    platform: Optional[str] = None,
    status: Optional[ConnectionStatus] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scopes(API_KEY_SCOPE_CONNECTIONS_READ)),
):
    query = db.query(Connection)
    if current_user.role != Role.ADMIN:
        query = query.filter(Connection.user_id == current_user.user_id)
    elif user_id:
        query = query.filter(Connection.user_id == user_id)
    if platform:
        query = query.filter(Connection.platform == platform)
    if status:
        query = query.filter(Connection.status == status)
    return query.order_by(Connection.created_utc.desc()).all()


@router.get("/{connection_id}", response_model=ConnectionResponse)
def get_connection(
    connection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scopes(API_KEY_SCOPE_CONNECTIONS_READ)),
):
    connection = db.query(Connection).filter(Connection.connection_id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    if connection.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not allowed")
    return connection


@router.patch("/{connection_id}", response_model=ConnectionResponse)
def update_connection(
    connection_id: str,
    data: ConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scopes(API_KEY_SCOPE_CONNECTIONS_WRITE)),
):
    connection = db.query(Connection).filter(Connection.connection_id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    if connection.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not allowed")

    payload = data.model_dump(exclude_unset=True)
    if "name" in payload:
        connection.name = payload["name"]
    if "platform" in payload:
        connection.platform = payload["platform"]
    if "mode" in payload:
        connection.mode = payload["mode"]
    if "status" in payload:
        connection.status = payload["status"]
    if "account_id" in payload:
        connection.account_id = payload["account_id"]
    if "capabilities_json" in payload:
        connection.capabilities_json = payload["capabilities_json"]
    if "config_json" in payload:
        connection.config_json = payload["config_json"]
    if "meta_json" in payload:
        connection.meta_json = payload["meta_json"]
    if "secrets_json" in payload:
        connection.secrets_json = _encrypt_secrets(payload["secrets_json"])

    connection.updated_utc = datetime.utcnow()
    db.commit()
    db.refresh(connection)
    return connection


@router.post("/{connection_id}/heartbeat", response_model=ConnectionResponse)
def record_heartbeat(
    connection_id: str,
    data: ConnectionHeartbeat,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scopes(API_KEY_SCOPE_CONNECTIONS_WRITE)),
):
    connection = db.query(Connection).filter(Connection.connection_id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    if connection.user_id != current_user.user_id and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not allowed")

    connection.last_heartbeat_utc = data.heartbeat_utc or datetime.utcnow()
    if data.status:
        connection.status = data.status
    if data.latency_ms is not None:
        connection.last_latency_ms = data.latency_ms

    connection.updated_utc = datetime.utcnow()
    db.commit()
    db.refresh(connection)
    return connection
