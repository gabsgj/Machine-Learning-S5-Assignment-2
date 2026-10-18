import unittest
from capability_embedding import load_data, compatibility, compose, goal_relevance, CapabilityEncoder

class TestCapabilityEmbedding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app, caps = load_data("dataset.json")
        cls.app = app
        cls.caps = {c.id: c for c in caps}
        cls.encoder = CapabilityEncoder(caps)

    def test_positive_compatibility(self):
        self.assertGreaterEqual(
            compatibility(self.caps["C1"], self.caps["C2"]), 0.75
        )

    def test_negative_compatibility(self):
        self.assertLess(
            compatibility(self.caps["C1"], self.caps["C3"]), 0.75
        )

    def test_composition(self):
        c = compose([self.caps["C1"], self.caps["C2"], self.caps["C4"]])
        self.assertTrue(c.effects["Notification.sent"])
        self.assertAlmostEqual(c.reliability, 0.941094, places=6)
        self.assertEqual(c.cost["time_ms"], 550)

    def test_goal_relevance(self):
        self.assertAlmostEqual(goal_relevance(self.caps["C4"], self.app["goal"]), 1/3)
        self.assertAlmostEqual(goal_relevance(self.caps["C1"], self.app["goal"]), 1/3)

    def test_vector_dimension(self):
        self.assertGreater(self.encoder.dimension, 0)

if __name__ == "__main__":
    unittest.main()
