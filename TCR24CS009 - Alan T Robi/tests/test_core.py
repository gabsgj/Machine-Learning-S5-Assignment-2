import unittest
import numpy as np

from src.capability import Capability, InputSpec, OutputSpec, CostSpec, load_capabilities_from_json
from src.state import State, Goal
from src.encoder import CapabilityVocabulary, CapabilityEncoder, CapabilityPCAEncoder
from src.similarity import similarity, functional_similarity
from src.compatibility import compatibility
from src.composition import compose
from src.evaluation import evaluate_goal_relevance

class TestCapabilityCore(unittest.TestCase):

    def setUp(self):
        self.capabilities = load_capabilities_from_json("data/capabilities.json")
        self.cap_map = {c.name: c for c in self.capabilities}
        self.vocab = CapabilityVocabulary(self.capabilities)
        self.encoder = CapabilityEncoder(self.vocab)

    def test_capability_validation(self):
        """Test that invalid capability definitions trigger ValueError."""
        with self.assertRaises(ValueError):
            # Invalid type
            c_bad = Capability(name="BadCap", type="INVALID_TYPE")
            c_bad.validate()

        with self.assertRaises(ValueError):
            # Invalid reliability
            c_bad = Capability(name="BadCap", type="API", reliability=1.5)
            c_bad.validate()

        with self.assertRaises(ValueError):
            # Negative cost
            c_bad = Capability(name="BadCap", type="API", cost=CostSpec(time=-10.0))
            c_bad.validate()

    def test_encoding(self):
        """Test structured vector encoding dimension and values."""
        c = self.cap_map["CreateOrder"]
        vec = self.encoder.encode_capability(c)
        self.assertEqual(len(vec), self.encoder.dimension)
        self.assertTrue(np.all(vec >= 0.0))

        # Test state and goal encoding
        state = State({"CartExists": True, "CartItemCount": 3})
        vec_s = self.encoder.encode_state(state)
        self.assertEqual(len(vec_s), self.encoder.dimension)

        goal = Goal(["Order.exists=true", "Payment.status=SUCCESS"])
        vec_g = self.encoder.encode_goal(goal)
        self.assertEqual(len(vec_g), self.encoder.dimension)

    def test_pca_dense_projection(self):
        """Test PCA dimensionality reduction."""
        matrix = np.array([self.encoder.encode_capability(c) for c in self.capabilities])
        pca_enc = CapabilityPCAEncoder(n_components=16)
        dense = pca_enc.fit_transform(matrix)
        self.assertEqual(dense.shape, (len(self.capabilities), 16))

    def test_similarity(self):
        """Test cosine similarity function."""
        c1 = self.cap_map["CreateOrder"]
        c2 = self.cap_map["CreateOrderDatabase"]
        v1 = self.encoder.encode_capability(c1)
        v2 = self.encoder.encode_capability(v2_cap := c2)

        sim_self = similarity(v1, v1)
        self.assertAlmostEqual(sim_self, 1.0, places=5)

        func_sim = functional_similarity(v1, v2, self.encoder)
        self.assertAlmostEqual(func_sim, 1.0, places=5)

    def test_compatibility(self):
        """Test CreateOrder -> MakePayment (compatible) vs CreateOrder -> CancelCart (incompatible)."""
        c_create = self.cap_map["CreateOrder"]
        c_pay = self.cap_map["MakePayment"]
        c_cancel = self.cap_map["CancelCart"]

        # CreateOrder -> MakePayment
        res_compat = compatibility(c_create, c_pay)
        self.assertTrue(res_compat.is_compatible)
        self.assertGreaterEqual(res_compat.compatibility_score, 0.5)

        # CreateOrder -> CancelCart
        res_incompat = compatibility(c_create, c_cancel)
        self.assertFalse(res_incompat.is_compatible)
        self.assertTrue(res_incompat.has_contradiction)

    def test_composition(self):
        """Test valid sequence composition and incompatible composition rejection."""
        c1 = self.cap_map["CreateOrder"]
        c2 = self.cap_map["MakePayment"]
        c3 = self.cap_map["SendNotification"]

        # Valid Composition
        comp = compose([c1, c2, c3], composite_name="CompletePurchase")
        self.assertEqual(comp.name, "CompletePurchase")
        self.assertIn("OrderExists=true", comp.effects)
        self.assertIn("PaymentStatus=SUCCESS", comp.effects)
        self.assertIn("NotificationSent=true", comp.effects)

        # Incompatible Composition
        with self.assertRaises(ValueError):
            compose([c1, self.cap_map["CancelCart"]])

    def test_alternative_implementations_distinguishable(self):
        """Test that alternative implementations remain distinguishable in mechanism/full space."""
        c_api = self.cap_map["CreateOrder"]
        c_db = self.cap_map["CreateOrderDatabase"]

        v_api = self.encoder.encode_capability(c_api)
        v_db = self.encoder.encode_capability(c_db)

        full_sim = similarity(v_api, v_db)
        func_sim = functional_similarity(v_api, v_db, self.encoder)

        self.assertAlmostEqual(func_sim, 1.0, places=5)
        self.assertLess(full_sim, 1.0)

    def test_goal_relevance(self):
        """Test goal relevance evaluation."""
        goal = Goal(["Order.exists=true", "Payment.status=SUCCESS"])
        rel_pay = evaluate_goal_relevance(self.cap_map["MakePayment"], goal)
        rel_prof = evaluate_goal_relevance(self.cap_map["UpdateProfile"], goal)

        self.assertGreater(rel_pay, 0.0)
        self.assertEqual(rel_prof, 0.0)


if __name__ == "__main__":
    unittest.main()
