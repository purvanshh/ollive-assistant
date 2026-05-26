"""Generate a comparison chart from saved evaluation results."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import seaborn as sns


def _load_results(results_path: Path) -> List[Dict[str, object]]:
    """Load evaluation results from disk."""
    return json.loads(results_path.read_text(encoding="utf-8"))


def _mean_scores(results: List[Dict[str, object]]) -> Dict[str, Dict[str, float]]:
    """Aggregate mean score per model per dimension."""
    totals: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for row in results:
        model = str(row["model"])
        dimension = str(row["dimension"])
        totals[model][dimension] += float(row["score"])
        counts[model][dimension] += 1

    means: Dict[str, Dict[str, float]] = {}
    for model, dimension_totals in totals.items():
        means[model] = {}
        for dimension, total in dimension_totals.items():
            means[model][dimension] = total / counts[model][dimension]
    return means


def main() -> None:
    """Create a grouped bar chart comparing both assistants."""
    repo_root = Path(__file__).resolve().parents[1]
    results_path = repo_root / "evaluation" / "results.json"
    output_path = repo_root / "evaluation" / "comparison.png"

    results = _load_results(results_path)
    means = _mean_scores(results)

    plot_data = {"dimension": [], "model": [], "score": []}
    for model, dimensions in means.items():
        for dimension, score in dimensions.items():
            plot_data["dimension"].append(dimension.title())
            plot_data["model"].append(model.replace("_", " ").title())
            plot_data["score"].append(score)

    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=plot_data, x="dimension", y="score", hue="model")
    ax.set_title("Assistant Comparison by Evaluation Dimension")
    ax.set_xlabel("Dimension")
    ax.set_ylabel("Mean Score")
    ax.set_ylim(0, 1)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"Saved comparison chart to {output_path}")


if __name__ == "__main__":
    main()
