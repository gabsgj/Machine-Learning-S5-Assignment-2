import unittest
from src.models import (
    StateVariableType, StateVariable, ApplicationState,
    ComparisonOp, GoalCondition, GoalSpecification,
    CapabilityType, Precondition, Effect, QualityAttributes, Capability
)


class TestModels(unittest.TestCase):

    def test_application_state_operations(self):
        state = ApplicationState(name="TestState", values={"x": True, "count": 5})
        self.assertTrue(state.get("x"))
        self.assertEqual(state.get("count"), 5)
        self.assertEqual(state.get("nonexistent", 42), 42)

        state.set("y", "ADMIN")
        self.assertEqual(state.get("y"), "ADMIN")

        clone = state.clone("Cloned")
        self.assertEqual(clone.name, "Cloned")
        self.assertTrue(clone.get("x"))

        clone.set("count", 10)
        diff = state.diff(clone)
        self.assertIn("count", diff)
        self.assertEqual(diff["count"], (5, 10))

        d = state.to_dict()
        reconstructed = ApplicationState.from_dict(d)
        self.assertEqual(reconstructed.values, state.values)

    def test_goal_specification(self):
        goal = GoalSpecification(
            name="TestGoal",
            conditions=[
                GoalCondition("order_created", True, ComparisonOp.EQ),
                GoalCondition("item_count", 0, ComparisonOp.EQ)
            ]
        )

        s1 = ApplicationState(values={"order_created": True, "item_count": 0})
        self.assertTrue(goal.is_satisfied_by(s1))
        self.assertEqual(goal.satisfaction_ratio(s1), 1.0)

        s2 = ApplicationState(values={"order_created": True, "item_count": 2})
        self.assertFalse(goal.is_satisfied_by(s2))
        self.assertEqual(goal.satisfaction_ratio(s2), 0.5)
        self.assertEqual(len(goal.unsatisfied_conditions(s2)), 1)

    def test_capability_preconditions_and_effects(self):
        cap = Capability(
            id="C_Test",
            name="TestCap",
            type=CapabilityType.API,
            preconditions=[Precondition("user_logged_in", True)],
            effects=[Effect("cart_cleared", True), Effect("balance", 10, action="DECREMENT")],
            reliability=0.99,
            availability=1.0
        )

        state = ApplicationState(values={"user_logged_in": True, "balance": 100})
        self.assertTrue(cap.is_applicable(state))

        next_state = cap.apply(state)
        self.assertTrue(next_state.get("cart_cleared"))
        self.assertEqual(next_state.get("balance"), 90)

        # Test serialization
        data = cap.to_dict()
        cap_loaded = Capability.from_dict(data)
        self.assertEqual(cap_loaded.id, cap.id)
        self.assertEqual(len(cap_loaded.preconditions), 1)
        self.assertEqual(len(cap_loaded.effects), 2)


if __name__ == "__main__":
    unittest.main()
