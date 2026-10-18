import numpy as np

from src.capability_embedding import BLOCK_DIM, encode_capability, encode_goal, encode_state


def test_encode_state_has_expected_dimension():
    state = {"state_id": "S0", "cart_exists": True, "item_count": 2}
    vector = encode_state(state)
    assert vector.shape == (BLOCK_DIM,)
    assert np.all(np.isfinite(vector))


def test_encode_goal_is_deterministic():
    goal = {"goal_id": "G1", "conditions": ["OrderExists=true"]}
    assert np.array_equal(encode_goal(goal), encode_goal(goal))


def test_encode_capability_has_expected_dimension_and_finite_values():
    capability = {
        "id": "C_TEST",
        "name": "TestCapability",
        "type": "API",
        "mechanism": "POST /test",
        "inputs": ["x:UUID"],
        "outputs": ["y:UUID"],
        "preconditions": ["Ready=true"],
        "effects": ["Done=true"],
        "constraints": ["x>0"],
        "resources": ["Database"],
        "execution_time_ms": 100,
        "money_cost": 0.01,
        "resource_cost": 1,
        "risk": 0.1,
        "reliability": 0.99,
        "availability": 1.0,
    }
    vector = encode_capability(capability)
    assert vector.shape == (6 * BLOCK_DIM + 6,)
    assert np.all(np.isfinite(vector))
