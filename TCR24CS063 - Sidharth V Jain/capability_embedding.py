from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Sequence, Tuple
from pathlib import Path
import json
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import StandardScaler


@dataclass
class Capability:
    id: str
    name: str
    type: str
    mechanism: Dict[str, Any]
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    preconditions: Dict[str, Any]
    effects: Dict[str, Any]
    constraints: List[str]
    resources: List[str]
    cost: Dict[str, float]
    reliability: float
    availability: int = 1


class FormalKVEncoder:
    """Unified encoder for states/goals represented as key-value structures."""

    def __init__(self, objects: Sequence[Dict[str, Any]]):
        self.vectorizer = DictVectorizer(sparse=False)
        self.vectorizer.fit([self._features(x) for x in objects])

    @staticmethod
    def _features(obj: Dict[str, Any]) -> Dict[str, float]:
        return {f"{k}={v}": 1.0 for k, v in obj.items()}

    def encode(self, obj: Dict[str, Any]) -> np.ndarray:
        return self.vectorizer.transform([self._features(obj)])[0]

    @property
    def dimension(self) -> int:
        return len(self.vectorizer.feature_names_)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return 0.0 if na == 0 or nb == 0 else float(np.dot(a, b) / (na * nb))


class StateGoalEncoder:
    """Single vector space for state and goal representations."""

    def __init__(self, states: Sequence[Dict[str, Any]], goals: Sequence[Dict[str, Any]]):
        self.encoder = FormalKVEncoder(list(states) + list(goals))

    def encode_state(self, state: Dict[str, Any]) -> np.ndarray:
        return self.encoder.encode(state)

    def encode_goal(self, goal: Dict[str, Any]) -> np.ndarray:
        return self.encoder.encode(goal)

    @property
    def dimension(self):
        return self.encoder.dimension


class CapabilityEncoder:
    """
    Five-block capability representation.

    Block weights emphasize formal execution semantics while preserving
    implementation and operational information:
        identity/mechanism : 0.10
        input/output       : 0.25
        logic              : 0.40
        resources          : 0.10
        operations         : 0.15
    """

    BLOCKS = ("identity", "io", "logic", "resources", "operations")
    DEFAULT_WEIGHTS = {
        "identity": 0.10,
        "io": 0.25,
        "logic": 0.40,
        "resources": 0.10,
        "operations": 0.15,
    }

    def __init__(self, capabilities: Sequence[Capability]):
        self.capabilities = list(capabilities)
        self.vectorizers = {}
        self.scalers = {}

        for block in self.BLOCKS:
            vec = DictVectorizer(sparse=False)
            X = vec.fit_transform(
                [self._block_features(c, block) for c in self.capabilities]
            )
            scaler = StandardScaler()
            scaler.fit(X)
            self.vectorizers[block] = vec
            self.scalers[block] = scaler

    @staticmethod
    def _block_features(c: Capability, block: str) -> Dict[str, float]:
        f = {}

        if block == "identity":
            f[f"type={c.type}"] = 1.0
            f[f"name={c.name}"] = 0.25
            for k, v in c.mechanism.items():
                f[f"mechanism:{k}={v}"] = 0.50

        elif block == "io":
            for i in c.inputs:
                f[f"in:name={i['name']}"] = 1.0
                f[f"in:type={i['type']}"] = 1.0
                f[f"in:domain={i['domain']}"] = 0.75
                f[f"in:required={i.get('required', True)}"] = 0.50
            for o in c.outputs:
                f[f"out:name={o['name']}"] = 1.0
                f[f"out:type={o['type']}"] = 1.0
                f[f"out:domain={o['domain']}"] = 0.75

        elif block == "logic":
            for k, v in c.preconditions.items():
                f[f"pre:{k}={v}"] = 1.0
            for k, v in c.effects.items():
                f[f"effect:{k}={v}"] = 1.0
            for x in c.constraints:
                f[f"constraint:{x}"] = 0.75

        elif block == "resources":
            for r in c.resources:
                f[f"resource:{r}"] = 1.0

        elif block == "operations":
            f["time_ms"] = float(c.cost.get("time_ms", 0))
            f["resource_cost"] = float(c.cost.get("resource", 0))
            f["money"] = float(c.cost.get("money", 0))
            f["risk"] = float(c.cost.get("risk", 0))
            f["reliability"] = float(c.reliability)
            f["availability"] = float(c.availability)

        return f

    def encode_blocks(self, c: Capability):
        result = {}
        for block in self.BLOCKS:
            raw = self.vectorizers[block].transform(
                [self._block_features(c, block)]
            )
            result[block] = self.scalers[block].transform(raw)[0]
        return result

    def encode(self, c: Capability) -> np.ndarray:
        blocks = self.encode_blocks(c)
        return np.concatenate([blocks[b] for b in self.BLOCKS])

    def similarity(self, a: Capability, b: Capability,
                   weights=None) -> float:
        weights = weights or self.DEFAULT_WEIGHTS
        A, B = self.encode_blocks(a), self.encode_blocks(b)
        return float(sum(
            weights[k] * cosine_similarity(A[k], B[k])
            for k in self.BLOCKS
        ))

    @property
    def dimension(self):
        return len(self.encode(self.capabilities[0]))


def _compatible_value(effect_value: Any, required_value: Any) -> bool:
    if required_value == ">0":
        return isinstance(effect_value, (int, float)) and effect_value > 0
    return effect_value == required_value


def effect_precondition_match(a: Capability, b: Capability) -> float:
    if not b.preconditions:
        return 1.0
    return sum(
        int(k in a.effects and _compatible_value(a.effects[k], v))
        for k, v in b.preconditions.items()
    ) / len(b.preconditions)


def output_input_match(a: Capability, b: Capability) -> float:
    required = [i for i in b.inputs if i.get("required", True)]
    if not required:
        return 1.0
    score = 0
    for i in required:
        score += int(any(
            o["type"] == i["type"] and
            (o["domain"] == i["domain"] or o["domain"] == "valid UUIDs")
            for o in a.outputs
        ))
    return score / len(required)


def constraint_compatibility(a: Capability, b: Capability) -> float:
    for k, v in b.preconditions.items():
        if k in a.effects and not _compatible_value(a.effects[k], v):
            return 0.0
    return 1.0


def compatibility(a: Capability, b: Capability) -> float:
    return float(
        0.55 * effect_precondition_match(a, b)
        + 0.25 * output_input_match(a, b)
        + 0.20 * constraint_compatibility(a, b)
    )


def compose(capabilities: Sequence[Capability]) -> Capability:
    if not capabilities:
        raise ValueError("At least one capability is required.")

    scores = [compatibility(a, b) for a, b in zip(capabilities, capabilities[1:])]
    if any(s < 0.75 for s in scores):
        raise ValueError(f"Invalid composition; compatibility scores={scores}")

    produced_types = set()
    external_inputs = []
    for c in capabilities:
        for i in c.inputs:
            if i.get("required", True) and i["type"] not in produced_types:
                external_inputs.append(i)
        produced_types.update(o["type"] for o in c.outputs)

    effects = {}
    for c in capabilities:
        effects.update(c.effects)

    return Capability(
        id="COMPOSITE_" + "_".join(c.id for c in capabilities),
        name=" ◦ ".join(c.name for c in capabilities),
        type="COMPOSITE",
        mechanism={"sequence": " -> ".join(c.id for c in capabilities)},
        inputs=external_inputs,
        outputs=capabilities[-1].outputs,
        preconditions=dict(capabilities[0].preconditions),
        effects=effects,
        constraints=sorted(set(x for c in capabilities for x in c.constraints)),
        resources=sorted(set(x for c in capabilities for x in c.resources)),
        cost={
            k: sum(c.cost.get(k, 0.0) for c in capabilities)
            for k in ("time_ms", "resource", "money", "risk")
        },
        reliability=float(np.prod([c.reliability for c in capabilities])),
        availability=int(all(c.availability for c in capabilities)),
    )


def goal_relevance(c: Capability, goal: Dict[str, Any]) -> float:
    if not goal:
        return 0.0
    return sum(
        int(k in c.effects and _compatible_value(c.effects[k], v))
        for k, v in goal.items()
    ) / len(goal)


def load_data(path="dataset.json"):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    caps = [Capability(**x) for x in data["capabilities"]]
    return data["application"], caps


def build_evaluation_pairs(caps):
    by = {c.id: c for c in caps}
    positive = [("C1", "C2"), ("C2", "C4"), ("C5", "C2"), ("C6", "C2")]
    negative = [("C1", "C3"), ("C2", "C3"), ("C3", "C2"), ("C7", "C2")]
    return [(by[a], by[b], 1) for a,b in positive] + [(by[a], by[b], 0) for a,b in negative]


def classification_metrics(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    accuracy = (tp + tn) / max(1, len(y_true))
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return dict(tp=tp, tn=tn, fp=fp, fn=fn,
                accuracy=accuracy, precision=precision,
                recall=recall, f1=f1)


def run_all(path="dataset.json"):
    app, caps = load_data(path)
    by = {c.id: c for c in caps}
    enc = CapabilityEncoder(caps)

    pairs = build_evaluation_pairs(caps)
    comp_rows = []
    y_true, y_pred = [], []
    for a, b, label in pairs:
        score = compatibility(a, b)
        pred = int(score >= 0.75)
        y_true.append(label); y_pred.append(pred)
        comp_rows.append({
            "a": a.id, "b": b.id, "label": label,
            "score": score, "prediction": pred
        })
    metrics = classification_metrics(y_true, y_pred)

    sim_rows = []
    alt_scores = []
    for x in ("C5", "C6"):
        s = enc.similarity(by["C1"], by[x])
        alt_scores.append(s)
        sim_rows.append({"pair": f"C1~{x}", "category": "alternative", "score": s})
    irrelevant = enc.similarity(by["C1"], by["C7"])
    sim_rows.append({"pair": "C1~C7", "category": "irrelevant", "score": irrelevant})

    composite = compose([by["C1"], by["C2"], by["C4"]])
    comp_component_scores = [
        enc.similarity(composite, by[x]) for x in ("C1", "C2", "C4")
    ]

    relevance = [
        {"id": c.id, "score": goal_relevance(c, app["goal"])}
        for c in caps
    ]

    op_rows = []
    for c in caps:
        time_n = c.cost.get("time_ms", 0) / 500.0
        money_n = c.cost.get("money", 0) / 0.25
        utility = (
            goal_relevance(c, app["goal"])
            + 0.25*c.reliability
            + 0.10*c.availability
            - 0.10*time_n
            - 0.10*money_n
            - 0.10*c.cost.get("risk", 0)
        )
        op_rows.append({
            "id": c.id, "goal_relevance": goal_relevance(c, app["goal"]),
            "reliability": c.reliability,
            "time_ms": c.cost.get("time_ms", 0),
            "money": c.cost.get("money", 0),
            "risk": c.cost.get("risk", 0),
            "utility": utility
        })

    sg = StateGoalEncoder([app["initial_state"]], [app["goal"]])

    return {
        "compatibility_rows": comp_rows,
        "compatibility_metrics": metrics,
        "similarity_rows": sim_rows,
        "alternative_mean": float(np.mean(alt_scores)),
        "irrelevant_score": float(irrelevant),
        "composite": composite,
        "composite_component_scores": comp_component_scores,
        "goal_relevance": relevance,
        "operational_rows": op_rows,
        "dimensions": {
            "state_goal": sg.dimension,
            "capability": enc.dimension
        }
    }


if __name__ == "__main__":
    out = run_all()
    print(json.dumps({
        "compatibility_metrics": out["compatibility_metrics"],
        "alternative_mean": out["alternative_mean"],
        "irrelevant_score": out["irrelevant_score"],
        "composite_reliability": out["composite"].reliability,
        "dimensions": out["dimensions"]
    }, indent=2))
