from typing import Any, Generator
from unittest.mock import MagicMock

import pytest
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from app.core.firebase import set_firestore_client
from app.core.security import (
    User,
    get_current_user,
    get_firebase_user,
    require_role,
    set_user_repository,
)
from app.main import create_app

test_router = APIRouter(prefix="/test-auth", tags=["Testing"])


@test_router.get("/token-only")
async def token_only_endpoint(user_data: dict[str, Any] = Depends(get_firebase_user)) -> dict[str, Any]:
    return {"status": "ok", "uid": user_data.get("uid")}


@test_router.get("/me")
async def current_user_endpoint(user: User = Depends(get_current_user)) -> dict[str, Any]:
    return {"uid": user.uid, "role": user.role, "name": getattr(user, "name", None)}


@test_router.get("/doctor-only")
async def doctor_only_endpoint(user: User = Depends(require_role("doctor"))) -> dict[str, Any]:
    return {"status": "allowed", "uid": user.uid, "role": user.role}


@pytest.fixture
def mock_firestore() -> Generator[MagicMock, None, None]:
    """Mock Firestore client so tests do not call real Firebase."""
    mock = MagicMock()
    set_firestore_client(mock)
    yield mock
    set_firestore_client(None)


@pytest.fixture
def test_app(mock_firestore: MagicMock) -> Any:
    """Create test application with test routes included."""
    application = create_app()
    application.include_router(test_router)
    return application


@pytest.fixture
def client(test_app: Any) -> Generator[TestClient, None, None]:
    """Provide a TestClient for testing endpoints."""
    with TestClient(test_app) as test_client:
        yield test_client
