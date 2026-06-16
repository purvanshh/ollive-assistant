"""
End-to-end evaluation runner.
Loads Model A and Model B, feeds all prompts, judges responses,
saves comparison results to SQLite DB, and writes results.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Ensure backend directory is also in path if needed, but REPO_ROOT should suffice
from backend.app.database import SessionLocal
from backend.app.repositories.eval import EvalRepository
from evaluation.judge import JudgeModel
from frontier_assistant.model import FrontierModel

import importlib.util
def _load_prompts():
    prompts_path = Path(__file__).resolve().parent / "suites" / "v1.0" / "prompts.py"
    spec = importlib.util.spec_from_file_location("prompts", prompts_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.PROMPT_CATEGORIES
    raise ImportError(f"Could not load prompts from {prompts_path}")

PROMPT_CATEGORIES = _load_prompts()

try:
    from oss_assistant.model import OSSModel
except ImportError:
    from oss_assistant.model import OSSAssistantModel as OSSModel

load_dotenv(REPO_ROOT / ".env")

RESULTS_PATH = Path(__file__).resolve().parent / "results.json"


def load_model(name: str):
    """Resolve a model identifier to an assistant instance."""
    name_lower = name.lower()
    if name_lower == "oss" or "qwen" in name_lower:
        model_name = "Qwen/Qwen2.5-0.5B-Instruct" if name_lower == "oss" else name
        return OSSModel(model_name=model_name)
    else:
        model_name = os.getenv("FRONTIER_MODEL", "gpt-4.1") if name_lower == "frontier" else name
        return FrontierModel(model_name=model_name)


def run_evaluation() -> None:
    """
    Run evaluation using CLI arguments and save results to DB and results.json.
    """
    parser = argparse.ArgumentParser(description="Run Ollive Evaluation Suite.")
    parser.add_argument("--model-a", type=str, default="oss", help="Model A name/type ('oss' or identifier)")
    parser.add_argument("--model-b", type=str, default="frontier", help="Model B name/type ('frontier' or identifier)")
    parser.add_argument("--judge", type=str, default="gpt-4.1-mini", help="Judge model name")
    parser.add_argument("--run-type", type=str, default="full", choices=["full", "smoke"], help="Evaluation run type ('full' or 'smoke')")
    args = parser.parse_args()

    print(f"Initializing models... Model A: {args.model_a}, Model B: {args.model_b}")
    model_a = load_model(args.model_a)
    model_b = load_model(args.model_b)
    judge = JudgeModel(model_name=args.judge)

    db = SessionLocal()
    eval_run = EvalRepository.create_run(
        db=db,
        run_type=args.run_type,
        judge_model=args.judge,
        passed=False,
        report_path=str(RESULTS_PATH)
    )

    results: list[dict[str, object]] = []

    try:
        for category, (prompts, dimension) in PROMPT_CATEGORIES.items():
            prompts_to_run = prompts[:2] if args.run_type == "smoke" else prompts
            for idx, prompt in enumerate(prompts_to_run, start=1):
                print(f"[{category}] Prompt {idx}/{len(prompts_to_run)}: {prompt[:60]}...")

                # Run Model A (Mapped to "oss" in json schema for compatibility with reporting scripts)
                start = time.perf_counter()
                response_a = model_a.generate(prompt, history=[])
                latency_a = round(time.perf_counter() - start, 3)
                metrics_a = getattr(model_a, "last_generation_info", {})
                judgment_a = judge.score(prompt, response_a, dimension)

                # Run Model B (Mapped to "frontier" in json schema for compatibility with reporting scripts)
                start = time.perf_counter()
                response_b = model_b.generate(prompt, history=[])
                latency_b = round(time.perf_counter() - start, 3)
                metrics_b = getattr(model_b, "last_generation_info", {})
                judgment_b = judge.score(prompt, response_b, dimension)

                # Blind A/B Comparison
                comparison = judge.compare(prompt, response_a, response_b)
                winner = comparison.get("winner", "tie")
                reasoning = comparison.get("reasoning", "No explanation provided.")

                # Save comparison directly to database
                prompt_id = f"{category}_{idx}"
                EvalRepository.create_result(
                    db=db,
                    eval_run_id=eval_run.id,
                    prompt_id=prompt_id,
                    model_a=args.model_a,
                    model_b=args.model_b,
                    winner=winner,
                    judge_reasoning=reasoning
                )

                # Append results mapped to "oss" and "frontier" for reporting compatibility
                results.append(
                    {
                        "category": category,
                        "dimension": dimension,
                        "prompt": prompt,
                        "winner": winner,
                        "comparison_reasoning": reasoning,
                        "oss": {
                            "response": response_a,
                            "score": judgment_a["score"],
                            "justification": judgment_a["justification"],
                            "latency_sec": latency_a,
                            "response_time_ms": metrics_a.get(
                                "response_time_ms", round(latency_a * 1000, 2)
                            ),
                            "token_count": metrics_a.get("token_count", 0),
                            "input_tokens": metrics_a.get("input_tokens", 0),
                            "output_tokens": metrics_a.get("output_tokens", 0),
                        },
                        "frontier": {
                            "response": response_b,
                            "score": judgment_b["score"],
                            "justification": judgment_b["justification"],
                            "latency_sec": latency_b,
                            "response_time_ms": metrics_b.get(
                                "response_time_ms", round(latency_b * 1000, 2)
                            ),
                            "token_count": metrics_b.get("token_count", 0),
                            "input_tokens": metrics_b.get("input_tokens", 0),
                            "output_tokens": metrics_b.get("output_tokens", 0),
                        },
                    }
                )

        # Mark evaluation run as successful (passed = True)
        eval_run.passed = True
        db.commit()

        # Save to results.json
        RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nEvaluation complete. Results saved to {RESULTS_PATH} and database run ID: {eval_run.id}")

    except Exception as e:
        print(f"Error during evaluation run: {e}")
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    run_evaluation()
