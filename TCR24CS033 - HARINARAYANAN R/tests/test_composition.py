import unittest
import numpy as np

from src.models import (
    StateVariable, StateVariableType, ApplicationState,
    Capability, Precondition, Effect, QualityAttributes
)
from src.embedding import EmbeddingSchema, EmbeddingSystem


class TestComposition(unittest.TestCase):

    def setUp(self):
        vars_list = [
            StateVariable("cart_exists", StateVariableType.BOOLEAN),
            StateVariable("order_exists", StateVariableType.BOOLEAN),
            StateVariable("payment_done", StateVariableType.BOOLEAN),
        ]
        self.schema = EmbeddingSchema(state_variables=vars_list)
        self.system = EmbeddingSystem(self.schema)

        self.c1 = Capability(
            id="C1", name="CreateOrder",
            preconditions=[Precondition("cart_exists", True)],
            effects=[Effect("order_exists", True)],
            quality=QualityAttributes(time_ms=100.0, monetary_cost=0.01),
            reliability=0.99
        )

        self.c2 = Capability(
            id="C2", name="MakePayment",
            preconditions=[Precondition("order_exists", True)],
            effects=[Effect("payment_done", True)],
            quality=QualityAttributes(time_ms=200.0, monetary_cost=0.05),
            reliability=0.98
        )

    def test_compose_pair_semantics(self):
        c12, emb12 = self.system.compose([self.c1, self.c2])

        self.assertTrue(c12.is_composite)
        self.assertEqual(c12.sub_capabilities, ["C1", "C2"])

        # Precondition of c2 (order_exists=True) was produced by c1, so it shouldn't be in c12's open preconditions
        prec_vars = [p.variable for p in c12.preconditions]
        self.assertIn("cart_exists", prec_vars)
        self.assertNotIn("order_exists", prec_vars)

        # Effects of both should be present
        eff_vars = [e.variable for e in c12.effects]
        self.assertIn("order_exists", eff_vars)
        self.assertIn("payment_done", eff_vars)

        # Additive costs & multiplicative reliability
        self.assertEqual(c12.quality.time_ms, 300.0)
        self.assertAlmostEqual(c12.quality.monetary_cost, 0.06, places=4)
        self.assertAlmostEqual(c12.reliability, 0.99 * 0.98, places=5)

    def test_vector_algebraic_composition_homomorphism(self):
        emb1 = self.system.encode_capability(self.c1)
        emb2 = self.system.encode_capability(self.c2)

        # Algebraic composition
        v_alg = self.system.composer.vector_compose(emb1, emb2)

        # Semantic composition
        c12, emb12 = self.system.compose([self.c1, self.c2])

        # Cosine alignment should be high (> 0.95)
        cos_sim = float(np.dot(v_alg, emb12.vector) / (np.linalg.norm(v_alg) * np.linalg.norm(emb12.vector)))
        self.assertGreater(cos_sim, 0.95)

    def test_composition_associativity(self):
        c3 = Capability(
            id="C3", name="SendReceipt",
            preconditions=[Precondition("payment_done", True)],
            effects=[Effect("cart_exists", False)],
            quality=QualityAttributes(time_ms=50.0, monetary_cost=0.005),
            reliability=0.995
        )

        # (C3 o C2) o C1
        c12, _ = self.system.compose([self.c1, self.c2])
        c_left, emb_left = self.system.compose([c12, c3])

        # C3 o (C2 o C1)
        c23, _ = self.system.compose([self.c2, c3])
        c_right, emb_right = self.system.compose([self.c1, c23])

        self.assertAlmostEqual(c_left.quality.time_ms, c_right.quality.time_ms)
        self.assertAlmostEqual(c_left.reliability, c_right.reliability, places=6)
        self.assertTrue(np.allclose(emb_left.vector, emb_right.vector, atol=1e-5))


if __name__ == "__main__":
    unittest.main()
