from .models import Capability


def _condition_satisfied(
    effect_value,
    required_value
):

    """
    Exact symbolic matching.

    Example:

    Effect:
        Order.exists = True

    Precondition:
        Order.exists = True

    Result:
        compatible
    """

    return effect_value == required_value


# =============================================================
# PRECONDITION -> EFFECT COMPATIBILITY
# =============================================================

def check_precondition_effect_compatibility(
    first: Capability,
    second: Capability
):

    # If second has no preconditions,
    # there is no precondition dependency.
    if not second.preconditions:
        return 1.0

    matched = 0

    for key, required_value in second.preconditions.items():

        if key in first.effects:

            actual_value = first.effects[key]

            if _condition_satisfied(
                actual_value,
                required_value
            ):

                matched += 1

    return (
        matched
        / len(second.preconditions)
    )


# =============================================================
# OUTPUT -> INPUT COMPATIBILITY
# =============================================================

def check_output_input_compatibility(
    first: Capability,
    second: Capability
):

    if not second.inputs:
        return 1.0

    matched = 0

    for input_name, input_spec in second.inputs.items():

        input_type = None

        if isinstance(input_spec, dict):

            input_type = input_spec.get(
                "type"
            )

        found = False

        for output_name, output_spec in first.outputs.items():

            output_type = None

            if isinstance(output_spec, dict):

                output_type = output_spec.get(
                    "type"
                )

            # Match by name
            if output_name == input_name:

                found = True
                break

            # Or match by data type
            if (
                input_type
                and input_type == output_type
            ):

                found = True
                break

        if found:
            matched += 1

    return (
        matched
        / len(second.inputs)
    )


# =============================================================
# OVERALL COMPATIBILITY SCORE
# =============================================================

def compatibility_score(
    first: Capability,
    second: Capability
):

    precondition_score = (
        check_precondition_effect_compatibility(
            first,
            second
        )
    )

    input_output_score = (
        check_output_input_compatibility(
            first,
            second
        )
    )

    # Preconditions/effects are slightly more important.
    return float(
        0.60 * precondition_score
        + 0.40 * input_output_score
    )


# =============================================================
# COMPATIBILITY DECISION
# =============================================================

def is_compatible(
    first: Capability,
    second: Capability,
    threshold=0.50
):

    score = compatibility_score(
        first,
        second
    )

    return score >= threshold