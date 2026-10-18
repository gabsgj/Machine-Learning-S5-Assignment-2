"""
Unit Tests for the 8 Required Formal Properties (Section 6.1 and Section 8):
1. Capability identity: Functionally different capabilities distinguishable.
2. State awareness: Capture relationship between capability and states.
3. Precondition-effect compatibility: Capture E_i => P_j, distinguish compatible from incompatible.
4. Input-output compatibility: Represent cases where O_i satisfies I_j.
5. Similarity and composability: Decouple resemblance from composability.
6. Composition: Represent composite capabilities algebraically in vector space.
7. Goal relevance: Measure progress toward desired goal.
8. Operational properties: Cost, reliability, availability, constraints, resources.
"""

import unittest
import numpy as np
import math

from capembed.core import (
    Capability,
    CapabilityType,
    InputSpec,
    OutputSpec,
    OperationalProfile,
    ExecutionMechanism,
    State,
    Goal,
    DomainSchema,
)
from capembed.pipeline import CapabilityEmbeddingSystem
from datasets.ecommerce_domain import get_ecommerce_domain


class TestFormalProperties(unittest.TestCase):
    def setUp(self):
        self.domain = get_ecommerce_domain()
        self.schema = self.domain["schema"]
        self.system = CapabilityEmbeddingSystem(self.schema)
        self.c1 = self.domain["c1"]
        self.c2 = self.domain["c2"]
        self.c3 = self.domain["c3"]
        self.c4 = self.domain["c4"]
        self.c5 = self.domain["c5"]
        self.init_state = self.domain["initial_state"]
        self.goal = self.domain["goal"]

    def test_property_1_capability_identity(self):
        """Property 1: Distinct capabilities have distinct non-zero vector representations."""
        ec1 = self.system.encode(self.c1)
        ec2 = self.system.encode(self.c2)
        ec3 = self.system.encode(self.c3)

        # Non-zero norm
        self.assertGreater(np.linalg.norm(ec1.vector), 0.0)
        self.assertGreater(np.linalg.norm(ec2.vector), 0.0)

        # Distinguishable (Euclidean distance > 0)
        dist_12 = np.linalg.norm(ec1.vector - ec2.vector)
        dist_13 = np.linalg.norm(ec1.vector - ec3.vector)
        self.assertGreater(dist_12, 0.5)
        self.assertGreater(dist_13, 0.5)

    def test_property_2_state_awareness(self):
        """Property 2: Vector representation captures state applicability."""
        ec1 = self.system.encode(self.c1)
        es_init = self.system.encode(self.init_state)

        # C1 is applicable to initial state
        score_applicable = self.system.state_applicability(es_init, ec1)
        self.assertEqual(score_applicable, 1.0)

        # Inapplicable state where Cart.exists is False
        inapplicable_state = self.init_state.copy()
        inapplicable_state.set("Cart.exists", False)
        es_inapp = self.system.encode(inapplicable_state)

        score_inapp = self.system.state_applicability(es_inapp, ec1)
        self.assertLess(score_inapp, 0.0)

    def test_property_3_precondition_effect_compatibility(self):
        """Property 3: C1 -> C2 is compatible, while C1 -> C3 is incompatible."""
        ec1 = self.system.encode(self.c1)
        ec2 = self.system.encode(self.c2)
        ec3 = self.system.encode(self.c3)

        c1_c2_detail = self.system.compatibility(ec1, ec2, detailed=True)
        c1_c3_detail = self.system.compatibility(ec1, ec3, detailed=True)

        # C1 -> C2 has positive PE compatibility (OrderExists satisfied)
        self.assertGreaterEqual(c1_c2_detail["precondition_effect"], 0.8)

        # C1 -> C3 has negative PE compatibility (OrderExists conflicted)
        self.assertLessEqual(c1_c3_detail["precondition_effect"], -0.8)

        # Clear discrimination
        self.assertGreater(c1_c2_detail["total_composability"], c1_c3_detail["total_composability"])

    def test_property_4_input_output_compatibility(self):
        """Property 4: Input-output dependencies are represented."""
        ec1 = self.system.encode(self.c1)  # Outputs order_id
        ec2 = self.system.encode(self.c2)  # Requires order_id

        detail = self.system.compatibility(ec1, ec2, detailed=True)
        self.assertGreater(detail["input_output"], 0.0)

    def test_property_5_similarity_vs_composability(self):
        """
        Property 5: Functional similarity and composability are decoupled.
        Substitutes (API vs DB) have high similarity but don't chain.
        Chaining capabilities (C1 -> C2) have high composability but low similarity.
        """
        c1_api = self.domain["alternatives"][0]
        c1_db = self.domain["alternatives"][1]

        ec_api = self.system.encode(c1_api)
        ec_db = self.system.encode(c1_db)
        ec1 = self.system.encode(self.c1)
        ec2 = self.system.encode(self.c2)

        # Substitutes: high functional similarity
        sim_substitutes = self.system.similarity(ec_api, ec_db, mode="functional")
        self.assertAlmostEqual(sim_substitutes, 1.0, places=3)

        # Composable chain: low functional similarity, high composability
        sim_chain = self.system.similarity(ec1, ec2, mode="functional")
        comp_chain = self.system.compatibility(ec1, ec2)

        self.assertLess(sim_chain, 0.4)
        self.assertGreater(comp_chain, 0.7)

    def test_property_6_composition_associativity(self):
        """Property 6: Composition in vector space is strictly associative."""
        ec1 = self.system.encode(self.c1)
        ec2 = self.system.encode(self.c2)
        ec5 = self.system.encode(self.c5)

        # Left: (C5 o C2) o C1
        c_left = self.system.compose([self.system.compose([ec1, ec2]), ec5])
        # Right: C5 o (C2 o C1)
        c_right = self.system.compose([ec1, self.system.compose([ec2, ec5])])

        diff = np.linalg.norm(c_left.vector - c_right.vector)
        self.assertLess(diff, 1e-6)

    def test_property_7_goal_relevance(self):
        """Property 7: Useful capabilities have positive relevance; irrelevant ones have 0."""
        ec1 = self.system.encode(self.c1)
        irr_cap = self.system.encode(self.domain["irrelevant"][0])
        eg = self.system.encode(self.goal)

        rel_useful = self.system.goal_relevance(ec1, eg)
        rel_irrelevant = self.system.goal_relevance(irr_cap, eg)

        self.assertGreater(rel_useful, 0.0)
        self.assertEqual(rel_irrelevant, 0.0)

    def test_property_8_operational_attributes(self):
        """Property 8: Operational QoS attributes are preserved and additive in log domain."""
        ec1 = self.system.encode(self.c1)
        ec2 = self.system.encode(self.c2)

        ec12 = self.system.compose([ec1, ec2])

        # Time is additive
        expected_time = self.c1.operational_profile.execution_time_ms + self.c2.operational_profile.execution_time_ms
        self.assertAlmostEqual(ec12.raw_capability.operational_profile.execution_time_ms, expected_time, places=2)

        # Reliability is multiplicative
        expected_rel = self.c1.operational_profile.reliability * self.c2.operational_profile.reliability
        self.assertAlmostEqual(ec12.raw_capability.operational_profile.reliability, expected_rel, places=4)

        # Vector coordinate -ln(Rel) is strictly additive
        expected_vec_log_rel = ec1.v_ops[5] + ec2.v_ops[5]
        self.assertAlmostEqual(ec12.v_ops[5], expected_vec_log_rel, places=5)


if __name__ == "__main__":
    unittest.main()
