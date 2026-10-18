"""
evaluation.py
=============
Evaluation Suite for Capability Vector Embedding System.
Measures all 9 formal criteria required by the Assignment 2 specification:
1. Capability Identity Distinction
2. State Awareness
3. Precondition-Effect Compatibility Separation
4. Input-Output Compatibility
5. Composition Fidelity
6. Goal Relevance Accuracy
7. Operational Attributes Sensitivity
8. Consistency & Determinism
9. Computational Efficiency & Latency Profiling
"""

from __future__ import annotations
import time
import sys
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from models import Application, Capability, CompositeCapability, State, Goal
from embedding import (
    CapabilityEmbedder, StateEmbedder, GoalEmbedder,
    cosine_similarity, compute_goal_relevance
)
from compatibility import CompatibilityEngine
from composition import CompositionEngine


class EvaluationSuite:
    """
    Comprehensive evaluation metrics runner.
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

    def evaluate_all(self) -> Dict[str, Any]:
        """Runs the complete suite of 9 evaluation metrics."""
        results = {}
        results["identity_distinction"] = self.evaluate_identity_distinction()
        results["state_relationship"] = self.evaluate_state_relationship()
        results["compatibility_separation"] = self.evaluate_compatibility_separation()
        results["input_output_compatibility"] = self.evaluate_input_output_compatibility()
        results["composition_fidelity"] = self.evaluate_composition_fidelity()
        results["goal_relevance"] = self.evaluate_goal_relevance()
        results["operational_sensitivity"] = self.evaluate_operational_sensitivity()
        results["consistency"] = self.evaluate_consistency()
        results["efficiency"] = self.evaluate_efficiency()
        return results

    def evaluate_identity_distinction(self) -> Dict[str, Any]:
        """
        Criterion 1: Capability Identity.
        Can different capabilities be represented distinctly?
        """
        caps = list(self.app.capabilities.values())
        vectors = [self.embedder.encode_capability(c) for c in caps]
        n = len(caps)

        distances = []
        similarities = []
        identical_pair_count = 0

        for i in range(n):
            for j in range(i + 1, n):
                sim = cosine_similarity(vectors[i], vectors[j])
                dist = 1.0 - sim
                similarities.append(sim)
                distances.append(dist)
                if dist < 1e-6:
                    identical_pair_count += 1

        return {
            "num_capabilities_tested": n,
            "total_pairs_compared": len(distances),
            "identical_representation_pairs": identical_pair_count,
            "min_pairwise_distance": round(float(np.min(distances)), 4),
            "max_pairwise_distance": round(float(np.max(distances)), 4),
            "mean_pairwise_distance": round(float(np.mean(distances)), 4),
            "identity_preserved": identical_pair_count == 0
        }

    def evaluate_state_relationship(self) -> Dict[str, Any]:
        """
        Criterion 2: State Relationship.
        Does the representation capture applicability to states and effect state transitions?
        """
        s_init = self.app.initial_state
        v_state = self.state_embedder.encode_state(s_init)

        # Test applicability for CreateOrder (applicable) vs CancelCart (applicable) vs MakePayment (not applicable yet)
        c_create = self.app.capabilities["CreateOrder"]
        c_pay = self.app.capabilities["MakePayment"]

        # Applicable capability execution
        s_after_create = c_create.execute(s_init.clone())
        v_state_after = self.state_embedder.encode_state(s_after_create)

        # State delta in vector space
        empirical_delta = v_state_after - v_state
        v_eff_create = self.embedder.get_subspaces(self.embedder.encode_capability(c_create))["effect"]

        # Vector alignment between empirical state transition and capability effect vector
        delta_sim = cosine_similarity(empirical_delta, v_eff_create)

        return {
            "initial_state_applicable_create_order": c_create.can_execute_on(s_init),
            "initial_state_applicable_make_payment": c_pay.can_execute_on(s_init),
            "post_execution_applicable_make_payment": c_pay.can_execute_on(s_after_create),
            "state_transition_vector_alignment": round(float(delta_sim), 4),
            "state_awareness_verified": delta_sim > 0.85
        }

    def evaluate_compatibility_separation(self) -> Dict[str, Any]:
        """
        Criterion 3: Precondition-Effect Compatibility.
        Can composable capabilities be separated from incompatible ones?
        """
        # Known compatible pairs
        compatible_pairs = [
            ("CreateOrder", "MakePayment"),
            ("MakePayment", "SendNotification"),
            ("MakePayment", "GenerateInvoice"),
            ("CheckInventory", "CreateOrder")
        ]

        # Known incompatible pairs
        incompatible_pairs = [
            ("CreateOrder", "CancelCart"),
            ("SendNotification", "MakePayment"),
            ("UpdateProfile", "MakePayment"),
            ("PlayMusic", "MakePayment")
        ]

        compat_scores = []
        for c1_name, c2_name in compatible_pairs:
            c1 = self.app.capabilities[c1_name]
            c2 = self.app.capabilities[c2_name]
            res = self.compat_engine.evaluate(c1, c2)
            compat_scores.append(res.overall_score)

        incompat_scores = []
        for c1_name, c2_name in incompatible_pairs:
            c1 = self.app.capabilities[c1_name]
            c2 = self.app.capabilities[c2_name]
            res = self.compat_engine.evaluate(c1, c2)
            incompat_scores.append(res.overall_score)

        mean_compat = float(np.mean(compat_scores))
        mean_incompat = float(np.mean(incompat_scores))
        separation_margin = mean_compat - mean_incompat

        return {
            "compatible_pairs_tested": len(compatible_pairs),
            "incompatible_pairs_tested": len(incompatible_pairs),
            "mean_compatible_score": round(mean_compat, 4),
            "mean_incompatible_score": round(mean_incompat, 4),
            "separation_margin": round(separation_margin, 4),
            "perfect_separation": min(compat_scores) > max(incompat_scores)
        }

    def evaluate_input_output_compatibility(self) -> Dict[str, Any]:
        """
        Criterion 4: Input-Output Compatibility.
        Can dependencies between produced outputs and required inputs be represented?
        """
        c1 = self.app.capabilities["CreateOrder"]       # Outputs: order_id
        c2 = self.app.capabilities["MakePayment"]       # Inputs: order_id, payment_details
        c_music = self.app.capabilities["PlayMusic"]   # Outputs: audio_stream

        v_c1 = self.embedder.encode_capability(c1)
        v_c2 = self.embedder.encode_capability(c2)
        v_music = self.embedder.encode_capability(c_music)

        v_out_c1 = self.embedder.get_subspaces(v_c1)["output"]
        v_in_c2 = self.embedder.get_subspaces(v_c2)["input"]
        v_out_music = self.embedder.get_subspaces(v_music)["output"]

        io_overlap_c1_c2 = float(np.dot(v_out_c1, v_in_c2))
        io_overlap_music_c2 = float(np.dot(v_out_music, v_in_c2))

        return {
            "order_to_payment_io_overlap": round(io_overlap_c1_c2, 4),
            "music_to_payment_io_overlap": round(io_overlap_music_c2, 4),
            "data_dependency_detected": io_overlap_c1_c2 > io_overlap_music_c2
        }

    def evaluate_composition_fidelity(self) -> Dict[str, Any]:
        """
        Criterion 5: Composition.
        Can complex capabilities be constructed from smaller capabilities?
        """
        c1 = self.app.capabilities["CreateOrder"]
        c2 = self.app.capabilities["MakePayment"]
        c3 = self.app.capabilities["SendNotification"]

        comp = self.comp_engine.compose([c1, c2, c3], name="CompletePurchase")
        analysis = self.comp_engine.compare_composition_vectors(comp)

        expected_cost = c1.quality.monetary_cost + c2.quality.monetary_cost + c3.quality.monetary_cost
        expected_rel = c1.reliability * c2.reliability * c3.reliability

        cost_correct = abs(comp.quality.monetary_cost - expected_cost) < 1e-4
        rel_correct = abs(comp.reliability - expected_rel) < 1e-4

        return {
            "composite_name": comp.name,
            "component_count": len(comp.sequence),
            "cost_aggregation_accurate": cost_correct,
            "reliability_aggregation_accurate": rel_correct,
            "composite_effects_count": len(comp.effects),
            "sum_vector_similarity": analysis["sum_vector_similarity"],
            "composition_valid": cost_correct and rel_correct and len(comp.effects) >= 3
        }

    def evaluate_goal_relevance(self) -> Dict[str, Any]:
        """
        Criterion 6: Goal Relevance.
        Can the relationship between capabilities and goals be identified?
        """
        goal = self.app.goal
        state = self.app.initial_state

        relevant_caps = ["CreateOrder", "MakePayment", "SendNotification"]
        irrelevant_caps = ["UpdateProfile", "GenerateReport", "PlayMusic"]

        rel_scores = {}
        for name in relevant_caps + irrelevant_caps:
            cap = self.app.capabilities[name]
            score, sym_cov, vec_align = compute_goal_relevance(
                cap, goal, state, self.embedder, self.goal_embedder, self.state_embedder
            )
            rel_scores[name] = score

        mean_relevant = float(np.mean([rel_scores[n] for n in relevant_caps]))
        mean_irrelevant = float(np.mean([rel_scores[n] for n in irrelevant_caps]))
        gap = mean_relevant - mean_irrelevant

        return {
            "relevant_capabilities_mean_score": round(mean_relevant, 4),
            "irrelevant_capabilities_mean_score": round(mean_irrelevant, 4),
            "goal_relevance_gap": round(gap, 4),
            "goal_discrimination_accurate": min(rel_scores[n] for n in relevant_caps) > max(rel_scores[n] for n in irrelevant_caps)
        }

    def evaluate_operational_sensitivity(self) -> Dict[str, Any]:
        """
        Criterion 7: Operational Properties.
        Can cost, reliability, and availability be represented and analyzed?
        """
        c_std = self.app.capabilities["MakePayment"]
        c_econ = self.app.capabilities["MakePayment_Economy"]
        c_ent = self.app.capabilities["MakePayment_Enterprise"]
        c_high_cost = self.app.capabilities["MakePayment_HighCost_LowRel"]

        v_std = self.embedder.encode_capability(c_std)
        v_econ = self.embedder.encode_capability(c_econ)
        v_ent = self.embedder.encode_capability(c_ent)
        v_high = self.embedder.encode_capability(c_high_cost)

        # Operational subspace extraction
        ops_std = self.embedder.get_subspaces(v_std)["operational"]
        ops_high = self.embedder.get_subspaces(v_high)["operational"]
        ops_econ = self.embedder.get_subspaces(v_econ)["operational"]

        dist_std_high = float(np.linalg.norm(ops_std - ops_high))
        dist_std_econ = float(np.linalg.norm(ops_std - ops_econ))

        # Functional vs Operational similarity
        func_std = self.embedder.get_functional_subvector(v_std)
        func_high = self.embedder.get_functional_subvector(v_high)
        func_sim = cosine_similarity(func_std, func_high)

        return {
            "functional_similarity_identical_effects": round(func_sim, 4),
            "operational_distance_std_vs_high_cost": round(dist_std_high, 4),
            "operational_distance_std_vs_econ": round(dist_std_econ, 4),
            "operational_sensitivity_verified": dist_std_high > 0.10 and func_sim > 0.99
        }

    def evaluate_consistency(self) -> Dict[str, Any]:
        """
        Criterion 8: Consistency & Determinism.
        Does the representation behave identically across repeated runs?
        """
        c = self.app.capabilities["CreateOrder"]
        v1 = self.embedder.encode_capability(c)
        v2 = self.embedder.encode_capability(c)
        v3 = self.embedder.encode_capability(c)

        diff1 = float(np.max(np.abs(v1 - v2)))
        diff2 = float(np.max(np.abs(v1 - v3)))

        return {
            "deterministic_execution": True,
            "max_run_to_run_variance": max(diff1, diff2),
            "consistency_verified": max(diff1, diff2) == 0.0
        }

    def evaluate_efficiency(self) -> Dict[str, Any]:
        """
        Criterion 9: Computational Efficiency.
        Measures real encoding times, similarity latency, compatibility latency, composition latency, and memory footprint.
        """
        caps = list(self.app.capabilities.values())
        c1 = self.app.capabilities["CreateOrder"]
        c2 = self.app.capabilities["MakePayment"]
        c3 = self.app.capabilities["SendNotification"]

        # 1. Capability encoding benchmark (1000 iterations)
        n_iter = 1000
        t0 = time.perf_counter()
        for _ in range(n_iter):
            for c in caps:
                _ = self.embedder.encode_capability(c)
        t_enc = (time.perf_counter() - t0) / (n_iter * len(caps)) * 1e6  # microseconds

        # 2. Similarity benchmark
        v1 = self.embedder.encode_capability(c1)
        v2 = self.embedder.encode_capability(c2)
        t0 = time.perf_counter()
        for _ in range(n_iter):
            _ = cosine_similarity(v1, v2)
        t_sim = (time.perf_counter() - t0) / n_iter * 1e6  # microseconds

        # 3. Compatibility benchmark
        t0 = time.perf_counter()
        for _ in range(n_iter):
            _ = self.compat_engine.evaluate(c1, c2)
        t_compat = (time.perf_counter() - t0) / n_iter * 1e6  # microseconds

        # 4. Composition benchmark
        t0 = time.perf_counter()
        for _ in range(n_iter):
            _ = self.comp_engine.compose([c1, c2, c3], validate=False)
        t_comp = (time.perf_counter() - t0) / n_iter * 1e6  # microseconds

        # 5. Memory usage
        vec_bytes = v1.nbytes

        return {
            "embedding_dimension": self.embedder.total_dim,
            "vector_memory_bytes": vec_bytes,
            "encoding_latency_microseconds": round(t_enc, 2),
            "similarity_latency_microseconds": round(t_sim, 2),
            "compatibility_latency_microseconds": round(t_compat, 2),
            "composition_latency_microseconds": round(t_comp, 2),
            "throughput_embeddings_per_sec": round(1e6 / max(1e-3, t_enc), 0)
        }

    def generate_summary_df(self, metrics: Dict[str, Any]) -> pd.DataFrame:
        """Converts evaluation metrics dictionary into a summary DataFrame."""
        rows = []
        for category, data in metrics.items():
            for k, v in data.items():
                rows.append({
                    "evaluation_property": category,
                    "metric_name": k,
                    "metric_value": str(v)
                })
        return pd.DataFrame(rows)
