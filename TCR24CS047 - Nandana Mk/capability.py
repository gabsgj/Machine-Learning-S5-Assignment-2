class Capability:
    def __init__(
        self,
        name,
        capability_type,
        inputs=None,
        outputs=None,
        preconditions=None,
        effects=None,
        constraints=None,
        resources=None,
        cost=None,
        reliability=1.0,
        availability=1,
        mechanism=None
    ):
        self.name = name
        self.capability_type = capability_type
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.preconditions = preconditions or {}
        self.effects = effects or {}
        self.constraints = constraints or []
        self.resources = resources or []
        self.cost = cost or {}
        self.reliability = reliability
        self.availability = availability
        self.mechanism = mechanism


    def __repr__(self):
        return f"Capability(name={self.name}, type={self.capability_type})"
