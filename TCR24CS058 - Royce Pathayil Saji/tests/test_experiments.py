from __future__ import annotations

import json
from pathlib import Path
import pytest

from experiments.run_all import (
    DATA_PATH,
    PLOTS_DIR,
    RESULTS_DIR,
    load_dataset,
    run_experiment_1,
    run_experiment_2,
    run_experiment_3,
    run_experiment_4,
    run_experiment_5,
)


def test_dataset_loads_correctly():
    capabilities, states, goals = load_dataset(DATA_PATH)
    assert len(capabilities) >= 12
    assert len(states) >= 3
    assert len(goals) >= 4


def test_required_capabilities_exist():
    capabilities, _, _ = load_dataset(DATA_PATH)
    required_ids = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12"]
    for cid in required_ids:
        assert cid in capabilities
        assert capabilities[cid].id == cid


def test_required_goals_exist():
    _, _, goals = load_dataset(DATA_PATH)
    assert "Goal_Master" in goals
    assert len(goals["Goal_Master"].conditions) >= 3


def test_experiment_1_compatibility_distinction():
    capabilities, _, _ = load_dataset(DATA_PATH)
    res = run_experiment_1(capabilities)
    records = {r["src_id"] + "->" + r["dst_id"]: r for r in res["records"]}

    # CreateOrder -> MakePayment must be compatible
    assert records["C1->C2"]["formally_compatible"] is True
    assert records["C1->C2"]["execution_score"] >= 0.70

    # CreateOrder -> CancelCart must be incompatible
    assert records["C1->C3"]["formally_compatible"] is False
    assert records["C1->C3"]["execution_score"] < 0.0

    # Directionality: MakePayment -> CreateOrder is incompatible
    assert records["C2->C1"]["formally_compatible"] is False
    assert records["C2->C1"]["execution_score"] < records["C1->C2"]["execution_score"]


def test_experiment_2_composition_structure():
    capabilities, _, _ = load_dataset(DATA_PATH)
    res = run_experiment_2(capabilities)

    assert res["composite_id"] == "C1_C2_C4"
    assert res["components"] == ["C1", "C2", "C4"]

    # External inputs should only retain cart_id
    assert "cart_id" in res["external_inputs"]
    assert "order_id" not in res["external_inputs"]
    assert "payment_id" not in res["external_inputs"]

    # Internal preconditions should be removed
    assert not any("order" in p.lower() for p in res["external_preconditions"])

    # Operational metrics aggregate correctly
    assert res["operational"]["execution_time_ms"] == res["operational"]["expected_time_ms"]
    assert abs(res["operational"]["reliability"] - res["operational"]["expected_reliability"]) < 1e-5


def test_experiment_3_alternative_implementations():
    capabilities, _, _ = load_dataset(DATA_PATH)
    res = run_experiment_3(capabilities)
    alts = {r["pair"]: r for r in res["alternatives"]}

    assert "API vs DB" in alts
    assert "API vs GUI" in alts
    assert "DB vs GUI" in alts

    for pair_name, r in alts.items():
        # Effects must be identical (1.0)
        assert abs(r["effect_similarity"] - 1.0) < 1e-6
        # Mechanisms must be distinct (0.0)
        assert abs(r["mechanism_similarity"] - 0.0) < 1e-6
        # Overall similarity in high range reflecting functional equivalence
        assert 0.75 <= r["full_similarity"] <= 0.98


def test_experiment_4_goal_relevance_ranking():
    capabilities, _, goals = load_dataset(DATA_PATH)
    res = run_experiment_4(capabilities, goals)

    rankings = {r["id"]: r["relevance_score"] for r in res["rankings"]}

    # Useful capabilities must have strictly positive relevance
    assert rankings["C1"] > 0.0
    assert rankings["C2"] > 0.0
    assert rankings["C4"] > 0.0

    # Irrelevant or contradictory capabilities must have zero relevance
    assert rankings["C7"] == 0.0
    assert rankings["C8"] == 0.0
    assert rankings["C3"] == 0.0

    # Useful capabilities must rank above irrelevant ones
    assert rankings["C1"] > rankings["C7"]


def test_experiment_5_operational_measurements():
    capabilities, _, _ = load_dataset(DATA_PATH)
    res = run_experiment_5(capabilities)

    # 1. Verify PSD-160 representation-level operational vectors
    rep_level = res["representation_level"]
    assert "operational_vectors" in rep_level
    assert "pairwise_comparisons" in rep_level
    expected_keys = {"norm_time", "norm_money", "norm_resource", "risk", "energy", "unreliability", "unavailability", "composite_cost"}
    for cid in ["C10", "C11", "C12", "C13"]:
        assert cid in rep_level["operational_vectors"]
        vec_entry = rep_level["operational_vectors"][cid]
        assert expected_keys.issubset(vec_entry.keys())
    assert len(rep_level["pairwise_comparisons"]) == 6
    for p in rep_level["pairwise_comparisons"]:
        assert 0.0 <= p["cosine_similarity"] <= 1.0001
        assert p["euclidean_distance"] >= 0.0

    # 2. Verify application-level utility analysis
    scenarios = res["utility_analysis"]["scenarios"]
    assert "Speed-focused" in scenarios
    assert "Reliability-focused" in scenarios
    assert "Cost-focused" in scenarios

    # In speed-focused, fast DB capability (C11) should rank #1
    speed_rankings = [r["id"] for r in scenarios["Speed-focused"]]
    assert speed_rankings[0] == "C11"

    # Unavailable capability (C13) should have 0 effective utility
    for s_name, rows in scenarios.items():
        c13_entry = next(r for r in rows if r["id"] == "C13")
        assert c13_entry["effective_utility"] == 0.0


def test_experiments_are_deterministic():
    capabilities, states, goals = load_dataset(DATA_PATH)
    run1 = run_experiment_1(capabilities)
    run2 = run_experiment_1(capabilities)

    assert run1 == run2


def test_result_files_exist():
    assert (RESULTS_DIR / "results.json").exists()
    assert (RESULTS_DIR / "compatibility.csv").exists()
    assert (RESULTS_DIR / "composition.csv").exists()
    assert (RESULTS_DIR / "alternative_implementations.csv").exists()
    assert (RESULTS_DIR / "goal_relevance.csv").exists()
    assert (RESULTS_DIR / "operational_attributes.csv").exists()
    assert (PLOTS_DIR / "compatibility_scores.png").exists()
    assert (PLOTS_DIR / "alternative_implementations.png").exists()
    assert (PLOTS_DIR / "goal_relevance.png").exists()
    assert (PLOTS_DIR / "operational_tradeoffs.png").exists()
