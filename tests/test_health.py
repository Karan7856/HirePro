from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_200():
    """GET /health should return 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_response_body():
    """GET /health should return {"status": "healthy"}."""
    response = client.get("/health")
    data = response.json()
    assert data == {"status": "healthy"}


def test_health_check_content_type():
    """GET /health should return application/json."""
    response = client.get("/health")
    assert response.headers["content-type"] == "application/json"
