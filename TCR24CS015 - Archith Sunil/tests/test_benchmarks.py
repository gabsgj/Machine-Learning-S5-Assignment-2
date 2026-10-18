import unittest
from src.dataset.loader import BenchmarkLoader


class TestBenchmarks(unittest.TestCase):

    def setUp(self):
        self.loader = BenchmarkLoader()

    def test_benchmark_loading(self):
        # 1. E-Commerce
        ecom = self.loader.load_ecommerce_benchmark()
        self.assertEqual(ecom.name, "ECommerce_OrderFulfillment")
        self.assertGreaterEqual(len(ecom.state_variables), 10)
        self.assertGreaterEqual(len(ecom.capabilities), 5)
        self.assertTrue(ecom.initial_state.get("Cart.exists"))
        self.assertEqual(len(ecom.goal.conditions), 3)

        # 2. Alternatives
        alts = self.loader.load_alternative_implementations()
        self.assertGreaterEqual(len(alts), 4)
        types = {c.type.value for c in alts}
        self.assertIn("API", types)
        self.assertIn("DATABASE", types)
        self.assertIn("GUI", types)

        # 3. Cloud DevOps
        devops = self.loader.load_cloud_devops_benchmark()
        self.assertEqual(devops.name, "CloudInfrastructure_Deployment")
        self.assertGreaterEqual(len(devops.capabilities), 5)

        # 4. FinTech KYC
        fintech = self.loader.load_fintech_kyc_benchmark()
        self.assertEqual(fintech.name, "Fintech_KYC_Settlement")
        self.assertGreaterEqual(len(fintech.capabilities), 4)


if __name__ == "__main__":
    unittest.main()
