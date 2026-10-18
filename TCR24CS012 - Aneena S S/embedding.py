"""
Embedding engine for Assignment 2.

Implements:
    encode(state), encode(goal), encode(capability)
    compose(capabilities)
    similarity(x, y)
    compatibility(Ci, Cj)
    goal_relevance(Ci, G)
    applicability(Ci, S)

Design summary
--------------
A capability's vector is the concatenation of independently-meaningful
blocks. Blocks that must support *exact* set-overlap reasoning (precondition,
effect, input, output) are multi-hot over vocabularies built from the whole
capability set, so that "capability A's effect atom" and "capability B's
precondition atom" are literally the same vector dimension when they are the
same real-world fact. Blocks that only need rough, collision-tolerant
similarity (constraints, mechanism) use feature hashing, so the embedding
does not require a fixed, pre-enumerated vocabulary for free-text fields and
can accept new constraint text without retraining. Operational attributes
(cost, reliability, availability) form their own continuous block, excluded
from the default "functional similarity" computation, so that two
capabilities that do the same thing at different cost are not treated as
functionally different -- and so changing an operational attribute never
silently perturbs a compatibility judgement.
"""

from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Dict, List, Tuple, Iterable, Optional
import hashlib
import math

import numpy as np

from capability_model import (
    Capability, State, Goal, IOSpec, CAPABILITY_TYPES, atom_eq
)

HASH_DIM_CONSTRAINT = 32
HASH_DIM_MECHANISM = 16


def _hash_bucket(token: str, dim: int) -> int:
    h = hashlib.md5(token.encode("utf-8")).hexdigest()
    return int(h, 16) % dim


def _hashed_vector(tokens: Iterable[str], dim: int) -> np.ndarray:
    v = np.zeros(dim, dtype=np.float64)
    for t in tokens:
        v[_hash_bucket(t, dim)] += 1.0
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v


@dataclass
class VectorLayout:
    """Records block boundaries inside the full concatenated vector so that
    sub-vectors (e.g. "just the effect block") can be sliced out later for
    compatibility / goal-relevance computations."""
    type_dim: int
    mech_dim: int
    pred_vocab: List[str]       # shared precondition/effect vocabulary
    io_vocab: List[str]         # shared input/output vocabulary
    constraint_dim: int
    resource_vocab: List[str]
    op_dim: int  # cost(5) + reliability(1) + availability(1)

    def slices(self) -> Dict[str, Tuple[int, int]]:
        i = 0
        out = {}
        for name, d in [
            ("type", self.type_dim),
            ("mechanism", self.mech_dim),
            ("precondition", len(self.pred_vocab)),
            ("effect", len(self.pred_vocab)),
            ("input", len(self.io_vocab)),
            ("output", len(self.io_vocab)),
            ("constraint", self.constraint_dim),
            ("resource", len(self.resource_vocab)),
            ("operational", self.op_dim),
        ]:
            out[name] = (i, i + d)
            i += d
        return out

    @property
    def total_dim(self) -> int:
        return sum(e - s for s, e in self.slices().values())

    # "functional" blocks are everything except the operational block --
    # used for the default similarity() call so cost/reliability differences
    # don't dominate or distort functional comparisons. Note this still
    # includes type/mechanism, so it answers "is this the same capability,
    # implementation included?" -- use pure_function_slice() below to answer
    # "does this do the same thing, regardless of implementation?".
    def functional_slice(self) -> Tuple[int, int]:
        s = self.slices()
        start = s["type"][0]
        end = s["resource"][1]
        return start, end

    # Precondition/effect/input/output/constraint/resource only -- excludes
    # both type and mechanism. This is the slice that answers "do these two
    # capabilities do the same thing", independent of how they're
    # implemented. Two alternative implementations of the same function
    # (API vs DATABASE vs GUI) should be near-identical on this slice even
    # though they differ in type and mechanism.
    def pure_function_slice(self) -> Tuple[int, int]:
        s = self.slices()
        return s["precondition"][0], s["resource"][1]

    # Type + mechanism only -- the implementation-identity slice. Two
    # alternative implementations of the same function should be *distinct*
    # on this slice even though they agree on pure_function_slice().
    def implementation_slice(self) -> Tuple[int, int]:
        s = self.slices()
        return s["type"][0], s["mechanism"][1]


class Embedder:
    """
    Builds vocabularies from a capability set (and optionally extra states /
    goals) and encodes states, goals and capabilities into a shared vector
    space.
    """

    def __init__(self, capabilities: List[Capability],
                 extra_states: Optional[List[State]] = None,
                 extra_goals: Optional[List[Goal]] = None):
        extra_states = extra_states or []
        extra_goals = extra_goals or []

        pred_vocab = set()
        io_vocab = set()
        resource_vocab = set()

        for c in capabilities:
            pred_vocab.update(c.preconditions)
            pred_vocab.update(c.effect_atoms())
            for spec in list(c.inputs) + list(c.outputs):
                io_vocab.add(spec.key())
            resource_vocab.update(c.resources)

        for s in extra_states:
            pred_vocab.update(s.atoms())
        for g in extra_goals:
            pred_vocab.update(g.conditions)

        self.layout = VectorLayout(
            type_dim=len(CAPABILITY_TYPES),
            mech_dim=HASH_DIM_MECHANISM,
            pred_vocab=sorted(pred_vocab),
            io_vocab=sorted(io_vocab),
            constraint_dim=HASH_DIM_CONSTRAINT,
            resource_vocab=sorted(resource_vocab),
            op_dim=7,  # time, money, resource, risk, energy, reliability, availability
        )
        self._pred_index = {a: i for i, a in enumerate(self.layout.pred_vocab)}
        self._io_index = {a: i for i, a in enumerate(self.layout.io_vocab)}
        self._res_index = {a: i for i, a in enumerate(self.layout.resource_vocab)}
        self._type_index = {t: i for i, t in enumerate(CAPABILITY_TYPES)}

        # Normalization constants for the operational block, derived from the
        # capability set so a single capability's cost is reported relative
        # to the rest of the dataset instead of an arbitrary fixed scale.
        times = [c.cost.get("time", 0.0) for c in capabilities] or [1.0]
        moneys = [c.cost.get("money", 0.0) for c in capabilities] or [1.0]
        resources = [c.cost.get("resource", 0.0) for c in capabilities] or [1.0]
        energies = [c.cost.get("energy", 0.0) for c in capabilities] or [1.0]
        self._norm = {
            "time": max(max(times), 1e-9),
            "money": max(max(moneys), 1e-9),
            "resource": max(max(resources), 1e-9),
            "energy": max(max(energies), 1e-9),
        }

    # ------------------------------------------------------------------
    # Multi-hot helpers
    # ------------------------------------------------------------------
    def _multi_hot(self, atoms: Iterable[str], index: Dict[str, int], dim: int) -> np.ndarray:
        v = np.zeros(dim, dtype=np.float64)
        for a in atoms:
            idx = index.get(a)
            if idx is not None:
                v[idx] = 1.0
        return v

    # ------------------------------------------------------------------
    # encode(state) / encode(goal)
    # ------------------------------------------------------------------
    def encode_state(self, s: State) -> np.ndarray:
        """States live in the same ground-atom space as preconditions/effects,
        so applicability can be checked as a direct atom-subset test."""
        return self._multi_hot(s.atoms(), self._pred_index, len(self.layout.pred_vocab))

    def encode_goal(self, g: Goal) -> np.ndarray:
        return self._multi_hot(g.conditions, self._pred_index, len(self.layout.pred_vocab))

    # ------------------------------------------------------------------
    # encode(capability)
    # ------------------------------------------------------------------
    def encode_capability(self, c: Capability) -> np.ndarray:
        type_v = np.zeros(self.layout.type_dim)
        type_v[self._type_index[c.type]] = 1.0

        mech_tokens = [f"{k}={v}" for k, v in c.mechanism.items()]
        if c.composed_of:
            mech_tokens.append("composed_of=" + ",".join(c.composed_of))
        mech_v = _hashed_vector(mech_tokens, self.layout.mech_dim)

        pre_v = self._multi_hot(c.preconditions, self._pred_index, len(self.layout.pred_vocab))
        eff_v = self._multi_hot(c.effect_atoms(), self._pred_index, len(self.layout.pred_vocab))

        in_v = self._multi_hot([spec.key() for spec in c.inputs], self._io_index, len(self.layout.io_vocab))
        out_v = self._multi_hot([spec.key() for spec in c.outputs], self._io_index, len(self.layout.io_vocab))

        con_v = _hashed_vector(c.constraints, self.layout.constraint_dim)
        res_v = self._multi_hot(c.resources, self._res_index, len(self.layout.resource_vocab))

        op_v = np.array([
            c.cost.get("time", 0.0) / self._norm["time"],
            c.cost.get("money", 0.0) / self._norm["money"],
            c.cost.get("resource", 0.0) / self._norm["resource"],
            c.cost.get("risk", 0.0),  # already in [0,1]
            c.cost.get("energy", 0.0) / self._norm["energy"],
            c.reliability,
            c.availability,
        ], dtype=np.float64)

        return np.concatenate([type_v, mech_v, pre_v, eff_v, in_v, out_v, con_v, res_v, op_v])

    # ------------------------------------------------------------------
    # similarity(x, y)
    # ------------------------------------------------------------------
    def similarity(self, v1: np.ndarray, v2: np.ndarray,
                    block: str = "functional", functional_only: Optional[bool] = None) -> float:
        """Cosine similarity, restricted to a chosen block:
          "full"            -- entire vector, including operational attributes
          "functional"      -- everything except operational (type/mechanism/P/E/I/O/K/R)
          "pure_function"   -- P/E/I/O/K/R only, excluding type and mechanism;
                                answers "same function, regardless of implementation?"
          "implementation"  -- type/mechanism only; answers "same implementation?"
        functional_only is accepted as a deprecated boolean alias
        (True -> "functional", False -> "full") for backward compatibility.
        """
        if functional_only is not None:
            block = "functional" if functional_only else "full"

        if block == "full":
            a, b = v1, v2
        elif block == "functional":
            s, e = self.layout.functional_slice()
            a, b = v1[s:e], v2[s:e]
        elif block == "pure_function":
            s, e = self.layout.pure_function_slice()
            a, b = v1[s:e], v2[s:e]
        elif block == "implementation":
            s, e = self.layout.implementation_slice()
            a, b = v1[s:e], v2[s:e]
        else:
            raise ValueError(f"Unknown block '{block}'")

        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    # ------------------------------------------------------------------
    # compatibility(Ci, Cj): directed, Ci -> Cj
    # ------------------------------------------------------------------
    def compatibility(self, ci: Capability, cj: Capability) -> Dict[str, object]:
        """
        Returns a dict with:
          effect_coverage  : fraction of Cj's preconditions entailed by Ci's effects
          io_coverage       : fraction of Cj's required inputs satisfiable by Ci's outputs
          contradiction     : True if Ci's effects directly negate a Cj precondition
                               on the same variable (e.g. OrderExists=true vs OrderExists=false)
          score             : weighted combination (0 if contradiction)
          compatible        : bool, score above threshold and no contradiction
        """
        ci_effects = dict(ci.effects)  # var -> value
        cj_pre_vars = {}
        for atom in cj.preconditions:
            # only equality atoms "var=value" are checked for entailment;
            # inequality atoms are treated as not-entailable from a single
            # equality effect (see Limitations in the report).
            if "=" in atom and not any(op in atom for op in (">", "<", "!")):
                var, _, val = atom.partition("=")
                cj_pre_vars[var] = val

        contradiction = False
        matched = 0
        for var, needed_val in cj_pre_vars.items():
            if var in ci_effects:
                produced_val = str(ci_effects[var])
                if produced_val == needed_val:
                    matched += 1
                else:
                    contradiction = True

        total_pre = max(len(cj_pre_vars), 1) if cj_pre_vars else 0
        effect_coverage = (matched / total_pre) if total_pre else 1.0

        cj_required_inputs = {spec.key() for spec in cj.inputs if spec.required}
        ci_outputs = {spec.key() for spec in ci.outputs}
        io_matched = len(cj_required_inputs & ci_outputs)
        io_total = max(len(cj_required_inputs), 1) if cj_required_inputs else 0
        io_coverage = (io_matched / io_total) if io_total else 1.0

        score = 0.0 if contradiction else (0.6 * effect_coverage + 0.4 * io_coverage)
        compatible = (not contradiction) and (effect_coverage >= 0.999)

        return {
            "effect_coverage": effect_coverage,
            "io_coverage": io_coverage,
            "contradiction": contradiction,
            "score": score,
            "compatible": compatible,
        }

    # ------------------------------------------------------------------
    # goal_relevance(Ci, G)
    # ------------------------------------------------------------------
    def goal_relevance(self, c: Capability, g: Goal) -> float:
        """Fraction of goal atoms directly produced by this capability's effects."""
        if not g.conditions:
            return 0.0
        g_vars = {}
        for atom in g.conditions:
            if "=" in atom:
                var, _, val = atom.partition("=")
                g_vars[var] = val
        if not g_vars:
            return 0.0
        matched = sum(
            1 for var, val in g_vars.items()
            if var in c.effects and str(c.effects[var]) == val
        )
        return matched / len(g_vars)

    # ------------------------------------------------------------------
    # applicability(Ci, S): does state S satisfy Ci's preconditions?
    # ------------------------------------------------------------------
    def applicability(self, c: Capability, s: State) -> Dict[str, object]:
        missing = []
        for atom in c.preconditions:
            ok = self._evaluate_atom(atom, s)
            if not ok:
                missing.append(atom)
        total = max(len(c.preconditions), 1)
        score = 1.0 - len(missing) / total if c.preconditions else 1.0
        return {"applicable": len(missing) == 0, "score": score, "missing": missing}

    @staticmethod
    def _evaluate_atom(atom: str, s: State) -> bool:
        for op in (">=", "<=", "!=", ">", "<", "="):
            if op in atom:
                var, _, raw = atom.partition(op)
                val = s.get(var)
                if val is None:
                    return False
                try:
                    lhs, rhs = float(val), float(raw)
                except (TypeError, ValueError):
                    lhs, rhs = val, raw
                    if op == "=":
                        return str(lhs) == str(rhs)
                    return False  # non-numeric comparison with inequality: undefined -> fail
                return {
                    ">": lhs > rhs, "<": lhs < rhs, ">=": lhs >= rhs,
                    "<=": lhs <= rhs, "!=": lhs != rhs, "=": lhs == rhs,
                }[op]
        return False

    # ------------------------------------------------------------------
    # compose(Ci, Cj): Ci executes before Cj. Returns a new Capability AND
    # its vector, so the composite is itself re-encodable / re-composable.
    # ------------------------------------------------------------------
    def compose(self, ci: Capability, cj: Capability, new_id: Optional[str] = None) -> Capability:
        compat = self.compatibility(ci, cj)
        if compat["contradiction"]:
            raise ValueError(
                f"Cannot compose {ci.id} -> {cj.id}: effect of {ci.id} "
                f"contradicts a precondition of {cj.id}."
            )

        # Preconditions: everything Ci needs, plus whatever Cj needs that
        # Ci's effects do not already establish.
        ci_effect_vars = set(ci.effects.keys())
        new_pre = list(ci.preconditions)
        for atom in cj.preconditions:
            if "=" in atom and not any(op in atom for op in (">", "<", "!")):
                var = atom.partition("=")[0]
                if var in ci_effect_vars and str(ci.effects[var]) == atom.partition("=")[2]:
                    continue  # already satisfied by Ci's effect
            if atom not in new_pre:
                new_pre.append(atom)

        # Effects: Ci's effects, overridden by Cj's effects on shared variables
        # (Cj runs second, so its effect on a variable is the final state).
        new_eff = dict(ci.effects)
        new_eff.update(cj.effects)

        # Inputs: Ci's inputs, plus Cj's required inputs not produced by Ci's outputs.
        ci_output_keys = {spec.key() for spec in ci.outputs}
        new_inputs = list(ci.inputs)
        existing_input_keys = {spec.key() for spec in new_inputs}
        for spec in cj.inputs:
            if spec.key() in ci_output_keys:
                continue
            if spec.key() not in existing_input_keys:
                new_inputs.append(spec)
                existing_input_keys.add(spec.key())

        # Outputs: union (downstream consumers may need either capability's output).
        new_outputs = list(ci.outputs)
        existing_output_keys = {spec.key() for spec in new_outputs}
        for spec in cj.outputs:
            if spec.key() not in existing_output_keys:
                new_outputs.append(spec)
                existing_output_keys.add(spec.key())

        new_constraints = tuple(dict.fromkeys(list(ci.constraints) + list(cj.constraints)))
        new_resources = tuple(sorted(set(ci.resources) | set(cj.resources)))

        new_cost = {
            "time": ci.cost.get("time", 0.0) + cj.cost.get("time", 0.0),
            "money": ci.cost.get("money", 0.0) + cj.cost.get("money", 0.0),
            "resource": ci.cost.get("resource", 0.0) + cj.cost.get("resource", 0.0),
            "risk": 1.0 - (1.0 - ci.cost.get("risk", 0.0)) * (1.0 - cj.cost.get("risk", 0.0)),
            "energy": ci.cost.get("energy", 0.0) + cj.cost.get("energy", 0.0),
        }
        new_reliability = ci.reliability * cj.reliability
        new_availability = min(ci.availability, cj.availability)

        composite_id = new_id or f"({ci.id}+{cj.id})"
        return Capability(
            id=composite_id,
            type="COMPOSITE",
            inputs=tuple(new_inputs),
            outputs=tuple(new_outputs),
            preconditions=tuple(new_pre),
            effects=new_eff,
            constraints=new_constraints,
            resources=new_resources,
            cost=new_cost,
            reliability=new_reliability,
            availability=new_availability,
            mechanism={"composition": f"{cj.id} after {ci.id}"},
            composed_of=tuple(list(ci.composed_of or (ci.id,)) + list(cj.composed_of or (cj.id,))),
        )

    def compose_chain(self, capabilities: List[Capability], new_id: Optional[str] = None) -> Capability:
        """Compose C1 -> C2 -> ... -> Cn left to right."""
        assert len(capabilities) >= 2
        acc = capabilities[0]
        for nxt in capabilities[1:]:
            acc = self.compose(acc, nxt)
        if new_id:
            acc = replace(acc, id=new_id)
        return acc
