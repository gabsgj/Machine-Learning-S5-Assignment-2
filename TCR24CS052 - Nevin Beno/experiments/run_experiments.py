from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.compatibility import compatibility, goal_relevance
from src.composition import compose_capabilities
from src.embedding import StructuredEmbedder
from src.evaluation import (
    evaluate_compatibility,
    evaluate_composition,
    evaluate_goal_relevance,
    evaluate_operational_effect,
    save_plots,
)
from src.models import Capability, Condition, Goal, IOField, Quality, State


def load_dataset(path: Path):
    raw = json.loads(path.read_text())

    def condition(x):
        return Condition(x["variable"], x["operator"], x["value"])

    def io_field(x):
        return IOField(
            x["name"], x["type"], x.get("domain", "any"), x.get("required", True)
        )

    capabilities = {}
    for item in raw["capabilities"]:
        capabilities[item["name"]] = Capability(
            name=item["name"],
            capability_type=item["capability_type"],
            inputs=[io_field(x) for x in item.get("inputs", [])],
            outputs=[io_field(x) for x in item.get("outputs", [])],
            preconditions=[condition(x) for x in item.get("preconditions", [])],
            effects=[condition(x) for x in item.get("effects", [])],
            constraints=[condition(x) for x in item.get("constraints", [])],
            resources=item.get("resources", []),
            quality=Quality(**item.get("quality", {})),
            reliability=item.get("reliability", 1.0),
            availability=item.get("availability", 1.0),
            mechanism=item.get("mechanism", {}),
            tags=item.get("tags", []),
        )

    state = State(raw["initial_state"])
    goal = Goal([condition(x) for x in raw["goal"]])
    return state, goal, capabilities


def main():
    data = ROOT / "data" / "capability_dataset.json"
    out = ROOT / "results"
    out.mkdir(exist_ok=True)

    state, goal, capabilities = load_dataset(data)
    emb = StructuredEmbedder()

    # Deliverable 2 API demonstration
    state_vector = emb.encode_state(state)
    goal_vector = emb.encode_goal(goal)
    cap_vectors = {k: emb.encode_capability(v) for k, v in capabilities.items()}

    # 1. Compatibility
    compat = evaluate_compatibility(capabilities, emb)
    compat.to_csv(out / "compatibility_results.csv", index=False)

    # 2. Composition
    chain = [
        capabilities["CreateOrder"],
        capabilities["MakePayment"],
        capabilities["SendNotification"],
    ]
    composite = compose_capabilities(chain, emb)
    comp_df = evaluate_composition(chain, emb)
    comp_df.to_csv(out / "composition_results.csv", index=False)

    # 3. Goal relevance
    goal_df = evaluate_goal_relevance(capabilities, goal, emb)
    goal_df.to_csv(out / "goal_relevance_results.csv", index=False)

    # 4. Operational properties
    op_df = evaluate_operational_effect(capabilities, emb)
    op_df.to_csv(out / "operational_results.csv", index=False)

    save_plots(compat, goal_df, op_df, out)

    summary = {
        "embedding_dimension": emb.DIM,
        "capability_count": len(capabilities),
        "state_vector_dimension": len(state_vector),
        "goal_vector_dimension": len(goal_vector),
        "composite_name": composite.name,
        "composition_reliability": composite.reliability,
        "composition_availability": composite.availability,
        "createorder_makepayment_compatibility": compatibility(
            capabilities["CreateOrder"], capabilities["MakePayment"]
        ),
        "createorder_cancelcart_compatibility": compatibility(
            capabilities["CreateOrder"], capabilities["CancelCart"]
        ),
        "createorder_goal_relevance": goal_relevance(
            capabilities["CreateOrder"], goal
        ),
        "complete_purchase_goal_relevance": goal_relevance(composite, goal),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2))

    print("\n=== Capability Embedding Experiment ===")
    print(f"Embedding dimension: {emb.DIM}")
    print(f"Capabilities: {len(capabilities)}")
    print("\nCompatibility:")
    print(compat[
        compat["from"].isin(["CreateOrder"]) &
        compat["to"].isin(["MakePayment", "CancelCart"])
    ].to_string(index=False))

    print("\nComposite:")
    print(composite.name)
    print(f"Reliability: {composite.reliability:.4f}")
    print(f"Availability: {composite.availability:.4f}")

    print("\nGoal relevance:")
    print(goal_df.sort_values("goal_relevance", ascending=False).to_string(index=False))

    print(f"\nResults written to: {out}")


if __name__ == "__main__":
    main()
