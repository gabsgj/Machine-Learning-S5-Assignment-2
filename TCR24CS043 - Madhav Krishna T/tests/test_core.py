from pathlib import Path

import numpy as np

from src.compatibility import compatibility
from src.formal_composition import compose_many
from src.encoder import encode_capability, encode_goal, encode_state
from src.data_models import load_core_dataset
from src.schema import Condition


ROOT = Path(__file__).resolve().parents[1]


def test_capability_vector_dimensions_and_normalization():
    _, caps = load_core_dataset(ROOT / "data" / "core_application.json")
    for capability in caps.values():
        vector = encode_capability(capability)
        assert vector.shape == (128,)
        assert np.isclose(np.linalg.norm(vector), 1.0, atol=1e-5)


def test_state_and_goal_dimensions():
    raw, _ = load_core_dataset(ROOT / "data" / "core_application.json")
    state = encode_state(raw["initial_state"])
    goal = encode_goal([Condition(**x) for x in raw["goal"]])
    assert state.shape == (64,)
    assert goal.shape == (64,)


def test_required_compatibility_relations():
    _, caps = load_core_dataset(ROOT / "data" / "core_application.json")
    assert compatibility(caps["C1"], caps["C2"]).compatible
    assert compatibility(caps["C2"], caps["C3"]).compatible
    assert not compatibility(caps["C1"], caps["C3"]).compatible
    assert not compatibility(caps["C1"], caps["C4"]).compatible


def test_three_step_composition():
    _, caps = load_core_dataset(ROOT / "data" / "core_application.json")
    composite = compose_many([caps["C1"], caps["C2"], caps["C3"]])
    assert composite.id == "C1__C2__C3"
    assert composite.reliability > 0.0
    effect_keys = {e.attribute for e in composite.effects}
    assert "Payment.status" in effect_keys
    assert "Notification.sent" in effect_keys
