"""Phase 01 — Formal Dataset Validation.

Validates the expanded application model before embedding evaluation."

Validates formal consistency of the expanded capability dataset before any
embedding/model training is performed.
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from typing import Any

from src.compatibility import compatibility, state_applicability
from src.encoder import cosine, encode_capability, encode_goal
from src.data_models import capability_from_dict
from src.schema import Condition
from src.formal_composition import compose_many

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "expanded_application.json"
RESULTS = ROOT / "results" / "final_v2_1" / "phase01_dataset_validation.json"
REPORT = ROOT / "results" / "final_v2_1" / "phase01_dataset_validation.md"


def functional_fingerprint(raw: dict[str, Any]) -> dict[str, Any]:
    """Return fields that define functional behavior, excluding implementation/ops metadata."""
    return {
        "inputs": raw.get("inputs", []),
        "outputs": raw.get("outputs", []),
        "preconditions": raw.get("preconditions", []),
        "effects": raw.get("effects", []),
        "constraints": raw.get("constraints", []),
    }


def main() -> None:
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    capabilities_raw = raw["capabilities"]
    caps = {item["id"]: capability_from_dict(item) for item in capabilities_raw}

    ids = [item["id"] for item in capabilities_raw]
    duplicate_ids = sorted({cid for cid in ids if ids.count(cid) > 1})

    relation_results = []
    correct = 0
    for relation in raw["expected_relations"]:
        result = compatibility(caps[relation["from"]], caps[relation["to"]])
        expected = relation["relation"] == "compatible"
        ok = result.compatible == expected
        correct += int(ok)
        relation_results.append({
            "from": relation["from"],
            "to": relation["to"],
            "expected_relation": relation["relation"],
            "predicted_compatible": result.compatible,
            "score": result.score,
            "effect_precondition_exact": result.effect_precondition_exact,
            "output_input_exact": result.output_input_exact,
            "conflict": result.conflict,
            "correct": ok,
        })

    relation_accuracy = correct / len(relation_results) if relation_results else 1.0

    chain_results = []
    for chain in raw["composition_chains"]:
        try:
            composite = compose_many([caps[cid] for cid in chain["capabilities"]])
            chain_results.append({
                "id": chain["id"],
                "capabilities": chain["capabilities"],
                "valid": True,
                "composite_id": composite.id,
                "reliability": composite.reliability,
                "execution_time_ms": composite.quality.execution_time_ms,
                "effect_count": len(composite.effects),
            })
        except Exception as exc:  # pragma: no cover - validation report path
            chain_results.append({
                "id": chain["id"],
                "capabilities": chain["capabilities"],
                "valid": False,
                "error": str(exc),
            })

    # Alternative implementations: functional contract should match while
    # implementation fields should differ.
    alt_groups = []
    raw_by_id = {item["id"]: item for item in capabilities_raw}
    for group in raw["alternative_implementation_groups"]:
        group_ids = group["capabilities"]
        fingerprints = [functional_fingerprint(raw_by_id[cid]) for cid in group_ids]
        same_function = all(fp == fingerprints[0] for fp in fingerprints[1:])
        mechanism_signatures = {
            json.dumps({
                "type": raw_by_id[cid].get("type"),
                "mechanism": raw_by_id[cid].get("mechanism", {}),
            }, sort_keys=True)
            for cid in group_ids
        }
        alt_groups.append({
            "group_id": group["group_id"],
            "capabilities": group_ids,
            "shared_function": group["shared_function"],
            "same_functional_contract": same_function,
            "distinct_mechanisms": len(mechanism_signatures) == len(group_ids),
        })

    state = raw["initial_state"]
    applicability = {
        cid: state_applicability(cap, state) for cid, cap in caps.items()
    }

    goal_vector = encode_goal([Condition(**item) for item in raw["goal"]])
    vectors = {cid: encode_capability(cap) for cid, cap in caps.items()}

    alt_similarity = {}
    alt_ids = raw["alternative_implementation_groups"][0]["capabilities"]
    for a, b in combinations(alt_ids, 2):
        alt_similarity[f"{a}<->{b}"] = cosine(vectors[a], vectors[b])

    irrelevant_ids = [cid for cid, value in raw["goal_relevance"].items() if not value]
    relevant_ids = [cid for cid, value in raw["goal_relevance"].items() if value]

    payload = {
        "dataset": raw["metadata"],
        "counts": {
            "capabilities": len(caps),
            "logical_capabilities": raw["metadata"]["logical_capability_count"],
            "alternative_implementations": len(raw["metadata"]["alternative_implementation_variants"]),
            "expected_relations": len(relation_results),
        },
        "schema": {
            "duplicate_ids": duplicate_ids,
            "unique_ids": len(duplicate_ids) == 0,
        },
        "relation_validation": {
            "accuracy": relation_accuracy,
            "results": relation_results,
        },
        "composition_validation": chain_results,
        "alternative_implementations": alt_groups,
        "initial_state_applicability": applicability,
        "alternative_embedding_similarity": alt_similarity,
        "goal_relevance_metadata": {
            "relevant_ids": relevant_ids,
            "irrelevant_ids": irrelevant_ids,
            "note": "These labels are evaluation metadata and are not encoder inputs.",
        },
    }

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Phase 01 — Formal Dataset Validation",
        "",
        f"- Capabilities: **{len(caps)}** ({raw['metadata']['logical_capability_count']} logical + {len(alt_ids)} implementation variants)",
        f"- Required relation accuracy: **{relation_accuracy:.4f}**",
        f"- Duplicate capability IDs: **{'none' if not duplicate_ids else ', '.join(duplicate_ids)}**",
        "",
        "## Composition chains",
    ]
    for item in chain_results:
        status = "PASS" if item["valid"] else "FAIL"
        lines.append(f"- `{item['id']}`: **{status}**")
        if item["valid"]:
            lines.append(f"  - composite: `{item['composite_id']}`")
            lines.append(f"  - reliability: `{item['reliability']:.6f}`")
            lines.append(f"  - execution time: `{item['execution_time_ms']:.1f} ms`")

    lines += ["", "## Alternative implementations"]
    for item in alt_groups:
        lines.append(
            f"- `{item['group_id']}`: functional contract same=`{item['same_functional_contract']}`, "
            f"mechanisms distinct=`{item['distinct_mechanisms']}`"
        )

    lines += ["", "## Alternative implementation vector similarity"]
    for pair, value in alt_similarity.items():
        lines.append(f"- `{pair}`: `{value:.4f}`")

    lines += ["", "## Initial-state applicability"]
    for cid, value in applicability.items():
        lines.append(f"- `{cid}`: `{value:.4f}`")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("=" * 78); print("PHASE 01 — FORMAL DATASET VALIDATION"); print("=" * 78)
    print(f"Capabilities: {len(caps)} ({raw['metadata']['logical_capability_count']} logical + {len(alt_ids)} alternative implementations)")
    print(f"Unique IDs: {not duplicate_ids}")
    print(f"Required relation accuracy: {relation_accuracy:.4f}")
    print("Composition chains:")
    for item in chain_results:
        print(f"  {item['id']}: {'PASS' if item['valid'] else 'FAIL'}")
    print("Alternative implementations:")
    for item in alt_groups:
        print(f"  {item['group_id']}: same_contract={item['same_functional_contract']} distinct_mechanisms={item['distinct_mechanisms']}")
    print("Vector similarity among CreateOrder variants:")
    for pair, value in alt_similarity.items():
        print(f"  {pair}: {value:.4f}")
    print(f"\nJSON: {RESULTS}")
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
