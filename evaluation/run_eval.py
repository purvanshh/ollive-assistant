"""Run the evaluation suite across both assistants and persist results."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.judge import JudgeModel
from evaluation.prompts import BIAS_PROMPTS, FACTUAL_PROMPTS, JAILBREAK_PROMPTS
from frontier_assistant.model import FrontierAssistantModel
from guardrails.filter import SafetyFilter
from oss_assistant.model import OSSAssistantModel

load_dotenv(REPO_ROOT / ".env")


def _prompt_groups() -> List[Tuple[str, str, List[str]]]:
    """Map prompt sets to the dimension they are meant to test."""
    return [
        ("hallucination", "factual", FACTUAL_PROMPTS),
        ("bias", "bias", BIAS_PROMPTS),
        ("safety", "jailbreak", JAILBREAK_PROMPTS),
    ]


def _evaluate_model(
    model_name: str,
    model: object,
    judge: JudgeModel,
    safety_filter: SafetyFilter,
) -> List[Dict[str, object]]:
    """Evaluate one assistant across all prompt groups."""
    results: List[Dict[str, object]] = []

    for dimension, category, prompts in _prompt_groups():
        for prompt in prompts:
            is_safe, reason = safety_filter.check(prompt)
            if is_safe:
                response = model.generate(prompt, [])
            else:
                response = f"Request blocked by safety filter. Reason: {reason}"

            judged_input = f"User prompt: {prompt}\nAssistant response: {response}"
            judgment = judge.score(judged_input, dimension)

            results.append(
                {
                    "model": model_name,
                    "category": category,
                    "dimension": dimension,
                    "prompt": prompt,
                    "response": response,
                    "score": judgment["score"],
                    "justification": judgment["justification"],
                    "blocked": not is_safe,
                    "block_reason": reason,
                }
            )

    return results


def main() -> None:
    """Run the full evaluation and write results to disk."""
    output_path = REPO_ROOT / "evaluation" / "results.json"

    judge = JudgeModel()
    safety_filter = SafetyFilter()
    models = {
        "oss_assistant": OSSAssistantModel(),
        "frontier_assistant": FrontierAssistantModel(),
    }

    all_results: List[Dict[str, object]] = []
    for model_name, model in models.items():
        all_results.extend(_evaluate_model(model_name, model, judge, safety_filter))

    output_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"Saved {len(all_results)} evaluation results to {output_path}")


if __name__ == "__main__":
    main()
