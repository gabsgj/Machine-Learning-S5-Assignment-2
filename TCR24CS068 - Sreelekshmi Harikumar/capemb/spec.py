"""Formal application model  A = (S, C, S_I, G, R, K)  and capability 11-tuple.

Everything here is *formal* (typed literals, ports, numbers).  The free-text
`description` fields exist only for documentation and for the text-embedding
baseline in the experiments; the embedding never reads them.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

CAP_TYPES = ["API", "DATABASE", "GUI", "EVENT", "FUNCTION", "FILE",
             "COMPUTATION", "MESSAGE", "SERVICE"]
OPS = {"==", "!=", ">", ">=", "<", "<=", "in", "not_in"}


@dataclass(frozen=True)
class Var:
    name: str
    type: str                 # "bool" | "enum" | "int"
    values: Tuple = ()        # enum domain
    lo: int = 0               # int domain
    hi: int = 1


@dataclass(frozen=True)
class Lit:
    """A condition  var <op> value  (used in preconditions, guards, goals)."""
    var: str
    op: str
    value: object

    def __str__(self):
        return f"{self.var} {self.op} {self.value}"


@dataclass(frozen=True)
class Port:
    name: str
    type: str
    domain: str
    required: bool = True

    @property
    def key(self):
        return f"{self.name}:{self.type}:{self.domain}"


@dataclass
class Capability:
    id: str
    type: str
    description: str = ""
    inputs: List[Port] = field(default_factory=list)
    outputs: List[Port] = field(default_factory=list)
    pre: List[Lit] = field(default_factory=list)            # P_i
    effects: Dict[str, object] = field(default_factory=dict)  # E_i  (var := value)
    guards: List[Lit] = field(default_factory=list)         # K_i (state-grounded)
    resources: List[str] = field(default_factory=list)      # R_i
    qos: Dict[str, float] = field(default_factory=dict)     # Q_i
    reliability: float = 1.0                                # Rel_i
    available: bool = True                                  # A_i
    window: Tuple[float, float] = (0.0, 24.0)               # A_i(t) window (hours)
    mechanism: Dict[str, str] = field(default_factory=dict)  # M_i
    alt_group: Optional[str] = None                         # ground truth for Exp.3 only

    def reads(self):
        return {l.var for l in self.pre} | {l.var for l in self.guards}


@dataclass
class Problem:
    id: str
    domain: str
    description: str
    vars: List[Var]
    init: Dict[str, object]
    goals: Dict[str, List[Lit]]          # named goals; "main" is G
    goal_text: Dict[str, str]
    resources: List[str]
    environment: List[str]               # resources currently available
    global_constraints: List[dict]       # K: {"id","forbid":[Lit,...]}
    domain_parent: Dict[str, str]        # port-domain hierarchy child -> parent
    context_ports: List[Port]
    caps: List[Capability]

    @property
    def goal(self):
        return self.goals["main"]

    def cap(self, cid):
        for c in self.caps:
            if c.id == cid:
                return c
        raise KeyError(cid)

    def var(self, name):
        for v in self.vars:
            if v.name == name:
                return v
        raise KeyError(name)


def _lit(d):
    v = d["value"]
    if isinstance(v, list):
        v = tuple(v)
    if d["op"] not in OPS:
        raise ValueError(f"bad op {d['op']}")
    return Lit(d["var"], d["op"], v)


def _port(d):
    return Port(d["name"], d["type"], d["domain"], d.get("required", True))


def load_problem(path) -> Problem:
    with open(path) as f:
        j = json.load(f)
    vars_ = [Var(v["name"], v["type"], tuple(v.get("values", ())),
                 v.get("lo", 0), v.get("hi", 1)) for v in j["state_variables"]]
    caps = []
    for c in j["capabilities"]:
        q = c.get("qos", {})
        av = c.get("availability", {})
        caps.append(Capability(
            id=c["id"], type=c["type"], description=c.get("description", ""),
            inputs=[_port(p) for p in c.get("inputs", [])],
            outputs=[_port(p) for p in c.get("outputs", [])],
            pre=[_lit(l) for l in c.get("preconditions", [])],
            effects={e["var"]: e["value"] for e in c.get("effects", [])},
            guards=[_lit(l) for l in c.get("constraints", [])],
            resources=list(c.get("resources", [])), qos=q,
            reliability=c.get("reliability", 1.0),
            available=av.get("available", True),
            window=tuple(av.get("window", (0.0, 24.0))),
            mechanism=c.get("mechanism", {}), alt_group=c.get("alt_group")))
    goals = {k: [_lit(l) for l in v] for k, v in j["goals"].items()}
    gk = [{"id": k["id"], "forbid": [_lit(l) for l in k["forbid"]],
           "description": k.get("description", "")}
          for k in j.get("global_constraints", [])]
    return Problem(j["problem_id"], j["domain"], j.get("description", ""), vars_,
                   j["initial_state"], goals, j.get("goal_text", {}),
                   j.get("resources", []), j.get("environment", j.get("resources", [])),
                   gk, j.get("domain_parent", {}),
                   [_port(p) for p in j.get("context_ports", [])], caps)
