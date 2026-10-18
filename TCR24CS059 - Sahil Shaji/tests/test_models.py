"""
Unit tests for core models (State, Goal, Capability, OperationalQuality).
"""

import unittest
from capability_embedding.core.state import State, Goal
from capability_embedding.core.capability import Capability
from capability_embedding.core.types import CapabilityType, ExecutionMechanism, InputSpec, OutputSpec
from capability_embedding.core.operational import OperationalQuality, ResourceRequirement


class TestCoreModels(unittest.TestCase):

    def test_state_basic_operations(self):
        s = State({"Cart.exists": True, "Cart.item_count": 3})
        self.assertTrue(s.satisfies({"Cart.exists": True}))
        self.assertFalse(s.satisfies({"Cart.exists": False}))
        self.assertFalse(s.satisfies({"Cart.item_count": 0}))

        # State transition
        s_prime = s.apply({"Order.exists": True})
        self.assertTrue(s_prime.get("Order.exists"))
        self.assertTrue(s_prime.get("Cart.exists"))
        self.assertFalse(s.contains("Order.exists"))  # Immutability preserved

    def test_goal_satisfaction(self):
        g = Goal({"Order.exists": True, "Payment.status": "SUCCESS"})
        s1 = State({"Order.exists": True, "Payment.status": "PENDING"})
        s2 = State({"Order.exists": True, "Payment.status": "SUCCESS"})

        self.assertFalse(g.is_satisfied_by(s1))
        self.assertTrue(g.is_satisfied_by(s2))
        self.assertEqual(g.satisfaction_ratio(s1), 0.5)
        self.assertEqual(g.satisfaction_ratio(s2), 1.0)

    def test_capability_applicability_and_execution(self):
        c = Capability(
            name="CreateOrder",
            capability_type=CapabilityType.API,
            preconditions={"Cart.exists": True},
            effects={"Order.exists": True}
        )
        s_valid = State({"Cart.exists": True})
        s_invalid = State({"Cart.exists": False})

        self.assertTrue(c.is_applicable_to(s_valid))
        self.assertFalse(c.is_applicable_to(s_invalid))

        s_next = c.apply(s_valid)
        self.assertTrue(s_next.get("Order.exists"))

    def test_operational_quality_composition(self):
        q1 = OperationalQuality(execution_time_ms=100.0, monetary_cost=0.02, reliability=0.99)
        q2 = OperationalQuality(execution_time_ms=200.0, monetary_cost=0.03, reliability=0.98)

        q12 = q1.compose_with(q2)
        self.assertEqual(q12.execution_time_ms, 300.0)
        self.assertEqual(q12.monetary_cost, 0.05)
        self.assertAlmostEqual(q12.reliability, 0.99 * 0.98, places=5)


if __name__ == "__main__":
    unittest.main()
