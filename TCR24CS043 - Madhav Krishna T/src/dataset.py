"""Generic dataset loading helpers for Phase 3+ experiments."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

from .data_models import capability_from_dict
from .schema import Capability


def load_dataset(path: str | Path) -> Tuple[dict, Dict[str, Capability]]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    capabilities = {item["id"]: capability_from_dict(item) for item in data["capabilities"]}
    return data, capabilities
