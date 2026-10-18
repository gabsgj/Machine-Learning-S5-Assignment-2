"""
Custom vector embedding for formally specified application capabilities.

The implementation deliberately avoids a pretrained language embedding. It constructs a
problem-specific structured feature space from the formal fields in Assignment 2.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence, Tuple
import math
import numpy as np


def _stable_hash(text: str, dim: int = 64) -> int:
    # Deterministic hash independent of Python's randomized hash seed.
    h = 2166136261
    for ch in text:
        h ^= ord(ch)
        h = (h * 16777619) & 0xffffffff
    return h % dim


def _norm_text(x: Any) -> str:
    return str(x).strip().lower()


def _flatten_dict(d: Dict[str, Any], prefix: str = "") -> List[str]:
    out = []
    for k, v in sorted(d.items()):
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.extend(_flatten_dict(v, key + "."))
        else:
            out.append(f"{key}={_norm_text(v)}")
    return out


def _token_set(items: Any) -> set:
    if items is None:
        return set()
    if isinstance(items, dict):
        return set(_flatten_dict(items))
    return {_norm_text(x) for x in items}


@dataclass
class Capability:
    name: str
    type: str
    mechanism: Dict[str, Any] = field(default_factory=dict)
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    preconditions: Dict[str, Any] = field(default_factory=dict)
    effects: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    cost: Dict[str, float] = field(default_factory=lambda: {
        "time": 0.0, "resource": 0.0, "money": 0.0, "risk": 0.0, "energy": 0.0
    })
    reliability: float = 1.0
    availability: float = 1.0


def capability_from_dict(d: Dict[str, Any]) -> Capability:
    return Capability(
        name=d["name"],
        type=d.get("type", "FUNCTION"),
        mechanism=d.get("mechanism", {}),
        inputs=d.get("inputs", []),
        outputs=d.get("outputs", []),
        preconditions=d.get("preconditions", {}),
        effects=d.get("effects", {}),
        constraints=d.get("constraints", []),
        resources=d.get("resources", []),
        cost=d.get("cost", {"time": 0, "resource": 0, "money": 0, "risk": 0, "energy": 0}),
        reliability=float(d.get("reliability", 1.0)),
        availability=float(d.get("availability", 1.0)),
    )


class CapabilityEmbedder:
    """
    Structured embedding.

    The vector is divided into:
      [functional hashed features | mechanism features | operational features]

    Functional features are deliberately given more weight than implementation features.
    This supports the requirement that different mechanisms may implement related functions.
    """

    FUNCTION_DIM = 128
    MECHANISM_DIM = 32
    OP_DIM = 8

    def __init__(self):
        self.dim = self.FUNCTION_DIM + self.MECHANISM_DIM + self.OP_DIM

    def _hashed_features(self, features: Sequence[str], dim: int) -> np.ndarray:
        v = np.zeros(dim, dtype=float)
        for feature in features:
            idx = _stable_hash(feature, dim)
            v[idx] += 1.0
        return v

    def encode_state(self, state: Dict[str, Any]) -> np.ndarray:
        features = [f"state:{x}" for x in _flatten_dict(state)]
        return self._normalize(self._hashed_features(features, self.FUNCTION_DIM))

    def encode_goal(self, goal: Dict[str, Any]) -> np.ndarray:
        features = [f"goal:{x}" for x in _flatten_dict(goal)]
        return self._normalize(self._hashed_features(features, self.FUNCTION_DIM))

    def _capability_features(self, c: Capability) -> Tuple[List[str], List[str]]:
        functional = [f"type:{_norm_text(c.type)}"]

        for i in c.inputs:
            functional += [
                f"input:name={_norm_text(i.get('name'))}",
                f"input:type={_norm_text(i.get('type'))}",
                f"input:domain={_norm_text(i.get('domain'))}",
                f"input:required={_norm_text(i.get('required', True))}",
            ]

        for o in c.outputs:
            functional += [
                f"output:name={_norm_text(o.get('name'))}",
                f"output:type={_norm_text(o.get('type'))}",
                f"output:domain={_norm_text(o.get('domain'))}",
            ]

        functional += [f"precondition:{x}" for x in _flatten_dict(c.preconditions)]
        functional += [f"effect:{x}" for x in _flatten_dict(c.effects)]
        functional += [f"constraint:{_norm_text(x)}" for x in c.constraints]
        functional += [f"resource:{_norm_text(x)}" for x in c.resources]

        mechanism = [f"mechanism:{x}" for x in _flatten_dict(c.mechanism)]
        return functional, mechanism

    def encode_capability(self, c: Capability) -> np.ndarray:
        functional, mechanism = self._capability_features(c)
        f = self._hashed_features(functional, self.FUNCTION_DIM)
        m = self._hashed_features(mechanism, self.MECHANISM_DIM)

        # Operational values are normalized to stable ranges.
        op = np.array([
            min(float(c.cost.get("time", 0.0)) / 1000.0, 1.0),
            min(float(c.cost.get("resource", 0.0)) / 100.0, 1.0),
            min(float(c.cost.get("money", 0.0)) / 100.0, 1.0),
            min(float(c.cost.get("risk", 0.0)), 1.0),
            min(float(c.cost.get("energy", 0.0)) / 100.0, 1.0),
            min(max(float(c.reliability), 0.0), 1.0),
            min(max(float(c.availability), 0.0), 1.0),
            len(c.resources) / 10.0,
        ], dtype=float)

        # Functional information dominates implementation details.
        vector = np.concatenate([1.0 * f, 0.25 * m, op])
        return self._normalize(vector)

    def encode_composite(self, capabilities: Sequence[Capability]) -> np.ndarray:
        if not capabilities:
            return np.zeros(self.dim, dtype=float)
        vectors = [self.encode_capability(c) for c in capabilities]
        # Mean gives a simple compositional representation; order is handled separately by
        # the dependency/compatibility matrix in compose().
        return self._normalize(np.mean(vectors, axis=0))

    def compose(self, capabilities: Sequence[Capability]) -> Dict[str, Any]:
        caps = list(capabilities)
        vector = self.encode_composite(caps)
        pairwise = []
        valid = True
        for a, b in zip(caps, caps[1:]):
            score, reasons = self.compatibility(a, b)
            pairwise.append({"from": a.name, "to": b.name, "score": score, "reasons": reasons})
            valid = valid and score >= 0.5
        return {
            "name": " -> ".join(c.name for c in caps),
            "vector": vector,
            "valid": valid,
            "links": pairwise,
        }

    def similarity(self, x: np.ndarray, y: np.ndarray) -> float:
        denom = np.linalg.norm(x) * np.linalg.norm(y)
        if denom == 0:
            return 0.0
        return float(np.dot(x, y) / denom)

    def compatibility(self, c1: Capability, c2: Capability) -> Tuple[float, List[str]]:
        """
        Compatibility combines:
          - effect -> precondition matches
          - output -> input matches
          - state variable agreement
          - a small functional similarity component

        Exact equality gets full credit. Boolean and simple numeric/string constraints are
        treated conservatively.
        """
        e1 = _token_set(c1.effects)
        p2 = _token_set(c2.preconditions)

        effect_keys = {x.split("=", 1)[0] for x in e1}
        pre_keys = {x.split("=", 1)[0] for x in p2}
        common_keys = effect_keys & pre_keys

        effect_pre_matches = 0
        reasons = []

        for ek in e1:
            if "=" not in ek:
                continue
            k, v = ek.split("=", 1)
            for pk in p2:
                if "=" not in pk:
                    continue
                pk2, pv = pk.split("=", 1)
                if k == pk2 and (v == pv or pv in (">0", "true", "1")):
                    effect_pre_matches += 1
                    reasons.append(f"effect {k}={v} satisfies precondition {pk2}={pv}")
                    break

        # Input/output compatibility is strongest when the produced output name/type
        # can satisfy a required input name/type. Type equality alone is not enough.
        io_matches = 0
        for o in c1.outputs:
            for i in c2.inputs:
                same_type = _norm_text(o.get("type")) == _norm_text(i.get("type"))
                same_name = _norm_text(o.get("name")) == _norm_text(i.get("name"))
                if same_type and same_name:
                    io_matches += 1

        # A dependency can be established through a shared state variable even when
        # the literal values are represented differently.
        state_link = 1 if common_keys else 0

        structural = min(1.0, 0.65 * (1 if effect_pre_matches else 0) +
                            0.20 * (1 if io_matches else 0) +
                            0.15 * state_link)

        sim = self.similarity(self.encode_capability(c1), self.encode_capability(c2))
        score = float(min(1.0, structural + 0.10 * max(sim, 0.0)))

        if not reasons:
            reasons.append("No direct effect-precondition match")
        if io_matches:
            reasons.append("Compatible input/output type")
        return score, reasons

    def goal_relevance(self, capability: Capability, goal: Dict[str, Any]) -> float:
        effect_tokens = _token_set(capability.effects)
        goal_tokens = _token_set(goal)
        if not goal_tokens:
            return 0.0
        exact = len(effect_tokens & goal_tokens) / len(goal_tokens)
        effect_keys = {x.split("=", 1)[0] for x in effect_tokens}
        goal_keys = {x.split("=", 1)[0] for x in goal_tokens}
        key_overlap = len(effect_keys & goal_keys) / len(goal_keys)
        return float(0.7 * exact + 0.3 * key_overlap)

    @staticmethod
    def _normalize(v: np.ndarray) -> np.ndarray:
        n = np.linalg.norm(v)
        return v / n if n else v


def evaluate_operational(c: Capability) -> Dict[str, float]:
    return {
        "reliability": c.reliability,
        "availability": c.availability,
        "time": c.cost.get("time", 0.0),
        "money": c.cost.get("money", 0.0),
        "risk": c.cost.get("risk", 0.0),
    }
