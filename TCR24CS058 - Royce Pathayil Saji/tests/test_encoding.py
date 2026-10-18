from __future__ import annotations

import numpy as np
import pytest

from src.models import (
    Capability,
    CapabilityType,
    Constraint,
    Goal,
    IOField,
    OperationalCost,
    Predicate,
    Resource,
    State,
)
from src.encoder import (
    COND_DIM,
    TOTAL_DIM,
    encode_capability,
    encode_goal,
    encode_state,
)


def test_state_vector_shape():
    s = State(id="S0", values={"Cart.exists": True, "Order.exists": False})
    v_s = encode_state(s)
    assert isinstance(v_s, np.ndarray)
    assert v_s.shape == (COND_DIM,)
    assert v_s.dtype == np.float64


def test_goal_vector_shape():
    g = Goal(
        id="G1",
        conditions=[
            Predicate("Order.exists", "=", True),
            Predicate("Payment.status", "=", "SUCCESS"),
        ],
    )
    v_g = encode_goal(g)
    assert isinstance(v_g, np.ndarray)
    assert v_g.shape == (COND_DIM,)


def test_capability_vector_shape():
    c = Capability(
        id="C1",
        name="CreateOrder",
        T=CapabilityType.API,
        I=[IOField(name="cart_id", type="UUID")],
        O=[IOField(name="order_id", type="UUID")],
        P=[Predicate(name="Cart.exists", operator="=", value=True)],
        E=[Predicate(name="Order.exists", operator="=", value=True)],
        K=[Constraint(expression="quantity > 0")],
        R=[Resource(name="Database")],
        Q=OperationalCost(execution_time_ms=100.0, monetary_cost=0.01, resource_cost=2.0, risk=0.1),
        Rel=0.99,
        A=1.0,
        M={"method": "POST", "endpoint": "/orders"},
    )
    v_c = encode_capability(c)
    assert isinstance(v_c, np.ndarray)
    assert v_c.shape == (TOTAL_DIM,)
    assert len(v_c) == 160


def test_boolean_polarity_and_contradiction():
    g_true = Goal(id="G_true", conditions=[Predicate("Order.exists", "=", True)])
    g_false = Goal(id="G_false", conditions=[Predicate("Order.exists", "=", False)])

    v_true = encode_goal(g_true)
    v_false = encode_goal(g_false)

    # Order.exists is index 3
    assert v_true[3] == 1.0
    assert v_false[3] == -1.0

    # Dot product should be -1.0 (contradictory)
    dot = np.dot(v_true, v_false)
    assert dot == -1.0


def test_unmentioned_predicates_are_zero():
    g = Goal(id="G_empty", conditions=[])
    v_g = encode_goal(g)
    assert np.all(v_g == 0.0)

    # When variable is not in condition, its slot is 0.0
    g_partial = Goal(id="G_part", conditions=[Predicate("Order.exists", "=", True)])
    v_part = encode_goal(g_partial)
    assert v_part[3] == 1.0
    assert v_part[0] == 0.0  # User.authenticated is unmentioned


def test_categorical_one_hot_encoding():
    g_success = Goal(id="G_succ", conditions=[Predicate("Payment.status", "=", "SUCCESS")])
    g_refund = Goal(id="G_ref", conditions=[Predicate("Payment.status", "=", "REFUNDED")])

    v_succ = encode_goal(g_success)
    v_ref = encode_goal(g_refund)

    # Payment.status: 8: NOT_STARTED, 9: PENDING, 10: SUCCESS, 11: REFUNDED
    assert v_succ[10] == 1.0
    assert v_succ[8] == 0.0
    assert v_succ[11] == 0.0

    assert v_ref[11] == 1.0
    assert v_ref[10] == 0.0


def test_numerical_normalization_and_operator_direction():
    g_gt = Goal(id="G_gt", conditions=[Predicate("Cart.item_count", ">", 3)])
    g_lt = Goal(id="G_lt", conditions=[Predicate("Cart.item_count", "<=", 5)])

    v_gt = encode_goal(g_gt)
    v_lt = encode_goal(g_lt)

    # Cart.item_count: indices 19 (magnitude) and 20 (operator direction)
    assert v_gt[19] == 0.3  # 3 / 10
    assert v_gt[20] == 1.0  # '>' direction is +1.0

    assert v_lt[19] == 0.5  # 5 / 10
    assert v_lt[20] == -1.0  # '<=' direction is -1.0


def test_input_output_encoding():
    c = Capability(
        id="C1",
        name="TestIO",
        T=CapabilityType.API,
        I=[
            IOField(name="cart_id", type="UUID", required=True),
            IOField(name="payment_method", type="TOKEN", required=False),
        ],
        O=[
            IOField(name="order_id", type="UUID"),
        ],
    )
    v = encode_capability(c)

    # Input slice is [16:40]
    # cart_id is index 0 -> 16 + 0 = 16 (required = 1.0)
    # payment_method is index 3 -> 16 + 3 = 19 (optional = 0.5)
    assert v[16] == 1.0
    assert v[19] == 0.5

    # Output slice is [40:64]
    # order_id is index 1 -> 40 + 1 = 41 (present = 1.0)
    assert v[41] == 1.0
    assert v[40] == 0.0  # cart_id is not in outputs


def test_operational_normalization_and_clamping():
    c = Capability(
        id="C_cost",
        name="CostlyCap",
        T=CapabilityType.API,
        Q=OperationalCost(
            execution_time_ms=2000.0,  # exceeds max 1000 -> clamped to 1.0
            monetary_cost=0.05,        # 0.05 / 0.10 = 0.5
            resource_cost=10.0,        # exceeds max 5 -> clamped to 1.0
            risk=0.2,
            energy_cost=5.0,           # 5.0 / 10.0 = 0.5
        ),
        Rel=0.95,                      # 1 - Rel = 0.05
        A=0.0,                         # 1 - A = 1.0
    )
    v = encode_capability(c)

    # Operational slice is [152:160]
    assert v[152] == 1.0  # time clamped to 1.0
    assert v[153] == 0.5  # money
    assert v[154] == 1.0  # resource clamped to 1.0
    assert v[155] == 0.2  # risk
    assert v[156] == 0.5  # energy
    assert abs(v[157] - 0.05) < 1e-6  # unreliability
    assert v[158] == 1.0  # unavailability (1 - 0 = 1)


def test_deterministic_encoding():
    c = Capability(
        id="C1",
        name="CreateOrder",
        T=CapabilityType.API,
        I=[IOField(name="cart_id", type="UUID")],
        O=[IOField(name="order_id", type="UUID")],
        P=[Predicate(name="Cart.exists", operator="=", value=True)],
        E=[Predicate(name="Order.exists", operator="=", value=True)],
    )
    v1 = encode_capability(c)
    v2 = encode_capability(c)

    assert np.array_equal(v1, v2)


def test_no_accidental_nan_or_inf():
    c = Capability(
        id="C_zero",
        name="EmptyCap",
        T=CapabilityType.FUNCTION,
    )
    v = encode_capability(c)
    assert np.isfinite(v).all()
    assert not np.isnan(v).any()
    assert not np.isinf(v).any()


def test_model_validation_rejects_invalid_values():
    with pytest.raises(ValueError):
        OperationalCost(execution_time_ms=-10.0)

    with pytest.raises(ValueError):
        Capability(id="C_bad", name="BadRel", T=CapabilityType.API, Rel=1.5)

    with pytest.raises(ValueError):
        Predicate(name="Var", operator="INVALID_OP", value=True)
