from typing import List

from .model import Capability
from .compatibility import are_compatible


def compose_capabilities(capabilities: List[Capability]) -> Capability:
    """
    Compose a sequence of compatible capabilities into one
    composite capability.
    """

    if not capabilities:
        raise ValueError("At least one capability is required.")

    # Check that every capability can follow the previous one.
    for first, second in zip(capabilities, capabilities[1:]):
        if not are_compatible(first, second):
            raise ValueError(
                f"Cannot compose '{first.name}' with '{second.name}'."
            )

    first = capabilities[0]
    last = capabilities[-1]

    # Combined preconditions come from the first capability.
    combined_preconditions = dict(first.preconditions)

    # Combined effects come from the last capability and
    # accumulated effects from the sequence.
    combined_effects = {}

    for capability in capabilities:
        combined_effects.update(capability.effects)

    # Combine inputs, outputs, constraints and resources.
    combined_inputs = set()

    for capability in capabilities:
        combined_inputs.update(capability.inputs)

    combined_outputs = set(last.outputs)

    combined_constraints = set()

    for capability in capabilities:
        combined_constraints.update(capability.constraints)

    combined_resources = set()

    for capability in capabilities:
        combined_resources.update(capability.resources)

    # Total cost is the sum of individual costs.
    total_cost = sum(capability.cost for capability in capabilities)

    # For a sequence of operations, cumulative reliability
    # is the product of individual reliabilities.
    cumulative_reliability = 1.0

    for capability in capabilities:
        cumulative_reliability *= capability.reliability

    # A composite capability is available only when every
    # component capability is available.
    composite_availability = min(
        capability.availability for capability in capabilities
    )

    name = " -> ".join(capability.name for capability in capabilities)

    return Capability(
        name=name,
        preconditions=combined_preconditions,
        effects=combined_effects,
        inputs=combined_inputs,
        outputs=combined_outputs,
        constraints=combined_constraints,
        resources=combined_resources,
        cost=total_cost,
        reliability=cumulative_reliability,
        availability=composite_availability,
    )
