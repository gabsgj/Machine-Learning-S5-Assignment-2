"""Concrete-value semantics and ground-truth oracles (EVALUATION ONLY).

None of this is used by the embedding.  It re-implements the meaning of
preconditions / effects directly on concrete values (True/False, enum names,
integers) so the vector algebra can be checked against an *independent* source
of truth:

  * pair_label  : exhaustive check over concrete valuations -> 4-way label
  * relevant_caps: capabilities occurring in some irredundant goal-reaching
                   sequence (brute-force reachability; used ONLY to label data,
                   it is not part of the embedding or its API)
"""
from __future__ import annotations
import itertools
import numpy as np
from .spec import Problem, Capability, Lit

CONFLICT, INDEPENDENT, PARTIAL, STRICT = 0, 1, 2, 3


def holds(l: Lit, s: dict) -> bool:
    v, x = s[l.var], l.value
    return {"==": lambda: v == x, "!=": lambda: v != x, ">": lambda: v > x,
            ">=": lambda: v >= x, "<": lambda: v < x, "<=": lambda: v <= x,
            "in": lambda: v in x, "not_in": lambda: v not in x}[l.op]()


def applicable(c: Capability, s: dict) -> bool:
    return all(holds(l, s) for l in c.pre) and all(holds(l, s) for l in c.guards)


def apply(c: Capability, s: dict) -> dict:
    t = dict(s)
    t.update(c.effects)
    return t


def sat(goal, s):
    return all(holds(l, s) for l in goal)


def rep_values(p: Problem, var: str, lits):
    v = p.var(var)
    if v.type == "bool":
        return [False, True]
    if v.type == "enum":
        return list(v.values)
    reps = {v.lo, v.hi}
    for l in lits:
        if l.var == var:
            for t in (l.value if isinstance(l.value, tuple) else (l.value,)):
                reps |= {t - 1, t, t + 1}
    return sorted(x for x in reps if v.lo <= x <= v.hi)


def _anc(p: Problem, d):
    out = {d}
    while d in p.domain_parent:
        d = p.domain_parent[d]
        out.add(d)
    return out


def _port_sets(p: Problem, c: Capability):
    out = set()
    for q in c.outputs:
        for d in _anc(p, q.domain):
            out.add((q.name, q.type, d))
    inp = {(q.name, q.type, q.domain) for q in c.inputs if q.required}
    return out, inp


def pair_label(p: Problem, a: Capability, b: Capability, use_ports=True,
               max_states=40000, seed=0) -> int:
    """Ground-truth relation 'b after a' by exhaustive valuation enumeration."""
    lits = list(a.pre) + list(a.guards) + list(b.pre) + list(b.guards)
    vars_ = sorted(a.reads() | b.reads())
    domains = [rep_values(p, v, lits) for v in vars_]
    total = int(np.prod([len(d) for d in domains])) if domains else 1
    if total > max_states:
        rng = np.random.default_rng(seed)
        combos = (tuple(d[rng.integers(len(d))] for d in domains) for _ in range(max_states))
    else:
        combos = itertools.product(*domains)
    base = dict(p.init)
    chain = contrib = False
    always = True
    seen_a = False
    for combo in combos:
        s = dict(base)
        s.update(dict(zip(vars_, combo)))
        if not applicable(a, s):
            continue
        seen_a = True
        s2 = apply(a, s)
        ok2 = applicable(b, s2)
        ok1 = applicable(b, s)
        chain |= ok2
        contrib |= (ok2 and not ok1)
        always &= ok2
    out_a, in_a = _port_sets(p, a)
    _, in_b = _port_sets(p, b)
    avail = out_a | in_a
    if use_ports:
        port_supply = any(k in out_a for k in in_b)
        port_cov = all(k in avail for k in in_b)
    else:
        port_supply, port_cov = False, True
    if not chain:
        return CONFLICT
    if not (contrib or port_supply):
        return INDEPENDENT
    if always and port_cov:
        return STRICT
    return PARTIAL


def label_matrix(p: Problem, use_ports=True):
    n = len(p.caps)
    M = np.zeros((n, n), int)
    for i, a in enumerate(p.caps):
        for j, b in enumerate(p.caps):
            M[i, j] = pair_label(p, a, b, use_ports)
    return M


# ----------------------------------------------------------- goal relevance
def relevant_caps(p: Problem, goal, extra_len=1, max_nodes=400000):
    """Capabilities appearing in at least one *irredundant* goal-reaching sequence
    (each capability used at most once).  Brute force; ground truth for Exp. 4."""
    caps = p.caps
    init = dict(p.init)
    # shortest plan length by BFS over (state, used) is overkill; iterative deepening
    result, shortest = set(), None
    nodes = [0]

    def valid_seq(seq):
        s = dict(init)
        for c in seq:
            if not applicable(c, s):
                return False
            s = apply(c, s)
        return sat(goal, s)

    def irredundant(seq):
        for i in range(len(seq)):
            if valid_seq(seq[:i] + seq[i + 1:]):
                return False
        return True

    def dfs(s, seq, used, limit):
        nodes[0] += 1
        if nodes[0] > max_nodes:
            return
        if sat(goal, s):
            if irredundant(seq):
                result.update(c.id for c in seq)
            return
        if len(seq) >= limit:
            return
        for c in caps:
            if c.id in used or not applicable(c, s):
                continue
            s2 = apply(c, s)
            if s2 == s:
                continue
            dfs(s2, seq + [c], used | {c.id}, limit)

    for limit in range(1, 14):
        nodes[0] = 0
        dfs(init, [], frozenset(), limit)
        if result:
            shortest = limit
            break
    if shortest is not None and extra_len:
        nodes[0] = 0
        dfs(init, [], frozenset(), shortest + extra_len)
    return result, shortest


# ---------------------------------------------------------- random states
def random_state(p: Problem, rng):
    s = {}
    for v in p.vars:
        if v.type == "bool":
            s[v.name] = bool(rng.integers(2))
        elif v.type == "enum":
            s[v.name] = v.values[rng.integers(len(v.values))]
        else:
            s[v.name] = int(rng.integers(v.lo, v.hi + 1))
    return s
