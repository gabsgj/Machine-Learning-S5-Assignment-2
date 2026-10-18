"""Dataset loading helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

from .schema import Capability, Condition, Constraint, InputSpec, OutputSpec, QualityAttributes


def capability_from_dict(data: dict) -> Capability:
    return Capability(
        id=data["id"],
        name=data["name"],
        type=data["type"],
        inputs=[InputSpec(**x) for x in data.get("inputs", [])],
        outputs=[OutputSpec(**x) for x in data.get("outputs", [])],
        preconditions=[Condition(**x) for x in data.get("preconditions", [])],
        effects=[Condition(**x) for x in data.get("effects", [])],
        constraints=[Constraint(**x) for x in data.get("constraints", [])],
        resources=list(data.get("resources", [])),
        quality=QualityAttributes(**data.get("quality", {})),
        reliability=float(data.get("reliability", 1.0)),
        availability=int(data.get("availability", 1)),
        mechanism=dict(data.get("mechanism", {})),
    )


def load_core_dataset(path: str | Path) -> Tuple[dict, Dict[str, Capability]]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    capabilities = {item["id"]: capability_from_dict(item) for item in data["capabilities"]}
    return data, capabilities
