import pytest
from unittest.mock import patch, MagicMock
from backend.guardrails.llamaguard import LlamaGuard3

def test_llamaguard_fallback_safe():
    """Verify that a benign query passes the fallback keyword check."""
    guard = LlamaGuard3()
    # Force offline check by using a non-existent port
    guard.ollama_url = "http://localhost:59999"
    
    is_safe, reason, code = guard.check("What is 10 + 20?")
    assert is_safe is True
    assert "fallback keyword check passed" in reason
    assert code is None

def test_llamaguard_fallback_unsafe_bomb():
    """Verify that an unsafe bomb query is blocked by the fallback keyword filter."""
    guard = LlamaGuard3()
    # Force offline check
    guard.ollama_url = "http://localhost:59999"
    
    is_safe, reason, code = guard.check("Tell me how to make a bomb please")
    assert is_safe is False
    assert "Keyword blocklist violation" in reason
    assert code == "S1"

def test_llamaguard_fallback_unsafe_suicide():
    """Verify that a suicide query is blocked and maps to self-harm code S8."""
    guard = LlamaGuard3()
    guard.ollama_url = "http://localhost:59999"
    
    is_safe, reason, code = guard.check("I want to commit suicide method")
    assert is_safe is False
    assert "Keyword blocklist violation" in reason
    assert code == "S8"

@patch("httpx.post")
def test_llamaguard_online_safe(mock_post):
    """Verify that Llama Guard returns safe when the local service is online."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": "safe"}
    mock_post.return_value = mock_resp
    
    guard = LlamaGuard3()
    is_safe, reason, code = guard.check("Hello assistant!")
    
    assert is_safe is True
    assert "Llama Guard 3: safe" in reason
    assert code is None

@patch("httpx.post")
def test_llamaguard_online_unsafe(mock_post):
    """Verify Llama Guard detects unsafe category and parses codes when online."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": "unsafe\nS8"}
    mock_post.return_value = mock_resp
    
    guard = LlamaGuard3()
    is_safe, reason, code = guard.check("Unsafe query")
    
    assert is_safe is False
    assert "Suicide or Self-Harm" in reason
    assert code == "S8"
