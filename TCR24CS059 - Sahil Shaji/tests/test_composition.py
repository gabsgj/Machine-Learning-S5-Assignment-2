"""
Unit tests for symbolic and vector composition algebra.
"""

import unittest
import numpy as np

from capability_embedding import (
    CapabilityEmbeddingSystem,
    Capability,
    CapabilityType,
    compose_two,
    compose_sequence,
    compose_embeddings,
    compose_vector_sequence,
    CompositionValidationError
)


class TestCompositionAlgebra(unittest.TestCase):

    def setUp(self):
        self.system = CapabilityEmbeddingSystem()
        self.c1 = Capability(
            name="CreateOrder",
            preconditions={"Cart.exists": True},
            effects={"Order.exists": True, "Order.status": "CREATED"}
        )
        self.c2 = Capability(
            name="MakePayment",
            preconditions={"Order.exists": True},
            effects={"Payment.status": "SUCCESS"}
        )
        self.c3 = Capability(
            name="CancelCart",
            preconditions={"Order.exists": False},
            effects={"Cart.exists": False}
        )

        # Register
        self.system.schema.auto_register_from_domain(capabilities=[self.c1, self.c2, self.c3])

    def test_valid_symbolic_composition(self):
        c12 = compose_two(self.c1, self.c2)
        self.assertTrue(c12.is_composite)
        # Preconditions: Cart.exists is required, Order.exists was satisfied internally!
        self.assertIn("Cart.exists", c12.preconditions)
        self.assertNotIn("Order.exists", c12.preconditions)
        # Effects: both accumulated
        self.assertEqual(c12.effects["Order.exists"], True)
        self.assertEqual(c12.effects["Payment.status"], "SUCCESS")

    def test_invalid_symbolic_composition(self):
        # C1 produces Order.exists = True, but C3 requires Order.exists = False!
        with self.assertRaises(CompositionValidationError):
            _ = compose_two(self.c1, self.c3)

    def test_vector_composition_effect_fidelity(self):
        c12_symb = compose_two(self.c1, self.c2)
        z12_symb = self.system.encode_capability(c12_symb)

        z1 = self.system.encode_capability(self.c1)
        z2 = self.system.encode_capability(self.c2)
        z12_vec = compose_embeddings(z1, z2)

        # Delta vectors should match exactly
        np.testing.assert_allclose(z12_symb.delta_vector, z12_vec.delta_vector, atol=1e-5)


if __name__ == "__main__":
    unittest.main()
