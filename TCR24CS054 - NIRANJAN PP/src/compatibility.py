from .model import Capability


def are_compatible(first: Capability, second: Capability) -> bool:
    """
    Check whether the effects of the first capability
    satisfy the preconditions of the second capability.
    """

    for key, required_value in second.preconditions.items():
        if key not in first.effects:
            return False

        if first.effects[key] != required_value:
            return False

    return True
