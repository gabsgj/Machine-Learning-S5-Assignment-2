"""
Run the five experiments required by PCCST503 Assignment 2.
"""

from pathlib import Path
import sys
import pandas as pd

# Make src importable when running:
# python src/run_experiments.py
sys.path.insert(0, str(Path(__file__).resolve().parent))

from capability_embedding import (
    example_application,
    encode_capability,
    encode_goal,
    encode_state,
    similarity,
    compatibility,
    compose,
    goal_relevance,
)


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


def add(rows, experiment, item, value, expected=None, passed=None):
    rows.append({
        "experiment": experiment,
        "item": item,
        "value": round(float(value), 6) if isinstance(value, (int, float)) else value,
        "expected": expected,
        "passed": passed,
    })


def main():
    app = example_application()
    rows = []

    # ---------------------------------------------------------------
    # Experiment 0: basic encoding
    # ---------------------------------------------------------------
    state_vector = encode_state(app["initial_state"])
    goal_vector = encode_goal(app["goal"])
    cap_vector = encode_capability(app["CreateOrder"])

    add(rows, "Encoding", "state_vector_dimension", len(state_vector))
    add(rows, "Encoding", "goal_vector_dimension", len(goal_vector))
    add(rows, "Encoding", "capability_vector_dimension", len(cap_vector))

    # ---------------------------------------------------------------
    # Experiment 1: compatibility
    # ---------------------------------------------------------------
    c12 = compatibility(app["CreateOrder"], app["MakePayment"])
    c13 = compatibility(app["CreateOrder"], app["CancelCart"])

    add(rows, "Capability compatibility",
        "CreateOrder -> MakePayment", c12, "high")
    add(rows, "Capability compatibility",
        "CreateOrder -> CancelCart", c13, "low")

    # ---------------------------------------------------------------
    # Experiment 2: composition
    # ---------------------------------------------------------------
    composite = compose([
        app["CreateOrder"],
        app["MakePayment"],
        app["SendNotification"],
    ])

    sim_create_composite = similarity(
        app["CreateOrder"], composite
    )
    sim_payment_composite = similarity(
        app["MakePayment"], composite
    )
    sim_notify_composite = similarity(
        app["SendNotification"], composite
    )

    add(rows, "Capability composition",
        "CreateOrder vs CompletePurchase", sim_create_composite)
    add(rows, "Capability composition",
        "MakePayment vs CompletePurchase", sim_payment_composite)
    add(rows, "Capability composition",
        "SendNotification vs CompletePurchase", sim_notify_composite)
    add(rows, "Capability composition",
        "Composite reliability", composite.reliability)
    add(rows, "Capability composition",
        "Composite availability", composite.availability)
    add(rows, "Capability composition",
        "Composite goal relevance",
        goal_relevance(composite, app["goal"]))

    # ---------------------------------------------------------------
    # Experiment 3: alternative implementations
    # ---------------------------------------------------------------
    api_db = similarity(
        app["CreateOrder"], app["CreateOrderDatabase"]
    )
    api_gui = similarity(
        app["CreateOrder"], app["CreateOrderGUI"]
    )

    add(rows, "Alternative implementations",
        "API vs Database", api_db)
    add(rows, "Alternative implementations",
        "API vs GUI", api_gui)

    # ---------------------------------------------------------------
    # Experiment 4: irrelevant capability
    # ---------------------------------------------------------------
    rel_create = goal_relevance(app["CreateOrder"], app["goal"])
    rel_payment = goal_relevance(app["MakePayment"], app["goal"])
    rel_notify = goal_relevance(app["SendNotification"], app["goal"])
    rel_profile = goal_relevance(app["UpdateProfile"], app["goal"])

    add(rows, "Goal relevance", "CreateOrder", rel_create)
    add(rows, "Goal relevance", "MakePayment", rel_payment)
    add(rows, "Goal relevance", "SendNotification", rel_notify)
    add(rows, "Goal relevance", "UpdateProfile", rel_profile)

    # ---------------------------------------------------------------
    # Experiment 5: operational attributes
    # ---------------------------------------------------------------
    add(rows, "Operational attributes",
        "CreateOrder reliability", app["CreateOrder"].reliability)
    add(rows, "Operational attributes",
        "CreateOrder money cost", app["CreateOrder"].money_cost)
    add(rows, "Operational attributes",
        "MakePayment reliability", app["MakePayment"].reliability)
    add(rows, "Operational attributes",
        "MakePayment risk", app["MakePayment"].risk)
    add(rows, "Operational attributes",
        "SendNotification availability", app["SendNotification"].availability)
    add(rows, "Operational attributes",
        "CompletePurchase reliability", composite.reliability)

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "experiment_results.csv", index=False)

    summary = f"""# Experiment Summary

## Encoding

All state and goal vectors use the same symbolic vocabulary. Capability
vectors additionally include six operational attributes.

## Experiment 1 — Capability Compatibility

- CreateOrder → MakePayment: {c12:.4f}
- CreateOrder → CancelCart: {c13:.4f}

The first pair is expected to be substantially more compatible because
CreateOrder produces `Order.exists = true`, which satisfies MakePayment's
precondition. CancelCart requires `Order.exists = false`.

## Experiment 2 — Composition

Composite capability:

`CompletePurchase = SendNotification ◦ MakePayment ◦ CreateOrder`

The implementation constructs a composite capability only when adjacent
precondition/effect requirements are satisfied.

Composite reliability:
`{composite.reliability:.4f}`

Composite availability:
`{composite.availability:.4f}`

Composite goal relevance:
`{goal_relevance(composite, app["goal"]):.4f}`

## Experiment 3 — Alternative Implementations

CreateOrder is compared with database and GUI implementations.

- API vs Database similarity: {api_db:.4f}
- API vs GUI similarity: {api_gui:.4f}

They share functional information but retain mechanism/type information,
so they are related without being represented as identical.

## Experiment 4 — Irrelevant Capabilities

Goal relevance:

- CreateOrder: {rel_create:.4f}
- MakePayment: {rel_payment:.4f}
- SendNotification: {rel_notify:.4f}
- UpdateProfile: {rel_profile:.4f}

UpdateProfile does not directly produce any of the specified purchase-goal
conditions.

## Experiment 5 — Operational Attributes

The representation records reliability, availability, risk, time cost,
resource cost and monetary cost. These are treated separately from the
symbolic functional features so that operational properties can be
analysed without changing the functional identity of a capability.

## Conclusion

The experiments show that a structured, problem-specific vector can
represent functional identity while a separate compatibility function
captures the stronger condition needed for composition.
"""

    (RESULTS / "experiment_summary.md").write_text(summary, encoding="utf-8")

    print(df.to_string(index=False))
    print("\nResults saved to:", RESULTS)


if __name__ == "__main__":
    main()
