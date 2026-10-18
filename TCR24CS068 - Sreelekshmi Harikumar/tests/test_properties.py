"""pytest suite:  python -m pytest tests -q
Checks the claims made in Deliverable 1 against concrete semantics."""
import os, sys
import numpy as np
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from capemb import *
from capemb import semantics as S, verify as V

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets")
NAMES = ["P0_assignment_minimal", "P1_ecommerce_checkout", "P2_ml_pipeline", "P3_loan_approval"]


def load(n):
    p = load_problem(os.path.join(D, n + ".json"))
    return p, CapabilityEmbedder(p)


@pytest.mark.parametrize("n", NAMES)
def test_apply_homomorphism(n):
    assert V.check_apply_homomorphism(load(n)[1])["mismatches"] == 0


@pytest.mark.parametrize("n", NAMES)
def test_composition_equals_sequential_execution(n):
    assert V.check_composition_semantics(load(n)[1])["mismatches"] == 0


@pytest.mark.parametrize("n", NAMES)
def test_associativity_and_identity(n):
    E = load(n)[1]
    r = V.check_associativity(E)
    assert r["block_equal"] == r["triples"] and r["validity_agree"] == r["triples"]
    i = V.check_identity(E)
    assert i["identity_ok"] == i["caps"]


@pytest.mark.parametrize("n", NAMES)
def test_pair_labels_match_oracle(n):
    p, E = load(n)
    ids = [c.id for c in p.caps]
    assert np.array_equal(S.label_matrix(p), E.compat_matrix(ids)["label"])


def test_assignment_experiment_1():
    p, E = load("P0_assignment_minimal")
    assert E.compat("CreateOrder", "MakePayment")["label_name"] == "STRICT"
    assert E.compat("CreateOrder", "CancelCart")["label_name"] == "CONFLICT"


def test_alternatives_same_function_different_implementation():
    p, E = load("P1_ecommerce_checkout")
    s = E.similarity_report("MakePayment_API", "MakePayment_DB")
    assert s["func"] == pytest.approx(1.0) and s["impl"] < 0.2 and s["overall"] < 1.0
    assert not np.allclose(E.flat(E.caps["MakePayment_API"]), E.flat(E.caps["MakePayment_DB"]))


def test_qos_independent_of_compat():
    p, E = load("P1_ecommerce_checkout")
    ids = [c.id for c in p.caps]
    m0 = E.compat_matrix(ids)["label"]
    import dataclasses
    p2 = dataclasses.replace(p, caps=[dataclasses.replace(c, reliability=0.5) for c in p.caps])
    assert np.array_equal(m0, CapabilityEmbedder(p2).compat_matrix(ids)["label"])


def test_composite_reliability_is_product():
    p, E = load("P1_ecommerce_checkout")
    ch = ["CreateOrder", "ValidatePaymentLimit", "MakePayment_API"]
    prod = np.prod([p.cap(i).reliability for i in ch])
    assert E.reliability(E.compose(ch)) == pytest.approx(prod)


def test_vector_state_goal_api():
    p, E = load("P1_ecommerce_checkout")
    s, g = E.encode(p.init), E.encode(p.goal)
    assert 0 <= E.similarity(s, g) < 1
    c = E.encode("CreateOrder")
    assert E.similarity(s, c) == pytest.approx(1.0)
