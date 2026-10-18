from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from app.models.formal import ApplicationScenario


DEFAULT_SCENARIO_PATH = Path(__file__).resolve().parents[3] / "data" / "scenarios" / "commerce.json"


def load_default_scenario(path: Path | None = None) -> ApplicationScenario:
    """Load the bundled scenario, with an injectable path for callers and tests."""
    scenario_path = path or DEFAULT_SCENARIO_PATH
    return ApplicationScenario.model_validate(
        json.loads(scenario_path.read_text(encoding="utf-8"))
    )


@dataclass
class ScenarioStore:
    """Small in-memory scenario repository used by the API.

    The store intentionally returns the model instance it owns, matching the
    existing API's in-memory mutation semantics while making the dependency
    explicit and straightforward to replace in tests.
    """

    _scenario: ApplicationScenario

    @classmethod
    def with_default_scenario(cls) -> "ScenarioStore":
        return cls(load_default_scenario())

    def get(self) -> ApplicationScenario:
        return self._scenario

    def replace(self, scenario: ApplicationScenario) -> ApplicationScenario:
        self._scenario = scenario
        return self._scenario
