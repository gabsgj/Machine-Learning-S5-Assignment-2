import csv
import ast
from pathlib import Path

import numpy as np

from src.capability_embedding import BLOCK_DIM, compose


ROOT = Path(__file__).resolve().parents[1]


def load_capabilities():
    with (ROOT / "data" / "capabilities.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for key in ["inputs", "outputs", "preconditions", "effects", "constraints", "resources"]:
            row[key] = ast.literal_eval(row[key])
        row["execution_time_ms"] = int(row["execution_time_ms"])
        for key in ["money_cost", "resource_cost", "risk", "reliability", "availability"]:
            row[key] = float(row[key])
    return {row["id"]: row for row in rows}


def test_composition_uses_boundary_inputs_and_outputs():
    caps = load_capabilities()
    composite, vector = compose([caps["C1"], caps["C2"], caps["C4"]])

    assert composite["inputs"] == caps["C1"]["inputs"]
    assert composite["outputs"] == caps["C4"]["outputs"]
    assert vector.shape == (6 * BLOCK_DIM + 6,)
    assert np.all(np.isfinite(vector))


def test_composition_aggregates_operational_properties():
    caps = load_capabilities()
    composite, _ = compose([caps["C1"], caps["C2"]])

    assert composite["execution_time_ms"] == 350
    assert np.isclose(composite["money_cost"], 0.03)
    assert np.isclose(composite["resource_cost"], 5.0)
    assert np.isclose(composite["reliability"], 0.99 * 0.97)
    assert np.isclose(composite["availability"], 1.0)


def test_composition_rejects_empty_sequence():
    try:
        compose([])
    except ValueError as exc:
        assert "At least one capability" in str(exc)
    else:
        raise AssertionError("compose([]) should raise ValueError")
