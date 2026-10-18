"""Validate every checked-in scenario against the backend's formal schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models.formal import ApplicationScenario  # noqa: E402



def main() -> int:
    scenario_paths = sorted((ROOT / "data" / "scenarios").rglob("*.json"))
    if not scenario_paths:
        print("No scenario files found under data/scenarios", file=sys.stderr)
        return 1

    failures: list[str] = []
    for path in scenario_paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            scenario = ApplicationScenario.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            failures.append(f"{path.relative_to(ROOT)}: {error}")
            continue
        print(
            f"ok {path.relative_to(ROOT)} "
            f"({len(scenario.states)} states, {len(scenario.goals)} goals, "
            f"{len(scenario.capabilities)} capabilities)"
        )

    if failures:
        print("\nScenario validation failed:", file=sys.stderr)
        print("\n".join(failures), file=sys.stderr)
        return 1

    print(f"Validated {len(scenario_paths)} scenario files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
