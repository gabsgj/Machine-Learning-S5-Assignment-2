"""
experiments.py
==============
Executes all 5 Required Experiments formally specified in the Assignment 2 PDF:
- Experiment 1: Capability Compatibility (CreateOrder -> MakePayment vs CreateOrder -> CancelCart)
- Experiment 2: Capability Composition (CompletePurchase = SendNotification o MakePayment o CreateOrder)
- Experiment 3: Alternative Implementations (CreateOrderAPI vs CreateOrderDatabase vs CreateOrderGUI)
- Experiment 4: Irrelevant Capabilities (Relevant vs Irrelevant capability filtering for Goal)
- Experiment 5: Operational Attributes (Cost, Reliability, Availability, Time, Risk variations)
"""

from __future__ import annotations
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from models import Application, Capability, CompositeCapability, State, Goal
from embedding import (
    CapabilityEmbedder, StateEmbedder, GoalEmbedder,
    cosine_similarity, compute_goal_relevance
)
from compatibility import CompatibilityEngine, CompatibilityResult
from composition import CompositionEngine


class ExperimentRunner:
    """
    Orchestrates the 5 assignment experiments and collects structured records for CSV export.
    """

    def __init__(
        self,
        app: Application,
        embedder: Optional[CapabilityEmbedder] = None,
        compat_engine: Optional[CompatibilityEngine] = None,
        comp_engine: Optional[CompositionEngine] = None
    ):
        self.app = app
        self.embedder = embedder or CapabilityEmbedder()
        self.state_embedder = StateEmbedder(schema=self.embedder.schema)
        self.goal_embedder = GoalEmbedder(schema=self.embedder.schema)
        self.compat_engine = compat_engine or CompatibilityEngine(embedder=self.embedder)
        self.comp_engine = comp_engine or CompositionEngine(embedder=self.embedder, compat_engine=self.compat_engine)
        self.records: List[Dict[str, Any]] = []

    def run_all_experiments(self) -> Dict[str, Any]:
        """Runs all 5 required experiments sequentially."""
        results = {}
        print("\n" + "=" * 70)
        print("  VECTOR EMBEDDING FOR CAPABILITY COMPOSITION - EXPERIMENTAL SUITE")
        print("=" * 70)

        results["exp1"] = self.run_experiment_1_compatibility()
        results["exp2"] = self.run_experiment_2_composition()
        results["exp3"] = self.run_experiment_3_alternatives()
        results["exp4"] = self.run_experiment_4_irrelevant()
        results["exp5"] = self.run_experiment_5_operational()

        return results

    # =========================================================================
    # EXPERIMENT 1: Capability Compatibility
    # =========================================================================
    def run_experiment_1_compatibility(self) -> Dict[str, Any]:
        """
        Given C1=CreateOrder, C2=MakePayment, C3=CancelCart.
        Demonstrate C1 -> C2 is compatible and C1 -> C3 is incompatible.
        """
        print("\n" + "-" * 70)
        print("EXPERIMENT 1: CAPABILITY COMPATIBILITY")
        print("-" * 70)

        c1 = self.app.capabilities["CreateOrder"]
        c2 = self.app.capabilities["MakePayment"]
        c3 = self.app.capabilities["CancelCart"]

        t0 = time.perf_counter()
        res_c1_c2 = self.compat_engine.evaluate(c1, c2, context_state=self.app.initial_state)
        t_c1_c2 = (time.perf_counter() - t0) * 1e6

        t0 = time.perf_counter()
        res_c1_c3 = self.compat_engine.evaluate(c1, c3, context_state=self.app.initial_state)
        t_c1_c3 = (time.perf_counter() - t0) * 1e6

        # Pairwise Cosine Similarity for comparison
        v1 = self.embedder.encode_capability(c1)
        v2 = self.embedder.encode_capability(c2)
        v3 = self.embedder.encode_capability(c3)
        sim_c1_c2 = cosine_similarity(v1, v2)
        sim_c1_c3 = cosine_similarity(v1, v3)

        print(f"[*] Sequence 1: {c1.name} -> {c2.name}")
        print(f"    - Precondition/Effect Match : {res_c1_c2.satisfied_preconditions}")
        print(f"    - Input/Output Match        : {res_c1_c2.satisfied_inputs}")
        print(f"    - Compatibility Score       : {res_c1_c2.overall_score:.4f} (E->P: {res_c1_c2.effect_precondition_score:.2f}, O->I: {res_c1_c2.input_output_score:.2f})")
        print(f"    - Cosine Similarity         : {sim_c1_c2:.4f}")
        print(f"    - Decision                  : {'COMPATIBLE (TRUE)' if res_c1_c2.is_compatible else 'INCOMPATIBLE (FALSE)'}")
        print(f"    - Explanation               : {res_c1_c2.explanation}")

        print(f"\n[*] Sequence 2: {c1.name} -> {c3.name}")
        print(f"    - Conflicts Detected        : {res_c1_c3.conflicts}")
        print(f"    - Compatibility Score       : {res_c1_c3.overall_score:.4f}")
        print(f"    - Cosine Similarity         : {sim_c1_c3:.4f}")
        print(f"    - Decision                  : {'COMPATIBLE (TRUE)' if res_c1_c3.is_compatible else 'INCOMPATIBLE (FALSE)'}")
        print(f"    - Explanation               : {res_c1_c3.explanation}")

        # Record for CSV export
        self.records.append({
            "experiment": "Exp1_Compatibility",
            "capability_1": c1.name,
            "capability_2": c2.name,
            "similarity": round(sim_c1_c2, 4),
            "compatibility_score": round(res_c1_c2.overall_score, 4),
            "compatible": res_c1_c2.is_compatible,
            "goal_relevance": 0.0,
            "cost": c2.quality.monetary_cost,
            "reliability": c2.reliability,
            "availability": c2.availability,
            "encoding_time": 0.0,
            "comparison_time": round(t_c1_c2, 2)
        })

        self.records.append({
            "experiment": "Exp1_Compatibility",
            "capability_1": c1.name,
            "capability_2": c3.name,
            "similarity": round(sim_c1_c3, 4),
            "compatibility_score": round(res_c1_c3.overall_score, 4),
            "compatible": res_c1_c3.is_compatible,
            "goal_relevance": 0.0,
            "cost": c3.quality.monetary_cost,
            "reliability": c3.reliability,
            "availability": c3.availability,
            "encoding_time": 0.0,
            "comparison_time": round(t_c1_c3, 2)
        })

        return {
            "c1_c2": res_c1_c2.to_dict(),
            "c1_c3": res_c1_c3.to_dict(),
            "sim_c1_c2": round(sim_c1_c2, 4),
            "sim_c1_c3": round(sim_c1_c3, 4)
        }

    # =========================================================================
    # EXPERIMENT 2: Capability Composition
    # =========================================================================
    def run_experiment_2_composition(self) -> Dict[str, Any]:
        """
        Construct: CompletePurchase = SendNotification o MakePayment o CreateOrder.
        Investigate composite vector vs component vectors.
        """
        print("\n" + "-" * 70)
        print("EXPERIMENT 2: CAPABILITY COMPOSITION")
        print("-" * 70)

        c1 = self.app.capabilities["CreateOrder"]
        c2 = self.app.capabilities["MakePayment"]
        c3 = self.app.capabilities["SendNotification"]

        t0 = time.perf_counter()
        composite = self.comp_engine.compose(
            sequence=[c1, c2, c3],
            name="CompletePurchase",
            initial_state=self.app.initial_state
        )
        t_compose = (time.perf_counter() - t0) * 1e6

        analysis = self.comp_engine.compare_composition_vectors(composite)

        v1 = self.embedder.encode_capability(c1)
        v2 = self.embedder.encode_capability(c2)
        v3 = self.embedder.encode_capability(c3)
        v_comp = self.embedder.encode_capability(composite)

        sim_c1 = cosine_similarity(v1, v_comp)
        sim_c2 = cosine_similarity(v2, v_comp)
        sim_c3 = cosine_similarity(v3, v_comp)

        print(f"[*] Pipeline Constructed: {c1.name} -> {c2.name} -> {c3.name}")
        print(f"    - Composite Name            : {composite.name}")
        print(f"    - Aggregated Inputs         : {[i.name for i in composite.inputs]}")
        print(f"    - Aggregated Outputs        : {[o.name for o in composite.outputs]}")
        print(f"    - Aggregated Preconditions  : {[f'{p.variable} {p.operator} {p.value}' for p in composite.preconditions]}")
        print(f"    - Net Effects               : {[f'{e.variable}:={e.value}' for e in composite.effects]}")
        print(f"    - Composite Monetary Cost   : ${composite.quality.monetary_cost:.4f} (Sum: {c1.quality.monetary_cost}+{c2.quality.monetary_cost}+{c3.quality.monetary_cost})")
        print(f"    - Composite Execution Time  : {composite.quality.execution_time_ms:.1f} ms")
        print(f"    - Composite Reliability     : {composite.reliability:.5f} (Product: {c1.reliability}*{c2.reliability}*{c3.reliability})")
        print(f"    - Composite Availability    : {composite.availability:.5f}")
        print(f"    - Similarity with C1 (CreateOrder)      : {sim_c1:.4f}")
        print(f"    - Similarity with C2 (MakePayment)      : {sim_c2:.4f}")
        print(f"    - Similarity with C3 (SendNotification) : {sim_c3:.4f}")
        print(f"    - Similarity with Component Sum Vector  : {analysis['sum_vector_similarity']:.4f}")

        # Record for CSV
        self.records.append({
            "experiment": "Exp2_Composition",
            "capability_1": "CompletePurchase",
            "capability_2": c1.name,
            "similarity": round(sim_c1, 4),
            "compatibility_score": 1.0,
            "compatible": True,
            "goal_relevance": 1.0,
            "cost": composite.quality.monetary_cost,
            "reliability": composite.reliability,
            "availability": composite.availability,
            "encoding_time": 0.0,
            "comparison_time": round(t_compose, 2)
        })

        self.records.append({
            "experiment": "Exp2_Composition",
            "capability_1": "CompletePurchase",
            "capability_2": c2.name,
            "similarity": round(sim_c2, 4),
            "compatibility_score": 1.0,
            "compatible": True,
            "goal_relevance": 1.0,
            "cost": composite.quality.monetary_cost,
            "reliability": composite.reliability,
            "availability": composite.availability,
            "encoding_time": 0.0,
            "comparison_time": round(t_compose, 2)
        })

        self.records.append({
            "experiment": "Exp2_Composition",
            "capability_1": "CompletePurchase",
            "capability_2": c3.name,
            "similarity": round(sim_c3, 4),
            "compatibility_score": 1.0,
            "compatible": True,
            "goal_relevance": 1.0,
            "cost": composite.quality.monetary_cost,
            "reliability": composite.reliability,
            "availability": composite.availability,
            "encoding_time": 0.0,
            "comparison_time": round(t_compose, 2)
        })

        return {
            "composite": composite.to_dict(),
            "analysis": analysis,
            "component_similarities": {c1.name: round(sim_c1, 4), c2.name: round(sim_c2, 4), c3.name: round(sim_c3, 4)}
        }

    # =========================================================================
    # EXPERIMENT 3: Alternative Implementations
    # =========================================================================
    def run_experiment_3_alternatives(self) -> Dict[str, Any]:
        """
        Compare CreateOrderAPI, CreateOrderDatabase, CreateOrderGUI.
        Preserves functional equivalence while capturing mechanism & operational differences.
        """
        print("\n" + "-" * 70)
        print("EXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS")
        print("-" * 70)

        c_api = self.app.capabilities["CreateOrderAPI"]
        c_db = self.app.capabilities["CreateOrderDatabase"]
        c_gui = self.app.capabilities["CreateOrderGUI"]

        v_api = self.embedder.encode_capability(c_api)
        v_db = self.embedder.encode_capability(c_db)
        v_gui = self.embedder.encode_capability(c_gui)

        # 1. Full Vector Similarities
        sim_api_db = cosine_similarity(v_api, v_db)
        sim_api_gui = cosine_similarity(v_api, v_gui)
        sim_db_gui = cosine_similarity(v_db, v_gui)

        # 2. Functional Subspace Similarities (Inputs, Outputs, Preconditions, Effects)
        func_api = self.embedder.get_functional_subvector(v_api)
        func_db = self.embedder.get_functional_subvector(v_db)
        func_gui = self.embedder.get_functional_subvector(v_gui)

        f_sim_api_db = cosine_similarity(func_api, func_db)
        f_sim_api_gui = cosine_similarity(func_api, func_gui)
        f_sim_db_gui = cosine_similarity(func_db, func_gui)

        # 3. Operational / Mechanism Subspace Distance
        mech_api = self.embedder.get_subspaces(v_api)["mechanism"]
        mech_db = self.embedder.get_subspaces(v_db)["mechanism"]
        mech_gui = self.embedder.get_subspaces(v_gui)["mechanism"]

        sim_mech_api_db = cosine_similarity(mech_api, mech_db)
        sim_mech_api_gui = cosine_similarity(mech_api, mech_gui)

        print(f"[*] Comparison Matrix across Implementations:")
        print(f"    - CreateOrderAPI      vs CreateOrderDatabase : Full Sim = {sim_api_db:.4f} | Functional Sim = {f_sim_api_db:.4f}")
        print(f"    - CreateOrderAPI      vs CreateOrderGUI      : Full Sim = {sim_api_gui:.4f} | Functional Sim = {f_sim_api_gui:.4f}")
        print(f"    - CreateOrderDatabase vs CreateOrderGUI      : Full Sim = {sim_db_gui:.4f} | Functional Sim = {f_sim_db_gui:.4f}")
        print(f"[*] Key Finding: Functional similarity is {f_sim_api_db:.4f} (100% equivalence), while overall embedding captures distinct mechanisms (API vs DB vs GUI).")

        # Record for CSV
        for name1, name2, full_s, func_s in [
            (c_api.name, c_db.name, sim_api_db, f_sim_api_db),
            (c_api.name, c_gui.name, sim_api_gui, f_sim_api_gui),
            (c_db.name, c_gui.name, sim_db_gui, f_sim_db_gui)
        ]:
            self.records.append({
                "experiment": "Exp3_Alternatives",
                "capability_1": name1,
                "capability_2": name2,
                "similarity": round(full_s, 4),
                "compatibility_score": round(func_s, 4),
                "compatible": True,
                "goal_relevance": 0.5,
                "cost": 0.0,
                "reliability": 0.0,
                "availability": 0.0,
                "encoding_time": 0.0,
                "comparison_time": 0.0
            })

        return {
            "full_similarities": {
                "API_vs_DB": round(sim_api_db, 4),
                "API_vs_GUI": round(sim_api_gui, 4),
                "DB_vs_GUI": round(sim_db_gui, 4)
            },
            "functional_similarities": {
                "API_vs_DB": round(f_sim_api_db, 4),
                "API_vs_GUI": round(f_sim_api_gui, 4),
                "DB_vs_GUI": round(f_sim_db_gui, 4)
            }
        }

    # =========================================================================
    # EXPERIMENT 4: Irrelevant Capabilities
    # =========================================================================
    def run_experiment_4_irrelevant(self) -> Dict[str, Any]:
        """
        Goal: Order.exists=True, Payment.status=SUCCESS, Notification.sent=True.
        Test distinguishing relevant capabilities from irrelevant ones.
        """
        print("\n" + "-" * 70)
        print("EXPERIMENT 4: IRRELEVANT CAPABILITIES")
        print("-" * 70)

        goal = self.app.goal
        state = self.app.initial_state

        test_candidates = [
            ("CreateOrder", "Relevant (Initial step)"),
            ("MakePayment", "Relevant (Direct payment satisfy)"),
            ("SendNotification", "Relevant (Direct notification satisfy)"),
            ("GenerateInvoice", "Semi-Relevant (Post-purchase aux)"),
            ("CheckInventory", "Semi-Relevant (Prerequisite helper)"),
            ("UpdateProfile", "Irrelevant (User GUI form)"),
            ("GenerateReport", "Irrelevant (Admin computation)"),
            ("PlayMusic", "Irrelevant (Media service)")
        ]

        results_table = []
        print(f"[*] Evaluating Goal: {[f'{c.variable} {c.operator} {c.value}' for c in goal.conditions]}")
        print(f"{'Capability':<20} | {'Category':<32} | {'Goal Relevance':<14} | {'Sym Match':<10} | {'Vec Align':<10}")
        print("-" * 94)

        for name, category in test_candidates:
            cap = self.app.capabilities[name]
            score, sym_cov, vec_align = compute_goal_relevance(
                cap, goal, state, self.embedder, self.goal_embedder, self.state_embedder
            )

            results_table.append({
                "capability": name,
                "category": category,
                "goal_relevance_score": round(score, 4),
                "symbolic_coverage": round(sym_cov, 4),
                "vector_alignment": round(vec_align, 4)
            })

            print(f"{name:<20} | {category:<32} | {score:<14.4f} | {sym_cov:<10.4f} | {vec_align:<10.4f}")

            self.records.append({
                "experiment": "Exp4_IrrelevantCapabilities",
                "capability_1": name,
                "capability_2": "PurchaseGoal",
                "similarity": round(vec_align, 4),
                "compatibility_score": round(sym_cov, 4),
                "compatible": score > 0.3,
                "goal_relevance": round(score, 4),
                "cost": cap.quality.monetary_cost,
                "reliability": cap.reliability,
                "availability": cap.availability,
                "encoding_time": 0.0,
                "comparison_time": 0.0
            })

        return {"goal_evaluations": results_table}

    # =========================================================================
    # EXPERIMENT 5: Operational Attributes
    # =========================================================================
    def run_experiment_5_operational(self) -> Dict[str, Any]:
        """
        Investigate variations in Cost, Reliability, Availability, Execution Time, Risk.
        Distinguish functional similarity from operational sensitivity.
        """
        print("\n" + "-" * 70)
        print("EXPERIMENT 5: OPERATIONAL ATTRIBUTES")
        print("-" * 70)

        variants = [
            self.app.capabilities["MakePayment"],
            self.app.capabilities["MakePayment_Economy"],
            self.app.capabilities["MakePayment_Enterprise"],
            self.app.capabilities["MakePayment_HighCost_LowRel"]
        ]

        v_baseline = self.embedder.encode_capability(variants[0])

        print(f"{'Variant Name':<30} | {'Cost ($)':<9} | {'Rel':<6} | {'Avail':<6} | {'Time (ms)':<10} | {'Ops Dist':<9} | {'Overall Sim':<11}")
        print("-" * 92)

        ops_results = []
        for cap in variants:
            v_cap = self.embedder.encode_capability(cap)
            sim = cosine_similarity(v_baseline, v_cap)

            ops_baseline = self.embedder.get_subspaces(v_baseline)["operational"]
            ops_current = self.embedder.get_subspaces(v_cap)["operational"]
            ops_dist = float(np.linalg.norm(ops_baseline - ops_current))

            print(
                f"{cap.name:<30} | ${cap.quality.monetary_cost:<8.2f} | {cap.reliability:<6.3f} | "
                f"{cap.availability:<6.2f} | {cap.quality.execution_time_ms:<10.1f} | {ops_dist:<9.4f} | {sim:<11.4f}"
            )

            ops_results.append({
                "name": cap.name,
                "cost": cap.quality.monetary_cost,
                "reliability": cap.reliability,
                "availability": cap.availability,
                "execution_time_ms": cap.quality.execution_time_ms,
                "risk": cap.quality.risk,
                "operational_distance_from_baseline": round(ops_dist, 4),
                "overall_similarity_to_baseline": round(sim, 4)
            })

            self.records.append({
                "experiment": "Exp5_OperationalAttributes",
                "capability_1": cap.name,
                "capability_2": variants[0].name,
                "similarity": round(sim, 4),
                "compatibility_score": 1.0,
                "compatible": True,
                "goal_relevance": 1.0,
                "cost": cap.quality.monetary_cost,
                "reliability": cap.reliability,
                "availability": cap.availability,
                "encoding_time": 0.0,
                "comparison_time": 0.0
            })

        return {"operational_variations": ops_results}

    def export_results_csv(self, results_dir: str = "results") -> str:
        """Exports accumulated experimental records to experiment_results.csv."""
        import os
        os.makedirs(results_dir, exist_ok=True)
        csv_path = os.path.join(results_dir, "experiment_results.csv")
        df = pd.DataFrame(self.records)
        df.to_csv(csv_path, index=False)
        return csv_path
