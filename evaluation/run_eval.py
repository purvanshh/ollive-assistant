"""
End-to-end evaluation runner.
Loads both assistants, feeds all prompts, judges responses, and writes results.json.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.judge import JudgeModel
from evaluation.prompts import PROMPT_CATEGORIES
from frontier_assistant.model import FrontierModel

try:
    from oss_assistant.model import OSSModel
except ImportError:
    from oss_assistant.model import OSSAssistantModel as OSSModel

load_dotenv(REPO_ROOT / ".env")

RESULTS_PATH = Path(__file__).resolve().parent / "results.json"


def run_evaluation() -> None:
    """
    Run all prompts through both assistants and persist judged results.
    """
    oss = OSSModel(model_name="Qwen/Qwen2.5-0.5B-Instruct")
    frontier = FrontierModel(model_name=os.getenv("FRONTIER_MODEL", "gpt-4.1"))
    judge = JudgeModel(model_name=os.getenv("JUDGE_MODEL", "gpt-4.1-mini"))

    results: list[dict[str, object]] = []

    for category, (prompts, dimension) in PROMPT_CATEGORIES.items():
        for idx, prompt in enumerate(prompts, start=1):
            print(f"[{category}] Prompt {idx}/{len(prompts)}: {prompt[:60]}...")

            start = time.perf_counter()
            # The local OSS scaffold expects a list history, so we pass an empty
            # conversation here instead of mutating the existing Phase 1 code.
            oss_response = oss.generate(prompt, history=[])
            oss_latency = round(time.perf_counter() - start, 3)
            oss_metrics = getattr(oss, "last_generation_info", {})
            oss_judgment = judge.score(prompt, oss_response, dimension)

            start = time.perf_counter()
            frontier_response = frontier.generate(prompt, history=[])
            frontier_latency = round(time.perf_counter() - start, 3)
            frontier_metrics = getattr(frontier, "last_generation_info", {})
            frontier_judgment = judge.score(prompt, frontier_response, dimension)

            results.append(
                {
                    "category": category,
                    "dimension": dimension,
                    "prompt": prompt,
                    "oss": {
                        "response": oss_response,
                        "score": oss_judgment["score"],
                        "justification": oss_judgment["justification"],
                        "latency_sec": oss_latency,
                        "response_time_ms": oss_metrics.get(
                            "response_time_ms", round(oss_latency * 1000, 2)
                        ),
                        "token_count": oss_metrics.get("token_count", 0),
                        "input_tokens": oss_metrics.get("input_tokens", 0),
                        "output_tokens": oss_metrics.get("output_tokens", 0),
                    },
                    "frontier": {
                        "response": frontier_response,
                        "score": frontier_judgment["score"],
                        "justification": frontier_judgment["justification"],
                        "latency_sec": frontier_latency,
                        "response_time_ms": frontier_metrics.get(
                            "response_time_ms", round(frontier_latency * 1000, 2)
                        ),
                        "token_count": frontier_metrics.get("token_count", 0),
                        "input_tokens": frontier_metrics.get("input_tokens", 0),
                        "output_tokens": frontier_metrics.get("output_tokens", 0),
                    },
                }
            )

    RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nEvaluation complete. Results saved to {RESULTS_PATH}")


if __name__ == "__main__":
    run_evaluation()
