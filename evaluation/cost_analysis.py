"""
Compute measured latency and token economics from evaluation results.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

RESULTS_PATH = Path(__file__).resolve().parent / "results.json"
OUTPUT_PATH = Path(__file__).resolve().parent / "cost_latency_table.md"

PRICING_PER_MILLION = {
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


def _percentile(sorted_values: list[float], percentile: float) -> float:
    """Compute a simple percentile from a sorted list."""
    if not sorted_values:
        return 0.0
    index = max(0, min(len(sorted_values) - 1, int(round(percentile * (len(sorted_values) - 1)))))
    return sorted_values[index]


def generate_report() -> None:
    """Create a markdown table with measured latency and cost metrics."""
    if not RESULTS_PATH.exists():
        raise FileNotFoundError(f"Run run_eval.py first. Missing {RESULTS_PATH}")

    rows = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    frontier_model = os.getenv("FRONTIER_MODEL", "gpt-4.1")
    pricing = PRICING_PER_MILLION.get(frontier_model, PRICING_PER_MILLION["gpt-4.1"])

    oss_latencies = [float(row["oss"]["response_time_ms"]) for row in rows]
    frontier_latencies = [float(row["frontier"]["response_time_ms"]) for row in rows]
    oss_tokens = [int(row["oss"]["token_count"]) for row in rows]
    frontier_tokens = [int(row["frontier"]["token_count"]) for row in rows]
    frontier_input_tokens = [int(row["frontier"]["input_tokens"]) for row in rows]
    frontier_output_tokens = [int(row["frontier"]["output_tokens"]) for row in rows]

    oss_avg_latency = sum(oss_latencies) / len(oss_latencies) if oss_latencies else 0.0
    frontier_avg_latency = (
        sum(frontier_latencies) / len(frontier_latencies) if frontier_latencies else 0.0
    )
    oss_p95_latency = _percentile(sorted(oss_latencies), 0.95)
    frontier_p95_latency = _percentile(sorted(frontier_latencies), 0.95)
    oss_avg_tokens = sum(oss_tokens) / len(oss_tokens) if oss_tokens else 0.0
    frontier_avg_tokens = (
        sum(frontier_tokens) / len(frontier_tokens) if frontier_tokens else 0.0
    )

    avg_frontier_input = (
        sum(frontier_input_tokens) / len(frontier_input_tokens)
        if frontier_input_tokens
        else 0.0
    )
    avg_frontier_output = (
        sum(frontier_output_tokens) / len(frontier_output_tokens)
        if frontier_output_tokens
        else 0.0
    )
    frontier_cost_per_call = (
        (avg_frontier_input / 1_000_000) * pricing["input"]
        + (avg_frontier_output / 1_000_000) * pricing["output"]
    )
    frontier_cost_per_1k = frontier_cost_per_call * 1000

    markdown = f"""# Cost & Latency Analysis

| Model | Avg Latency (ms) | p95 Latency (ms) | Avg Tokens | Cost per 1k calls ($) |
|-------|------------------:|-----------------:|-----------:|----------------------:|
| OSS (Qwen 0.5B) | {oss_avg_latency:.2f} | {oss_p95_latency:.2f} | {oss_avg_tokens:.2f} | 0.00 |
| Frontier ({frontier_model}) | {frontier_avg_latency:.2f} | {frontier_p95_latency:.2f} | {frontier_avg_tokens:.2f} | {frontier_cost_per_1k:.4f} |

### Notes
- OSS latency is measured from actual local inference runtime and is suitable for HF Spaces CPU benchmarking.
- Frontier token counts come from OpenAI usage objects, including tool-call follow-up requests when present.
- Frontier cost per 1k calls uses the configured model's public input/output pricing.
"""

    OUTPUT_PATH.write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    generate_report()
