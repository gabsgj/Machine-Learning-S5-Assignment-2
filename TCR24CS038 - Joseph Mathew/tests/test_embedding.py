"""Comprehensive Unit & Regression Tests for Capability Embedding System.

Runs under Python standard library `unittest`.
"""

import unittest
import numpy as np

from src.models.state import State, Goal, Condition, Effect
from src.models.capability import Capability, CapabilityType, ExecutionMechanism, DataParameter
from src.models.operational import CostProfile, ResourceRequirement, Constraint
from src.embedding.schema import EmbeddingSchema
from src.embedding.encoder import CapabilityEncoder
from src.embedding.composition import compose_capabilities, compose_sequence, compose_vectors
from src.embedding.metrics import (
    cosine_similarity, functional_similarity, mechanism_similarity,
    composability_score, goal_relevance_score
)
from src.data.ecommerce_dataset import build_ecommerce_domain


class TestCapabilityEmbedding(unittest.TestCase):

    def setUp(self):
        self.domain = build_ecommerce_domain()
        self.schema = self.domain["schema"]
        self.encoder = CapabilityEncoder(self.schema)
        self.caps = self.domain["named_capabilities"]

    def test_schema_partitioning(self):
        total_dim = self.schema.total_dim
        self.assertGreater(total_dim, 0)
        self.assertEqual(self.schema.slice_preconditions.stop, self.schema.dim_preconditions)
        self.assertEqual(self.schema.slice_effects.start, self.schema.dim_preconditions)
        self.assertEqual(self.schema.slice_resources.stop, total_dim)

    def test_state_application(self):
        s0 = State(variables={"cart_exists": True, "order_exists": False})
        effs = [Effect(variable="order_exists", action="set", value=True)]
        s1 = s0.apply_effects(effs)
        self.assertTrue(s1.variables["order_exists"])
        self.assertFalse(s0.variables["order_exists"])

    def test_encoder_subspaces(self):
        cap = self.caps["CreateOrder"]
        vec = self.encoder.encode_capability(cap)
        self.assertEqual(vec.shape, (self.schema.total_dim,))
        subspaces = self.encoder.get_subspaces(vec)
        self.assertEqual(len(subspaces), 8)
        self.assertGreater(np.max(np.abs(subspaces["effects"])), 0)

    def test_composition_associativity(self):
        c1 = self.caps["CreateOrder"]
        c2 = self.caps["MakePayment"]
        c3 = self.caps["SendNotification"]

        c12 = compose_capabilities(c1, c2)
        c12_3 = compose_capabilities(c12, c3)

        c23 = compose_capabilities(c2, c3)
        c1_23 = compose_capabilities(c1, c23)

        self.assertEqual([e.variable for e in c12_3.effects], [e.variable for e in c1_23.effects])
        self.assertAlmostEqual(c12_3.cost.monetary_cost, c1_23.cost.monetary_cost, places=5)
        self.assertAlmostEqual(c12_3.reliability, c1_23.reliability, places=5)

    def test_composability_vs_similarity(self):
        v_c1 = self.encoder.encode_capability(self.caps["CreateOrder"])
        v_c2 = self.encoder.encode_capability(self.caps["MakePayment"])
        v_c3 = self.encoder.encode_capability(self.caps["CancelCart"])

        # C1 -> C2 is composable
        score_12, _ = composability_score(v_c1, v_c2, self.schema)
        # C1 -> C3 is incompatible
        score_13, _ = composability_score(v_c1, v_c3, self.schema)

        self.assertGreater(score_12, 0.4)
        self.assertLess(score_13, 0.0)
        self.assertGreater(score_12, score_13)

    def test_alternative_implementations_subspace_separation(self):
        v_api = self.encoder.encode_capability(self.caps["CreateOrder"])
        v_db = self.encoder.encode_capability(self.caps["CreateOrder_Database"])

        fun_sim = functional_similarity(v_api, v_db, self.schema)
        mech_sim = mechanism_similarity(v_api, v_db, self.schema)

        self.assertGreaterEqual(fun_sim, 0.95)
        self.assertLess(mech_sim, 0.40)


if __name__ == "__main__":
    unittest.main()
