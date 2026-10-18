import json

from embedding import (
    encode_state,
    encode_goal,
    encode_capability
)

from experiments import run_all_experiments


# Initial application state
initial_state = [
    "Cart.exists=true",
    "Cart.item_count>0",
    "Inventory.available=true",
    "Order.exists=false",
    "Payment.status=NOT_STARTED",
    "Notification.sent=false"
]


# Application goal
goal = [
    "Order.exists=true",
    "Payment.status=SUCCESS",
    "Notification.sent=true"
]


# Load capabilities from JSON file
def load_capabilities():

    with open("data/capabilities.json", "r") as file:
        return json.load(file)


# Find a capability by name
def find_capability(capabilities, name):

    for capability in capabilities:

        if capability["name"] == name:
            return capability

    return None


# Main program
def main():

    print("=" * 60)
    print("ASSIGNMENT 2")
    print("VECTOR EMBEDDING FOR CAPABILITY COMPOSITION")
    print("=" * 60)

    # Load capabilities
    capabilities = load_capabilities()

    # Encode initial state
    state_vector = encode_state(initial_state)

    print("\nInitial State Vector:")
    print(state_vector)

    # Encode goal
    goal_vector = encode_goal(goal)

    print("\nGoal Vector:")
    print(goal_vector)

    # Find CreateOrder capability
    create_order = find_capability(
        capabilities,
        "CreateOrder"
    )

    # Encode capability
    capability_vector = encode_capability(
        create_order
    )

    print("\nCreateOrder Vector:")
    print(capability_vector)

    print("\nVector Dimension:")
    print(len(capability_vector))

    # Run all experiments
    run_all_experiments()


if __name__ == "__main__":
    main()