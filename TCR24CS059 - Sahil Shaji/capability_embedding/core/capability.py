"""
Formal Capability Representation (Section 4).
Ci = (Ti, Ii, Oi, Pi, Ei, Ki, Ri, Qi, Reli, Ai, Mi)
"""

from typing import Dict, Any, List, Optional, Sequence
from dataclasses import dataclass, field
import copy

from .types import CapabilityType, ExecutionMechanism, InputSpec, OutputSpec
from .operational import OperationalQuality, ResourceRequirement, CapabilityConstraint
from .state import State


class Capability:
    """
    Formal Capability Representation (Section 4).
    A reusable operation characterized by:
      - Ti: Capability type
      - Ii, Oi: Input and output specifications
      - Pi, Ei: Preconditions and effects
      - Ki: Capability-specific constraints
      - Ri: Resource requirements
      - Qi: Cost and quality attributes
      - Reli: Reliability
      - Ai: Availability
      - Mi: Execution mechanism
    """

    def __init__(
        self,
        name: str,
        capability_type: CapabilityType = CapabilityType.FUNCTION,
        inputs: Optional[List[InputSpec]] = None,
        outputs: Optional[List[OutputSpec]] = None,
        preconditions: Optional[Dict[str, Any]] = None,
        effects: Optional[Dict[str, Any]] = None,
        constraints: Optional[List[CapabilityConstraint]] = None,
        resources: Optional[List[ResourceRequirement]] = None,
        quality: Optional[OperationalQuality] = None,
        mechanism: Optional[ExecutionMechanism] = None,
        sub_capabilities: Optional[List["Capability"]] = None,
    ):
        self.name = name
        self.capability_type = capability_type
        self.inputs: List[InputSpec] = list(inputs or [])
        self.outputs: List[OutputSpec] = list(outputs or [])
        self.preconditions: Dict[str, Any] = dict(preconditions or {})
        self.effects: Dict[str, Any] = dict(effects or {})
        self.constraints: List[CapabilityConstraint] = list(constraints or [])
        self.resources: List[ResourceRequirement] = list(resources or [])
        self.quality: OperationalQuality = quality or OperationalQuality()
        self.mechanism: ExecutionMechanism = mechanism or ExecutionMechanism(mechanism_type=capability_type)
        self.sub_capabilities: List["Capability"] = list(sub_capabilities or [])

    @property
    def is_composite(self) -> bool:
        return len(self.sub_capabilities) > 0

    @property
    def reliability(self) -> float:
        return self.quality.reliability

    @property
    def availability(self) -> float:
        return self.quality.availability

    def is_applicable_to(self, state: State) -> bool:
        """Ci is applicable to S <=> S |= Pi (Section 4.3)."""
        return state.satisfies(self.preconditions)

    def apply(self, state: State) -> State:
        """Ci: S -> S', S' = Apply(S, Ei) (Section 4.3)."""
        if not self.is_applicable_to(state):
            raise ValueError(f"Capability '{self.name}' not applicable to state: preconditions not met.")
        return state.apply(self.effects)

    def requires_input(self, name: str) -> bool:
        return any(inp.name == name for inp in self.inputs)

    def produces_output(self, name: str) -> bool:
        return any(out.name == name for out in self.outputs)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.capability_type.value,
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
            "preconditions": dict(self.preconditions),
            "effects": dict(self.effects),
            "constraints": [c.to_dict() for c in self.constraints],
            "resources": [r.to_dict() for r in self.resources],
            "quality": self.quality.to_dict(),
            "mechanism": self.mechanism.to_dict(),
            "is_composite": self.is_composite,
            "sub_capabilities": [c.name for c in self.sub_capabilities]
        }

    def clone(self) -> "Capability":
        return Capability(
            name=self.name,
            capability_type=self.capability_type,
            inputs=[InputSpec(**i.to_dict()) for i in self.inputs],
            outputs=[OutputSpec(**o.to_dict()) for o in self.outputs],
            preconditions=dict(self.preconditions),
            effects=dict(self.effects),
            constraints=list(self.constraints),
            resources=list(self.resources),
            quality=OperationalQuality(**self.quality.to_dict()),
            mechanism=ExecutionMechanism(self.mechanism.mechanism_type, dict(self.mechanism.details)),
            sub_capabilities=[c.clone() for c in self.sub_capabilities]
        )

    def __repr__(self) -> str:
        tag = "CompositeCapability" if self.is_composite else "Capability"
        return f"{tag}(name='{self.name}', type={self.capability_type.value})"
