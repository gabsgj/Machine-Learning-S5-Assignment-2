def check_compatibility(capability1, capability2):

    for condition, required_value in capability2.preconditions.items():

        if condition not in capability1.effects:
            return False

        produced_value = capability1.effects[condition]

        if produced_value != required_value:
            return False

    return True


def compose(capabilities):

    if len(capabilities) == 0:
        return None

    for i in range(len(capabilities) - 1):

        current = capabilities[i]
        next_capability = capabilities[i + 1]

        if not check_compatibility(current, next_capability):
            return None

    composite = {
        "name": "CompositeCapability",
        "components": [c.name for c in capabilities],
        "preconditions": capabilities[0].preconditions.copy(),
        "effects": capabilities[-1].effects.copy(),
        "cost": sum(c.cost for c in capabilities),
        "reliability": multiply_reliability(capabilities),
        "availability": min(c.availability for c in capabilities)
    }

    return composite


def multiply_reliability(capabilities):

    result = 1.0

    for capability in capabilities:
        result *= capability.reliability

    return result