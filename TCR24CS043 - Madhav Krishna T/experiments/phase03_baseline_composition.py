"""Experiment 2: capability composition for the expanded SCE-128 dataset.

Evaluates symbolic composition chains and compares:
1. Independently encoded formal composite vectors.
2. Recursive deterministic vector composition (v1 baseline).
3. Goal alignment of formal composite effects.
4. Step-wise compatibility along each chain.

The experiment deliberately treats symbolic composition as ground truth and
reports vector composition consistency separately.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np

from src.compatibility import compatibility
from src.formal_composition import compose_many, vector_compose
from src.dataset import load_dataset
from src.encoder import (
    cosine,
    encode_capability,
    encode_effects_common,
    encode_goal,
)
from src.schema import Condition

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "expanded_application.json"
RESULT_JSON = ROOT / "results" / "baseline_v1_1" / "phase03_baseline_composition.json"
RESULT_MD = ROOT / "results" / "baseline_v1_1" / "phase03_baseline_composition.md"


def mean(values: List[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def relation_features(result) -> List[float]:
    return [
        result.effect_precondition_vector,
        result.output_input_vector,
        result.conflict,
    ]


def chain_metrics(chain_id: str, chain_ids: List[str], caps: Dict[str, object], goal) -> Dict:
    chain_caps = [caps[cid] for cid in chain_ids]
    atomic_vectors = [encode_capability(c) for c in chain_caps]
    goal_vec = encode_goal(goal)

    # Build the formal composite incrementally. This is the ground-truth
    # object against which vector composition is evaluated.
    formal_composite = chain_caps[0]
    vector_composite = atomic_vectors[0].copy()

    prefixes: List[dict] = []
    link_results: List[dict] = []

    # Prefix length 1 is an exact identity comparison.
    encoded_formal = encode_capability(formal_composite)
    prefixes.append({
        "length": 1,
        "capabilities": [chain_caps[0].id],
        "formal_composite_id": formal_composite.id,
        "formal_composite_name": formal_composite.name,
        "vector_consistency": cosine(vector_composite, encoded_formal),
        "formal_goal_alignment": cosine(encode_effects_common(formal_composite), goal_vec),
        "formal_reliability": formal_composite.reliability,
        "formal_execution_time_ms": formal_composite.quality.execution_time_ms,
    })

    for idx in range(1, len(chain_caps)):
        source = formal_composite
        target = chain_caps[idx]
        relation = compatibility(source, target)
        if not relation.compatible:
            raise RuntimeError(
                f"Expected valid composition chain {chain_id} contains incompatible step "
                f"{source.id}->{target.id} (score={relation.score:.4f})"
            )

        link_results.append({
            "from": source.id,
            "to": target.id,
            "formal_score": relation.score,
            "effect_precondition_exact": relation.effect_precondition_exact,
            "output_input_exact": relation.output_input_exact,
            "effect_precondition_vector": relation.effect_precondition_vector,
            "output_input_vector": relation.output_input_vector,
            "conflict": relation.conflict,
            "compatible": relation.compatible,
        })

        formal_composite = compose_many([source, target])
        vector_composite = vector_compose(
            vector_composite,
            atomic_vectors[idx],
            relation_features(relation),
        )
        encoded_formal = encode_capability(formal_composite)

        prefix_ids = chain_ids[: idx + 1]
        prefixes.append({
            "length": idx + 1,
            "capabilities": prefix_ids,
            "formal_composite_id": formal_composite.id,
            "formal_composite_name": formal_composite.name,
            "vector_consistency": cosine(vector_composite, encoded_formal),
            "formal_goal_alignment": cosine(encode_effects_common(formal_composite), goal_vec),
            "formal_reliability": formal_composite.reliability,
            "formal_execution_time_ms": formal_composite.quality.execution_time_ms,
        })

    return {
        "chain_id": chain_id,
        "chain_length": len(chain_ids),
        "final_composite_id": formal_composite.id,
        "final_composite_name": formal_composite.name,
        "links": link_results,
        "prefixes": prefixes,
        "final_vector_consistency": prefixes[-1]["vector_consistency"],
        "final_goal_alignment": prefixes[-1]["formal_goal_alignment"],
        "final_reliability": formal_composite.reliability,
        "final_execution_time_ms": formal_composite.quality.execution_time_ms,
    }


def main() -> None:
    raw, caps = load_dataset(DATA_PATH)
    goal = [Condition(**g) for g in raw["goal"]]

    chain_results = []
    for chain in raw["composition_chains"]:
        chain_results.append(
            chain_metrics(
                chain["id"],
                chain["capabilities"],
                caps,
                goal,
            )
        )

    all_consistency = [
        p["vector_consistency"]
        for c in chain_results
        for p in c["prefixes"]
        if p["length"] > 1
    ]
    all_goal_alignment = [
        p["formal_goal_alignment"]
        for c in chain_results
        for p in c["prefixes"]
    ]

    payload = {
        "experiment": "Experiment 2 - Capability Composition",
        "model": "SCE-128-v1.1",
        "dataset": DATA_PATH.name,
        "chain_count": len(chain_results),
        "overall": {
            "mean_nontrivial_vector_consistency": mean(all_consistency),
            "min_nontrivial_vector_consistency": min(all_consistency) if all_consistency else 0.0,
            "mean_formal_goal_alignment": mean(all_goal_alignment),
            "final_goal_alignment_mean": mean([c["final_goal_alignment"] for c in chain_results]),
        },
        "chains": chain_results,
    }

    RESULT_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    report: List[str] = []
    report.append("# Experiment 2 — Capability Composition")
    report.append("")
    report.append("## Purpose")
    report.append("Evaluate whether the formal capability composition model produces coherent composite representations and whether the deterministic vector composition baseline remains close to the independently encoded formal composite.")
    report.append("")
    report.append("## Method")
    report.append("For each valid chain, symbolic composition is treated as ground truth. The v1 vector composition operator is applied recursively and compared against the independently encoded formal composite using cosine similarity.")
    report.append("")
    report.append("## Overall results")
    report.append(f"- Mean non-trivial vector composition consistency: **{payload['overall']['mean_nontrivial_vector_consistency']:.4f}**")
    report.append(f"- Minimum non-trivial vector composition consistency: **{payload['overall']['min_nontrivial_vector_consistency']:.4f}**")
    report.append(f"- Mean formal composite goal alignment: **{payload['overall']['mean_formal_goal_alignment']:.4f}**")
    report.append(f"- Mean final goal alignment: **{payload['overall']['final_goal_alignment_mean']:.4f}**")
    report.append("")

    for chain in chain_results:
        report.append(f"## {chain['chain_id']}")
        report.append("")
        ids = chain["prefixes"][-1]["capabilities"]
        report.append(f"Chain: `{' → '.join(ids)}`")
        report.append(f"Final composite: **{chain['final_composite_name']}**")
        report.append(f"Final reliability: **{chain['final_reliability']:.6f}**")
        report.append(f"Final execution time: **{chain['final_execution_time_ms']:.1f} ms**")
        report.append(f"Final vector consistency: **{chain['final_vector_consistency']:.4f}**")
        report.append(f"Final goal alignment: **{chain['final_goal_alignment']:.4f}**")
        report.append("")
        report.append("### Prefix analysis")
        report.append("| Length | Prefix | Vector consistency | Formal goal alignment | Reliability | Time (ms) |")
        report.append("|---:|---|---:|---:|---:|---:|")
        for p in chain["prefixes"]:
            report.append(
                f"| {p['length']} | `{' → '.join(p['capabilities'])}` | "
                f"{p['vector_consistency']:.4f} | {p['formal_goal_alignment']:.4f} | "
                f"{p['formal_reliability']:.6f} | {p['formal_execution_time_ms']:.1f} |"
            )
        report.append("")
        report.append("### Step compatibility")
        report.append("| From | To | Score | PE exact | IO exact | PE vector | IO vector |")
        report.append("|---|---|---:|---:|---:|---:|---:|")
        for r in chain["links"]:
            report.append(
                f"| {r['from']} | {r['to']} | {r['formal_score']:.4f} | "
                f"{r['effect_precondition_exact']:.2f} | {r['output_input_exact']:.2f} | "
                f"{r['effect_precondition_vector']:.4f} | {r['output_input_vector']:.4f} |"
            )
        report.append("")

    report.append("## Interpretation guidance")
    report.append("Vector composition consistency is a baseline measure, not a learned-model performance claim. A decline in consistency as chain length grows would motivate a learned Compose_theta operator in the later stage of the project.")
    RESULT_MD.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("=" * 78); print("PHASE 03 — BASELINE VECTOR COMPOSITION"); print("=" * 78)
    print(f"Chains evaluated: {len(chain_results)}")
    for chain in chain_results:
        print(f"{chain['chain_id']}:")
        print(f"  length={chain['chain_length']}")
        print(f"  final_vector_consistency={chain['final_vector_consistency']:.4f}")
        print(f"  final_goal_alignment={chain['final_goal_alignment']:.4f}")
        print(f"  final_reliability={chain['final_reliability']:.6f}")
        print(f"  final_execution_time_ms={chain['final_execution_time_ms']:.1f}")
        print("  prefix consistency:")
        for p in chain["prefixes"]:
            print(f"    L{p['length']}: {p['vector_consistency']:.4f}")
    print("Overall:")
    print(f"  mean_nontrivial_vector_consistency={payload['overall']['mean_nontrivial_vector_consistency']:.4f}")
    print(f"  min_nontrivial_vector_consistency={payload['overall']['min_nontrivial_vector_consistency']:.4f}")
    print(f"  final_goal_alignment_mean={payload['overall']['final_goal_alignment_mean']:.4f}")
    print(f"\nJSON: {RESULT_JSON}")
    print(f"Report: {RESULT_MD}")


if __name__ == "__main__":
    main()
