import unittest
import numpy as np

from src.models import (
    StateVariable, StateVariableType,
    Capability, CapabilityType, Precondition, Effect, ExecutionMechanism
)
from src.embedding import EmbeddingSchema, EmbeddingSystem


class TestSimilarityAndCompatibility(unittest.TestCase):

    def setUp(self):
        self.schema = EmbeddingSchema(state_variables=[
            StateVariable("state_a", StateVariableType.BOOLEAN),
            StateVariable("state_b", StateVariableType.BOOLEAN),
            StateVariable("order_exists", StateVariableType.BOOLEAN)
        ])
        self.system = EmbeddingSystem(self.schema)

    def test_similarity_metrics(self):
        c_api = Capability(
            id="C_API", name="CapAPI", type=CapabilityType.API,
            preconditions=[Precondition("state_a", True)],
            effects=[Effect("state_b", True)],
            mechanism=ExecutionMechanism("HTTP_API", {"endpoint": "/test"})
        )
        c_db = Capability(
            id="C_DB", name="CapDB", type=CapabilityType.DATABASE,
            preconditions=[Precondition("state_a", True)],
            effects=[Effect("state_b", True)],
            mechanism=ExecutionMechanism("SQL_QUERY", {"table": "test"})
        )

        sim_func = self.system.similarity(c_api, c_db, metric="functional")
        self.assertAlmostEqual(sim_func, 1.0, places=4)

        sim_mech = self.system.similarity(c_api, c_db, metric="mechanism")
        self.assertLess(sim_mech, 0.9)

    def test_compatibility_detection(self):
        c1 = Capability(
            id="C1", name="CreateOrder",
            effects=[Effect("order_exists", True)]
        )
        c2 = Capability(
            id="C2", name="MakePayment",
            preconditions=[Precondition("order_exists", True)]
        )
        c3 = Capability(
            id="C3", name="CancelCart",
            preconditions=[Precondition("order_exists", False)]
        )

        sc_comp = self.system.compatibility(c1, c2)
        self.assertTrue(sc_comp.is_compatible)
        self.assertGreater(sc_comp.total_score, 0.8)

        sc_incomp = self.system.compatibility(c1, c3)
        self.assertFalse(sc_incomp.is_compatible)
        self.assertEqual(sc_incomp.total_score, 0.0)
        self.assertGreater(len(sc_incomp.conflicts), 0)


if __name__ == "__main__":
    unittest.main()
