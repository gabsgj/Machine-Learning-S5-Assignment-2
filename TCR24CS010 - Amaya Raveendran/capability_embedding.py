import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

VECTOR_DIM = 128
COST_KEYS = ["time", "resource", "money", "risk", "energy"]
COST_MAX = {"time": 1, "resource": 10, "money": 1, "risk": 1, "energy": 10}


def norm(x):
    return str(x).strip().lower().replace(" ", "_")


def index(feature, dim=VECTOR_DIM):
    return int.from_bytes(hashlib.sha256(feature.encode()).digest()[:8], "big") % dim


def add_feature(vector, feature, value=1.0):
    sign = 1.0 if hashlib.sha256((feature + "#sign").encode()).digest()[0] % 2 == 0 else -1.0
    vector[index(feature)] += sign * value


@dataclass
class Capability:
    name: str
    type: str
    mechanism: Dict[str, Any]
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    preconditions: List[str]
    effects: List[str]
    constraints: List[str]
    resources: List[str]
    cost: Dict[str, float]
    reliability: float
    availability: int = 1
    components: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class CapabilityEmbedding:
    # Convert the formal capability information into a fixed-size vector.

    def __init__(self, dim=VECTOR_DIM):
        self.dim = dim

    def normalize(self, vector):
        n = np.linalg.norm(vector)
        return vector if n == 0 else vector / n

    def encode_state(self, state):
        vector = np.zeros(self.dim)
        for key, value in state.items():
            add_feature(vector, f"state:{norm(key)}={norm(value)}")
        return self.normalize(vector)

    def encode_goal(self, goal):
        vector = np.zeros(self.dim)
        for key, value in goal.items():
            add_feature(vector, f"goal:{norm(key)}={norm(value)}")
        return self.normalize(vector)

    def encode_capability(self, capability):
        vector = np.zeros(self.dim)

        add_feature(vector, f"type:{norm(capability.type)}")

        for key, value in capability.mechanism.items():
            add_feature(vector, f"mechanism:{norm(key)}={norm(value)}")

        for item in capability.inputs:
            add_feature(vector, "input:" + norm(json.dumps(item, sort_keys=True)))

        for item in capability.outputs:
            add_feature(vector, "output:" + norm(json.dumps(item, sort_keys=True)))

        for group, values in [
            ("precondition", capability.preconditions),
            ("effect", capability.effects),
            ("constraint", capability.constraints),
            ("resource", capability.resources)
        ]:
            for value in values:
                add_feature(vector, f"{group}:{norm(value)}")

        operational = [
            capability.cost.get("time", 0) / COST_MAX["time"],
            capability.cost.get("resource", 0) / COST_MAX["resource"],
            capability.cost.get("money", 0) / COST_MAX["money"],
            capability.cost.get("risk", 0) / COST_MAX["risk"],
            capability.cost.get("energy", 0) / COST_MAX["energy"],
            capability.reliability,
            float(capability.availability),
            min(1.0, len(capability.components) / 10)
        ]

        vector[-8:] = np.clip(operational, 0, 1)
        return self.normalize(vector)

    @staticmethod
    def similarity(x, y):
        nx, ny = np.linalg.norm(x), np.linalg.norm(y)
        if nx == 0 or ny == 0:
            return 0.0
        return float(np.dot(x, y) / (nx * ny))

    @staticmethod
    def parse(condition):
        for operator in ["<=", ">=", "!=", "=", "<", ">"]:
            if operator in condition:
                left, right = condition.split(operator, 1)
                return norm(left), norm(right)
        return norm(condition), ""

    @classmethod
    def satisfies(cls, effect, precondition):
        effect_key, effect_value = cls.parse(effect)
        pre_key, pre_value = cls.parse(precondition)

        if effect_key != pre_key:
            return False
        if effect_value == pre_value:
            return True
        if pre_value == "true" and effect_value in {"true", "1"}:
            return True
        return False

    def effect_precondition_score(self, first, second):
        if not second.preconditions:
            return 1.0

        matched = sum(
            any(self.satisfies(effect, precondition) for effect in first.effects)
            for precondition in second.preconditions
        )
        return matched / len(second.preconditions)

    def input_output_score(self, first, second):
        if not second.inputs:
            return 1.0

        matched = 0

        for item in second.inputs:
            item_type = norm(item.get("type", ""))
            item_name = norm(item.get("name", ""))

            if any(
                item_type == norm(output.get("type", "")) or
                item_name == norm(output.get("name", ""))
                for output in first.outputs
            ):
                matched += 1

        return matched / len(second.inputs)

    def compatibility(self, first, second):
        # A missing precondition means the capabilities cannot be composed directly.
        precondition_score = self.effect_precondition_score(first, second)

        if precondition_score < 1.0:
            return 0.0

        return round(
            0.7 * precondition_score + 0.3 * self.input_output_score(first, second),
            6
        )

    def compose(self, capabilities: Sequence[Capability]):
        if not capabilities:
            raise ValueError("At least one capability is required")

        capabilities = list(capabilities)
        effects = list(capabilities[0].effects)
        outputs = list(capabilities[0].outputs)

        for capability in capabilities[1:]:
            for precondition in capability.preconditions:
                if not any(self.satisfies(effect, precondition) for effect in effects):
                    raise ValueError("Incompatible composition")

            for item in capability.inputs:
                if not any(
                    norm(item.get("type", "")) == norm(output.get("type", "")) or
                    norm(item.get("name", "")) == norm(output.get("name", ""))
                    for output in outputs
                ):
                    raise ValueError("Incompatible input-output composition")

            effects.extend(capability.effects)
            outputs.extend(capability.outputs)

        return Capability(
            name=" ∘ ".join(c.name for c in capabilities),
            type="COMPOSITE",
            mechanism={"composition": "SEQUENTIAL"},
            inputs=capabilities[0].inputs,
            outputs=capabilities[-1].outputs,
            preconditions=capabilities[0].preconditions,
            effects=list(dict.fromkeys(e for c in capabilities for e in c.effects)),
            constraints=list(dict.fromkeys(x for c in capabilities for x in c.constraints)),
            resources=list(dict.fromkeys(x for c in capabilities for x in c.resources)),
            cost={
                key: sum(c.cost.get(key, 0) for c in capabilities)
                for key in COST_KEYS
            },
            reliability=math.prod(c.reliability for c in capabilities),
            availability=int(all(c.availability for c in capabilities)),
            components=[c.name for c in capabilities]
        )


def load_dataset(path="capabilities.json"):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)
