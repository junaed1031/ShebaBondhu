from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """Test that GET /health returns 200 and expected health metadata."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("version") == "1.0.0"
    assert data.get("firestore") == "connected"
    assert "timestamp" in data
    assert "X-Request-ID" in response.headers
