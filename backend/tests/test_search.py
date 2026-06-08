import pytest
import json
from types import SimpleNamespace
from backend.app.tools.search import web_search
from backend.frontier_assistant.tools import WEB_SEARCH_SCHEMA, execute_tool_call

def test_web_search_fallback():
    # Test that web_search executes and returns valid structure even when keys are missing or offline
    results = web_search("ollive gateway project")
    assert isinstance(results, list)
    assert len(results) > 0
    for r in results:
        assert "title" in r
        assert "link" in r
        assert "snippet" in r

def test_web_search_schema():
    # Verify search schema parameters and structure
    assert WEB_SEARCH_SCHEMA["type"] == "function"
    assert WEB_SEARCH_SCHEMA["function"]["name"] == "web_search"
    assert "query" in WEB_SEARCH_SCHEMA["function"]["parameters"]["properties"]

def test_execute_tool_call_search():
    # Mock a tool call for web search and verify execution
    tc = SimpleNamespace(
        id="call_abc123",
        function=SimpleNamespace(
            name="web_search",
            arguments=json.dumps({"query": "testing gateway search"})
        )
    )
    result_msg = execute_tool_call(tc)
    assert result_msg["role"] == "tool"
    assert result_msg["tool_call_id"] == "call_abc123"
    
    # Content must be a JSON string of results
    content_data = json.loads(result_msg["content"])
    assert isinstance(content_data, list)
    assert len(content_data) > 0
    assert "title" in content_data[0]
