from __future__ import annotations

import math
import numpy as np
import pytest

from src.models import (
    Capability,
    CapabilityType,
    Constraint,
    IOField,
    OperationalCost,
    Predicate,
    Resource,
)
from src.composer import CompositionError, compose
from src.encoder import encode_capability
from src.metrics import similarity


def test_two_step_composition():
    create_order = Capability(
        id="C1",
        name="CreateOrder",
        T=CapabilityType.API,
        I=[IOField(name="cart_id", type="UUID", required=True)],
        O=[IOField(name="order_id", type="UUID")],
        P=[Predicate(name="Cart.exists", operator="=", value=True)],
        E=[Predicate(name="Order.exists", operator="=", value=True)],
        Q=OperationalCost(execution_time_ms=100.0, monetary_cost=0.01, resource_cost=1.0, risk=0.02),
        Rel=0.99,
        A=1.0,
    )
    make_payment = Capability(
        id="C2",
        name="MakePayment",
        T=CapabilityType.API,
        I=[IOField(name="order_id", type="UUID", required=True)],
        O=[IOField(name="payment_id", type="UUID")],
        P=[Predicate(name="Order.exists", operator="=", value=True)],
        E=[Predicate(name="Payment.status", operator="=", value="SUCCESS")],
        Q=OperationalCost(execution_time_ms=250.0, monetary_cost=0.02, resource_cost=2.0, risk=0.05),
        Rel=0.98,
        A=1.0,
    )

    composite = compose([create_order, make_payment])

    # 1. Type and structure
    assert composite.T == CapabilityType.COMPOSITE
    assert composite.id == "C1_C2"
    assert composite.components == ["C1", "C2"]
    assert "SEQUENTIAL_COMPOSITION" in composite.M.get("type", "")

    # 2. Inputs: cart_id remains, order_id is internal
    input_names = [i.name for i in composite.I]
    assert "cart_id" in input_names
    assert "order_id" not in input_names

    # 3. Preconditions: Cart.exists remains external, Order.exists is internalized
    pre_names = [p.name for p in composite.P]
    assert any("cart" in name.lower() for name in pre_names)
    assert not any("order" in name.lower() for name in pre_names)

    # 4. Outputs: terminal output is payment_id
    output_names = [o.name for o in composite.O]
    assert output_names == ["payment_id"]

    # 5. Effects: Payment.status = SUCCESS is present
    effect_names = [e.name for e in composite.E]
    assert any("payment" in name.lower() for name in effect_names)

    # 6. Operational aggregation
    assert composite.Q.execution_time_ms == 350.0
    assert abs(composite.Q.monetary_cost - 0.03) < 1e-6
    assert composite.Q.resource_cost == 3.0
    assert abs(composite.Rel - (0.99 * 0.98)) < 1e-6
    assert composite.A == 1.0


def test_three_step_composition():
    c1 = Capability(
        id="C1",
        name="CreateOrder",
        T=CapabilityType.API,
        I=[IOField(name="cart_id", type="UUID", required=True)],
        O=[IOField(name="order_id", type="UUID")],
        P=[Predicate(name="Cart.exists", operator="=", value=True)],
        E=[Predicate(name="Order.exists", operator="=", value=True)],
        Q=OperationalCost(execution_time_ms=100.0, monetary_cost=0.01, resource_cost=1.0, risk=0.02),
        Rel=0.99,
        A=1.0,
    )
    c2 = Capability(
        id="C2",
        name="MakePayment",
        T=CapabilityType.API,
        I=[IOField(name="order_id", type="UUID", required=True)],
        O=[IOField(name="payment_id", type="UUID")],
        P=[Predicate(name="Order.exists", operator="=", value=True)],
        E=[Predicate(name="Payment.status", operator="=", value="SUCCESS")],
        Q=OperationalCost(execution_time_ms=250.0, monetary_cost=0.02, resource_cost=2.0, risk=0.03),
        Rel=0.97,
        A=1.0,
    )
    c3 = Capability(
        id="C3",
        name="SendNotification",
        T=CapabilityType.EVENT,
        I=[IOField(name="payment_id", type="UUID", required=True)],
        O=[IOField(name="notification_id", type="UUID")],
        P=[Predicate(name="Payment.status", operator="=", value="SUCCESS")],
        E=[Predicate(name="Notification.sent", operator="=", value=True)],
        Q=OperationalCost(execution_time_ms=50.0, monetary_cost=0.005, resource_cost=1.0, risk=0.01),
        Rel=0.95,
        A=1.0,
    )

    composite = compose([c1, c2, c3])

    assert composite.id == "C1_C2_C3"
    assert composite.components == ["C1", "C2", "C3"]

    # Inputs: only cart_id remains external
    input_names = [i.name for i in composite.I]
    assert input_names == ["cart_id"]

    # Preconditions: Order.exists and Payment.status are internalized
    pre_names = [p.name for p in composite.P]
    assert any("cart" in name.lower() for name in pre_names)
    assert not any("order" in name.lower() for name in pre_names)
    assert not any("payment" in name.lower() for name in pre_names)

    # Terminal output is notification_id
    assert [o.name for o in composite.O] == ["notification_id"]

    # Final effects contain all non-overridden effects
    effect_names = [e.name for e in composite.E]
    assert any("notification" in name.lower() for name in effect_names)
    assert any("payment" in name.lower() for name in effect_names)
    assert any("order" in name.lower() for name in effect_names)

    # Reliability is product of all 3
    expected_rel = 0.99 * 0.97 * 0.95
    assert abs(composite.Rel - expected_rel) < 1e-5


def test_invalid_composition_fails():
    c1 = Capability(
        id="C1",
        name="CreateOrder",
        T=CapabilityType.API,
        O=[IOField(name="order_id", type="UUID")],
        E=[Predicate(name="Order.exists", operator="=", value=True)],
    )
    c3 = Capability(
        id="C3",
        name="CancelCart",
        T=CapabilityType.API,
        I=[IOField(name="cart_id", type="UUID", required=True)],
        P=[Predicate(name="Order.exists", operator="=", value=False)],
    )

    with pytest.raises(CompositionError) as exc_info:
        compose([c1, c3])

    err = exc_info.value
    assert err.producer_id == "C1"
    assert err.consumer_id == "C3"
    assert any("contradicted" in r.lower() or "not produced" in r.lower() for r in err.reasons)


def test_effect_override():
    c1 = Capability(
        id="C1",
        name="StartPayment",
        T=CapabilityType.API,
        E=[Predicate(name="Payment.status", operator="=", value="PENDING")],
    )
    c2 = Capability(
        id="C2",
        name="FinalizePayment",
        T=CapabilityType.API,
        P=[Predicate(name="Payment.status", operator="=", value="PENDING")],
        E=[Predicate(name="Payment.status", operator="=", value="SUCCESS")],
    )

    composite = compose([c1, c2])

    payment_effects = [e for e in composite.E if "payment" in e.name.lower()]
    assert len(payment_effects) == 1
    assert payment_effects[0].value == "SUCCESS"


def test_operational_aggregation_exact():
    c1 = Capability(
        id="C1",
        name="Cap1",
        T=CapabilityType.API,
        Q=OperationalCost(execution_time_ms=100.0, monetary_cost=0.01, resource_cost=1.0, risk=0.02),
        Rel=0.99,
        A=1.0,
    )
    c2 = Capability(
        id="C2",
        name="Cap2",
        T=CapabilityType.API,
        Q=OperationalCost(execution_time_ms=200.0, monetary_cost=0.02, resource_cost=2.0, risk=0.03),
        Rel=0.98,
        A=1.0,
    )

    composite = compose([c1, c2])

    assert composite.Q.execution_time_ms == 300.0
    assert abs(composite.Q.monetary_cost - 0.03) < 1e-6
    assert composite.Q.resource_cost == 3.0

    expected_risk = 1.0 - (1.0 - 0.02) * (1.0 - 0.03)
    assert abs(composite.Q.risk - expected_risk) < 1e-6

    expected_rel = 0.99 * 0.98
    assert abs(composite.Rel - expected_rel) < 1e-6
    assert composite.A == 1.0


def test_composite_encoding_and_similarity():
    c1 = Capability(
        id="C1",
        name="CreateOrder",
        T=CapabilityType.API,
        I=[IOField(name="cart_id", type="UUID")],
        O=[IOField(name="order_id", type="UUID")],
        P=[Predicate(name="Cart.exists", operator="=", value=True)],
        E=[Predicate(name="Order.exists", operator="=", value=True)],
    )
    c2 = Capability(
        id="C2",
        name="MakePayment",
        T=CapabilityType.API,
        I=[IOField(name="order_id", type="UUID")],
        O=[IOField(name="payment_id", type="UUID")],
        P=[Predicate(name="Order.exists", operator="=", value=True)],
        E=[Predicate(name="Payment.status", operator="=", value="SUCCESS")],
    )

    composite = compose([c1, c2])
    vec = encode_capability(composite)

    # 1. Dimension and validity
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (160,)
    assert np.isfinite(vec).all()
    assert not np.isnan(vec).any()

    # 2. Sequential composition flag is set in mechanism block [0:16]
    # Type COMPOSITE is index 9, sequential composition flag is index 15
    assert vec[9] == 1.0
    assert vec[15] == 1.0

    # 3. Deterministic encoding
    vec2 = encode_capability(composite)
    assert np.array_equal(vec, vec2)

    # 4. Can compute similarity with other capabilities
    sim_score = similarity(composite, c1)
    assert -1.0 <= sim_score <= 1.0
