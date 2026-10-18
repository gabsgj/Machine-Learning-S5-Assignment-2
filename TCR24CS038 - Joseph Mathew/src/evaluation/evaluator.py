"""Comprehensive Benchmark Evaluator across all 9 Evaluation Criteria.

Section 8 Evaluation Criteria:
1. Capability representation: Distinctness of capability embeddings.
2. State relationship: Relationship between capability effects and states.
3. Precondition-effect compatibility: Separability of composable vs conflicting capabilities.
4. Input-output compatibility: Data flow dependencies representation.
5. Composition: Multi-step composition accuracy and homomorphism.
6. Goal relevance: Correlation with goal delta reduction.
7. Operational properties: Decoupled multi-attribute preservation.
8. Consistency: Evaluation across multiple problem domains.
9. Efficiency: Compute latency and vector memory footprint.
"""

from __future__ import annotations
import time
import sys
from typing import Dict, Any, List, Tuple
import numpy as np

from src.models.capability import Capability
from src.embedding.schema import EmbeddingSchema
from src.embedding.encoder import CapabilityEncoder
from src.embedding.composition import compose_capabilities, compose_sequence, compose_vectors
from src.embedding.metrics import (
    cosine_similarity, functional_similarity, composability_score, goal_relevance_score
)
from src.data.ecommerce_dataset import build_ecommerce_domain
from src.data.cloud_pipeline_dataset import build_cloud_pipeline_domain


class SystemEvaluator:
    """Evaluates the embedding against the formal criteria in Section 8."""

    def __init__(self):
        self.ecommerce_data = build_ecommerce_domain()
        self.cloud_data = build_cloud_pipeline_domain()

    def evaluate_criterion_1_capability_representation(self) -> Dict[str, Any]:
        """Can different capabilities be represented distinctly?"""
        domain = self.ecommerce_data
        encoder = CapabilityEncoder(domain["schema"])
        caps = domain["capabilities"]
        vectors = [encoder.encode_capability(c) for c in caps]

        # Check pairwise distances
        n = len(caps)
        min_dist = float("inf")
        max_sim = -1.0
        collision_count = 0

        for i in range(n):
            for j in range(i + 1, n):
                d = float(np.linalg.norm(vectors[i] - vectors[j]))
                sim = cosine_similarity(vectors[i], vectors[j])
                if d < 1e-4:
                    collision_count += 1
                min_dist = min(min_dist, d)
                max_sim = max(max_sim, sim)

        return {
            "criterion": "1. Capability Representation",
            "passed": collision_count == 0,
            "total_capabilities": n,
            "min_pairwise_distance": min_dist,
            "max_pairwise_cosine": max_sim,
            "zero_collision_guarantee": collision_count == 0
        }

    def evaluate_criterion_2_state_relationship(self) -> Dict[str, Any]:
        """Does the representation capture the relationship between capabilities and states?"""
        domain = self.ecommerce_data
        encoder = CapabilityEncoder(domain["schema"])
        init_state = domain["initial_state"]
        c1 = domain["named_capabilities"]["CreateOrder"]

        v_s0 = encoder.encode_state(init_state)
        # Apply C1 symbolically to state
        s1 = c1.apply(init_state)
        v_s1 = encoder.encode_state(s1)

        # Expected state delta in vector space
        actual_delta = v_s1 - v_s0
        v_c1 = encoder.encode_capability(c1)
        v_eff = v_c1[domain["schema"].slice_effects]

        # Check alignment between effect vector and state transition delta
        alignment = cosine_similarity(v_eff, actual_delta)
        return {
            "criterion": "2. State Relationship",
            "passed": alignment > 0.95,
            "state_delta_alignment": alignment,
            "captured_variables": [e.variable for e in c1.effects]
        }

    def evaluate_criterion_3_precondition_effect_compatibility(self) -> Dict[str, Any]:
        """Can composable capabilities be distinguished from incompatible ones?"""
        domain = self.ecommerce_data
        encoder = CapabilityEncoder(domain["schema"])
        caps = domain["named_capabilities"]

        v1 = encoder.encode_capability(caps["CreateOrder"])
        v2 = encoder.encode_capability(caps["MakePayment"])
        v3 = encoder.encode_capability(caps["CancelCart"])

        score_comp, _ = composability_score(v1, v2, domain["schema"])
        score_incomp, _ = composability_score(v1, v3, domain["schema"])
        margin = score_comp - score_incomp

        return {
            "criterion": "3. Precondition-Effect Compatibility",
            "passed": score_comp > 0.5 and score_incomp < 0.0,
            "composable_pair_score": score_comp,
            "incompatible_pair_score": score_incomp,
            "separation_margin": margin
        }

    def evaluate_criterion_4_input_output_compatibility(self) -> Dict[str, Any]:
        """Can dependencies between capabilities be represented?"""
        domain = self.ecommerce_data
        encoder = CapabilityEncoder(domain["schema"])
        caps = domain["named_capabilities"]

        # C1 produces order_id -> C2 consumes order_id
        v1 = encoder.encode_capability(caps["CreateOrder"])
        v2 = encoder.encode_capability(caps["MakePayment"])
        # QueryWeather produces weather_data -> C2 does NOT consume weather_data
        v_weather = encoder.encode_capability(caps["QueryWeather"])

        _, brk_comp = composability_score(v1, v2, domain["schema"])
        _, brk_incomp = composability_score(v_weather, v2, domain["schema"])

        return {
            "criterion": "4. Input-Output Compatibility",
            "passed": brk_comp["data_compatibility"] > 0.8 and brk_incomp["data_compatibility"] < 0.2,
            "valid_dataflow_score": brk_comp["data_compatibility"],
            "invalid_dataflow_score": brk_incomp["data_compatibility"]
        }

    def evaluate_criterion_5_composition(self) -> Dict[str, Any]:
        """Can complex capabilities be represented from smaller capabilities?"""
        domain = self.ecommerce_data
        schema = domain["schema"]
        encoder = CapabilityEncoder(schema)
        caps = domain["named_capabilities"]

        c1 = caps["CreateOrder"]
        c2 = caps["MakePayment"]
        c3 = caps["SendNotification"]

        c123_sym = compose_sequence([c1, c2, c3])
        v123_sym = encoder.encode_capability(c123_sym)

        v1 = encoder.encode_capability(c1)
        v2 = encoder.encode_capability(c2)
        v3 = encoder.encode_capability(c3)
        v123_alg = compose_vectors(compose_vectors(v1, v2, schema), v3, schema)

        homomorphism_sim = cosine_similarity(v123_sym, v123_alg)
        mae = float(np.mean(np.abs(v123_sym - v123_alg)))

        return {
            "criterion": "5. Composition",
            "passed": homomorphism_sim > 0.90,
            "homomorphism_cosine": homomorphism_sim,
            "mean_absolute_error": mae,
            "composite_name": c123_sym.name
        }

    def evaluate_criterion_6_goal_relevance(self) -> Dict[str, Any]:
        """Can the relationship between capabilities and goals be identified?"""
        domain = self.ecommerce_data
        schema = domain["schema"]
        encoder = CapabilityEncoder(schema)
        goal = domain["goal"]
        init = domain["initial_state"]

        v_g = encoder.encode_goal(goal)
        v_s0 = encoder.encode_state(init)

        v_useful = encoder.encode_capability(domain["named_capabilities"]["CreateOrder"])
        v_irrel = encoder.encode_capability(domain["named_capabilities"]["CompressLogFiles"])

        rel_useful = goal_relevance_score(v_useful, v_g, v_s0, schema)
        rel_irrel = goal_relevance_score(v_irrel, v_g, v_s0, schema)

        return {
            "criterion": "6. Goal Relevance",
            "passed": rel_useful > 0.4 and abs(rel_irrel) < 0.05,
            "useful_relevance": rel_useful,
            "irrelevant_relevance": rel_irrel,
            "discrimination_ratio": float(rel_useful / (abs(rel_irrel) + 1e-4))
        }

    def evaluate_criterion_7_operational_properties(self) -> Dict[str, Any]:
        """Can cost, reliability, availability, and constraints be represented appropriately?"""
        domain = self.ecommerce_data
        schema = domain["schema"]
        encoder = CapabilityEncoder(schema)
        caps = domain["named_capabilities"]

        c_prem = caps["MakePayment_PremiumGateway"]
        c_budg = caps["MakePayment_BudgetGateway"]
        v_prem = encoder.encode_capability(c_prem)
        v_budg = encoder.encode_capability(c_budg)

        # Functional logic is identical
        f_sim = functional_similarity(v_prem, v_budg, schema)
        # Operational subspace is markedly distinct
        op_dist = float(np.linalg.norm(v_prem[schema.slice_operational] - v_budg[schema.slice_operational]))

        return {
            "criterion": "7. Operational Properties",
            "passed": f_sim > 0.95 and op_dist > 0.2,
            "functional_invariance": f_sim,
            "operational_subspace_distance": op_dist
        }

    def evaluate_criterion_8_consistency(self) -> Dict[str, Any]:
        """Does the representation behave consistently across different problems?"""
        # Test on second independent domain: Cloud DevOps Pipeline
        domain = self.cloud_data
        schema = domain["schema"]
        encoder = CapabilityEncoder(schema)
        caps = domain["named_capabilities"]

        v_compile = encoder.encode_capability(caps["CompileCode"])
        v_build = encoder.encode_capability(caps["BuildContainer"])
        v_deploy = encoder.encode_capability(caps["DeployK8s"])
        v_clean = encoder.encode_capability(caps["CleanDiskCaches"])

        # Compile -> BuildContainer is compatible
        score_cb, _ = composability_score(v_compile, v_build, schema)
        # CleanDiskCaches -> DeployK8s is not chained
        score_incomp, _ = composability_score(v_clean, v_deploy, schema)

        # Multi-step composition in cloud domain
        c_pipe = compose_sequence([caps["CompileCode"], caps["BuildContainer"], caps["DeployK8s"]])
        v_pipe_sym = encoder.encode_capability(c_pipe)
        v_pipe_alg = compose_vectors(compose_vectors(v_compile, v_build, schema), v_deploy, schema)
        pipe_sim = cosine_similarity(v_pipe_sym, v_pipe_alg)

        return {
            "criterion": "8. Consistency",
            "passed": score_cb > 0.5 and pipe_sim > 0.90,
            "cloud_domain_chain_score": score_cb,
            "cloud_pipeline_composition_sim": pipe_sim,
            "secondary_domain": domain["domain_name"]
        }

    def evaluate_criterion_9_efficiency(self) -> Dict[str, Any]:
        """What are the computational and storage requirements?"""
        domain = self.ecommerce_data
        schema = domain["schema"]
        encoder = CapabilityEncoder(schema)
        caps = domain["capabilities"]

        # Measure encoding throughput
        start = time.perf_counter()
        n_iters = 2000
        for _ in range(n_iters):
            for c in caps:
                _ = encoder.encode_capability(c)
        total_time = time.perf_counter() - start
        total_encodings = n_iters * len(caps)
        encodings_per_sec = total_encodings / total_time
        latency_us = (total_time / total_encodings) * 1e6

        # Measure memory per vector
        sample_vec = encoder.encode_capability(caps[0])
        bytes_per_vector = sample_vec.nbytes

        return {
            "criterion": "9. Efficiency",
            "passed": encodings_per_sec > 10000,
            "encodings_per_second": encodings_per_sec,
            "average_latency_microseconds": latency_us,
            "vector_dimension": schema.total_dim,
            "storage_bytes_per_vector": bytes_per_vector
        }

    def run_all_evaluations(self) -> List[Dict[str, Any]]:
        results = [
            self.evaluate_criterion_1_capability_representation(),
            self.evaluate_criterion_2_state_relationship(),
            self.evaluate_criterion_3_precondition_effect_compatibility(),
            self.evaluate_criterion_4_input_output_compatibility(),
            self.evaluate_criterion_5_composition(),
            self.evaluate_criterion_6_goal_relevance(),
            self.evaluate_criterion_7_operational_properties(),
            self.evaluate_criterion_8_consistency(),
            self.evaluate_criterion_9_efficiency()
        ]
        return results
