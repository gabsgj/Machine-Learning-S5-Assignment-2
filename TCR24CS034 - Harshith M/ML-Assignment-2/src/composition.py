from .models import Capability
from .compatibility import is_compatible


def _product(values):

    result = 1.0

    for value in values:
        result *= float(value)

    return result


def compose(capabilities):

    if not capabilities:

        raise ValueError(
            "At least one capability is required."
        )

    # ---------------------------------------------------------
    # Check every adjacent capability
    # ---------------------------------------------------------

    for first, second in zip(
        capabilities,
        capabilities[1:]
    ):

        if not is_compatible(
            first,
            second
        ):

            raise ValueError(
                f"Incompatible composition: "
                f"{first.name} -> {second.name}"
            )

    # ---------------------------------------------------------
    # First and last capabilities
    # ---------------------------------------------------------

    first = capabilities[0]
    last = capabilities[-1]

    # ---------------------------------------------------------
    # Construct composite capability
    # ---------------------------------------------------------

    composite = Capability(

        name=" -> ".join(
            capability.name
            for capability in capabilities
        ),

        capability_type="COMPOSITE",

        # Initial inputs come from first capability
        inputs=first.inputs.copy(),

        # Final outputs come from last capability
        outputs=last.outputs.copy(),

        # Initial preconditions
        preconditions=first.preconditions.copy(),

        # Final effects
        effects=last.effects.copy(),

        # Combine constraints
        constraints=[
            constraint
            for capability in capabilities
            for constraint in capability.constraints
        ],

        # Combine resources
        resources=sorted(
            set(
                resource
                for capability in capabilities
                for resource in capability.resources
            )
        ),

        # Sequential execution costs
        cost_time=sum(
            capability.cost_time
            for capability in capabilities
        ),

        cost_resource=sum(
            capability.cost_resource
            for capability in capabilities
        ),

        cost_money=sum(
            capability.cost_money
            for capability in capabilities
        ),

        # Accumulated risk, limited to 1
        risk=min(
            1.0,
            sum(
                capability.risk
                for capability in capabilities
            )
        ),

        # Probability of all steps succeeding
        reliability=_product(
            capability.reliability
            for capability in capabilities
        ),

        # Probability all required services are available
        availability=_product(
            capability.availability
            for capability in capabilities
        ),

        execution={
            "composition": [
                capability.name
                for capability in capabilities
            ],
            "mechanism": "sequential_composition"
        },

        components=[
            capability.name
            for capability in capabilities
        ],

        component_types=[
            capability.capability_type
            for capability in capabilities
        ]
    )

    return composite