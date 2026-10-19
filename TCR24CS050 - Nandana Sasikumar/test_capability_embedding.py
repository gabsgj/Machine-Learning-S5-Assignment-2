"""
test_capability_embedding.py
=============================
Unit tests verifying the formal embedding implementation:
- State & Goal encoding
- Capability encoding
- Directional compatibility (asymmetry and conflict detection)
- Functional vs total similarity
- Composition algebra
- Goal relevance
"""

import unittest
import numpy as np

from capability_embedding import (
    Domain,
    State,
    Goal,
    Capability,
    QoS,
    encode,
    encode_state,
    encode_goal,
    encode_capability,
    similarity,
    compatibility,
    goal_relevance,
    compose,
)
from dataset import (
    ecommerce_domain,
    initial_state,
    goal_complete_purchase,
    c1_create_order,
    c2_make_payment_api,
    c3_cancel_cart,
    c4_make_payment_db,
    c5_make_payment_gui,
    c6_send_notification,
    c7_browse_products,
)


class TestCapabilityEmbedding(unittest.TestCase):

    def setUp(self):
        self.domain = ecommerce_domain

    def test_encode_state(self):
        vec = encode(initial_state, self.domain)
        self.assertEqual(len(vec), self.domain.num_variables)
        # Cart.exists was True -> +1.0
        cart_idx = self.domain.var_to_idx["Cart.exists"]
        self.assertEqual(vec[cart_idx], 1.0)
        # Order.exists was False -> -1.0
        order_idx = self.domain.var_to_idx["Order.exists"]
        self.assertEqual(vec[order_idx], -1.0)

    def test_encode_goal(self):
        vec = encode(goal_complete_purchase, self.domain)
        self.assertEqual(len(vec), self.domain.num_variables)
        order_idx = self.domain.var_to_idx["Order.exists"]
        self.assertEqual(vec[order_idx], 1.0)
        # Non-goal variable should be 0.0
        user_idx = self.domain.var_to_idx["User.authenticated"]
        self.assertEqual(vec[user_idx], 0.0)

    def test_encode_capability_dimensions(self):
        vec = encode(c1_create_order, self.domain)
        expected_dim = self.domain.capability_vector_dim
        self.assertEqual(len(vec), expected_dim)

    def test_compatibility_and_asymmetry(self):
        # C1 -> C2 should be compatible (+1.0)
        c1_c2 = compatibility(c1_create_order, c2_make_payment_api, self.domain)
        self.assertGreater(c1_c2, 0.0)

        # C1 -> C3 should be incompatible (conflict on Order.exists)
        c1_c3 = compatibility(c1_create_order, c3_cancel_cart, self.domain)
        self.assertLess(c1_c3, 0.0)

        # C2 -> C1 should be 0.0 (asymmetric, C2 does not satisfy C1)
        c2_c1 = compatibility(c2_make_payment_api, c1_create_order, self.domain)
        self.assertEqual(c2_c1, 0.0)

    def test_similarity_functional_vs_total(self):
        # Alternative implementations have functional similarity = 1.0
        func_sim = similarity(c2_make_payment_api, c4_make_payment_db, self.domain, mode="functional")
        self.assertAlmostEqual(func_sim, 1.0, places=4)

        # But total similarity differs due to mechanism and QoS
        total_sim = similarity(c2_make_payment_api, c4_make_payment_db, self.domain, mode="total")
        self.assertLess(total_sim, 1.0)
        self.assertGreater(total_sim, 0.5)

    def test_composition_algebra(self):
        comp, comp_vec = compose([c1_create_order, c2_make_payment_api, c6_send_notification], self.domain)
        self.assertIn("Order.exists", comp.effects)
        self.assertIn("Payment.status_success", comp.effects)
        self.assertIn("Notification.sent", comp.effects)

        # Cost is additive
        expected_cost = round(0.010 + 0.050 + 0.003, 4)
        self.assertAlmostEqual(comp.qos.monetary_cost, expected_cost, places=4)

        # Reliability is multiplicative
        expected_rel = round(0.99 * 0.98 * 0.97, 4)
        self.assertAlmostEqual(comp.qos.reliability, expected_rel, places=4)

        # Goal relevance of composite is 1.0
        rel = goal_relevance(comp, goal_complete_purchase, self.domain)
        self.assertAlmostEqual(rel, 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
