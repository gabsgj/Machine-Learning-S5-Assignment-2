"""
Unit tests for similarity metrics and alternative implementations.
"""

import unittest
from capability_embedding import (
    CapabilityEmbeddingSystem,
    Capability,
    CapabilityType,
    ExecutionMechanism,
    functional_similarity,
    mechanism_similarity,
    similarity
)


class TestSimilarityMetrics(unittest.TestCase):

    def setUp(self):
        self.system = CapabilityEmbeddingSystem()

        self.c_api = Capability(
            name="CreateOrder_API",
            capability_type=CapabilityType.API,
            preconditions={"Cart.exists": True},
            effects={"Order.exists": True},
            mechanism=ExecutionMechanism(CapabilityType.API, {"endpoint": "/orders"})
        )
        self.c_db = Capability(
            name="CreateOrder_DB",
            capability_type=CapabilityType.DATABASE,
            preconditions={"Cart.exists": True},
            effects={"Order.exists": True},
            mechanism=ExecutionMechanism(CapabilityType.DATABASE, {"table": "orders"})
        )

        self.system.schema.auto_register_from_domain(capabilities=[self.c_api, self.c_db])
        self.z_api = self.system.encode_capability(self.c_api)
        self.z_db = self.system.encode_capability(self.c_db)

    def test_functional_equivalence_with_mechanism_distinction(self):
        # 1. Functional similarity should be 1.0 (exact same state effects)
        s_func = functional_similarity(self.z_api, self.z_db)
        self.assertAlmostEqual(s_func, 1.0, places=5)

        # 2. Mechanism similarity should be < 1.0 (different implementation types)
        s_mech = mechanism_similarity(self.z_api, self.z_db)
        self.assertLess(s_mech, 0.95)


if __name__ == "__main__":
    unittest.main()
