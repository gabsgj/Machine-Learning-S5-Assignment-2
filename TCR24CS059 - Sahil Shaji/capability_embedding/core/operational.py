"""
Operational attributes, quality parameters, resources, and constraints (Sections 4.4 - 4.6).
"""

from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass, field
import math


@dataclass
class OperationalQuality:
    """
    Formal operational cost, quality, and dependability attributes.
    Section 4.5: Q_i = (C_time, C_resource, C_money, C_risk, C_energy)
    Section 4.6: Reliability in [0, 1], Availability in [0, 1]
    """
    execution_time_ms: float = 10.0
    monetary_cost: float = 0.01
    resource_cost: float = 1.0
    risk: float = 0.05
    energy_cost: float = 0.5
    reliability: float = 0.99
    availability: float = 1.0

    def __post_init__(self):
        # Bound probabilities
        self.reliability = max(1e-6, min(1.0, float(self.reliability)))
        self.availability = max(0.0, min(1.0, float(self.availability)))
        self.risk = max(0.0, min(0.9999, float(self.risk)))
        self.execution_time_ms = max(0.0, float(self.execution_time_ms))
        self.monetary_cost = max(0.0, float(self.monetary_cost))
        self.resource_cost = max(0.0, float(self.resource_cost))
        self.energy_cost = max(0.0, float(self.energy_cost))

    @property
    def log_reliability(self) -> float:
        """Negative log reliability: allows additive linear composition."""
        return -math.log(self.reliability)

    @property
    def log_availability(self) -> float:
        """Negative log availability: allows additive linear composition."""
        avail = max(1e-6, self.availability)
        return -math.log(avail)

    def compose_with(self, other: "OperationalQuality") -> "OperationalQuality":
        """
        Algebraic composition of operational qualities (Section 5):
        - Latency, monetary cost, resource cost, energy are additive.
        - Reliability is multiplicative (independent failure mode assumption).
        - Availability is multiplicative (joint availability assumption).
        - Risk aggregates via independent failure: 1 - (1 - r1)(1 - r2).
        """
        combined_rel = self.reliability * other.reliability
        combined_avail = self.availability * other.availability
        combined_risk = 1.0 - (1.0 - self.risk) * (1.0 - other.risk)

        return OperationalQuality(
            execution_time_ms=self.execution_time_ms + other.execution_time_ms,
            monetary_cost=self.monetary_cost + other.monetary_cost,
            resource_cost=self.resource_cost + other.resource_cost,
            risk=combined_risk,
            energy_cost=self.energy_cost + other.energy_cost,
            reliability=combined_rel,
            availability=combined_avail
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_time_ms": self.execution_time_ms,
            "monetary_cost": self.monetary_cost,
            "resource_cost": self.resource_cost,
            "risk": self.risk,
            "energy_cost": self.energy_cost,
            "reliability": self.reliability,
            "availability": self.availability
        }


@dataclass
class ResourceRequirement:
    """
    Resource requirement specification (Section 4.4).
    Examples: Database, Payment gateway, File system, Authentication token, Network, GPU.
    """
    name: str
    resource_type: str = "SYSTEM"
    quantity: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "resource_type": self.resource_type,
            "quantity": self.quantity
        }


@dataclass
class CapabilityConstraint:
    """
    Capability-specific constraints (Section 4.4).
    k_j in K_i (e.g. quantity > 0, user.role in {CUSTOMER, ADMIN}).
    """
    expression: str
    variables: List[str] = field(default_factory=list)
    constraint_type: str = "STATE_CONSTRAINT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expression": self.expression,
            "variables": list(self.variables),
            "constraint_type": self.constraint_type
        }
