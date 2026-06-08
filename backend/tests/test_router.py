import pytest
from backend.app.routers.chat import classify_intent
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_intent_classification():
    # Test coding intent
    intent, model, reason = classify_intent("Write a Python script to compute primes")
    assert intent == "coding"
    assert model == "frontier"
    assert "coding" in reason

    # Test math complex intent
    intent, model, reason = classify_intent("Solve the equation x^2 + 5x + 6 = 0")
    assert intent == "math"
    assert model == "frontier"
    assert "math" in reason

    # Test reasoning intent
    intent, model, reason = classify_intent("Explain step-by-step why the sky is blue")
    assert intent == "reasoning"
    assert model == "frontier"
    assert "reasoning" in reason

    # Test simple calculator math intent
    intent, model, reason = classify_intent("Calculate 25 + 75")
    assert intent == "calculator"
    assert model == "oss"
    assert "calculator" in reason

    # Test default simple chat intent
    intent, model, reason = classify_intent("Hello! How is the weather today?")
    assert intent == "simple_chat"
    assert model == "oss"
    assert "simple chat" in reason


def test_api_routing_with_override():
    import json
    headers = {"X-API-Key": "test_api_key_12345"}
    
    # 1. Create Conversation
    res = client.post(
        "/api/v1/conversations",
        json={"user_id": "router_test_user", "title": "Router Check"},
        headers=headers
    )
    assert res.status_code == 201
    conv_id = res.json()["id"]

    # 2. Forced Frontier Override
    res_frontier = client.post(
        "/api/v1/chat",
        json={"conversation_id": conv_id, "prompt": "Hi", "model_override": "frontier"},
        headers=headers
    )
    assert res_frontier.status_code == 200
    
    lines = [line for line in res_frontier.iter_lines() if line]
    first_chunk = None
    for line in lines:
        if line.startswith("data: ") and not line.endswith("[DONE]"):
            chunk_data = json.loads(line[6:])
            if "routing_reason" in chunk_data:
                first_chunk = chunk_data
                break
                
    assert first_chunk is not None
    assert "force frontier" in first_chunk["routing_reason"]
    assert "gpt-4" in first_chunk["model"] or "gemini" in first_chunk["model"].lower()

    # 3. Clean up
    client.delete(f"/api/v1/conversations/{conv_id}", headers=headers)
