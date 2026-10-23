from typing import Any
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.security import UserRepository, set_user_repository


def test_missing_token_returns_401(client: TestClient) -> None:
    """Unauthenticated requests without Authorization header must return 401 AUTH_ERROR."""
    response = client.get("/test-auth/me")
    assert response.status_code == 401

    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "AUTH_ERROR"
    assert "request_id" in data["error"]
    assert data["error"]["request_id"] == response.headers.get("X-Request-ID")


def test_invalid_token_returns_401(client: TestClient) -> None:
    """Requests with an invalid or expired token must return 401 AUTH_ERROR."""
    with patch(
        "firebase_admin.auth.verify_id_token",
        side_effect=ValueError("Firebase ID token verification failed"),
    ):
        response = client.get(
            "/test-auth/me",
            headers={"Authorization": "Bearer invalid-or-expired-token"},
        )
        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AUTH_ERROR"
        assert "request_id" in data["error"]
        assert data["error"]["request_id"] == response.headers.get("X-Request-ID")


def test_unregistered_user_returns_404(client: TestClient) -> None:
    """
    Valid Firebase token but missing Firestore user document must return 404 NOT_REGISTERED (not 401).
    """
    mock_repo = AsyncMock(spec=UserRepository)
    mock_repo.get_by_uid.return_value = None
    set_user_repository(mock_repo)

    try:
        with patch(
            "firebase_admin.auth.verify_id_token",
            return_value={"uid": "unregistered-uid-123", "email": "user@example.com"},
        ):
            response = client.get(
                "/test-auth/me",
                headers={"Authorization": "Bearer valid-firebase-token"},
            )
            assert response.status_code == 404

            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "NOT_REGISTERED"
            assert "request_id" in data["error"]
            assert data["error"]["request_id"] == response.headers.get("X-Request-ID")
    finally:
        set_user_repository(None)


def test_wrong_role_returns_403(client: TestClient) -> None:
    """Users with wrong role accessing a role-restricted endpoint must return 403 FORBIDDEN."""
    mock_repo = AsyncMock(spec=UserRepository)
    mock_repo.get_by_uid.return_value = {
        "uid": "patient-uid-456",
        "name": "Rahela Begum",
        "role": "patient",
    }
    set_user_repository(mock_repo)

    try:
        with patch(
            "firebase_admin.auth.verify_id_token",
            return_value={"uid": "patient-uid-456", "email": "patient@example.com"},
        ):
            # Endpoint requires "doctor", but user has role "patient"
            response = client.get(
                "/test-auth/doctor-only",
                headers={"Authorization": "Bearer valid-firebase-token"},
            )
            assert response.status_code == 403

            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == "FORBIDDEN"
            assert "request_id" in data["error"]
            assert data["error"]["request_id"] == response.headers.get("X-Request-ID")
    finally:
        set_user_repository(None)
