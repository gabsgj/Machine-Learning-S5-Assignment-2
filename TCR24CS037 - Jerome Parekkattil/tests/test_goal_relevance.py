import csv
import ast
from pathlib import Path

from src.capability_embedding import goal_relevance

ROOT = Path(__file__).resolve().parents[1]


def load_data():
    with (ROOT / "data" / "capabilities.csv").open(newline="", encoding="utf-8") as f:
        caps = list(csv.DictReader(f))
    with (ROOT / "data" / "goals.csv").open(newline="", encoding="utf-8") as f:
        goals = list(csv.DictReader(f))

    for row in caps:
        row["effects"] = ast.literal_eval(row["effects"])
    for row in goals:
        row["conditions"] = [x.strip() for x in row["conditions"].split(";") if x.strip()]
    return {c["id"]: c for c in caps}, {g["goal_id"]: g for g in goals}


def test_goal_relevance_returns_finite_scalar():
    caps, goals = load_data()
    score = goal_relevance(caps["C1"], goals["G1"])
    assert isinstance(score, float)
    assert score == score  # not NaN
