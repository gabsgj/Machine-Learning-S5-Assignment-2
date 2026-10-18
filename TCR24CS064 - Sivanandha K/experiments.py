import json
import sys
from pathlib import Path

import numpy as np
import os


# Add src directory to Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root / "src"))

from capability_embedding import (
    Capability,
    encode_capability,
    encode_state,
    encode_goal,
    similarity,
    compatibility,
    compose
)


# Load dataset

dataset_path = os.path.join(os.path.dirname(__file__), "capability_dataset.json")

with open(dataset_path, "r") as file:
    dataset = json.load(file)


# Convert JSON data into Capability objects

capabilities = {}

for name, data in dataset["capabilities"].items():

    capabilities[name] = Capability(
        name=name,
        capability_type=data["type"],
        inputs=data["inputs"],
        outputs=data["outputs"],
        preconditions=data["preconditions"],
        effects=data["effects"],
        resources=data["resources"],
        mechanism=data["mechanism"],
        cost=data["cost"],
        risk=data["risk"],
        reliability=data["reliability"],
        availability=data["availability"]
    )


# Experiment 1: Capability representation

print("\n" + "=" * 60)
print("EXPERIMENT 1: CAPABILITY REPRESENTATION")
print("=" * 60)

for name in [
    "CreateOrder",
    "MakePayment",
    "CancelCart"
]:

    vector = encode_capability(capabilities[name])

    print(
        name,
        "-> vector dimension =",
        len(vector),
        ", non-zero features =",
        np.count_nonzero(vector)
    )

# Experiment 2: Capability compatibility

print("\n" + "=" * 60)
print("EXPERIMENT 2: CAPABILITY COMPATIBILITY")
print("=" * 60)

pairs = [
    ("CreateOrder", "MakePayment"),
    ("CreateOrder", "CancelCart")
]

for first_name, second_name in pairs:

    first_capability = capabilities[first_name]
    second_capability = capabilities[second_name]

    compatibility_score = compatibility(
        first_capability,
        second_capability
    )

    print(
        first_name,
        "->",
        second_name,
        ":",
        round(compatibility_score, 3)
    )


# Experiment 3: Similarity

print("\n" + "=" * 60)
print("EXPERIMENT 3: VECTOR SIMILARITY")
print("=" * 60)

create_order_vector = encode_capability(
    capabilities["CreateOrder"]
)

database_order_vector = encode_capability(
    capabilities["CreateOrderDatabase"]
)

cancel_cart_vector = encode_capability(
    capabilities["CancelCart"]
)

print(
    "CreateOrder vs CreateOrderDatabase =",
    round(
        similarity(
            create_order_vector,
            database_order_vector
        ),
        3
    )
)

print(
    "CreateOrder vs CancelCart =",
    round(
        similarity(
            create_order_vector,
            cancel_cart_vector
        ),
        3
    )
)


# Experiment 4: Alternative implementations

print("\n" + "=" * 60)
print("EXPERIMENT 4: ALTERNATIVE IMPLEMENTATIONS")
print("=" * 60)

api_vector = encode_capability(
    capabilities["CreateOrder"]
)

database_vector = encode_capability(
    capabilities["CreateOrderDatabase"]
)

gui_vector = encode_capability(
    capabilities["CreateOrderGUI"]
)

print(
    "API vs Database =",
    round(similarity(api_vector, database_vector), 3)
)

print(
    "API vs GUI =",
    round(similarity(api_vector, gui_vector), 3)
)

print(
    "Database vs GUI =",
    round(similarity(database_vector, gui_vector), 3)
)

# Experiment 5: Irrelevant capabilities

print("\n" + "=" * 60)
print("EXPERIMENT 5: IRRELEVANT CAPABILITY")
print("=" * 60)

goal_vector = encode_goal(
    dataset["goals"]["complete_purchase"]
)

check_inventory_vector = encode_capability(
    capabilities["CheckInventory"]
)

create_order_vector = encode_capability(
    capabilities["CreateOrder"]
)

print(
    "CreateOrder vs CompletePurchase goal =",
    round(
        similarity(
            create_order_vector,
            goal_vector
        ),
        3
    )
)

print(
    "CheckInventory vs CompletePurchase goal =",
    round(
        similarity(
            check_inventory_vector,
            goal_vector
        ),
        3
    )
)

# Experiment 6: Composition

print("\n" + "=" * 60)
print("EXPERIMENT 6: CAPABILITY COMPOSITION")
print("=" * 60)

create_order = capabilities["CreateOrder"]
make_payment = capabilities["MakePayment"]
send_notification = capabilities["SendNotification"]

print(
    "CreateOrder -> MakePayment compatibility =",
    round(
        compatibility(
            create_order,
            make_payment
        ),
        3
    )
)

print(
    "MakePayment -> SendNotification compatibility =",
    round(
        compatibility(
            make_payment,
            send_notification
        ),
        3
    )
)

composite = compose([
    create_order,
    make_payment,
    send_notification
])

composite_vector = encode_capability(composite)

print(
    "Composite capability vector dimension =",
    len(composite_vector)
)

print(
    "Composite cost =",
    round(composite.cost, 3)
)

print(
    "Composite risk =",
    round(composite.risk, 3)
)

print(
    "Composite reliability =",
    round(composite.reliability, 3)
)

print(
    "Composite availability =",
    round(composite.availability, 3)
)


# Experiment 7: Operational properties

print("\n" + "=" * 60)
print("EXPERIMENT 7: OPERATIONAL ATTRIBUTES")
print("=" * 60)

for name in [
    "CreateOrder",
    "CreateOrderDatabase",
    "CreateOrderGUI",
    "MakePayment"
]:

    capability = capabilities[name]

    print(
        name,
        ": cost =",
        capability.cost,
        ", risk =",
        capability.risk,
        ", reliability =",
        capability.reliability,
        ", availability =",
        capability.availability
    )


# State encoding

print("\n" + "=" * 60)
print("STATE AND GOAL ENCODING")
print("=" * 60)

initial_state_vector = encode_state(
    dataset["states"]["initial_state"]
)

goal_vector = encode_goal(
    dataset["goals"]["complete_purchase"]
)

print(
    "Initial state vector dimension =",
    len(initial_state_vector)
)

print(
    "Goal vector dimension =",
    len(goal_vector)
)

print(
    "CreateOrder vs initial state =",
    round(
        similarity(
            create_order_vector,
            initial_state_vector
        ),
        3
    )
)
