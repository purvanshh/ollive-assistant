"""
Cost and latency analysis utilities for the evaluation results.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

RESULTS_PATH = Path(__file__).resolve().parent / "results.json"
OUTPUT_PATH = Path(__file__).resolve().parent / "cost_latency_table.md"

PRICING = {
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}


def estimate_tokens(text: str) -> int:
    """
    Estimate token count with a lightweight word-based heuristic.
    """
    return int(len(text.split()) * 1.3)


def generate_report() -> None:
    """
    Build a Markdown cost and latency summary from evaluation results.
    """
    if not RESULTS_PATH.exists():
        raise FileNotFoundError(f"Run run_eval.py first. Missing {RESULTS_PATH}")

    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    stats = {
        "oss": {"calls": 0, "latency": 0.0, "input_tokens": 0, "output_tokens": 0},
        "frontier": {
            "calls": 0,
            "latency": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
        },
    }

    for record in data:
        stats["oss"]["calls"] += 1
        stats["oss"]["latency"] += float(record["oss"]["latency_sec"])
        stats["oss"]["input_tokens"] += estimate_tokens(record["prompt"])
        stats["oss"]["output_tokens"] += estimate_tokens(record["oss"]["response"])

        stats["frontier"]["calls"] += 1
        stats["frontier"]["latency"] += float(record["frontier"]["latency_sec"])
        stats["frontier"]["input_tokens"] += estimate_tokens(record["prompt"])
        stats["frontier"]["output_tokens"] += estimate_tokens(
            record["frontier"]["response"]
        )

    oss_mean_latency = (
        stats["oss"]["latency"] / stats["oss"]["calls"] if stats["oss"]["calls"] else 0.0
    )
    frontier_mean_latency = (
        stats["frontier"]["latency"] / stats["frontier"]["calls"]
        if stats["frontier"]["calls"]
        else 0.0
    )

    frontier_model = os.getenv("FRONTIER_MODEL", "gpt-4.1")
    pricing = PRICING.get(frontier_model, PRICING["gpt-4.1"])
    frontier_input_cost = (
        stats["frontier"]["input_tokens"] / 1_000_000
    ) * pricing["input"]
    frontier_output_cost = (
        stats["frontier"]["output_tokens"] / 1_000_000
    ) * pricing["output"]
    frontier_total_cost = frontier_input_cost + frontier_output_cost

    oss_tokens_per_second = (
        stats["oss"]["output_tokens"] / stats["oss"]["latency"]
        if stats["oss"]["latency"]
        else 0.0
    )
    frontier_tokens_per_second = (
        stats["frontier"]["output_tokens"] / stats["frontier"]["latency"]
        if stats["frontier"]["latency"]
        else 0.0
    )

    markdown = f"""# Cost & Latency Analysis

| Metric | OSS (Qwen 0.5B) | Frontier ({frontier_model}) |
|--------|-----------------|-----------------------------|
| Total API Calls | {stats['oss']['calls']} | {stats['frontier']['calls']} |
| Mean Latency (s) | {oss_mean_latency:.3f} | {frontier_mean_latency:.3f} |
| Total Input Tokens (est.) | {stats['oss']['input_tokens']:,} | {stats['frontier']['input_tokens']:,} |
| Total Output Tokens (est.) | {stats['oss']['output_tokens']:,} | {stats['frontier']['output_tokens']:,} |
| Deployment Cost | $0.00 (HF Spaces Free Tier) | ${frontier_total_cost:.4f} |
| Tokens / Second (mean) | {oss_tokens_per_second:.1f} | {frontier_tokens_per_second:.1f} |

### Notes
- OSS deployment cost assumes Hugging Face Spaces free-tier CPU hosting.
- Frontier pricing uses the configured OpenAI model's public token pricing.
- Token counts are estimated via `len(text.split()) * 1.3`.
- Frontier latency includes API round-trip time; OSS latency is local generation time.
"""

    OUTPUT_PATH.write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    generate_report()
