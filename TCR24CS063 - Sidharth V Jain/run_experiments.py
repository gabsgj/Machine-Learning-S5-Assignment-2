from pathlib import Path
import csv, json
import matplotlib.pyplot as plt
import numpy as np
from capability_embedding import run_all

OUT = Path("artifacts")
OUT.mkdir(exist_ok=True)

result = run_all("dataset.json")

with open(OUT / "metrics.json", "w", encoding="utf-8") as f:
    json.dump({
        "compatibility_metrics": result["compatibility_metrics"],
        "alternative_mean": result["alternative_mean"],
        "irrelevant_score": result["irrelevant_score"],
        "composite_component_scores": result["composite_component_scores"],
        "dimensions": result["dimensions"],
        "composite_reliability": result["composite"].reliability,
        "composite_cost": result["composite"].cost
    }, f, indent=2)

for filename, rows in [
    ("compatibility.csv", result["compatibility_rows"]),
    ("similarity.csv", result["similarity_rows"]),
    ("goal_relevance.csv", result["goal_relevance"]),
    ("operational.csv", result["operational_rows"])
]:
    fields = sorted({k for r in rows for k in r})
    with open(OUT / filename, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

with open(OUT / "composite.json", "w", encoding="utf-8") as f:
    json.dump(result["composite"].__dict__, f, indent=2)

rows = result["compatibility_rows"]
labels = [f'{r["a"]}→{r["b"]}' for r in rows]
scores = [r["score"] for r in rows]
plt.figure(figsize=(8, 4.5))
plt.bar(labels, scores)
plt.axhline(0.75, linestyle="--", label="composition threshold")
plt.ylabel("Compatibility score")
plt.xlabel("Capability pair")
plt.title("Formal capability compatibility")
plt.legend()
plt.tight_layout()
plt.savefig(OUT / "compatibility_scores.png", dpi=220)
plt.close()

rows = result["similarity_rows"]
labels = [r["pair"] for r in rows]
scores = [r["score"] for r in rows]
plt.figure(figsize=(7, 4.5))
plt.bar(labels, scores)
plt.axhline(0, linestyle=":")
plt.ylabel("Structured similarity")
plt.xlabel("Pair")
plt.title("Alternative implementations vs. irrelevant capability")
plt.tight_layout()
plt.savefig(OUT / "similarity_comparison.png", dpi=220)
plt.close()

rows = result["goal_relevance"]
labels = [r["id"] for r in rows]
scores = [r["score"] for r in rows]
plt.figure(figsize=(8, 4.5))
plt.bar(labels, scores)
plt.ylabel("Goal-effect fraction")
plt.xlabel("Capability")
plt.title("Capability relevance to application goal")
plt.tight_layout()
plt.savefig(OUT / "goal_relevance.png", dpi=220)
plt.close()

print(json.dumps({
    "compatibility_metrics": result["compatibility_metrics"],
    "alternative_mean": result["alternative_mean"],
    "irrelevant_score": result["irrelevant_score"],
    "composite_reliability": result["composite"].reliability,
    "composite_cost": result["composite"].cost,
    "dimensions": result["dimensions"]
}, indent=2))
