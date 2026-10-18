"""
Unit tests for compatibility, composability, and applicability metrics.
"""

import unittest
from capability_embedding import (
    CapabilityEmbeddingSystem,
    Capability,
    composability,
    precondition_effect_compatibility,
    state_applicability,
    State
)


class TestCompatibilityMetrics(unittest.TestCase):

    def setUp(self):
        self.system = CapabilityEmbeddingSystem()
        self.c1 = Capability("CreateOrder", preconditions={}, effects={"Order.exists": True})
        self.c2 = Capability("MakePayment", preconditions={"Order.exists": True}, effects={})
        self.c3 = Capability("CancelCart", preconditions={"Order.exists": False}, effects={})

        self.system.schema.auto_register_from_domain(capabilities=[self.c1, self.c2, self.c3])
        self.z1 = self.system.encode_capability(self.c1)
        self.z2 = self.system.encode_capability(self.c2)
        self.z3 = self.system.encode_capability(self.c3)

    def test_canonical_compatibility_pattern(self):
        # C1 -> C2 must be compatible
        comp_12 = composability(self.z1, self.z2)
        pe_12 = precondition_effect_compatibility(self.z1, self.z2)
        self.assertGreater(comp_12, 0.0)
        self.assertEqual(pe_12, 1.0)

        # C1 -> C3 must be incompatible
        comp_13 = composability(self.z1, self.z3)
        pe_13 = precondition_effect_compatibility(self.z1, self.z3)
        self.assertLess(comp_13, 0.0)
        self.assertEqual(pe_13, -1.0)

    def test_state_applicability(self):
        s_true = self.system.encode_state(State({"Order.exists": True}))
        s_false = self.system.encode_state(State({"Order.exists": False}))

        self.assertEqual(state_applicability(s_true, self.z2), 1.0)
        self.assertEqual(state_applicability(s_false, self.z2), 0.0)


if __name__ == "__main__":
    unittest.main()
