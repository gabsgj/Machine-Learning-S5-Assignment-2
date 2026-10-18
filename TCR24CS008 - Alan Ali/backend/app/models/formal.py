from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Predicate(StrictModel):
    name: str = Field(min_length=1)
    operator: Literal["=", "!=", ">", ">=", "<", "<=", "in"] = "="
    value: Any


class State(StrictModel):
    id: str = Field(min_length=1)
    values: dict[str, Any]


class Goal(StrictModel):
    id: str = Field(min_length=1)
    conditions: list[Predicate] = Field(min_length=1)


class IOField(StrictModel):
    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    domain: str | None = None
    required: bool = True


class OperationalCost(StrictModel):
    time_ms: float = Field(default=0, ge=0)
    money: float = Field(default=0, ge=0)
    resource: float = Field(default=0, ge=0)
    risk: float = Field(default=0, ge=0)
    energy: float = Field(default=0, ge=0)


class Capability(StrictModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: Literal["API", "DATABASE", "GUI", "EVENT", "FUNCTION", "FILE", "COMPUTATION", "MESSAGE", "SERVICE", "COMPOSITE"]
    mechanism: dict[str, str] = Field(default_factory=dict)
    inputs: list[IOField] = Field(default_factory=list)
    outputs: list[IOField] = Field(default_factory=list)
    preconditions: list[Predicate] = Field(default_factory=list)
    effects: list[Predicate] = Field(default_factory=list)
    constraints: list[Predicate] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)
    cost: OperationalCost = Field(default_factory=OperationalCost)
    reliability: float = Field(ge=0, le=1)
    availability: float = Field(default=1, ge=0, le=1)
    components: list[str] = Field(default_factory=list)

    @field_validator("mechanism")
    @classmethod
    def mechanism_values_nonempty(cls, value: dict[str, str]) -> dict[str, str]:
        if any(not key.strip() or not item.strip() for key, item in value.items()):
            raise ValueError("mechanism keys and values must be non-empty")
        return value


class ApplicationScenario(StrictModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    states: list[State] = Field(default_factory=list)
    goals: list[Goal] = Field(default_factory=list)
    capabilities: list[Capability] = Field(default_factory=list)
