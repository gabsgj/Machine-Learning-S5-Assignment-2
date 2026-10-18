from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from capability_embedding import Capability, CapabilityEmbedding, load_dataset


def main():
    data = load_dataset(ROOT / "capabilities.json")
    encoder = CapabilityEmbedding()
    capabilities = {
        item["name"]: Capability.from_dict(item)
        for item in data["capabilities"]
    }

    c1 = capabilities["C1_CreateOrder"]
    c2 = capabilities["C2_MakePayment"]
    c3 = capabilities["C3_CancelCart"]
    c3_chain = capabilities["C3_SendNotification"]

    print("=" * 70)
    print("ASSIGNMENT 2: VECTOR EMBEDDING FOR CAPABILITY COMPOSITION")
    print("=" * 70)

    print("\n1. CAPABILITY COMPATIBILITY")
    score12 = encoder.compatibility(c1, c2)
    score13 = encoder.compatibility(c1, c3)

    print("C1 = CreateOrder")
    print("C2 = MakePayment")
    print("C3 = CancelCart")
    print(f"C1 -> C2 compatibility = {score12:.3f}")
    print(f"C1 -> C3 compatibility = {score13:.3f}")
    print("Expected: C1 -> C2 compatible; C1 -> C3 incompatible.")
    print("Result:", "PASS" if score12 == 1.0 and score13 == 0.0 else "CHECK")

    print("\n2. CAPABILITY COMPOSITION")
    # Build the three-step composite capability.
    composite = encoder.compose([c1, c2, c3_chain])

    vector1 = encoder.encode_capability(c1)
    vector2 = encoder.encode_capability(c2)
    vector3 = encoder.encode_capability(c3_chain)
    vector_composite = encoder.encode_capability(composite)

    print("C1_CreateOrder -> C2_MakePayment -> C3_SendNotification")
    print("Composite:", composite.name)
    print(f"Similarity(composite, C1) = {encoder.similarity(vector_composite, vector1):.3f}")
    print(f"Similarity(composite, C2) = {encoder.similarity(vector_composite, vector2):.3f}")
    print(f"Similarity(composite, C3) = {encoder.similarity(vector_composite, vector3):.3f}")
    print(f"Composite reliability = {composite.reliability:.4f}")
    print(f"Composite availability = {composite.availability}")

    print("\n3. ALTERNATIVE IMPLEMENTATIONS")
    print(
        f"CreateOrder(API) vs CreateOrderDB = "
        f"{encoder.similarity(vector1, encoder.encode_capability(capabilities['CreateOrderDB'])):.3f}"
    )
    print(
        f"CreateOrder(API) vs CreateOrderGUI = "
        f"{encoder.similarity(vector1, encoder.encode_capability(capabilities['CreateOrderGUI'])):.3f}"
    )

    print("\n4. IRRELEVANT CAPABILITIES")
    goal = data["application"]["goal"]

    def goal_relevance(capability):
        matched = 0
        for key, value in goal.items():
            condition = f"{key}={value}"
            if any(encoder.satisfies(effect, condition) for effect in capability.effects):
                matched += 1
        return matched / len(goal)

    print(f"Goal relevance(CreateOrder) = {goal_relevance(c1):.3f}")
    print(f"Goal relevance(MakePayment) = {goal_relevance(c2):.3f}")
    print(
        f"Goal relevance(UpdateInventory) = "
        f"{goal_relevance(capabilities['UpdateInventory']):.3f}"
    )

    print("\n5. OPERATIONAL ATTRIBUTES")
    database_capability = capabilities["CreateOrderDB"]

    alternative = Capability.from_dict({
        **database_capability.__dict__,
        "name": "CreateOrderDB_LowReliability",
        "reliability": 0.70,
        "cost": {
            **database_capability.cost,
            "time": 0.50,
            "risk": 0.50
        }
    })

    original_vector = encoder.encode_capability(database_capability)
    alternative_vector = encoder.encode_capability(alternative)

    print(f"Original reliability = {database_capability.reliability:.2f}")
    print(f"Alternative reliability = {alternative.reliability:.2f}")
    print(f"Original execution time = {database_capability.cost['time']:.2f}")
    print(f"Alternative execution time = {alternative.cost['time']:.2f}")
    print(f"Original risk = {database_capability.cost['risk']:.2f}")
    print(f"Alternative risk = {alternative.cost['risk']:.2f}")
    print(f"Vector similarity = {encoder.similarity(original_vector, alternative_vector):.3f}")

    print("\n6. ENCODING INTERFACE")
    state_vector = encoder.encode_state(data["application"]["initial_state"])
    goal_vector = encoder.encode_goal(data["application"]["goal"])
    capability_vector = encoder.encode_capability(c1)

    print("encode(state) shape =", state_vector.shape)
    print("encode(goal) shape =", goal_vector.shape)
    print("encode(capability) shape =", capability_vector.shape)


if __name__ == "__main__":
    main()
