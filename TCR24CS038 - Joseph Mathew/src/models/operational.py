"""Operational attributes, costs, reliability, availability, resources, and constraints.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class CostProfile(BaseModel):
    """Quality and cost vector Q_i = (C_time, C_resource, C_money, C_risk, C_energy)."""
    execution_time_ms: float = 0.0
    monetary_cost: float = 0.0
    resource_units: float = 0.0
    risk: float = 0.0        # in [0, 1]
    energy_joules: float = 0.0

    def as_vector(self) -> List[float]:
        return [
            self.execution_time_ms,
            self.monetary_cost,
            self.resource_units,
            self.risk,
            self.energy_joules
        ]

    def add(self, other: CostProfile) -> CostProfile:
        """Compose cost profiles sequentially: costs add up, risk accumulates."""
        # Risk of at least one failure or risk aggregate: 1 - (1-r1)*(1-r2)
        combined_risk = 1.0 - (1.0 - min(1.0, max(0.0, self.risk))) * (1.0 - min(1.0, max(0.0, other.risk)))
        return CostProfile(
            execution_time_ms=self.execution_time_ms + other.execution_time_ms,
            monetary_cost=self.monetary_cost + other.monetary_cost,
            resource_units=self.resource_units + other.resource_units,
            risk=combined_risk,
            energy_joules=self.energy_joules + other.energy_joules,
        )


class ResourceRequirement(BaseModel):
    """Resource requirement r_j in R_i (e.g. Database, GPU, PaymentGateway, Network)."""
    name: str
    amount: float = 1.0
    exclusive: bool = False


class Constraint(BaseModel):
    """Capability-specific constraint k in K_i."""
    name: str
    expression: str
    constraint_type: str = "operational"  # 'input', 'state', 'resource', 'security', 'temporal'

    def check(self, context: Dict[str, Any]) -> bool:
        # Simple evaluation or rule satisfaction
        return True


class OperationalProfile(BaseModel):
    """Consolidated operational attributes."""
    cost: CostProfile = Field(default_factory=CostProfile)
    reliability: float = Field(default=1.0, ge=0.0, le=1.0)
    availability: float = Field(default=1.0, ge=0.0, le=1.0)
    resources: List[ResourceRequirement] = Field(default_factory=list)
    constraints: List[Constraint] = Field(default_factory=list)

    def compose_with(self, other: OperationalProfile) -> OperationalProfile:
        """Sequential composition of operational profiles."""
        combined_cost = self.cost.add(other.cost)
        combined_rel = self.reliability * other.reliability
        combined_avail = min(self.availability, other.availability)
        
        # Merge resources by name
        res_map: Dict[str, ResourceRequirement] = {}
        for r in self.resources + other.resources:
            if r.name in res_map:
                res_map[r.name] = ResourceRequirement(
                    name=r.name,
                    amount=res_map[r.name].amount + r.amount,
                    exclusive=res_map[r.name].exclusive or r.exclusive
                )
            else:
                res_map[r.name] = r.model_copy()
                
        # Merge constraints
        all_constraints = list(self.constraints)
        for c in other.constraints:
            if c not in all_constraints:
                all_constraints.append(c)
                
        return OperationalProfile(
            cost=combined_cost,
            reliability=combined_rel,
            availability=combined_avail,
            resources=list(res_map.values()),
            constraints=all_constraints
        )
