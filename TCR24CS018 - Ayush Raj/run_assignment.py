#!/usr/bin/env python3
"""
Assignment 2: Design of a Vector Embedding for Capability Composition
Top-level demonstration script executing Deliverables 1, 2, 3, and 4.
"""

import sys
import os
import unittest

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

from experiments.run_all_experiments import (
    run_experiment_1,
    run_experiment_2,
    run_experiment_3,
    run_experiment_4,
    run_experiment_5,
    validate_cross_domain_consistency,
    generate_figures,
)


def run_tests():
    print("\n" + "="*80)
    print("STEP 1: RUNNING FORMAL PROPERTIES & COMPOSITION ENGINE UNIT TESTS")
    print("="*80)
    loader = unittest.TestLoader()
    suite = loader.discover("tests")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        print("[FAIL] Some unit tests failed!")
        sys.exit(1)
    print("[PASS] All unit tests passed successfully!")


def run_experiments():
    print("\n" + "="*80)
    print("STEP 2: EXECUTING FORMAL EXPERIMENTS 1 THROUGH 5")
    print("="*80)
    res1 = run_experiment_1()
    res2 = run_experiment_2()
    res3 = run_experiment_3()
    res4 = run_experiment_4()
    res5 = run_experiment_5()

    print("\n" + "="*80)
    print("STEP 3: CROSS-DOMAIN VALIDATION (DEVOPS & HEALTHCARE)")
    print("="*80)
    validate_cross_domain_consistency()

    print("\n" + "="*80)
    print("STEP 4: GENERATING PUBLICATION-QUALITY FIGURES")
    print("="*80)
    fig_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
    generate_figures(res1, res2, res3, res4, res5, fig_dir)


def main():
    print("="*80)
    print(" ASSIGNMENT 2: VECTOR EMBEDDING FOR CAPABILITY COMPOSITION ")
    print(" Formal Representations, Compatibility, and Compositional Reasoning ")
    print("="*80)

    run_tests()
    run_experiments()

    print("\n" + "="*80)
    print("SUMMARY OF DELIVERABLES COMPLETED:")
    print("  [x] Deliverable 1: Formal Embedding Design (Mathematical specification)")
    print("  [x] Deliverable 2: Working Implementation (capembed package)")
    print("  [x] Deliverable 3: Experimental Dataset (E-Commerce, DevOps, Healthcare)")
    print("  [x] Deliverable 4: Comprehensive Technical Report (report/TECHNICAL_REPORT.md)")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
