"""Run the complete cleaned SCE-128 evaluation pipeline in phase order."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PHASES = [
    ("Phase 01", "Formal dataset validation", "experiments.phase01_dataset_validation"),
    ("Phase 02", "Capability compatibility", "experiments.phase02_capability_compatibility"),
    ("Phase 03", "Baseline vector composition", "experiments.phase03_baseline_composition"),
    ("Phase 04", "Alternative implementations", "experiments.phase04_alternative_implementations"),
    ("Phase 05", "Goal relevance", "experiments.phase05_goal_relevance"),
    ("Phase 06", "Operational attributes", "experiments.phase06_operational_attributes"),
    ("Phase 07", "Leakage-free learned composition", "experiments.phase07_leakage_free_composition"),
    ("Phase 08", "Final integrated evaluation", "experiments.phase08_final_evaluation"),
]


def run(module: str) -> float:
    start = time.perf_counter()
    subprocess.run([sys.executable, "-m", module], cwd=ROOT, check=True)
    return time.perf_counter() - start


def main() -> None:
    print("=" * 78)
    print("SCE-128 v2.1 — COMPLETE EVALUATION PIPELINE")
    print("=" * 78)
    print(f"Project root: {ROOT}")
    print(f"Python      : {sys.executable}")
    print()

    timings = []
    for phase, label, module in PHASES:
        print("-" * 78)
        print(f"START {phase}: {label}")
        print(f"Module: python -m {module}")
        elapsed = run(module)
        timings.append((phase, label, elapsed))
        print(f"DONE  {phase}: {elapsed:.2f}s")

    print("-" * 78)
    print("REGRESSION TESTS")
    start = time.perf_counter()
    subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, check=True)
    test_elapsed = time.perf_counter() - start

    print("=" * 78)
    print("PIPELINE COMPLETE")
    print("=" * 78)
    print("Phase timings:")
    for phase, label, elapsed in timings:
        print(f"  {phase}: {elapsed:.2f}s — {label}")
    print(f"Tests: completed successfully in {test_elapsed:.2f}s")
    print()
    print("Primary final report:")
    print(f"  {ROOT / 'results' / 'final_v2_1' / 'phase08_final_evaluation.md'}")
    print("Primary final JSON:")
    print(f"  {ROOT / 'results' / 'final_v2_1' / 'phase08_final_evaluation.json'}")
    print()
    print("Next artifact: technical report")


if __name__ == "__main__":
    main()
