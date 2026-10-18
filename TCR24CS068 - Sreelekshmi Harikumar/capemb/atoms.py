"""Atom universe: grounding typed state variables into a ternary literal space.

bool  x        -> 1 atom  "x"                       (+1 true / -1 false)
enum  x{a,b,c} -> 3 atoms "x=a","x=b","x=c"         (mutually exclusive)
int   n        -> atoms   "n>=c" for every cut-point c that occurs in the
                  specification (monotone: n>=c2  =>  n>=c1 for c1<c2)

A *ternary vector* over atoms has entries in {-1, 0, +1}:
   +1 literal asserted true, -1 asserted false, 0 unconstrained / unknown.
"""
from __future__ import annotations
import numpy as np
from .spec import Problem, Lit


def int_thresholds(lit: Lit):
    """Normalise an integer comparison into [(cut, polarity)] over atoms n>=cut."""
    t = lit.value
    return {">": [(t + 1, +1)], ">=": [(t, +1)], "<": [(t, -1)],
            "<=": [(t + 1, -1)], "==": [(t, +1), (t + 1, -1)]}[lit.op]


class AtomUniverse:
    def __init__(self, problem: Problem, extra_lits=()):
        self.problem = problem
        self.vars = {v.name: v for v in problem.vars}
        cuts = {v.name: set() for v in problem.vars if v.type == "int"}

        def reg(l: Lit):
            v = self.vars[l.var]
            if v.type == "int":
                if l.op not in (">", ">=", "<", "<=", "=="):
                    raise ValueError(f"unsupported int op {l.op} on {l.var}")
                for c, _ in int_thresholds(l):
                    cuts[l.var].add(c)

        for c in problem.caps:
            for l in list(c.pre) + list(c.guards):
                reg(l)
        for g in problem.goals.values():
            for l in g:
                reg(l)
        for k in problem.global_constraints:
            for l in k["forbid"]:
                reg(l)
        for l in extra_lits:
            reg(l)

        self.names, self.index, self.groups, self.cutvals = [], {}, {}, {}
        for v in problem.vars:
            idxs = []
            if v.type == "bool":
                idxs.append(self._add((v.name, "T"), v.name))
            elif v.type == "enum":
                for val in v.values:
                    idxs.append(self._add((v.name, val), f"{v.name}={val}"))
            else:
                self.cutvals[v.name] = sorted(cuts[v.name])
                for c in self.cutvals[v.name]:
                    idxs.append(self._add((v.name, c), f"{v.name}>={c}"))
            self.groups[v.name] = np.array(idxs, dtype=int)
        self.d = len(self.names)

    def _add(self, key, name):
        self.index[key] = len(self.names)
        self.names.append(name)
        return self.index[key]

    # ---- literal / assignment grounding ----------------------------------
    def lit_vec(self, lit: Lit):
        """Primary atoms of a condition -> {atom: polarity}."""
        v = self.vars[lit.var]
        out = {}
        if v.type == "bool":
            want = bool(lit.value) if lit.op == "==" else not bool(lit.value)
            out[self.index[(v.name, "T")]] = +1 if want else -1
        elif v.type == "enum":
            op, x = lit.op, lit.value
            if op == "==":
                out[self.index[(v.name, x)]] = +1
            elif op == "!=":
                out[self.index[(v.name, x)]] = -1
            elif op == "in":
                S = set(x)
                if len(S) == 1:
                    out[self.index[(v.name, next(iter(S)))]] = +1
                else:
                    for val in v.values:
                        if val not in S:
                            out[self.index[(v.name, val)]] = -1
            elif op == "not_in":
                for val in x:
                    out[self.index[(v.name, val)]] = -1
            else:
                raise ValueError(op)
        else:
            for c, pol in int_thresholds(lit):
                out[self.index[(v.name, c)]] = pol
        return out

    def assign_vec(self, var, value):
        """Effect  var := value  -> full ternary assignment of the var's group."""
        v = self.vars[var]
        out = {}
        if v.type == "bool":
            out[self.index[(var, "T")]] = +1 if value else -1
        elif v.type == "enum":
            for val in v.values:
                out[self.index[(var, val)]] = +1 if val == value else -1
        else:
            for c in self.cutvals[var]:
                out[self.index[(var, c)]] = +1 if value >= c else -1
        return out

    # ---- vectors -----------------------------------------------------------
    def zeros(self):
        return np.zeros(self.d)

    def from_lits(self, lits):
        v = self.zeros()
        for l in lits:
            for i, p in self.lit_vec(l).items():
                if v[i] == -p:
                    raise ValueError(f"contradictory literals on {self.names[i]}")
                v[i] = p
        return v

    def from_assign(self, effects: dict):
        v = self.zeros()
        for var, val in effects.items():
            for i, p in self.assign_vec(var, val).items():
                v[i] = p
        return v

    def state_vec(self, state: dict):
        """Complete (bipolar) state encoding phi_S."""
        v = self.zeros()
        for var, val in state.items():
            for i, p in self.assign_vec(var, val).items():
                v[i] = p
        return v

    def saturate(self, v):
        """Add literals implied by the typed structure (enum exclusivity,
        integer monotonicity).  Never removes information."""
        v = v.copy()
        for name, idx in self.groups.items():
            if len(idx) == 0:
                continue
            t = self.vars[name].type
            vals = v[idx]
            if t == "enum":
                if (vals == 1).any():
                    vals = np.where(vals == 1, 1, -1)
                elif (vals != -1).sum() == 1:
                    vals = np.where(vals != -1, 1, -1)
                v[idx] = vals
            elif t == "int":
                pos = np.where(vals == 1)[0]
                neg = np.where(vals == -1)[0]
                if len(pos):
                    m = pos.max()
                    vals[: m + 1] = np.where(vals[: m + 1] == -1, -1, 1)
                if len(neg):
                    m = neg.min()
                    vals[m:] = np.where(vals[m:] == 1, 1, -1)
                v[idx] = vals
        return v

    def describe(self, v):
        """Human-readable list of non-zero atoms (for reports)."""
        return [("" if v[i] > 0 else "NOT ") + self.names[i] for i in np.nonzero(v)[0]]

    def decode_witness(self, v, rng):
        """Pick a concrete state satisfying ternary vector v (used in tests)."""
        state = {}
        for name, idx in self.groups.items():
            var = self.vars[name]
            vals = v[idx] if len(idx) else np.array([])
            if var.type == "bool":
                state[name] = bool(vals[0] == 1) if vals[0] != 0 else bool(rng.integers(2))
            elif var.type == "enum":
                if (vals == 1).any():
                    state[name] = var.values[int(np.argmax(vals == 1))]
                else:
                    ok = [x for x, t in zip(var.values, vals) if t != -1]
                    state[name] = ok[rng.integers(len(ok))]
            else:
                lo, hi = var.lo, var.hi
                for c, t in zip(self.cutvals[name], vals):
                    if t == 1:
                        lo = max(lo, c)
                    elif t == -1:
                        hi = min(hi, c - 1)
                if lo > hi:
                    lo = hi = var.lo
                state[name] = int(rng.integers(lo, hi + 1))
        return state
