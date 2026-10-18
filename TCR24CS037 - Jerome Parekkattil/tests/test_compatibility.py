import csv
from pathlib import Path

from src.capability_embedding import compatibility


ROOT = Path(__file__).resolve().parents[1]


def load_capabilities():
    with (ROOT / "data" / "capabilities.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    import ast

    numeric = {
        "execution_time_ms": int,
        "money_cost": float,
        "resource_cost": float,
        "risk": float,
        "reliability": float,
        "availability": float,
    }
    for row in rows:
        for key in ["inputs", "outputs", "preconditions", "effects", "constraints", "resources"]:
            row[key] = ast.literal_eval(row[key])
        for key, converter in numeric.items():
            row[key] = converter(row[key])
    return {row["id"]: row for row in rows}


def test_known_positive_pair_scores_above_negative_pair():
    caps = load_capabilities()
    positive = compatibility(caps["C1"], caps["C2"])
    negative = compatibility(caps["C1"], caps["C3"])
    assert positive > negative


def test_compatibility_is_directional():
    caps = load_capabilities()
    forward = compatibility(caps["C1"], caps["C2"])
    reverse = compatibility(caps["C2"], caps["C1"])
    assert forward != reverse
