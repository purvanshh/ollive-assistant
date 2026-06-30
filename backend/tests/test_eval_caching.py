import os
import json
import pytest
from unittest.mock import MagicMock, patch
from evaluation.judge import JudgeModel

@pytest.fixture
def clean_cache():
    """Ensure judge_cache.json is clean before and after tests."""
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cache_path = os.path.join(repo_root, "evaluation", "judge_cache.json")
    if os.path.exists(cache_path):
        os.remove(cache_path)
    yield cache_path
    if os.path.exists(cache_path):
        os.remove(cache_path)

@patch("evaluation.judge.OpenAI")
def test_judge_scoring_and_compare_caching(mock_openai_class, clean_cache):
    # Setup OpenAI client mock
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Mock completion for score
    mock_completion_score = MagicMock()
    mock_completion_score.choices = [
        MagicMock(message=MagicMock(content="Score: 5\nJustification: Perfect answer."))
    ]
    
    # Mock completion for compare
    mock_completion_compare = MagicMock()
    mock_completion_compare.choices = [
        MagicMock(message=MagicMock(content="Winner: A\nReasoning: Model A is better."))
    ]
    
    # Define side effect for mock client chat.completions.create
    def completions_side_effect(*args, **kwargs):
        messages = kwargs.get("messages", [])
        system_content = messages[0]["content"]
        if "expert evaluator scoring" in system_content:
            return mock_completion_score
        else:
            return mock_completion_compare

    mock_client.chat.completions.create.side_effect = completions_side_effect

    judge = JudgeModel(model_name="gpt-4.1-mini")
    
    # 1. First score call (should call OpenAI API)
    res1 = judge.score("What is 1+1?", "It is 2.", "factual_accuracy")
    assert res1["score"] == 5
    assert res1["justification"] == "Perfect answer."
    assert mock_client.chat.completions.create.call_count == 1

    # 2. Second score call with same inputs (should return cached result and NOT call OpenAI)
    res2 = judge.score("What is 1+1?", "It is 2.", "factual_accuracy")
    assert res2["score"] == 5
    assert res2["justification"] == "Perfect answer."
    assert mock_client.chat.completions.create.call_count == 1  # count remains 1
    
    # 3. First compare call (should call OpenAI API)
    cmp1 = judge.compare("What is 1+1?", "It is 2.", "It is 3.")
    assert cmp1["winner"] == "a"
    assert cmp1["reasoning"] == "Model A is better."
    assert mock_client.chat.completions.create.call_count == 2
    
    # 4. Second compare call with same inputs (should return cached result and NOT call OpenAI)
    cmp2 = judge.compare("What is 1+1?", "It is 2.", "It is 3.")
    assert cmp2["winner"] == "a"
    assert cmp2["reasoning"] == "Model A is better."
    assert mock_client.chat.completions.create.call_count == 2  # count remains 2
    
    # Verify cache file is written to disk
    assert os.path.exists(clean_cache)
    with open(clean_cache, "r", encoding="utf-8") as f:
        cache_data = json.load(f)
        assert len(cache_data) == 2
