"""
Unit tests for goal relevance and operational quality evaluation.
"""

import unittest
from capability_embedding import (
    CapabilityEmbeddingSystem,
    Capability,
    Goal,
    State,
    goal_relevance,
    OperationalQuality,
    compute_operational_pareto_frontier
)


class TestGoalAndOperational(unittest.TestCase):

    def setUp(self):
        self.system = CapabilityEmbeddingSystem()

        self.goal = Goal({"Order.exists": True, "Payment.status": "SUCCESS"})
        self.s0 = State({"Order.exists": False, "Payment.status": "NOT_STARTED"})

        self.c_useful = Capability("CreateOrder", preconditions={}, effects={"Order.exists": True})
        self.c_irrelevant = Capability("BrowseCatalog", preconditions={}, effects={"Catalog.viewed": True})
        self.c_detrimental = Capability("CancelOrder", preconditions={}, effects={"Order.exists": False})

        self.system.schema.auto_register_from_domain(
            states=[self.s0],
            goals=[self.goal],
            capabilities=[self.c_useful, self.c_irrelevant, self.c_detrimental]
        )

        self.z_g = self.system.encode_goal(self.goal)
        self.z_s0 = self.system.encode_state(self.s0)
        self.z_useful = self.system.encode_capability(self.c_useful)
        self.z_irrel = self.system.encode_capability(self.c_irrelevant)
        self.z_detr = self.system.encode_capability(self.c_detrimental)

    def test_goal_relevance_distinction(self):
        rel_useful = goal_relevance(self.z_useful, self.z_g, self.z_s0)
        rel_irrel = goal_relevance(self.z_irrel, self.z_g, self.z_s0)
        rel_detr = goal_relevance(self.z_detr, self.z_g, self.z_s0)

        self.assertGreater(rel_useful, 0.2)
        self.assertAlmostEqual(rel_irrel, 0.0, places=4)
        self.assertLess(rel_detr, -0.2)

    def test_pareto_frontier_extraction(self):
        # C_fast_cheap: 10ms, $0.01, rel=0.99
        c1 = Capability("FastCheap", quality=OperationalQuality(execution_time_ms=10.0, monetary_cost=0.01, reliability=0.99))
        # C_slow_expensive_reliable: 500ms, $0.10, rel=0.9999
        c2 = Capability("SlowHighRel", quality=OperationalQuality(execution_time_ms=500.0, monetary_cost=0.10, reliability=0.9999))
        # C_dominated: 1000ms, $0.50, rel=0.90 (strictly worse than c1 and c2)
        c3 = Capability("Dominated", quality=OperationalQuality(execution_time_ms=1000.0, monetary_cost=0.50, reliability=0.90))

        z1 = self.system.encode_capability(c1)
        z2 = self.system.encode_capability(c2)
        z3 = self.system.encode_capability(c3)

        frontier, mask = compute_operational_pareto_frontier([z1, z2, z3])
        frontier_names = [f.name for f in frontier]

        self.assertIn("FastCheap", frontier_names)
        self.assertIn("SlowHighRel", frontier_names)
        self.assertNotIn("Dominated", frontier_names)


if __name__ == "__main__":
    unittest.main()
