import unittest
import numpy as np

from src.models import (
    StateVariable, StateVariableType, ApplicationState,
    GoalCondition, GoalSpecification,
    Capability, CapabilityType, Precondition, Effect, QualityAttributes
)
from src.embedding import EmbeddingSchema, CapabilityEncoder


class TestEncoder(unittest.TestCase):

    def setUp(self):
        vars_list = [
            StateVariable("is_auth", StateVariableType.BOOLEAN),
            StateVariable("role", StateVariableType.ENUM, domain=["USER", "ADMIN"]),
            StateVariable("balance", StateVariableType.FLOAT),
        ]
        self.schema = EmbeddingSchema(state_variables=vars_list)
        self.encoder = CapabilityEncoder(self.schema)

    def test_encode_state(self):
        state = ApplicationState(values={"is_auth": True, "role": "ADMIN", "balance": 150.0})
        emb = self.encoder.encode_state(state)
        self.assertEqual(emb.dim, self.schema.state_dim)
        self.assertEqual(emb.vector[0], 1.0)
        self.assertEqual(emb.vector[2], 1.0)

    def test_encode_goal(self):
        goal = GoalSpecification(conditions=[
            GoalCondition("is_auth", True),
            GoalCondition("role", "ADMIN")
        ])

        emb = self.encoder.encode_goal(goal)
        self.assertEqual(len(emb.val_vector), self.schema.state_dim)
        self.assertEqual(len(emb.mask_vector), self.schema.state_dim)

        s_good = ApplicationState(values={"is_auth": True, "role": "ADMIN"})
        s_good_emb = self.encoder.encode_state(s_good)
        self.assertTrue(emb.is_satisfied_by(s_good_emb))

        s_bad = ApplicationState(values={"is_auth": False, "role": "ADMIN"})
        s_bad_emb = self.encoder.encode_state(s_bad)
        self.assertFalse(emb.is_satisfied_by(s_bad_emb))

    def test_encode_capability(self):
        cap = Capability(
            id="C_Test",
            name="TestCap",
            type=CapabilityType.API,
            preconditions=[Precondition("is_auth", True)],
            effects=[Effect("balance", 50.0)],
            resources=["Database", "Network"],
            quality=QualityAttributes(time_ms=100.0, monetary_cost=0.01),
            reliability=0.99,
            availability=1.0
        )

        emb = self.encoder.encode_capability(cap)
        self.assertEqual(emb.dim, self.schema.capability_dim)
        self.assertGreater(emb.dim, self.schema.state_dim)

        self.assertEqual(len(emb.pre_val), self.schema.state_dim)
        self.assertEqual(len(emb.pre_mask), self.schema.state_dim)
        self.assertEqual(len(emb.eff_val), self.schema.state_dim)
        self.assertEqual(len(emb.eff_mask), self.schema.state_dim)
        self.assertEqual(len(emb.type_vec), self.schema.type_dim)
        self.assertEqual(len(emb.resource_vec), self.schema.resource_dim)
        self.assertEqual(len(emb.operational_vec), 7)

        self.assertEqual(emb.pre_mask[0], 1.0)
        self.assertEqual(emb.pre_val[0], 1.0)


if __name__ == "__main__":
    unittest.main()
