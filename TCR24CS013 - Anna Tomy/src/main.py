import json
import os
import sys

from models import State, Goal, Capability
from embedding import EmbeddingModel
from experiments import run_all_experiments


def load_problem(filename: str):

    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)

    states = [
        State(
            id=item["id"],
            values=item["values"]
        )
        for item in data.get("states", [])
    ]

    goals = [
        Goal(
            id=item["id"],
            conditions=item["conditions"]
        )
        for item in data.get("goals", [])
    ]

    capabilities = [
        Capability.from_dict(item)
        for item in data.get("capabilities", [])
    ]

    return states, goals, capabilities


def print_dataset_summary(
    states,
    goals,
    capabilities
):
    print("=" * 70)
    print("MACHINE LEARNING ASSIGNMENT 2")
    print("VECTOR EMBEDDING FOR CAPABILITY COMPOSITION")
    print("=" * 70)

    print("\nDataset summary")
    print("-" * 70)
    print(f"States:         {len(states)}")
    print(f"Goals:          {len(goals)}")
    print(f"Capabilities:   {len(capabilities)}")


def main():

    project_root = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

    data_file = os.path.join(
        project_root,
        "data",
        "problems.json"
    )

    if not os.path.exists(data_file):
        print(f"Dataset not found: {data_file}")
        sys.exit(1)

    states, goals, capabilities = load_problem(
        data_file
    )

    print_dataset_summary(
        states,
        goals,
        capabilities
    )

    model = EmbeddingModel(
        states=states,
        goals=goals,
        capabilities=capabilities
    )

    print("\nEmbedding configuration")
    print("-" * 70)

    sample_capability = capabilities[0]

    sample_vector = model.encode_capability(
        sample_capability
    )

    state_vector = model.encode_state(
        states[0]
    )

    goal_vector = model.encode_goal(
        goals[0]
    )

    print(f"State vector dimension:       {len(state_vector)}")
    print(f"Goal vector dimension:        {len(goal_vector)}")
    print(f"Capability vector dimension:  {len(sample_vector)}")

    print("\nRunning experiments...")

    run_all_experiments(
        model,
        capabilities
    )

    print("\n" + "=" * 70)
    print("ALL EXPERIMENTS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()