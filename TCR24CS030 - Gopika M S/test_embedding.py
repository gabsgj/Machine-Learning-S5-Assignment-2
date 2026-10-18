import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from capability_embedding import (
    example_application,
    encode_state,
    encode_goal,
    encode_capability,
    similarity,
    compatibility,
    compose,
    goal_relevance,
)


class TestCapabilityEmbedding(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = example_application()

    def test_state_encoding(self):
        vector = encode_state(self.app["initial_state"])
        self.assertGreater(len(vector), 0)

    def test_goal_encoding(self):
        vector = encode_goal(self.app["goal"])
        self.assertGreater(len(vector), 0)

    def test_capability_encoding(self):
        vector = encode_capability(self.app["CreateOrder"])
        self.assertGreater(len(vector), len(encode_state(self.app["initial_state"])))

    def test_capability_similarity_is_symmetric(self):
        a = self.app["CreateOrder"]
        b = self.app["MakePayment"]
        self.assertAlmostEqual(
            similarity(a, b),
            similarity(b, a),
            places=7
        )

    def test_create_order_to_payment_is_compatible(self):
        score = compatibility(
            self.app["CreateOrder"],
            self.app["MakePayment"]
        )
        self.assertGreater(score, 0.4)

    def test_create_order_to_cancel_cart_is_lower(self):
        good = compatibility(
            self.app["CreateOrder"],
            self.app["MakePayment"]
        )
        bad = compatibility(
            self.app["CreateOrder"],
            self.app["CancelCart"]
        )
        self.assertGreater(good, bad)

    def test_composition(self):
        composite = compose([
            self.app["CreateOrder"],
            self.app["MakePayment"],
            self.app["SendNotification"],
        ])
        self.assertIn("CreateOrder", composite.name)
        self.assertIn("MakePayment", composite.name)
        self.assertIn("SendNotification", composite.name)
        self.assertLessEqual(composite.reliability, 1.0)

    def test_goal_relevance(self):
        composite = compose([
            self.app["CreateOrder"],
            self.app["MakePayment"],
            self.app["SendNotification"],
        ])
        self.assertEqual(goal_relevance(composite, self.app["goal"]), 1.0)

    def test_irrelevant_capability(self):
        relevance = goal_relevance(
            self.app["UpdateProfile"],
            self.app["goal"]
        )
        self.assertEqual(relevance, 0.0)


if __name__ == "__main__":
    unittest.main()
