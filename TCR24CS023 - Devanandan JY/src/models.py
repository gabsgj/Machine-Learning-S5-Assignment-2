import numpy as np

class ApplicationState:
    def __init__(self, variables: dict):
        self.variables = variables

class Capability:
    def __init__(self, name: str, type_val: str, preconditions: dict, effects: dict, 
                 latency: float = 0.0, cost: float = 0.0, reliability: float = 1.0):
        self.name = name
        self.type = type_val
        self.preconditions = preconditions
        self.effects = effects
        self.latency = latency
        self.cost = cost
        # Bound reliability to prevent log(0)
        self.reliability = max(min(reliability, 1.0), 1e-6)