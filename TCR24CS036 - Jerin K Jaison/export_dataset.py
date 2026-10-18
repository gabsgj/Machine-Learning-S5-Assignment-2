"""
Exports the experimental dataset (capabilities, states, goals) as a single
human-readable JSON file -- Deliverable 3, independent of the Python object
model, so it can be inspected or reused without importing the code.
"""

import json
from dataclasses import asdict
from dataset import build_capabilities, build_states, build_goals


def main():
    caps = build_capabilities()
    states = build_states()
    goals = build_goals()

    out = {
        "capabilities": {cid: asdict(c) for cid, c in caps.items()},
        "states": {sid: s.assignments for sid, s in states.items()},
        "goals": {gid: list(g.conditions) for gid, g in goals.items()},
        "notes": {
            "CreateOrder, MakePayment, CancelCart, SendNotification":
                "base e-commerce domain from the assignment PDF",
            "CreateOrder_API/_DB/_GUI":
                "alternative implementations of CreateOrder for Experiment 3",
            "GetWeatherForecast, LogAnalyticsEvent":
                "goal-irrelevant capabilities for Experiment 4",
            "MakePayment_Degraded":
                "operational-attribute variant of MakePayment for Experiment 5",
        },
    }
    with open("experimental_dataset.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    print("wrote experimental_dataset.json")


if __name__ == "__main__":
    main()
