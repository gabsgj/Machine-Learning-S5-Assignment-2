from pathlib import Path

from src.dataset import load_dataset
from src.encoder import cosine, encode_effects_common, encode_goal
from src.schema import Condition


def test_goal_relevance_experiment_can_score_all_capabilities():
    root = Path(__file__).resolve().parents[1]
    data, caps = load_dataset(root / "data" / "expanded_application.json")
    goal = [Condition(**item) for item in data["goal"]]
    goal_vec = encode_goal(goal)

    scores = {
        cid: cosine(encode_effects_common(caps[cid]), goal_vec)
        for cid in data["goal_relevance"]
    }

    assert set(scores) == set(data["goal_relevance"])
    assert all(-1.0 <= s <= 1.0 for s in scores.values())


def test_goal_relevance_metadata_contains_both_classes():
    root = Path(__file__).resolve().parents[1]
    data, _ = load_dataset(root / "data" / "expanded_application.json")
    labels = list(data["goal_relevance"].values())
    assert any(labels)
    assert any(not x for x in labels)
