import pytest
from unittest.mock import patch, MagicMock
import httpx
from backend.oss_assistant.model import OSSAssistantModel

def test_oss_model_offline_fallback():
    """Verify that when Ollama is offline, the wrapper returns a graceful error."""
    model = OSSAssistantModel(model_name="Qwen/Qwen2.5-0.5B-Instruct")
    # Pinging a non-existent port to force connection refusal
    model.ollama_url = "http://localhost:59999"
    
    response = model.generate("Hello")
    assert "currently offline or unreachable" in response
    assert model.last_generation_info["token_count"] == 0

@patch("httpx.post")
def test_oss_model_success(mock_post):
    """Verify that the wrapper correctly parses Ollama success JSON responses."""
    # Setup mock response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {"role": "assistant", "content": "Hello! I am Qwen."},
        "prompt_eval_count": 12,
        "eval_count": 8
    }
    mock_post.return_value = mock_resp

    model = OSSAssistantModel(model_name="Qwen/Qwen2.5-0.5B-Instruct")
    response = model.generate("Hi assistant")
    
    assert response == "Hello! I am Qwen."
    assert model.last_generation_info["input_tokens"] == 12
    assert model.last_generation_info["output_tokens"] == 8
    assert model.last_generation_info["token_count"] == 20
    assert model.last_generation_info["model"] == "qwen2.5:0.5b"

@patch("httpx.stream")
def test_oss_model_streaming(mock_stream):
    """Verify that the streaming generator yields chunks properly."""
    # Setup mock stream context manager
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.iter_lines.return_value = [
        '{"message": {"content": "Hello"}, "done": false}',
        '{"message": {"content": " world"}, "done": false}',
        '{"message": {"content": "!"}, "done": true}'
    ]
    
    # Mock context manager behavior
    mock_stream.return_value.__enter__.return_value = mock_resp
    
    model = OSSAssistantModel(model_name="Qwen/Qwen2.5-0.5B-Instruct")
    chunks = list(model.generate_stream("Stream test"))
    
    assert "".join(chunks) == "Hello world!"
