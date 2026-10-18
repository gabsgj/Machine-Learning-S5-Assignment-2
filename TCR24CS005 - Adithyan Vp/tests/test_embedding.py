import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.capability_embedding import CapabilityEmbedder, capability_from_dict


class TestEmbedding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(ROOT / "data" / "dataset.json", encoding="utf-8") as f:
            data = json.load(f)
        cls.emb = CapabilityEmbedder()
        cls.caps = {x["name"]: capability_from_dict(x) for x in data["capabilities"]}

    def test_dimensions(self):
        v = self.emb.encode_capability(self.caps["CreateOrder"])
        self.assertEqual(v.shape[0], self.emb.dim)

    def test_compatibility(self):
        good, _ = self.emb.compatibility(self.caps["CreateOrder"], self.caps["MakePayment"])
        bad, _ = self.emb.compatibility(self.caps["CreateOrder"], self.caps["CancelCart"])
        self.assertGreater(good, bad)

    def test_alternative_implementations(self):
        a = self.emb.encode_capability(self.caps["CreateOrder"])
        b = self.emb.encode_capability(self.caps["CreateOrderDB"])
        c = self.emb.encode_capability(self.caps["ViewProfile"])
        self.assertGreater(self.emb.similarity(a,b), self.emb.similarity(a,c))

    def test_composition(self):
        result = self.emb.compose([
            self.caps["CreateOrder"],
            self.caps["MakePayment"],
            self.caps["SendNotification"]
        ])
        self.assertTrue(result["valid"])

    def test_goal_relevance(self):
        goal = {"Order.exists": True, "Payment.status": "SUCCESS", "Notification.sent": True}
        self.assertGreater(
            self.emb.goal_relevance(self.caps["MakePayment"], goal),
            self.emb.goal_relevance(self.caps["ViewProfile"], goal)
        )


if __name__ == "__main__":
    unittest.main()
