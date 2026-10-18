def compose(capabilities):

    if not capabilities:
        return None

    first = capabilities[0]
    last = capabilities[-1]

    composite = {
        "name": "Composite_" + "_".join(
            capability["name"] for capability in capabilities
        ),

        "type": "COMPOSITE",

        "preconditions": first.get(
            "preconditions", {}
        ),

        "effects": last.get(
            "effects", {}
        ),

        "inputs": first.get(
            "inputs", []
        ),

        "outputs": last.get(
            "outputs", []
        ),

        "resources": [],

        "cost": 0,

        "reliability": 1,

        "availability": 1
    }

    # Combine resources
    for capability in capabilities:
        for resource in capability.get("resources", []):

            if resource not in composite["resources"]:
                composite["resources"].append(resource)

    # Total cost
    composite["cost"] = sum(
        capability.get("cost", 0)
        for capability in capabilities
    )

    # Overall reliability
    for capability in capabilities:
        composite["reliability"] *= capability.get(
            "reliability", 1
        )

    # Overall availability
    for capability in capabilities:
        composite["availability"] *= capability.get(
            "availability", 1
        )

    return composite