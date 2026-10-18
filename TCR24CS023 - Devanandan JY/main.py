import os
from src.experiments import run_experiments

if __name__ == "__main__":
    benchmark_path = os.path.join("data", "web_deployment_benchmark.json")
    print(f"Loading Benchmark Data: {benchmark_path}\n")
    run_experiments(benchmark_path)