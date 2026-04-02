"""Health endpoint tests."""


def test_health_returns_healthy(client):
    """Health endpoint should return success with healthy status."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
