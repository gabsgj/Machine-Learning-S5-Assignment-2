import pytest

from app.composition import check_compatibility, compose
from app.composition.composer import CompositionError
from app.experiments.runner import load_default_scenario


def test_compatible_and_incompatible_precondition_effect_pairs():
    caps = {c.id: c for c in load_default_scenario().capabilities}
    assert check_compatibility(caps["create-order-api"], caps["make-payment"])["compatible"]
    result = check_compatibility(caps["create-order-api"], caps["cancel-cart"])
    assert not result["compatible"]
    assert result["evidence"] and result["reasons"]


def test_compatibility_checks_typed_inputs():
    caps = {c.id: c for c in load_default_scenario().capabilities}
    result = check_compatibility(caps["make-payment"], caps["send-receipt"])
    assert result["compatible"]
    assert any(row["requirement"] == "input" for row in result["evidence"])


def test_three_capability_composition_aggregates_semantics_and_operations():
    caps = {c.id: c for c in load_default_scenario().capabilities}
    composite, checks = compose([caps["create-order-api"], caps["make-payment"], caps["send-receipt"]])
    assert len(checks) == 2 and all(row["compatible"] for row in checks)
    assert composite.components == ["create-order-api", "make-payment", "send-receipt"]
    assert {effect.name for effect in composite.effects} >= {"Order.exists", "Payment.status", "Notification.sent"}
    assert composite.cost.time_ms == 960
    assert composite.reliability == pytest.approx(0.99 * 0.97 * 0.995)


def test_composition_fails_with_diagnostics():
    caps = {c.id: c for c in load_default_scenario().capabilities}
    with pytest.raises(CompositionError) as caught:
        compose([caps["create-order-api"], caps["cancel-cart"]])
    assert caught.value.diagnostics[0]["compatible"] is False


def test_unavailable_capability_cannot_compose():
    caps = {c.id: c for c in load_default_scenario().capabilities}
    unavailable = caps["make-payment"].model_copy(update={"availability": 0})
    assert not check_compatibility(caps["create-order-api"], unavailable)["compatible"]

