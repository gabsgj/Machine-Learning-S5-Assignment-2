"""Evaluation utilities shared by the final experiment suite."""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple


def mean(values: Sequence[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def binary_metrics(y_true: Sequence[bool], y_pred: Sequence[bool]) -> Dict[str, float | int]:
    tp = sum(t and p for t, p in zip(y_true, y_pred))
    tn = sum((not t) and (not p) for t, p in zip(y_true, y_pred))
    fp = sum((not t) and p for t, p in zip(y_true, y_pred))
    fn = sum(t and (not p) for t, p in zip(y_true, y_pred))
    total = len(y_true)
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def rank_auc(labels: Sequence[bool], scores: Sequence[float]) -> float:
    """Pairwise ranking AUC without an sklearn dependency."""
    positives = [s for y, s in zip(labels, scores) if y]
    negatives = [s for y, s in zip(labels, scores) if not y]
    if not positives or not negatives:
        return 0.5
    wins = 0
    ties = 0
    for p in positives:
        for n in negatives:
            if p > n:
                wins += 1
            elif p == n:
                ties += 1
    return (wins + 0.5 * ties) / (len(positives) * len(negatives))


def contract_signature(cap) -> dict:
    """Canonical functional contract excluding mechanism/operational metadata."""
    return {
        "inputs": [
            {"name": x.name, "type": x.type, "domain": x.domain, "required": x.required}
            for x in cap.inputs
        ],
        "outputs": [
            {"name": x.name, "type": x.type, "domain": x.domain}
            for x in cap.outputs
        ],
        "preconditions": [
            {"attribute": x.attribute, "operator": x.operator, "value": x.value}
            for x in cap.preconditions
        ],
        "effects": [
            {"attribute": x.attribute, "operator": x.operator, "value": x.value}
            for x in cap.effects
        ],
        "constraints": [{"expression": x.expression} for x in cap.constraints],
    }


def exact_contract_match(a, b) -> bool:
    return contract_signature(a) == contract_signature(b)
