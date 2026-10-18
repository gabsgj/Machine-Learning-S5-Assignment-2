from typing import Dict, List

from models import Capability, CompositeCapability


def compose_capabilities(
    first: Capability,
    second: Capability
) -> CompositeCapability:

    """
    Sequential composition:

        first -> second

    The result represents:

        second ◦ first
    """

    # Preconditions already established by the first capability
    # do not need to remain external preconditions.
    combined_preconditions: Dict[str, object] = dict(
        first.preconditions
    )

    for variable, required_value in second.preconditions.items():

        first_effect_value = first.effects.get(variable)

        if first_effect_value == required_value:
            # The first capability establishes this condition.
            continue

        combined_preconditions[variable] = required_value

    # Start with first effects, then apply second effects.
    combined_effects: Dict[str, object] = dict(first.effects)
    combined_effects.update(second.effects)

    # Inputs required from outside the composition.
    combined_inputs = list(first.inputs)

    for input_spec in second.inputs:
        if input_spec not in combined_inputs:
            combined_inputs.append(input_spec)

    # Outputs produced by the final capability.
    combined_outputs = list(second.outputs)

    # Combine resources.
    combined_resources: List[str] = []

    for resource in first.resources + second.resources:
        if resource not in combined_resources:
            combined_resources.append(resource)

    return CompositeCapability(
        id=f"{first.id}_THEN_{second.id}",
        name=f"{first.name} -> {second.name}",
        components=[first.id, second.id],

        preconditions=combined_preconditions,
        effects=combined_effects,

        inputs=combined_inputs,
        outputs=combined_outputs,

        resources=combined_resources,

        time_cost=first.time_cost + second.time_cost,
        money_cost=first.money_cost + second.money_cost,
        resource_cost=first.resource_cost + second.resource_cost,

        # A simple sequential risk aggregation.
        risk=1.0 - (
            (1.0 - first.risk)
            * (1.0 - second.risk)
        ),

        # Independent success probabilities multiply.
        reliability=(
            first.reliability * second.reliability
        ),

        available=(
            first.available and second.available
        )
    )


def compose_chain(
    capabilities: List[Capability]
) -> CompositeCapability:

    if not capabilities:
        raise ValueError("Cannot compose an empty capability list.")

    if len(capabilities) == 1:
        c = capabilities[0]

        return CompositeCapability(
            id=c.id,
            name=c.name,
            components=[c.id],
            preconditions=dict(c.preconditions),
            effects=dict(c.effects),
            inputs=list(c.inputs),
            outputs=list(c.outputs),
            resources=list(c.resources),
            time_cost=c.time_cost,
            money_cost=c.money_cost,
            resource_cost=c.resource_cost,
            risk=c.risk,
            reliability=c.reliability,
            available=c.available,
        )

    result = compose_capabilities(
        capabilities[0],
        capabilities[1]
    )

    for capability in capabilities[2:]:

        intermediate = Capability(
            id=result.id,
            name=result.name,
            description="Composite capability",
            type="COMPOSITE",
            mechanism="Sequential composition",

            inputs=result.inputs,
            outputs=result.outputs,

            preconditions=result.preconditions,
            effects=result.effects,

            resources=result.resources,

            time_cost=result.time_cost,
            money_cost=result.money_cost,
            resource_cost=result.resource_cost,
            risk=result.risk,

            reliability=result.reliability,
            available=result.available,
        )

        result = compose_capabilities(
            intermediate,
            capability
        )

    return result