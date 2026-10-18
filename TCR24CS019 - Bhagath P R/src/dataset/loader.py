from __future__ import annotations
import json
import os
from typing import Dict, List, Optional
from src.models.problem import ApplicationProblem
from src.models.capability import Capability
from src.dataset.generator import (
    create_ecommerce_benchmark,
    create_alternative_implementations_benchmark,
    create_cloud_devops_benchmark,
    create_fintech_kyc_benchmark,
    save_benchmarks_to_disk
)


class BenchmarkLoader:
    """Loads and provides access to benchmark application domains."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        if not os.path.exists(os.path.join(self.data_dir, "ecommerce_benchmark.json")):
            save_benchmarks_to_disk(self.data_dir)

    def load_ecommerce_benchmark(self) -> ApplicationProblem:
        path = os.path.join(self.data_dir, "ecommerce_benchmark.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            return ApplicationProblem.from_dict(data)
        return create_ecommerce_benchmark()

    def load_alternative_implementations(self) -> List[Capability]:
        path = os.path.join(self.data_dir, "alternative_implementations.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            return [Capability.from_dict(c) for c in data]
        return create_alternative_implementations_benchmark()

    def load_cloud_devops_benchmark(self) -> ApplicationProblem:
        path = os.path.join(self.data_dir, "cloud_devops_benchmark.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            return ApplicationProblem.from_dict(data)
        return create_cloud_devops_benchmark()

    def load_fintech_kyc_benchmark(self) -> ApplicationProblem:
        path = os.path.join(self.data_dir, "fintech_kyc_benchmark.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            return ApplicationProblem.from_dict(data)
        return create_fintech_kyc_benchmark()
