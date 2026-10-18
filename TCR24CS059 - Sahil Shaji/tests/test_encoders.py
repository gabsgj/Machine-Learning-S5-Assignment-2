"""
Unit tests for Encoders and Embedding representations.
"""

import unittest
import numpy as np

from capability_embedding import CapabilityEmbeddingSystem, encode
from capability_embedding.core.state import State, Goal
from capability_embedding.core.capability import Capability
from capability_embedding.core.types import CapabilityType


class TestEncoders(unittest.TestCase):

    def setUp(self):
        self.system = CapabilityEmbeddingSystem()

    def test_encode_state(self):
        s = State({"Cart.exists": True, "Order.exists": False})
        z_s = self.system.encode_state(s)
        self.assertGreater(len(z_s.raw), 0)
        self.assertEqual(z_s.entity_type, "state")

    def test_encode_goal(self):
        g = Goal({"Order.exists": True, "Payment.status": "SUCCESS"})
        z_g = self.system.encode_goal(g)
        self.assertGreater(len(z_g.raw), 0)
        self.assertEqual(z_g.entity_type, "goal")

    def test_encode_capability(self):
        c = Capability(
            name="CreateOrder",
            capability_type=CapabilityType.API,
            preconditions={"Cart.exists": True},
            effects={"Order.exists": True}
        )
        z_c = self.system.encode_capability(c)
        self.assertEqual(z_c.entity_type, "capability")
        self.assertGreater(z_c.norm(), 0)

    def test_unified_encode_dispatch(self):
        s = State({"Cart.exists": True})
        g = Goal({"Order.exists": True})
        c = Capability("TestCap", preconditions={"A": True}, effects={"B": True})

        e_s = encode(s)
        e_g = encode(g)
        e_c = encode(c)

        self.assertEqual(e_s.entity_type, "state")
        self.assertEqual(e_g.entity_type, "goal")
        self.assertEqual(e_c.entity_type, "capability")


if __name__ == "__main__":
    unittest.main()
