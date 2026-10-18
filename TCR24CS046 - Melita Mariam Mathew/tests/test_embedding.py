"""
Comprehensive Unit Test Suite for Capability Vector Embedding System.
Assignment 2: Design of a Vector Embedding for Capability Composition.
Student: Melita Mariam Mathew
Registration Number: TCCR24CS046
"""

import unittest
import numpy as np

from src.models import (
    Capability,
    CompositeCapability,
    State,
    Goal,
    CapabilityType,
    ExecutionMechanism,
    OperationalAttributes,
    StateCondition,
    InputSpec,
    OutputSpec,
)
from src.embedding import CapabilityEmbeddingSpace
from src.composition import CompositionEngine
from dataset.dataset import build_benchmark_dataset


class TestCapabilityEmbedding(unittest.TestCase):
    def setUp(self):
        self.dataset = build_benchmark_dataset()
        self.space = CapabilityEmbeddingSpace(
            state_variables=self.dataset["state_variables"],
            io_vocab=self.dataset["io_vocab"],
        )
        self.engine = CompositionEngine(self.space)
        self.caps = self.dataset["capabilities"]

    def test_capability_identity(self):
        """Evaluation Criteria 1: Can different capabilities be represented distinctly?"""
        v_c1 = self.space.encode_capability(self.caps["C1_CreateOrder_API"])
        v_c2 = self.space.encode_capability(self.caps["C2_MakePayment"])
        v_c3 = self.space.encode_capability(self.caps["C3_CancelCart"])

        # Check distinctness
        self.assertFalse(np.allclose(v_c1, v_c2))
        self.assertFalse(np.allclose(v_c1, v_c3))
        self.assertFalse(np.allclose(v_c2, v_c3))
        self.assertGreater(np.linalg.norm(v_c1 - v_c2), 0.5)

    def test_state_relationship(self):
        """Evaluation Criteria 2: Does representation capture relationship between capabilities and states?"""
        s0 = self.dataset["initial_state"]
        c1 = self.caps["C1_CreateOrder_API"]

        # C1 is applicable to initial state S0
        self.assertTrue(c1.is_applicable(s0))

        # After applying C1, new state S1 has Order.exists == True
        s1 = c1.execute(s0)
        self.assertTrue(s1.variables["Order.exists"])
        self.assertEqual(s1.variables["Order.status"], "CREATED")

        # C2 is applicable to S1, but not to S0
        c2 = self.caps["C2_MakePayment"]
        self.assertFalse(c2.is_applicable(s0))
        self.assertTrue(c2.is_applicable(s1))

    def test_precondition_effect_compatibility(self):
        """Evaluation Criteria 3: Precondition-effect compatibility."""
        c1 = self.caps["C1_CreateOrder_API"]
        c2 = self.caps["C2_MakePayment"]
        c3 = self.caps["C3_CancelCart"]

        res_12 = self.space.compatibility(c1, c2)
        res_13 = self.space.compatibility(c1, c3)

        self.assertTrue(res_12["is_compatible"])
        self.assertGreater(res_12["compatibility_score"], 0.5)
        self.assertEqual(res_12["conflict_penalty"], 0.0)

        # C1 -> C3 has conflicting precondition Order.exists == False
        self.assertFalse(res_13["is_compatible"])
        self.assertLess(res_13["compatibility_score"], 0.0)
        self.assertEqual(res_13["conflict_penalty"], 1.0)

    def test_directional_asymmetry(self):
        """Verification that compatibility is directed: Comp(C1 -> C2) != Comp(C2 -> C1)."""
        c1 = self.caps["C1_CreateOrder_API"]
        c2 = self.caps["C2_MakePayment"]

        score_fwd = self.space.compatibility(c1, c2)["compatibility_score"]
        score_rev = self.space.compatibility(c2, c1)["compatibility_score"]

        self.assertGreater(score_fwd, score_rev)
        self.assertGreater(abs(score_fwd - score_rev), 0.5)

    def test_input_output_compatibility(self):
        """Evaluation Criteria 4: Input-output compatibility."""
        c1 = self.caps["C1_CreateOrder_API"]
        c2 = self.caps["C2_MakePayment"]

        # C1 outputs order_id, C2 requires order_id
        res = self.space.compatibility(c1, c2)
        self.assertGreater(res["io_satisfaction_score"], 0.0)

    def test_composition_algebra_and_fidelity(self):
        """Evaluation Criteria 5: Can complex capabilities be represented from smaller capabilities?"""
        c1 = self.caps["C1_CreateOrder_API"]
        c2 = self.caps["C2_MakePayment"]
        c4 = self.caps["C4_SendNotification"]

        fidelity = self.engine.evaluate_composition_fidelity([c1, c2, c4])

        self.assertAlmostEqual(fidelity["full_cosine_similarity"], 1.0, places=3)
        self.assertLess(fidelity["l2_error"], 1e-4)
        self.assertAlmostEqual(fidelity["subspace_similarities"]["effect"], 1.0, places=3)
        self.assertAlmostEqual(fidelity["subspace_similarities"]["precondition"], 1.0, places=3)

    def test_composition_associativity(self):
        """Verifies that composition operator is associative: (C1 >> C2) >> C4 == C1 >> (C2 >> C4)."""
        c1 = self.caps["C1_CreateOrder_API"]
        c2 = self.caps["C2_MakePayment"]
        c4 = self.caps["C4_SendNotification"]

        # Left grouping: (c1 >> c2) >> c4
        c12 = CompositeCapability.compose(c1, c2)
        comp_left = CompositeCapability.compose(c12, c4)

        # Right grouping: c1 >> (c2 >> c4)
        c24 = CompositeCapability.compose(c2, c4)
        comp_right = CompositeCapability.compose(c1, c24)

        v_left = self.space.encode_capability(comp_left)
        v_right = self.space.encode_capability(comp_right)

        np.testing.assert_allclose(v_left, v_right, atol=1e-5)

    def test_alternative_implementations(self):
        """Verifies that API, DB, and GUI alternatives share functional equivalence while distinguishing mechanisms."""
        c_api = self.caps["C1_CreateOrder_API"]
        c_db = self.caps["C1_CreateOrder_DB"]
        c_gui = self.caps["C1_CreateOrder_GUI"]

        sim_func_api_db = self.space.similarity(c_api, c_db, mode="functional")
        sim_func_api_gui = self.space.similarity(c_api, c_gui, mode="functional")
        self.assertAlmostEqual(sim_func_api_db, 1.0, places=3)
        self.assertAlmostEqual(sim_func_api_gui, 1.0, places=3)

        sim_mech_api_db = self.space.similarity(c_api, c_db, mode="mechanism")
        self.assertLess(sim_mech_api_db, 1.0)

        # Check vectors are not identical in total space
        v_api = self.space.encode_capability(c_api)
        v_db = self.space.encode_capability(c_db)
        self.assertGreater(np.linalg.norm(v_api - v_db), 0.5)

    def test_goal_relevance(self):
        """Evaluation Criteria 6: Can relationship between capabilities and goals be identified?"""
        goal = self.dataset["primary_goal"]
        s0 = self.dataset["initial_state"]

        c1 = self.caps["C1_CreateOrder_API"]
        c_irr = self.caps["C_IRR_1_SalesReport"]

        rel_useful = self.space.goal_relevance(c1, goal, s0)
        rel_irr = self.space.goal_relevance(c_irr, goal, s0)

        self.assertGreater(rel_useful, 0.2)
        self.assertEqual(rel_irr, 0.0)

    def test_operational_propagation(self):
        """Evaluation Criteria 7: Can cost, reliability, availability be represented appropriately?"""
        c1 = self.caps["C1_CreateOrder_API"]
        c2 = self.caps["C2_MakePayment"]

        c12 = CompositeCapability.compose(c1, c2)
        expected_latency = c1.operational.time_ms + c2.operational.time_ms
        expected_cost = c1.operational.cost_money + c2.operational.cost_money
        expected_rel = c1.operational.reliability * c2.operational.reliability

        self.assertAlmostEqual(c12.operational.time_ms, expected_latency, places=2)
        self.assertAlmostEqual(c12.operational.cost_money, expected_cost, places=4)
        self.assertAlmostEqual(c12.operational.reliability, expected_rel, places=5)


if __name__ == "__main__":
    unittest.main()
