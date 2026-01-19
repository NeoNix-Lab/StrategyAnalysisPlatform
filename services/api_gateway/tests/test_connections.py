import pytest
from sqlalchemy.orm import sessionmaker

from auth import service as auth_service
from quant_shared.models.models import User, Role


def test_connection_crud(client, test_engine):
    if client is None:
        pytest.skip("API Client not available (likely import error in conftest)")

    user_email = "conn_user@test.local"
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = session_local()
    try:
        user = User(
            user_id="test-user-1",
            email=user_email,
            hashed_password="test",
            role=Role.USER,
            is_active=True,
        )
        session.add(user)
        session.commit()
    finally:
        session.close()

    token = auth_service.create_access_token(data={"sub": user_email})
    auth_headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/api/auth/api-keys",
        json={
            "label": "connector",
            "scopes": ["connections:read", "connections:write"],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    api_key = resp.json()["api_key"]
    headers = {"X-API-Key": api_key}

    create_payload = {
        "name": "Primary Binance",
        "platform": "BINANCE",
        "mode": "LIVE",
        "status": "PENDING",
        "capabilities_json": {"market_data": True, "trading": True},
        "config_json": {"recv_window": 5000},
    }

    resp = client.post("/api/connections", json=create_payload, headers=headers)
    assert resp.status_code == 200, resp.text
    connection = resp.json()
    connection_id = connection["connection_id"]
    assert connection["platform"] == "BINANCE"

    resp = client.get(f"/api/connections/{connection_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "Primary Binance"

    patch_payload = {
        "status": "CONNECTED",
        "meta_json": {"note": "connected for smoke test"},
    }
    resp = client.patch(f"/api/connections/{connection_id}", json=patch_payload, headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "CONNECTED"

    heartbeat_payload = {"latency_ms": 12.5, "status": "CONNECTED"}
    resp = client.post(
        f"/api/connections/{connection_id}/heartbeat",
        json=heartbeat_payload,
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["last_latency_ms"] == 12.5
    assert data["status"] == "CONNECTED"
