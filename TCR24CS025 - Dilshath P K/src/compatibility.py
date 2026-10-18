def check_compatibility(capability1, capability2):

    effects = capability1.get("effects", {})
    preconditions = capability2.get("preconditions", {})

    if not preconditions:
        return 1.0

    satisfied = 0

    for key, required_value in preconditions.items():

        if key in effects and effects[key] == required_value:
            satisfied += 1

    return satisfied / len(preconditions)