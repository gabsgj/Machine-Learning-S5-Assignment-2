from dataclasses import replace
from typing import List

from models import Capability
from embedding import EmbeddingModel
from composition import compose_chain


def get_capability(
    capabilities: List[Capability],
    capability_id: str
) -> Capability:

    for capability in capabilities:
        if capability.id == capability_id:
            return capability

    raise ValueError(
        f"Capability '{capability_id}' was not found."
    )


# -------------------------------------------------------------
# Experiment 1
# -------------------------------------------------------------

def experiment_1_compatibility(
    model: EmbeddingModel,
    capabilities: List[Capability]
):

    print("\n" + "=" * 70)
    print("EXPERIMENT 1: CAPABILITY COMPATIBILITY")
    print("=" * 70)

    c1 = get_capability(
        capabilities,
        "CreateOrder"
    )

    c2 = get_capability(
        capabilities,
        "MakePayment_API"
    )

    c3 = get_capability(
        capabilities,
        "CancelCart"
    )

    pairs = [
        (c1, c2),
        (c1, c3),
    ]

    for first, second in pairs:

        compatibility = model.compatibility(
            first,
            second
        )

        precondition_score = (
            model.precondition_effect_compatibility(
                first,
                second
            )
        )

        io_score = (
            model.input_output_compatibility(
                first,
                second
            )
        )

        dependency = model.dependency_score(
            first,
            second
        )

        similarity = model.similarity(
            first,
            second
        )

        print(f"\n{first.id} -> {second.id}")
        print(
            f"  Vector similarity:       {similarity:.4f}"
        )
        print(
            f"  Precondition/effect:     "
            f"{precondition_score:.4f}"
        )
        print(
            f"  Input/output:            "
            f"{io_score:.4f}"
        )
        print(
            f"  Dependency score:        "
            f"{dependency:.4f}"
        )
        print(
            f"  Compatibility score:     "
            f"{compatibility:.4f}"
        )


# -------------------------------------------------------------
# Experiment 2
# -------------------------------------------------------------

def experiment_2_composition(
    model: EmbeddingModel,
    capabilities: List[Capability]
):

    print("\n" + "=" * 70)
    print("EXPERIMENT 2: CAPABILITY COMPOSITION")
    print("=" * 70)

    c1 = get_capability(
        capabilities,
        "CreateOrder"
    )

    c2 = get_capability(
        capabilities,
        "MakePayment_API"
    )

    c3 = get_capability(
        capabilities,
        "SendNotification"
    )

    compatibility_12 = model.compatibility(
        c1,
        c2
    )

    compatibility_23 = model.compatibility(
        c2,
        c3
    )

    print("\nCompatibility chain:")

    print(
        f"  {c1.id} -> {c2.id}: "
        f"{compatibility_12:.4f}"
    )

    print(
        f"  {c2.id} -> {c3.id}: "
        f"{compatibility_23:.4f}"
    )

    composite = compose_chain(
        [c1, c2, c3]
    )

    composite_vector = model.encode_capability(
        Capability(
            id=composite.id,
            name=composite.name,
            description="Composite capability",
            type="COMPOSITE",
            mechanism="Sequential composition",
            inputs=composite.inputs,
            outputs=composite.outputs,
            preconditions=composite.preconditions,
            effects=composite.effects,
            resources=composite.resources,
            time_cost=composite.time_cost,
            money_cost=composite.money_cost,
            resource_cost=composite.resource_cost,
            risk=composite.risk,
            reliability=composite.reliability,
            available=composite.available,
        )
    )

    print("\nComposite capability:")

    print(
        f"  Name:          {composite.name}"
    )

    print(
        f"  Components:    "
        f"{' -> '.join(composite.components)}"
    )

    print(
        f"  Preconditions: "
        f"{composite.preconditions}"
    )

    print(
        f"  Effects:       "
        f"{composite.effects}"
    )

    print(
        f"  Time cost:     "
        f"{composite.time_cost:.2f} ms"
    )

    print(
        f"  Money cost:    "
        f"{composite.money_cost:.4f}"
    )

    print(
        f"  Reliability:   "
        f"{composite.reliability:.6f}"
    )

    print(
        f"  Vector size:   "
        f"{len(composite_vector)}"
    )


# -------------------------------------------------------------
# Experiment 3
# -------------------------------------------------------------

def experiment_3_alternative_implementations(
    model: EmbeddingModel,
    capabilities: List[Capability]
):

    print("\n" + "=" * 70)
    print("EXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS")
    print("=" * 70)

    api = get_capability(
        capabilities,
        "MakePayment_API"
    )

    database = get_capability(
        capabilities,
        "MakePayment_DB"
    )

    gui = get_capability(
        capabilities,
        "MakePayment_GUI"
    )

    alternatives = [
        api,
        database,
        gui
    ]

    print("\nPairwise similarities:")

    for i in range(len(alternatives)):

        for j in range(i + 1, len(alternatives)):

            first = alternatives[i]
            second = alternatives[j]

            similarity = model.similarity(
                first,
                second
            )

            compatibility = model.compatibility(
                first,
                second
            )

            print(
                f"  {first.id} <-> {second.id}: "
                f"similarity={similarity:.4f}, "
                f"compatibility={compatibility:.4f}"
            )

    print(
        "\nThe experiment checks whether:"
    )

    print(
        "  - functionally equivalent capabilities "
        "remain close"
    )

    print(
        "  - implementation mechanisms remain "
        "distinguishable"
    )


# -------------------------------------------------------------
# Experiment 4
# -------------------------------------------------------------

def experiment_4_irrelevant_capabilities(
    model: EmbeddingModel,
    capabilities: List[Capability]
):

    print("\n" + "=" * 70)
    print("EXPERIMENT 4: IRRELEVANT CAPABILITIES")
    print("=" * 70)

    reference = get_capability(
        capabilities,
        "MakePayment_API"
    )

    irrelevant_ids = [
        "BrowseCatalog",
        "UpdateWishlist",
        "CancelCart",
    ]

    print(
        "\nReference capability:",
        reference.id
    )

    for capability_id in irrelevant_ids:

        capability = get_capability(
            capabilities,
            capability_id
        )

        similarity = model.similarity(
            reference,
            capability
        )

        compatibility = model.compatibility(
            reference,
            capability
        )

        dependency = model.dependency_score(
            reference,
            capability
        )

        print(
            f"\n  {capability.id}"
        )

        print(
            f"    similarity:    "
            f"{similarity:.4f}"
        )

        print(
            f"    compatibility: "
            f"{compatibility:.4f}"
        )

        print(
            f"    dependency:    "
            f"{dependency:.4f}"
        )


# -------------------------------------------------------------
# Experiment 5
# -------------------------------------------------------------

def experiment_5_operational_attributes(
    model: EmbeddingModel,
    capabilities: List[Capability]
):

    print("\n" + "=" * 70)
    print("EXPERIMENT 5: OPERATIONAL ATTRIBUTES")
    print("=" * 70)

    api = get_capability(
        capabilities,
        "MakePayment_API"
    )

    database = get_capability(
        capabilities,
        "MakePayment_DB"
    )

    gui = get_capability(
        capabilities,
        "MakePayment_GUI"
    )

    implementations = [
        api,
        database,
        gui,
    ]

    print("\nOperational properties:")

    for capability in implementations:

        print(f"\n{capability.id}")

        print(
            f"  Type:         {capability.type}"
        )

        print(
            f"  Time:         "
            f"{capability.time_cost} ms"
        )

        print(
            f"  Money:        "
            f"{capability.money_cost}"
        )

        print(
            f"  Resource:     "
            f"{capability.resource_cost}"
        )

        print(
            f"  Risk:         "
            f"{capability.risk}"
        )

        print(
            f"  Reliability:  "
            f"{capability.reliability}"
        )

    # ---------------------------------------------------------
    # Controlled experiment
    #
    # Keep the functionality exactly the same and change only
    # operational attributes.
    # ---------------------------------------------------------

    print(
        "\nControlled operational-attribute experiment:"
    )

    cheap_fast = replace(
        api,
        id="API_CheapFast",
        time_cost=20.0,
        money_cost=0.001,
        resource_cost=1.0,
        risk=0.001,
        reliability=0.999
    )

    expensive_slow = replace(
        api,
        id="API_ExpensiveSlow",
        time_cost=1000.0,
        money_cost=1.0,
        resource_cost=10.0,
        risk=0.5,
        reliability=0.5
    )

    print(
        "\nSame functional capability, "
        "different operational properties:"
    )

    print(
        f"  Original -> Cheap/Fast: "
        f"{model.similarity(api, cheap_fast):.6f}"
    )

    print(
        f"  Original -> Expensive/Slow: "
        f"{model.similarity(api, expensive_slow):.6f}"
    )

    print(
        f"  Cheap/Fast -> Expensive/Slow: "
        f"{model.similarity(cheap_fast, expensive_slow):.6f}"
    )

    print(
        "\nOperational vectors:"
    )

    original_vector = model.encode_capability(api)
    cheap_vector = model.encode_capability(cheap_fast)
    expensive_vector = model.encode_capability(
        expensive_slow
    )

    # Last five dimensions are the operational attributes.
    original_ops = original_vector[-5:]
    cheap_ops = cheap_vector[-5:]
    expensive_ops = expensive_vector[-5:]

    print(
        f"  Original:       {original_ops}"
    )

    print(
        f"  Cheap/Fast:     {cheap_ops}"
    )

    print(
        f"  Expensive/Slow: {expensive_ops}"
    )

    print(
        "\nThe functional fields remain unchanged while "
        "the operational dimensions change."
    )


# -------------------------------------------------------------
# Run all experiments
# -------------------------------------------------------------

def run_all_experiments(
    model: EmbeddingModel,
    capabilities: List[Capability]
):

    experiment_1_compatibility(
        model,
        capabilities
    )

    experiment_2_composition(
        model,
        capabilities
    )

    experiment_3_alternative_implementations(
        model,
        capabilities
    )

    experiment_4_irrelevant_capabilities(
        model,
        capabilities
    )

    experiment_5_operational_attributes(
        model,
        capabilities
    )