"""
Evaluation report generator.
Reads results.json, computes per-dimension means, and exports a comparison chart.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

RESULTS_PATH = Path(__file__).resolve().parent / "results.json"
OUTPUT_PATH = Path(__file__).resolve().parent / "comparison.png"


def generate_report() -> None:
    """
    Load evaluation results and render a grouped bar chart for both models.
    """
    if not RESULTS_PATH.exists():
        raise FileNotFoundError(f"Run run_eval.py first. Missing {RESULTS_PATH}")

    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))

    dims = ["hallucination", "bias", "safety"]
    dim_labels = {
        "hallucination": "Factual Accuracy",
        "bias": "Bias & Stereotype Safety",
        "safety": "Jailbreak Resistance",
    }

    plot_rows: list[dict[str, object]] = []
    for dim in dims:
        oss_scores = [row["oss"]["score"] for row in data if row["dimension"] == dim]
        frontier_scores = [row["frontier"]["score"] for row in data if row["dimension"] == dim]

        oss_mean = sum(oss_scores) / len(oss_scores) if oss_scores else 0.0
        frontier_mean = sum(frontier_scores) / len(frontier_scores) if frontier_scores else 0.0

        plot_rows.append(
            {"Model": "OSS (Qwen 0.5B)", "Dimension": dim_labels[dim], "Score": oss_mean}
        )
        plot_rows.append(
            {"Model": "Frontier (OpenAI)", "Dimension": dim_labels[dim], "Score": frontier_mean}
        )

    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(10, 6))
    df = pd.DataFrame(plot_rows)
    sns.barplot(
        data=df,
        x="Dimension",
        y="Score",
        hue="Model",
        palette={"OSS (Qwen 0.5B)": "#4C72B0", "Frontier (OpenAI)": "#DD8452"},
        ax=ax,
    )

    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Mean Score (Higher = Better)")
    ax.set_xlabel("")
    ax.set_title("AI Assistant Evaluation: OSS vs Frontier Model", pad=20)
    ax.legend(title="", loc="lower right")

    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", padding=3, fontsize=11)

    plt.tight_layout()
    fig.savefig(OUTPUT_PATH, dpi=300, bbox_inches="tight")
    print(f"Report saved to {OUTPUT_PATH}")

    print("\n" + "=" * 50)
    print("EVALUATION SUMMARY")
    print("=" * 50)
    for dim in dims:
        oss_mean = next(
            row["Score"]
            for row in plot_rows
            if row["Dimension"] == dim_labels[dim] and row["Model"] == "OSS (Qwen 0.5B)"
        )
        frontier_mean = next(
            row["Score"]
            for row in plot_rows
            if row["Dimension"] == dim_labels[dim] and row["Model"] == "Frontier (OpenAI)"
        )
        print(f"{dim_labels[dim]:30s} | OSS: {oss_mean:.2f} | Frontier: {frontier_mean:.2f}")
    print("=" * 50)


if __name__ == "__main__":
    generate_report()
