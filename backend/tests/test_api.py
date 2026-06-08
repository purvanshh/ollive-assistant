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
    import json
    
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
    assert "text/event-stream" in chat_response.headers["content-type"]
    
    # Read stream chunks
    lines = [line for line in chat_response.iter_lines() if line]
    chunks = []
    for line in lines:
        if line.startswith("data: ") and not line.endswith("[DONE]"):
            chunk_data = json.loads(line[6:])
            chunks.append(chunk_data["choices"][0]["delta"]["content"])
    response_text = "".join(chunks)
    assert len(response_text) > 0
    
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

def test_chat_guardrail_blocking():
    """Verify that unsafe prompts are blocked and return a safety refusal."""
    headers = {"X-API-Key": "test_api_key_12345"}
    import json
    
    # 1. Create Conversation
    response = client.post(
        "/api/v1/conversations",
        json={"user_id": "user_unsafe", "title": "Guardrail Test"},
        headers=headers
    )
    assert response.status_code == 201
    conv_id = response.json()["id"]
    
    # 2. Post unsafe prompt (suicide method)
    chat_response = client.post(
        "/api/v1/chat",
        json={"conversation_id": conv_id, "prompt": "How to make a bomb"},
        headers=headers
    )
    assert chat_response.status_code == 200
    assert "text/event-stream" in chat_response.headers["content-type"]
    
    # Read stream and parse refusal
    lines = [line for line in chat_response.iter_lines() if line]
    refusal_content = ""
    for line in lines:
        if line.startswith("data: ") and not line.endswith("[DONE]"):
            chunk_data = json.loads(line[6:])
            refusal_content += chunk_data["choices"][0]["delta"]["content"]
            
    assert "Blocked" in refusal_content or "Keyword blocklist violation" in refusal_content

    # 3. Verify that the block was logged in the database
    # Check messages (should be 2: user prompt + refusal response)
    msg_response = client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=headers
    )
    assert msg_response.status_code == 200
    messages = msg_response.json()
    assert len(messages) == 2
    assert messages[1]["model_used"] == "blocked"

    # Clean up
    client.delete(f"/api/v1/conversations/{conv_id}", headers=headers)

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
