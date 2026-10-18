import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

VALID_CAPABILITY_TYPES = {
    "API", "DATABASE", "GUI", "EVENT", "FUNCTION", 
    "FILE", "COMPUTATION", "MESSAGE", "SERVICE"
}

@dataclass
class InputSpec:
    name: str
    type: str
    domain: str = ""
    required: bool = True

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "InputSpec":
        return cls(
            name=d["name"],
            type=d["type"],
            domain=d.get("domain", ""),
            required=d.get("required", True)
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "domain": self.domain,
            "required": self.required
        }

@dataclass
class OutputSpec:
    name: str
    type: str
    domain: str = ""

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "OutputSpec":
        return cls(
            name=d["name"],
            type=d["type"],
            domain=d.get("domain", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "domain": self.domain
        }

@dataclass
class CostSpec:
    time: float = 0.0
    resource: float = 0.0
    money: float = 0.0
    risk: float = 0.0
    energy: float = 0.0

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CostSpec":
        return cls(
            time=float(d.get("time", 0.0)),
            resource=float(d.get("resource", 0.0)),
            money=float(d.get("money", 0.0)),
            risk=float(d.get("risk", 0.0)),
            energy=float(d.get("energy", 0.0))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "time": self.time,
            "resource": self.resource,
            "money": self.money,
            "risk": self.risk,
            "energy": self.energy
        }

@dataclass
class Capability:
    name: str
    type: str
    inputs: List[InputSpec] = field(default_factory=list)
    outputs: List[OutputSpec] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    effects: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    cost: CostSpec = field(default_factory=CostSpec)
    reliability: float = 1.0
    availability: float = 1.0
    mechanism: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate formal capability parameters according to assignment specifications."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Capability must have a non-empty string 'name'")
        if self.type not in VALID_CAPABILITY_TYPES:
            raise ValueError(f"Invalid capability type '{self.type}'. Must be one of {VALID_CAPABILITY_TYPES}")
        if not (0.0 <= self.reliability <= 1.0):
            raise ValueError(f"Reliability must be in range [0.0, 1.0], got {self.reliability}")
        if not (0.0 <= self.availability <= 1.0):
            raise ValueError(f"Availability must be in range [0.0, 1.0], got {self.availability}")
        if self.cost.time < 0 or self.cost.resource < 0 or self.cost.money < 0 or self.cost.risk < 0 or self.cost.energy < 0:
            raise ValueError("Cost attributes (time, resource, money, risk, energy) must be non-negative")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Capability":
        cost_obj = CostSpec.from_dict(data.get("cost", {})) if isinstance(data.get("cost"), dict) else CostSpec()
        inputs_list = [InputSpec.from_dict(i) for i in data.get("inputs", [])]
        outputs_list = [OutputSpec.from_dict(o) for o in data.get("outputs", [])]
        
        cap = cls(
            name=data["name"],
            type=data["type"],
            inputs=inputs_list,
            outputs=outputs_list,
            preconditions=data.get("preconditions", []),
            effects=data.get("effects", []),
            constraints=data.get("constraints", []),
            resources=data.get("resources", []),
            cost=cost_obj,
            reliability=float(data.get("reliability", 1.0)),
            availability=float(data.get("availability", 1.0)),
            mechanism=data.get("mechanism", {})
        )
        cap.validate()
        return cap

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
            "preconditions": self.preconditions,
            "effects": self.effects,
            "constraints": self.constraints,
            "resources": self.resources,
            "cost": self.cost.to_dict(),
            "reliability": self.reliability,
            "availability": self.availability,
            "mechanism": self.mechanism
        }

def load_capabilities_from_json(filepath: str) -> List[Capability]:
    """Load and validate a list of formal capabilities from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_list = json.load(f)
    capabilities = []
    for item in raw_list:
        cap = Capability.from_dict(item)
        capabilities.append(cap)
    return capabilities
