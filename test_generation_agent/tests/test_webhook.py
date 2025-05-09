"""
Test script for the webhook functionality.
"""
import json
import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the app
from app.main import app

# Create a test client
client = TestClient(app)

def get_mock_payload():
    """Load the mock payload from the JSON file"""
    mock_file = Path(__file__).resolve().parent / "mock_payload.json"
    with open(mock_file, "r") as f:
        return json.load(f)

def test_health_endpoint():
    """Test the health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"

def test_mock_webhook_endpoint():
    """Test the mock webhook endpoint"""
    payload = get_mock_payload()
    response = client.post("/api/v1/webhook/mock", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert "story_id" in data["details"]
    assert data["details"]["story_id"] == "123"

def test_mock_webhook_with_invalid_payload():
    """Test the mock webhook endpoint with invalid payload"""
    # Empty payload
    response = client.post("/api/v1/webhook/mock", json={})
    assert response.status_code == 400
    
    # Missing required fields
    response = client.post("/api/v1/webhook/mock", json={"resource": {}})
    assert response.status_code == 400

def test_azure_devops_webhook_endpoint():
    """Test the Azure DevOps webhook endpoint"""
    payload = get_mock_payload()
    
    # Without signature validation in testing
    response = client.post("/api/v1/webhook/azure-devops", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received" or data["status"] == "ignored"
    
    if data["status"] == "received":
        assert "story_id" in data["details"]
        assert data["details"]["story_id"] == "123"

def test_webhook_with_different_event_types():
    """Test the webhook with different event types"""
    payload = get_mock_payload()
    
    # Test with workitem.updated event
    payload["eventType"] = "workitem.updated"
    response = client.post("/api/v1/webhook/mock", json=payload)
    assert response.status_code == 200
    
    # Test with unsupported event type
    payload["eventType"] = "workitem.deleted"
    response = client.post("/api/v1/webhook/azure-devops", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"

if __name__ == "__main__":
    # Run the tests manually with pytest
    pytest.main(["-xvs", __file__])
