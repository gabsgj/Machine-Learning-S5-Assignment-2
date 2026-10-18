import time
import sys
from typing import List, Dict, Tuple, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

from src.capability import Capability
from src.state import Goal
from src.encoder import CapabilityEncoder
from src.similarity import cosine_similarity
from src.compatibility import compatibility
from src.utils import canonicalize_predicate

class TextualBaselineEncoder:
    """
    Baseline 1: Textual / TF-IDF Vectorizer baseline.
    Represents capabilities solely by concatenating textual representations of names, types, inputs, outputs, and effects.
    """
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.is_fitted = False

    def _cap_to_text(self, c: Capability) -> str:
        inps = " ".join([f"{i.name} {i.type}" for i in c.inputs])
        outs = " ".join([f"{o.name} {o.type}" for o in c.outputs])
        preconds = " ".join(c.preconditions)
        effects = " ".join(c.effects)
        resources = " ".join(c.resources)
        text = f"{c.name} {c.type} {inps} {outs} {preconds} {effects} {resources}"
        return text

    def fit_transform(self, capabilities: List[Capability]) -> np.ndarray:
        corpus = [self._cap_to_text(c) for c in capabilities]
        matrix = self.vectorizer.fit_transform(corpus).toarray()
        self.is_fitted = True
        return matrix

    def transform(self, capabilities: List[Capability]) -> np.ndarray:
        corpus = [self._cap_to_text(c) for c in capabilities]
        return self.vectorizer.transform(corpus).toarray()


class FlatUnweightedEncoder:
    """
    Baseline 2: Flat Unweighted Feature Vector baseline.
    Represents capabilities as a simple flat bag-of-tokens without explicit sub-space separation,
    sub-vector weighting, or directional compatibility structures.
    """
    def __init__(self, capabilities: List[Capability]):
        tokens = set()
        for c in capabilities:
            tokens.add(c.name)
            tokens.add(c.type)
            for i in c.inputs: tokens.add(i.name)
            for o in c.outputs: tokens.add(o.name)
            for p in c.preconditions: tokens.add(p)
            for e in c.effects: tokens.add(e)
            for r in c.resources: tokens.add(r)
        self.vocab = sorted(list(tokens))
        self.dimension = len(self.vocab)

    def encode(self, c: Capability) -> np.ndarray:
        vec = np.zeros(self.dimension, dtype=np.float64)
        c_tokens = {c.name, c.type}
        for i in c.inputs: c_tokens.add(i.name)
        for o in c.outputs: c_tokens.add(o.name)
        for p in c.preconditions: c_tokens.add(p)
        for e in c.effects: c_tokens.add(e)
        for r in c.resources: c_tokens.add(r)

        for tok in c_tokens:
            if tok in self.vocab:
                vec[self.vocab.index(tok)] = 1.0
        return vec


def normalize_pred(pred: str) -> str:
    """Normalize predicate strings using shared canonicalize_predicate."""
    return canonicalize_predicate(pred)


def evaluate_goal_relevance(c: Capability, goal: Goal) -> float:
    """
    Evaluate goal relevance of a capability C towards goal G.
    Returns ratio of satisfied goal condition predicates.
    """
    g_conditions = goal.to_predicates()
    if not g_conditions:
        return 0.0

    norm_effects = [normalize_pred(e) for e in c.effects]
    satisfied_count = 0

    for g_pred in g_conditions:
        g_norm = normalize_pred(g_pred)
        if g_norm in norm_effects:
            satisfied_count += 1

    return float(satisfied_count / len(g_conditions))


def evaluate_compatibility_classification(
    capabilities: List[Capability], 
    ground_truth_pairs: List[Tuple[str, str, bool]], 
    encoder: CapabilityEncoder
) -> Dict[str, float]:
    """
    Evaluate binary compatibility classification accuracy, precision, recall, and F1 score
    across a set of labelled capability pairs (C1_name, C2_name, label).
    """
    cap_map = {c.name: c for c in capabilities}
    y_true = []
    y_pred_proposed = []
    y_pred_baseline = []

    # Get flat baseline
    flat_encoder = FlatUnweightedEncoder(capabilities)
    flat_vecs = {c.name: flat_encoder.encode(c) for c in capabilities}

    for c1_name, c2_name, label in ground_truth_pairs:
        if c1_name not in cap_map or c2_name not in cap_map:
            continue
        c1 = cap_map[c1_name]
        c2 = cap_map[c2_name]
        y_true.append(1 if label else 0)

        # Proposed Directional Compatibility
        res = compatibility(c1, c2)
        y_pred_proposed.append(1 if res.is_compatible else 0)

        # Flat Baseline (Cosine similarity > 0.5)
        sim_flat = cosine_similarity(flat_vecs[c1_name], flat_vecs[c2_name])
        y_pred_baseline.append(1 if sim_flat > 0.5 else 0)

    metrics = {
        "proposed_accuracy": float(accuracy_score(y_true, y_pred_proposed)),
        "proposed_precision": float(precision_score(y_true, y_pred_proposed, zero_division=0)),
        "proposed_recall": float(recall_score(y_true, y_pred_proposed, zero_division=0)),
        "proposed_f1": float(f1_score(y_true, y_pred_proposed, zero_division=0)),
        "baseline_accuracy": float(accuracy_score(y_true, y_pred_baseline)),
        "baseline_precision": float(precision_score(y_true, y_pred_baseline, zero_division=0)),
        "baseline_recall": float(recall_score(y_true, y_pred_baseline, zero_division=0)),
        "baseline_f1": float(f1_score(y_true, y_pred_baseline, zero_division=0))
    }
    return metrics


def measure_efficiency_metrics(
    capabilities: List[Capability], 
    encoder: CapabilityEncoder
) -> Dict[str, float]:
    """
    Measure computation latency (ms) and storage size (bytes) of the proposed vector representation.
    """
    start_time = time.perf_counter()
    n_runs = 1000
    for _ in range(n_runs):
        for c in capabilities:
            v = encoder.encode_capability(c)
    total_time = time.perf_counter() - start_time
    avg_encode_time_ms = (total_time / (n_runs * len(capabilities))) * 1000.0

    sample_vec = encoder.encode_capability(capabilities[0])
    vector_memory_bytes = sample_vec.nbytes

    start_comp_time = time.perf_counter()
    for _ in range(n_runs):
        for i in range(len(capabilities) - 1):
            compatibility(capabilities[i], capabilities[i+1])
    total_comp_time = time.perf_counter() - start_comp_time
    avg_compat_time_ms = (total_comp_time / (n_runs * (len(capabilities) - 1))) * 1000.0

    return {
        "vector_dimension": int(encoder.dimension),
        "vector_memory_bytes": int(vector_memory_bytes),
        "avg_encode_time_ms": float(avg_encode_time_ms),
        "avg_compat_time_ms": float(avg_compat_time_ms)
    }
