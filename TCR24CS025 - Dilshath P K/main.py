import os
import pandas as pd

from src.embedding import CapabilityEmbedding
from src.compatibility import check_compatibility
from src.composition import compose
from data.dataset import capabilities


embedding = CapabilityEmbedding()
results_dir = "results"
os.makedirs(results_dir, exist_ok=True)

print("=" * 55)
print("CAPABILITY EMBEDDING - EXPERIMENTS")
print("=" * 55)


# Experiment 1: Capability compatibility
print("\nEXPERIMENT 1: COMPATIBILITY")

create_order = capabilities[0]
make_payment = capabilities[1]
send_notification = capabilities[2]
cancel_cart = capabilities[3]

compatibility_results = []

for first, second in [
    (create_order, make_payment),
    (create_order, cancel_cart),
    (make_payment, send_notification),
]:
    score = check_compatibility(first, second)
    result = "COMPATIBLE" if score == 1.0 else "INCOMPATIBLE"

    print(
        f"{first['name']} -> {second['name']}: "
        f"{score:.2f} ({result})"
    )

    compatibility_results.append({
        "First": first["name"],
        "Second": second["name"],
        "Compatibility": score,
        "Result": result
    })

pd.DataFrame(compatibility_results).to_csv(
    f"{results_dir}/compatibility_results.csv",
    index=False
)


# Experiment 2: Capability composition
print("\nEXPERIMENT 2: COMPOSITION")

composite = compose([
    create_order,
    make_payment,
    send_notification
])

print("Composite:", composite["name"])
print("Preconditions:", composite["preconditions"])
print("Effects:", composite["effects"])
print("Total cost:", round(composite["cost"], 4))
print("Combined reliability:", round(composite["reliability"], 4))

composite_vector = embedding.encode_capability(composite)
print("Composite vector dimensions:", len(composite_vector))


# Experiment 3: Alternative implementations
print("\nEXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS")

implementations = [
    {
        "name": "CreateOrderAPI",
        "type": "API",
        "inputs": ["cart_id"],
        "outputs": ["order_id"],
        "preconditions": {"Cart.exists": True},
        "effects": {"Order.exists": True},
        "resources": ["NETWORK"],
        "cost": 0.01,
        "reliability": 0.99,
        "availability": 1
    },
    {
        "name": "CreateOrderDatabase",
        "type": "DATABASE",
        "inputs": ["cart_id"],
        "outputs": ["order_id"],
        "preconditions": {"Cart.exists": True},
        "effects": {"Order.exists": True},
        "resources": ["DATABASE"],
        "cost": 0.02,
        "reliability": 0.98,
        "availability": 1
    },
    {
        "name": "CreateOrderGUI",
        "type": "GUI",
        "inputs": ["cart_id"],
        "outputs": ["order_id"],
        "preconditions": {"Cart.exists": True},
        "effects": {"Order.exists": True},
        "resources": ["NETWORK"],
        "cost": 0.03,
        "reliability": 0.97,
        "availability": 1
    }
]

alternative_results = []

for i in range(len(implementations)):
    for j in range(i + 1, len(implementations)):
        a = implementations[i]
        b = implementations[j]

        score = embedding.similarity(
            embedding.encode_capability(a),
            embedding.encode_capability(b)
        )

        print(f"{a['name']} vs {b['name']}: {score:.4f}")

        alternative_results.append({
            "Capability A": a["name"],
            "Capability B": b["name"],
            "Similarity": score
        })

pd.DataFrame(alternative_results).to_csv(
    f"{results_dir}/alternative_implementations.csv",
    index=False
)


# Experiment 4: Goal relevance
print("\nEXPERIMENT 4: GOAL RELEVANCE")

goal = {
    "Order.exists": True,
    "Payment.status": "SUCCESS",
    "Notification.sent": True
}

relevance_results = []

for capability in capabilities:
    effects = capability.get("effects", {})

    matched = [
        key for key, value in effects.items()
        if key in goal and goal[key] == value
    ]

    relevant = len(matched) > 0

    print(
        f"{capability['name']}: "
        f"{'RELEVANT' if relevant else 'IRRELEVANT'}"
    )

    relevance_results.append({
        "Capability": capability["name"],
        "Matched Goal Conditions": len(matched),
        "Relevant": relevant
    })

pd.DataFrame(relevance_results).to_csv(
    f"{results_dir}/goal_relevance.csv",
    index=False
)


# Experiment 5: Operational attributes
print("\nEXPERIMENT 5: OPERATIONAL ATTRIBUTES")

payment_a = {
    "name": "PaymentServiceA",
    "type": "API",
    "inputs": ["order_id", "amount"],
    "outputs": ["payment_id"],
    "preconditions": {"Order.exists": True},
    "effects": {"Payment.status": "SUCCESS"},
    "resources": ["PAYMENT_GATEWAY"],
    "cost": 0.10,
    "reliability": 0.99,
    "availability": 1
}

payment_b = {
    "name": "PaymentServiceB",
    "type": "API",
    "inputs": ["order_id", "amount"],
    "outputs": ["payment_id"],
    "preconditions": {"Order.exists": True},
    "effects": {"Payment.status": "SUCCESS"},
    "resources": ["PAYMENT_GATEWAY"],
    "cost": 0.02,
    "reliability": 0.90,
    "availability": 1
}

for service in [payment_a, payment_b]:
    print(
        f"{service['name']}: "
        f"cost={service['cost']}, "
        f"reliability={service['reliability']}, "
        f"availability={service['availability']}"
    )

pd.DataFrame([payment_a, payment_b]).to_csv(
    f"{results_dir}/operational_attributes.csv",
    index=False
)


# State and goal encoding
print("\nSTATE AND GOAL ENCODING")

initial_state = {
    "Cart.exists": True,
    "Cart.item_count": 3,
    "Order.exists": False,
    "Payment.status": "NOT_STARTED"
}

state_vector = embedding.encode_state(initial_state)
goal_vector = embedding.encode_goal(goal)

print("State vector dimensions:", len(state_vector))
print("Goal vector dimensions:", len(goal_vector))

print("\nRESULT FILES SAVED IN:", results_dir)
print("ALL FIVE EXPERIMENTS COMPLETED")
