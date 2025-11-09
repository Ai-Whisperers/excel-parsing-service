import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "python_layer" in data
    assert data["python_layer"] == "healthy"

def test_flight_list_endpoint():
    response = client.get("/api/v1/flight/list")
    assert response.status_code == 200
    data = response.json()
    assert "flights" in data
