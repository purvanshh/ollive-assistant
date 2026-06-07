import pytest
import os
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_env():
    """Ensure environment is set for tests."""
    os.environ["API_KEY"] = "test_api_key_12345"

def test_health_check_open():
    """Verify health check is open and returns success."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "database" in data["dependencies"]

def test_protected_routes_unauthorized():
    """Verify other endpoints block requests without valid key."""
    # List conversations without header
    response = client.get("/api/v1/conversations?user_id=test_user")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"

    # List conversations with invalid header
    response = client.get(
        "/api/v1/conversations?user_id=test_user",
        headers={"X-API-Key": "wrong_key"}
    )
    assert response.status_code == 401

def test_conversation_flow_authorized():
    """Verify standard CRUD and chat completions work with correct auth."""
    headers = {"X-API-Key": "test_api_key_12345"}
    
    # 1. Create Conversation
    response = client.post(
        "/api/v1/conversations",
        json={"user_id": "user_abc", "title": "API Test"},
        headers=headers
    )
    assert response.status_code == 201
    conv = response.json()
    assert conv["user_id"] == "user_abc"
    conv_id = conv["id"]
    
    # 2. Chat completion (saves messages)
    chat_response = client.post(
        "/api/v1/chat",
        json={"conversation_id": conv_id, "prompt": "Hi assistant, this is a test!"},
        headers=headers
    )
    assert chat_response.status_code == 200
    chat_data = chat_response.json()
    assert "stub response" in chat_data["content"]
    
    # 3. Retrieve messages
    msg_response = client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=headers
    )
    assert msg_response.status_code == 200
    messages = msg_response.json()
    assert len(messages) == 2  # User message + assistant stub
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    
    # 4. Clean up
    del_response = client.delete(
        f"/api/v1/conversations/{conv_id}",
        headers=headers
    )
    assert del_response.status_code == 204

def test_rate_limiting():
    """Verify that requests exceeding limits receive 429."""
    # Reset limiter limits if needed, or trigger 429
    # Our default limit is 30/minute. Let's make 35 quick requests to /api/v1/health
    # which is not protected but is bound by default limits.
    # Note: TestClient can sometimes bypass limits unless configured, but slowapi supports TestClient.
    responses = []
    for _ in range(35):
        responses.append(client.get("/api/v1/health"))
        
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes

def test_metrics_endpoint():
    """Verify that /metrics endpoint is open and exposes Prometheus metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "ollive_requests_total" in response.text
    assert "ollive_request_latency_seconds" in response.text
    assert "ollive_active_conversations" in response.text
