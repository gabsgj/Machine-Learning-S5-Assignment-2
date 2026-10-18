"""
Unit Tests for Capability Composition Engine:
- Multi-step composition chains
- Intermediate precondition internalization
- State execution parity
- Directional non-commutativity
"""

import unittest
import numpy as np

from capembed.pipeline import CapabilityEmbeddingSystem
from datasets.ecommerce_domain import get_ecommerce_domain
from datasets.devops_domain import get_devops_domain


class TestCompositionEngine(unittest.TestCase):
    def setUp(self):
        self.domain = get_ecommerce_domain()
        self.system = CapabilityEmbeddingSystem(self.domain["schema"])
        self.c1 = self.domain["c1"]
        self.c2 = self.domain["c2"]
        self.c4 = self.domain["c4"]
        self.c5 = self.domain["c5"]

    def test_non_commutativity(self):
        """Sequential composition is non-commutative: C2 o C1 != C1 o C2."""
        ec1 = self.system.encode(self.c1)
        ec2 = self.system.encode(self.c2)

        comp_12 = self.system.compose([ec1, ec2])
        comp_21 = self.system.compose([ec2, ec1])

        # Preconditions differ because C2 requires Order.exists which C1 does not produce if run second
        self.assertNotEqual(comp_12.raw_capability.preconditions, comp_21.raw_capability.preconditions)
        self.assertGreater(np.linalg.norm(comp_12.vector - comp_21.vector), 0.1)

    def test_precondition_absorption(self):
        """Preconditions of downstream capabilities satisfied upstream are absorbed."""
        ec1 = self.system.encode(self.c1)
        ec2 = self.system.encode(self.c2)

        # C2 requires Order.exists = True. C1 produces Order.exists = True.
        comp_12 = self.system.compose([ec1, ec2])

        # Order.exists should NOT be an external precondition of the composite capability
        self.assertNotIn("Order.exists", comp_12.raw_capability.preconditions)
        # But initial preconditions of C1 remain
        self.assertIn("Cart.exists", comp_12.raw_capability.preconditions)

    def test_end_to_end_state_execution_equivalence(self):
        """Executing composite capability produces identical state to sequential individual execution."""
        chain = [self.c1, self.c2, self.c4, self.c5]
        s_curr = self.domain["initial_state"].copy()

        # Step by step execution
        for c in chain:
            s_curr = c.execute(s_curr)

        # Composite execution
        enc_chain = [self.system.encode(c) for c in chain]
        composite_cap = self.system.compose(enc_chain)

        s_composite = composite_cap.raw_capability.execute(self.domain["initial_state"].copy())

        self.assertEqual(s_curr.variables, s_composite.variables)

    def test_devops_pipeline_composition(self):
        """Validates composition on the 7-step DevOps pipeline."""
        devops = get_devops_domain()
        sys = CapabilityEmbeddingSystem(devops["schema"])
        chain = devops["pipeline_chain"]
        enc_chain = [sys.encode(c) for c in chain]

        comp = sys.compose(enc_chain, name="FullCI_CD")
        self.assertEqual(len(comp.raw_capability.sub_capabilities), 7)
        self.assertTrue(comp.raw_capability.effects["Cluster.deployed"])
        self.assertTrue(comp.raw_capability.effects["HealthCheck.passed"])


if __name__ == "__main__":
    unittest.main()
