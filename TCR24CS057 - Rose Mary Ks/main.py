
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity


# --------------------------------------------------
# 1. PROJECT SETUP
# --------------------------------------------------

RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)


# --------------------------------------------------
# 2. DEFINE CAPABILITIES
# --------------------------------------------------

capabilities = {
    "CreateOrder": {
        "type": "transaction",
        "inputs": ["cart_items", "user_id"],
        "outputs": ["order_id"],
        "preconditions": {
            "user.authenticated": True,
            "cart.nonempty": True
        },
        "effects": {
            "order.exists": True,
            "cart.cleared": True
        },
        "resources": ["database", "order_service"],
        "latency": 120,
        "reliability": 0.99,
        "risk": 0.02,
        "cost": 2.0
    },

    "MakePayment": {
        "type": "transaction",
        "inputs": ["order_id", "payment_method"],
        "outputs": ["payment_id", "payment_status"],
        "preconditions": {
            "order.exists": True
        },
        "effects": {
            "payment.completed": True
        },
        "resources": ["payment_gateway", "database"],
        "latency": 250,
        "reliability": 0.98,
        "risk": 0.03,
        "cost": 3.0
    },

    "SendNotification": {
        "type": "communication",
        "inputs": ["user_id", "payment_status", "message"],
        "outputs": ["notification_sent"],
        "preconditions": {
            "payment.completed": True
        },
        "effects": {
            "notification.sent": True
        },
        "resources": ["notification_service"],
        "latency": 80,
        "reliability": 0.97,
        "risk": 0.01,
        "cost": 1.0
    },

    "CancelCart": {
        "type": "transaction",
        "inputs": ["user_id", "cart_id"],
        "outputs": ["cancellation_status"],
        "preconditions": {
            "cart.exists": True
        },
        "effects": {
            "cart.cancelled": True
        },
        "resources": ["database", "cart_service"],
        "latency": 100,
        "reliability": 0.96,
        "risk": 0.04,
        "cost": 1.5
    },

    "CreateOrderDB": {
        "type": "transaction",
        "inputs": ["cart_items", "user_id"],
        "outputs": ["order_id"],
        "preconditions": {
            "user.authenticated": True,
            "cart.nonempty": True
        },
        "effects": {
            "order.exists": True,
            "cart.cleared": True
        },
        "resources": ["database"],
        "latency": 150,
        "reliability": 0.98,
        "risk": 0.02,
        "cost": 1.5
    },

    "CreateOrderGUI": {
        "type": "transaction",
        "inputs": ["cart_items", "user_id"],
        "outputs": ["order_id"],
        "preconditions": {
            "user.authenticated": True,
            "cart.nonempty": True
        },
        "effects": {
            "order.exists": True,
            "cart.cleared": True
        },
        "resources": ["gui", "order_service"],
        "latency": 180,
        "reliability": 0.97,
        "risk": 0.03,
        "cost": 2.5
    },

    "RefundPayment": {
        "type": "transaction",
        "inputs": ["payment_id"],
        "outputs": ["refund_id"],
        "preconditions": {
            "payment.completed": True
        },
        "effects": {
            "payment.refunded": True
        },
        "resources": ["payment_gateway", "database"],
        "latency": 200,
        "reliability": 0.97,
        "risk": 0.04,
        "cost": 2.0
    },

    "TrackDelivery": {
        "type": "monitoring",
        "inputs": ["order_id"],
        "outputs": ["tracking_status"],
        "preconditions": {
            "order.exists": True
        },
        "effects": {
            "delivery.tracked": True
        },
        "resources": ["tracking_service"],
        "latency": 90,
        "reliability": 0.99,
        "risk": 0.01,
        "cost": 1.0
    }
}


# --------------------------------------------------
# 3. DEFINE INITIAL STATE AND GOAL
# --------------------------------------------------

initial_state = {
    "user.authenticated": True,
    "cart.nonempty": True,
    "cart.exists": True,
    "order.exists": False,
    "payment.completed": False,
    "notification.sent": False
}

# Data already available before executing capabilities
initial_data = {
    "cart_items",
    "user_id",
    "payment_method",
    "message",
    "cart_id"
}

# Desired final state
goal = {
    "order.exists": True,
    "payment.completed": True,
    "notification.sent": True
}


# --------------------------------------------------
# 4. CREATE THE FEATURE VOCABULARY
# --------------------------------------------------

# Every capability and goal will be represented
# using the same feature vocabulary.

feature_set = set()

for name, cap in capabilities.items():
    feature_set.add("type:" + cap["type"])

    for item in cap["inputs"]:
        feature_set.add("input:" + item)

    for item in cap["outputs"]:
        feature_set.add("output:" + item)

    for key, value in cap["preconditions"].items():
        feature_set.add(f"pre:{key}={value}")

    for key, value in cap["effects"].items():
        feature_set.add(f"effect:{key}={value}")

    for item in cap["resources"]:
        feature_set.add("resource:" + item)

# Goal features use the same effect-feature format.
for key, value in goal.items():
    feature_set.add(f"effect:{key}={value}")

FEATURES = sorted(feature_set)
FEATURE_INDEX = {feature: i for i, feature in enumerate(FEATURES)}


# --------------------------------------------------
# 5. ENCODE CAPABILITIES AND GOALS
# --------------------------------------------------

def multi_hot(feature_names):
    """
    Convert a list of feature names into a
    multi-hot numerical vector.
    """
    vector = np.zeros(len(FEATURES))

    for feature in feature_names:
        if feature in FEATURE_INDEX:
            vector[FEATURE_INDEX[feature]] = 1

    return vector


def encode_capability(cap):
    """
    Create a vector representation of a capability.
    """
    feature_names = []

    feature_names.append("type:" + cap["type"])

    for item in cap["inputs"]:
        feature_names.append("input:" + item)

    for item in cap["outputs"]:
        feature_names.append("output:" + item)

    for key, value in cap["preconditions"].items():
        feature_names.append(f"pre:{key}={value}")

    for key, value in cap["effects"].items():
        feature_names.append(f"effect:{key}={value}")

    for item in cap["resources"]:
        feature_names.append("resource:" + item)

    return multi_hot(feature_names)


def encode_goal(goal_state):
    """
    Encode the desired goal state in the
    same feature space as capability effects.
    """
    feature_names = [
        f"effect:{key}={value}"
        for key, value in goal_state.items()
    ]

    return multi_hot(feature_names)


# Generate embeddings for all capabilities.
embeddings = {
    name: encode_capability(cap)
    for name, cap in capabilities.items()
}

goal_embedding = encode_goal(goal)


# --------------------------------------------------
# 6. CALCULATE COSINE SIMILARITY
# --------------------------------------------------

def cosine_score(vector_a, vector_b):
    """
    Calculate cosine similarity between two vectors.
    """
    score = cosine_similarity(
        [vector_a],
        [vector_b]
    )[0][0]

    return float(score)


def goal_relevance(capability_name):
    """
    Measure how relevant a capability is
    to the requested goal.
    """
    return cosine_score(
        embeddings[capability_name],
        goal_embedding
    )


# --------------------------------------------------
# 7. CHECK CAPABILITY COMPATIBILITY
# --------------------------------------------------

def is_compatible(cap_a_name, cap_b_name):
    """
    Check whether the first capability can connect
    to the second capability.

    Compatibility is simplified to:
    1. An output-input data match, OR
    2. An effect-precondition match.
    """
    cap_a = capabilities[cap_a_name]
    cap_b = capabilities[cap_b_name]

    data_match = bool(
        set(cap_a["outputs"]) & set(cap_b["inputs"])
    )

    effect_match = any(
        key in cap_a["effects"]
        and cap_a["effects"][key] == value
        for key, value in cap_b["preconditions"].items()
    )

    return data_match or effect_match


# --------------------------------------------------
# 8. CHECK PRECONDITIONS AND APPLY CAPABILITIES
# --------------------------------------------------

def check_preconditions(capability, state):
    """
    Check whether all required state conditions
    are satisfied.
    """
    for key, required_value in capability["preconditions"].items():
        if state.get(key) != required_value:
            return False

    return True


def execute_sequence(sequence):
    """
    Execute a sequence using a simulated state
    and track the data produced by each capability.
    """
    state = initial_state.copy()
    available_data = initial_data.copy()
    execution_log = []

    for name in sequence:
        cap = capabilities[name]

        missing_inputs = [
            item for item in cap["inputs"]
            if item not in available_data
        ]

        if missing_inputs:
            execution_log.append({
                "capability": name,
                "success": False,
                "reason": "Missing inputs: " + ", ".join(missing_inputs)
            })
            return state, available_data, execution_log, False

        if not check_preconditions(cap, state):
            execution_log.append({
                "capability": name,
                "success": False,
                "reason": "Preconditions not satisfied"
            })
            return state, available_data, execution_log, False

        # Apply capability effects to the current state.
        state.update(cap["effects"])

        # Make capability outputs available to later steps.
        available_data.update(cap["outputs"])

        execution_log.append({
            "capability": name,
            "success": True,
            "reason": "Executed successfully"
        })

    return state, available_data, execution_log, True


def goal_satisfied(state, goal_state):
    """
    Check whether the final state satisfies
    every required goal condition.
    """
    return all(
        state.get(key) == value
        for key, value in goal_state.items()
    )


# --------------------------------------------------
# 9. COMPOSE CAPABILITIES
# --------------------------------------------------

def compose(sequence):
    """
    Create a simplified composite capability
    from an ordered list of capabilities.
    """
    combined_inputs = set()
    combined_outputs = set()
    combined_preconditions = {}
    combined_effects = {}
    combined_resources = set()

    previous_outputs = set()
    previous_effects = {}

    for name in sequence:
        cap = capabilities[name]

        # Inputs not produced by an earlier capability
        # become external inputs to the composition.
        for item in cap["inputs"]:
            if item not in previous_outputs:
                combined_inputs.add(item)

        # Preconditions already guaranteed by an
        # earlier effect do not need to be external.
        for key, value in cap["preconditions"].items():
            if previous_effects.get(key) != value:
                combined_preconditions[key] = value

        combined_outputs.update(cap["outputs"])
        combined_resources.update(cap["resources"])

        previous_outputs.update(cap["outputs"])
        previous_effects.update(cap["effects"])
        combined_effects.update(cap["effects"])

    total_latency = sum(
        capabilities[name]["latency"]
        for name in sequence
    )

    total_reliability = np.prod([
        capabilities[name]["reliability"]
        for name in sequence
    ])

    total_risk = 1 - np.prod([
        1 - capabilities[name]["risk"]
        for name in sequence
    ])

    total_cost = sum(
        capabilities[name]["cost"]
        for name in sequence
    )

    return {
        "sequence": sequence,
        "inputs": sorted(combined_inputs),
        "outputs": sorted(combined_outputs),
        "preconditions": combined_preconditions,
        "effects": combined_effects,
        "resources": sorted(combined_resources),
        "latency": total_latency,
        "reliability": float(total_reliability),
        "risk": float(total_risk),
        "cost": total_cost
    }


# --------------------------------------------------
# 10. EXPERIMENT 1: CAPABILITY COMPATIBILITY
# --------------------------------------------------

print("\nEXPERIMENT 1: CAPABILITY COMPATIBILITY")

compatibility_pairs = [
    ("CreateOrder", "MakePayment"),
    ("MakePayment", "SendNotification"),
    ("CreateOrder", "TrackDelivery"),
    ("CancelCart", "RefundPayment")
]

compatibility_results = []

for first, second in compatibility_pairs:
    result = is_compatible(first, second)

    compatibility_results.append({
        "Capability A": first,
        "Capability B": second,
        "Compatible": result
    })

    print(f"{first} -> {second}: {result}")


# --------------------------------------------------
# 11. EXPERIMENT 2: CAPABILITY COMPOSITION
# --------------------------------------------------

print("\nEXPERIMENT 2: CAPABILITY COMPOSITION")

sequence = [
    "CreateOrder",
    "MakePayment",
    "SendNotification"
]

composite = compose(sequence)

final_state, available_data, execution_log, executed = (
    execute_sequence(sequence)
)

print("\nSelected sequence:")
print(" -> ".join(sequence))

print("\nExecution log:")
for entry in execution_log:
    print(entry["capability"], ":", entry["reason"])

print("\nComposite capability:")
print(json.dumps(composite, indent=4))

print("\nFinal state:")
print(json.dumps(final_state, indent=4))

satisfied = goal_satisfied(final_state, goal)

print("\nGoal satisfied:", satisfied)


# --------------------------------------------------
# 12. EXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS
# --------------------------------------------------

print("\nEXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS")

alternatives = [
    "CreateOrder",
    "CreateOrderDB",
    "CreateOrderGUI"
]

alternative_results = []

for name in alternatives:
    score = goal_relevance(name)

    alternative_results.append({
        "Capability": name,
        "Goal Similarity": score
    })

    print(f"{name}: {score:.4f}")

alternative_df = pd.DataFrame(alternative_results)
alternative_df.to_csv(
    os.path.join(RESULTS_DIR, "alternative_implementations.csv"),
    index=False
)

plt.figure(figsize=(8, 5))
plt.bar(
    alternative_df["Capability"],
    alternative_df["Goal Similarity"]
)
plt.xlabel("Alternative Capability")
plt.ylabel("Cosine Similarity")
plt.title("Goal Relevance of Alternative Implementations")
plt.ylim(0, 1)
plt.tight_layout()
plt.savefig(
    os.path.join(RESULTS_DIR, "alternative_implementations.png")
)
plt.close()


# --------------------------------------------------
# 13. EXPERIMENT 4: RELEVANT AND IRRELEVANT CAPABILITIES
# --------------------------------------------------

print("\nEXPERIMENT 4: GOAL RELEVANCE")

relevance_results = []

for name in capabilities:
    score = goal_relevance(name)

    relevance_results.append({
        "Capability": name,
        "Goal Similarity": score
    })

    print(f"{name}: {score:.4f}")

relevance_df = pd.DataFrame(relevance_results)
relevance_df.to_csv(
    os.path.join(RESULTS_DIR, "goal_relevance.csv"),
    index=False
)

plt.figure(figsize=(10, 5))
plt.bar(
    relevance_df["Capability"],
    relevance_df["Goal Similarity"]
)
plt.xlabel("Capability")
plt.ylabel("Cosine Similarity")
plt.title("Capability Relevance to Goal")
plt.xticks(rotation=35, ha="right")
plt.ylim(0, 1)
plt.tight_layout()
plt.savefig(
    os.path.join(RESULTS_DIR, "goal_relevance.png")
)
plt.close()


# --------------------------------------------------
# 14. EXPERIMENT 5: OPERATIONAL ATTRIBUTES
# --------------------------------------------------

print("\nEXPERIMENT 5: OPERATIONAL ATTRIBUTES")

operational_results = []

for name, cap in capabilities.items():
    operational_results.append({
        "Capability": name,
        "Latency": cap["latency"],
        "Reliability": cap["reliability"],
        "Risk": cap["risk"],
        "Cost": cap["cost"]
    })

operational_df = pd.DataFrame(operational_results)

print(operational_df.to_string(index=False))

operational_df.to_csv(
    os.path.join(RESULTS_DIR, "operational_attributes.csv"),
    index=False
)

# Plot latency
plt.figure(figsize=(9, 5))
plt.bar(
    operational_df["Capability"],
    operational_df["Latency"]
)
plt.xlabel("Capability")
plt.ylabel("Latency (ms)")
plt.title("Capability Latency")
plt.xticks(rotation=35, ha="right")
plt.tight_layout()
plt.savefig(
    os.path.join(RESULTS_DIR, "capability_latency.png")
)
plt.close()

# Plot reliability
plt.figure(figsize=(9, 5))
plt.bar(
    operational_df["Capability"],
    operational_df["Reliability"]
)
plt.xlabel("Capability")
plt.ylabel("Reliability")
plt.title("Capability Reliability")
plt.ylim(0, 1.05)
plt.xticks(rotation=35, ha="right")
plt.tight_layout()
plt.savefig(
    os.path.join(RESULTS_DIR, "capability_reliability.png")
)
plt.close()


# --------------------------------------------------
# 15. SAVE ALL EMBEDDINGS
# --------------------------------------------------

embedding_results = {}

for name, vector in embeddings.items():
    embedding_results[name] = vector.tolist()

embedding_results["Goal"] = goal_embedding.tolist()

with open(
    os.path.join(RESULTS_DIR, "embeddings.json"),
    "w"
) as file:
    json.dump(embedding_results, file, indent=4)


# --------------------------------------------------
# 16. SAVE SUMMARY
# --------------------------------------------------

summary = {
    "feature_count": len(FEATURES),
    "capability_count": len(capabilities),
    "selected_sequence": sequence,
    "execution_successful": executed,
    "goal_satisfied": satisfied,
    "composite_capability": composite
}

with open(
    os.path.join(RESULTS_DIR, "summary.json"),
    "w"
) as file:
    json.dump(summary, file, indent=4)


# --------------------------------------------------
# 17. DISPLAY FINAL RESULTS
# --------------------------------------------------

print("\n" + "=" * 45)
print("FINAL RESULTS")
print("=" * 45)

print("Number of capabilities:", len(capabilities))
print("Embedding vector size:", len(FEATURES))
print("Execution successful:", executed)
print("Goal satisfied:", satisfied)

print("\nComposite latency:", composite["latency"], "ms")
print(
    "Composite reliability:",
    f'{composite["reliability"]:.4f}'
)
print(
    "Composite risk:",
    f'{composite["risk"]:.4f}'
)
print("Composite cost:", composite["cost"])

print("\nResults saved in the 'results' folder.")
print("Program completed.")