"""Structured, compositional capability embedding.

A capability is embedded as a *partitioned* vector (blocks):

  algebraic blocks (used by compat / compose; exact)
     pre  : ternary over atoms   preconditions P_i
     grd  : ternary over atoms   state-grounded constraints K_i
     eff  : ternary over atoms   effects E_i  (type-saturated assignments)
     inp  : {0,.5,1} over ports  required (1) / optional (.5) inputs I_i
     out  : {0,1}    over ports  outputs O_i (closed under domain hierarchy)
     typ  : counts   over the 9 capability types T_i
     mech : hashed counts (signed feature hashing) execution mechanism M_i
     res  : {0,1}    over resources R_i
     qadd : [time, money, res-cost, energy, hazard, -ln Rel]  (additive monoid)
     qext : [availability(min), window-start(max), window-end(min)]

Composition  C2 o C1  is a monoid homomorphism block by block (see compose2).
Similarity (symmetric, "what is it like?") and compatibility (directed,
"can B run after A?") are different measures over the same blocks.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional, Sequence
import numpy as np

from .spec import Problem, Capability, CAP_TYPES, Lit
from .atoms import AtomUniverse

CONFLICT, INDEPENDENT, PARTIAL, STRICT = 0, 1, 2, 3
LABELS = ["CONFLICT", "INDEPENDENT", "PARTIAL", "STRICT"]

W_FUNC = dict(pre=0.20, grd=0.10, eff=0.40, inp=0.10, out=0.20)
W_IMPL = dict(typ=0.40, mech=0.40, res=0.20)
W_OVERALL = dict(func=0.70, impl=0.15, qos=0.15)
QOS_KEYS = ["time_ms", "money", "resource_cost", "energy"]


# ------------------------------------------------------------------ helpers
def merge(a, b):
    return np.where(a != 0, a, b)


def cos0(a, b):
    """Cosine with the convention  cos(0,0)=1  (both 'empty' => identical)."""
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 and nb == 0:
        return 1.0
    if na == 0 or nb == 0:
        return 0.0
    return float(a @ b / (na * nb))


def _hash(token, d):
    h = int(hashlib.md5(token.encode()).hexdigest()[:12], 16)
    return h % d, (1.0 if (h >> 40) & 1 else -1.0)


@dataclass
class StateEmb:
    vec: np.ndarray


@dataclass
class GoalEmb:
    vec: np.ndarray


@dataclass
class Context:
    state: Optional[np.ndarray] = None     # saturated state vector (or None=unknown)
    ports: Optional[np.ndarray] = None     # data available in the environment


@dataclass
class CapEmb:
    id: str
    parts: tuple
    pre: np.ndarray
    grd: np.ndarray
    eff: np.ndarray
    inp: np.ndarray
    out: np.ndarray
    typ: np.ndarray
    mech: np.ndarray
    res: np.ndarray
    qadd: np.ndarray
    qext: np.ndarray
    valid: bool = True
    conflicts: list = field(default_factory=list)

    @property
    def is_composite(self):
        return len(self.parts) > 1

    def req(self):
        return merge(self.pre, self.grd)

    def blocks(self):
        return dict(pre=self.pre, grd=self.grd, eff=self.eff, inp=self.inp,
                    out=self.out, typ=self.typ, mech=self.mech, res=self.res,
                    qadd=self.qadd, qext=self.qext)


# --------------------------------------------------------------- embedder
class CapabilityEmbedder:
    def __init__(self, problem: Problem, d_mech: int = 64,
                 w_func=None, w_impl=None, w_overall=None):
        self.p = problem
        self.U = AtomUniverse(problem)
        self.d_mech = d_mech
        self.w_func = w_func or W_FUNC
        self.w_impl = w_impl or W_IMPL
        self.w_overall = w_overall or W_OVERALL
        # port vocabulary (with domain-hierarchy closure on outputs/context)
        keys = set()
        for c in problem.caps:
            for q in c.inputs:
                keys.add(q.key)
            for q in c.outputs:
                keys |= set(self._closure_keys(q))
        for q in problem.context_ports:
            keys |= set(self._closure_keys(q))
        self.port_keys = sorted(keys)
        self.pidx = {k: i for i, k in enumerate(self.port_keys)}
        self.res_names = sorted(set(problem.resources) |
                                {r for c in problem.caps for r in c.resources})
        self.ridx = {r: i for i, r in enumerate(self.res_names)}
        self.tidx = {t: i for i, t in enumerate(CAP_TYPES)}
        # dataset-wide scales for the *metric view* of QoS
        qs = [self._qadd(c) for c in problem.caps]
        self.scale = np.maximum(np.max(qs, axis=0), 1e-9)
        self.caps = {c.id: self.encode_capability(c) for c in problem.caps}
        self.ctx_ports = self._port_vec(problem.context_ports, closure=True)

    # ---------------------------------------------------------- port utils
    def _closure_keys(self, port):
        keys, d, seen = [], port.domain, set()
        while d is not None and d not in seen:
            keys.append(f"{port.name}:{port.type}:{d}")
            seen.add(d)
            d = self.p.domain_parent.get(d)
        return keys

    def _port_vec(self, ports, closure=False):
        v = np.zeros(len(self.port_keys))
        for q in ports:
            ks = self._closure_keys(q) if closure else [q.key]
            for k in ks:
                v[self.pidx[k]] = max(v[self.pidx[k]], 1.0 if (q.required or closure) else 0.5)
        return v

    # ------------------------------------------------------------- QoS
    def _qadd(self, c: Capability):
        q = c.qos
        risk = min(max(q.get("risk", 0.0), 0.0), 0.999999)
        rel = min(max(c.reliability, 1e-9), 1.0)
        return np.array([q.get("time_ms", 0.0), q.get("money", 0.0),
                         q.get("resource_cost", 0.0), q.get("energy", 0.0),
                         -np.log(1 - risk), -np.log(rel)])

    def qos_metric(self, e: CapEmb):
        """Metric view of operational attributes, normalised per problem:
        [time(log), money, resource, energy, risk, unreliability] ~ [0,1]."""
        a = e.qadd
        s = self.scale
        return np.array([np.log1p(a[0]) / np.log1p(s[0]), a[1] / s[1], a[2] / s[2],
                         a[3] / s[3], 1 - np.exp(-a[4]), 1 - np.exp(-a[5])])

    def reliability(self, e):
        return float(np.exp(-e.qadd[5]))

    def risk(self, e):
        return float(1 - np.exp(-e.qadd[4]))

    # ------------------------------------------------------ encode: atoms
    def encode_state(self, state: dict) -> StateEmb:
        return StateEmb(self.U.saturate(self.U.state_vec(state)))

    def encode_goal(self, goal: Sequence[Lit]) -> GoalEmb:
        return GoalEmb(self.U.from_lits(goal))

    def encode_capability(self, c: Capability) -> CapEmb:
        U = self.U
        mech = np.zeros(self.d_mech)
        toks = [f"type:{c.type}"] + [f"{k}" for k in c.mechanism] + \
               [f"{k}={v}" for k, v in c.mechanism.items()]
        for t in toks[1:]:
            i, s = _hash(t, self.d_mech)
            mech[i] += s
        typ = np.zeros(len(CAP_TYPES))
        typ[self.tidx[c.type]] = 1
        res = np.zeros(len(self.res_names))
        for r in c.resources:
            res[self.ridx[r]] = 1
        qext = np.array([1.0 if c.available else 0.0, c.window[0], c.window[1]])
        return CapEmb(id=c.id, parts=(c.id,), pre=U.from_lits(c.pre),
                      grd=U.from_lits(c.guards), eff=U.from_assign(c.effects),
                      inp=self._port_vec(c.inputs), out=self._out_vec(c), typ=typ, mech=mech, res=res,
                      qadd=self._qadd(c), qext=qext)

    def _out_vec(self, c):
        v = np.zeros(len(self.port_keys))
        for q in c.outputs:
            for k in self._closure_keys(q):
                v[self.pidx[k]] = 1.0
        return v

    def encode(self, x):
        """encode(state | goal | capability | capability-id | composite)."""
        if isinstance(x, (CapEmb, StateEmb, GoalEmb)):
            return x
        if isinstance(x, Capability):
            return self.caps.get(x.id) or self.encode_capability(x)
        if isinstance(x, str):
            return self.caps[x]
        if isinstance(x, dict):
            return self.encode_state(x)
        if isinstance(x, (list, tuple)):
            if x and isinstance(x[0], Lit):
                return self.encode_goal(x)
            return self.compose(x)
        raise TypeError(type(x))

    def context(self, state: Optional[dict] = None, with_ports=True) -> Context:
        return Context(self.encode_state(state).vec if state is not None else None,
                       self.ctx_ports if with_ports else None)

    # ------------------------------------------------------------ compose
    def compose2(self, a, b) -> CapEmb:
        """b o a : run a first, then b.  Block-wise monoid homomorphism."""
        a, b = self.encode(a), self.encode(b)
        U = self.U
        reqA, reqB = a.req(), b.req()
        gA = np.where(a.eff != 0, a.eff, U.saturate(reqA))      # guarantee after a
        bad = (reqB != 0) & (gA == -reqB)
        touched = a.eff != 0
        keep = lambda x: np.where(touched, 0.0, x)
        pre = merge(a.pre, keep(b.pre))
        grd = merge(a.grd, keep(b.grd))
        eff = np.where(b.eff != 0, b.eff, a.eff)                # last writer wins
        inp = np.maximum(a.inp, b.inp * (1 - np.clip(a.out, 0, 1)))
        out = np.maximum(a.out, b.out)
        qext = np.array([min(a.qext[0], b.qext[0]), max(a.qext[1], b.qext[1]),
                         min(a.qext[2], b.qext[2])])
        conflicts = a.conflicts + b.conflicts + [U.names[i] for i in np.nonzero(bad)[0]]
        return CapEmb(id=f"{b.id}∘{a.id}", parts=a.parts + b.parts, pre=pre, grd=grd,
                      eff=eff, inp=inp, out=out, typ=a.typ + b.typ, mech=a.mech + b.mech,
                      res=np.maximum(a.res, b.res), qadd=a.qadd + b.qadd, qext=qext,
                      valid=a.valid and b.valid and not bad.any(), conflicts=conflicts)

    def compose(self, seq) -> CapEmb:
        """compose([C1, C2, ..., Cn]) = Cn o ... o C1  (C1 executes first)."""
        seq = [self.encode(x) for x in seq]
        out = seq[0]
        for nxt in seq[1:]:
            out = self.compose2(out, nxt)
        return out

    # ---------------------------------------------- state-capability layer
    def apply(self, state: StateEmb, c: CapEmb) -> StateEmb:
        """phi_S(Apply(S,E)) = phi_S(S) (+) e   (override)."""
        return StateEmb(np.where(c.eff != 0, c.eff, state.vec))

    def applicability(self, state: StateEmb, c: CapEmb):
        """(coverage, conflict-fraction): how much of req(c) holds in state."""
        r = c.req()
        need = r != 0
        N = need.sum()
        if N == 0:
            return 1.0, 0.0
        s = state.vec
        return float((need & (s == r)).sum() / N), float((need & (s == -r)).sum() / N)

    def is_applicable(self, state: StateEmb, c: CapEmb):
        cov, conf = self.applicability(state, c)
        return c.valid and cov == 1.0 and conf == 0.0

    def goal_progress(self, state: StateEmb, goal: GoalEmb):
        g = goal.vec
        n = (g != 0).sum()
        return 1.0 if n == 0 else float(((g != 0) & (state.vec == g)).sum() / n)

    # ------------------------------------------------- compatibility (A->B)
    def compat_matrix(self, A, B=None, ctx: Optional[Context] = None,
                      persist=True, saturate=True, use_ports=True):
        """Directed compatibility of every a in A with every b in B ("b after a")."""
        A = [self.encode(a) for a in A]
        B = A if B is None else [self.encode(b) for b in B]
        U = self.U
        reqA = np.stack([a.req() for a in A])
        base = np.stack([U.saturate(r) for r in reqA]) if saturate else reqA.copy()
        if not persist:
            base = np.zeros_like(base)
        E = np.stack([a.eff for a in A])
        G = np.where(E != 0, E, base)
        if ctx is not None and ctx.state is not None:
            G = np.where(G != 0, G, ctx.state[None, :])
        R = np.stack([b.req() for b in B])
        Nov = np.where((E != 0) & (E != base), E, 0.0)
        pn = lambda x: ((x > 0).astype(float), (x < 0).astype(float))
        Gp, Gn = pn(G); Rp, Rn = pn(R); Vp, Vn = pn(Nov)
        match = Gp @ Rp.T + Gn @ Rn.T
        conf = Gp @ Rn.T + Gn @ Rp.T
        supply = Vp @ Rp.T + Vn @ Rn.T
        N = np.abs(R).sum(1)[None, :]
        safe = np.where(N == 0, 1, N)
        cov = np.where(N == 0, 1.0, match / safe)
        conff = np.where(N == 0, 0.0, conf / safe)
        if use_ports:
            Out = np.stack([a.out for a in A])
            Inp = np.stack([(a.inp >= 1).astype(float) for a in A])
            Av = np.maximum(Out, Inp) if persist else Out
            if ctx is not None and ctx.ports is not None:
                Av = np.maximum(Av, ctx.ports[None, :])
            Need = np.stack([(b.inp >= 1).astype(float) for b in B])
            Nio = Need.sum(1)[None, :]
            sio = np.where(Nio == 0, 1, Nio)
            covio = np.where(Nio == 0, 1.0, (Av @ Need.T) / sio)
            supio = (Out > 0).astype(float) @ Need.T
        else:
            covio = np.ones_like(cov)
            supio = np.zeros_like(cov)
        label = np.full(cov.shape, PARTIAL)
        label[(cov > 1 - 1e-9) & (covio > 1 - 1e-9)] = STRICT
        indep = (supply == 0) & (supio == 0)
        label[indep] = INDEPENDENT
        label[conf > 0] = CONFLICT
        score = np.where(conf > 0, -conff, np.where(indep, 0.0, np.minimum(cov, covio)))
        return dict(label=label, score=score, cov=cov, conflict=conff, supply=supply,
                    covio=covio, supio=supio,
                    applicable=(conf == 0) & (cov > 1 - 1e-9) & (covio > 1 - 1e-9))

    def compat(self, a, b, ctx: Optional[Context] = None, **kw):
        m = self.compat_matrix([a], [b], ctx, **kw)
        r = {k: v[0, 0] for k, v in m.items()}
        r["label_name"] = LABELS[int(r["label"])]
        return r

    def naive_compat_matrix(self, A, B=None):
        """Baseline: raw dot product <e_a, req_b> (no saturation, persistence, ports)."""
        A = [self.encode(a) for a in A]
        B = A if B is None else [self.encode(b) for b in B]
        E = np.stack([a.eff for a in A])
        R = np.stack([b.req() for b in B])
        dot = E @ R.T
        N = np.maximum(np.abs(R).sum(1)[None, :], 1)
        sc = dot / N
        sup = (np.where(E > 0, E, 0) @ np.where(R > 0, R, 0).T +
               np.where(E < 0, -E, 0) @ np.where(R < 0, -R, 0).T)
        label = np.full(sc.shape, PARTIAL)
        label[sc >= 1 - 1e-9] = STRICT
        label[(dot == 0) & (sup == 0)] = INDEPENDENT
        label[dot < 0] = CONFLICT
        return dict(label=label, score=sc)

    # ----------------------------------------------------------- similarity
    @staticmethod
    def _block_sim(a, b, weights):
        """Weighted block cosine.  A block that is empty in BOTH capabilities carries
        no information and is dropped from the weighted average (weights renormalised)."""
        num = den = 0.0
        for k, w in weights.items():
            x, y = getattr(a, k), getattr(b, k)
            if not x.any() and not y.any():
                continue
            num += w * cos0(x, y)
            den += w
        return num / den if den else 1.0

    def similarity_report(self, a, b):
        a, b = self.encode(a), self.encode(b)
        f = self._block_sim(a, b, self.w_func)
        im = self._block_sim(a, b, self.w_impl)
        qa, qb = self.qos_metric(a), self.qos_metric(b)
        q = float(max(0.0, 1 - np.mean(np.abs(qa - qb))))
        o = self.w_overall
        return dict(func=f, impl=im, qos=q,
                    overall=o["func"] * f + o["impl"] * im + o["qos"] * q)

    def similarity(self, x, y, mode="overall"):
        """Compare two encoded entities (type-dispatched).

        cap~cap     : overall / func / impl / qos similarity   (symmetric)
        state~cap   : precondition coverage minus conflict      (applicability)
        cap~goal    : direct goal alignment
        state~goal  : goal progress
        state~state : cosine of bipolar vectors
        goal~goal   : cosine
        """
        x, y = self.encode(x), self.encode(y)
        if isinstance(x, CapEmb) and isinstance(y, CapEmb):
            return self.similarity_report(x, y)[mode]
        if isinstance(x, StateEmb) and isinstance(y, CapEmb):
            cov, conf = self.applicability(x, y)
            return cov - conf
        if isinstance(x, CapEmb) and isinstance(y, StateEmb):
            return self.similarity(y, x)
        if isinstance(x, CapEmb) and isinstance(y, GoalEmb):
            return self.direct_alignment(x, y)
        if isinstance(x, GoalEmb) and isinstance(y, CapEmb):
            return self.direct_alignment(y, x)
        if isinstance(x, StateEmb) and isinstance(y, GoalEmb):
            return self.goal_progress(x, y)
        if isinstance(x, GoalEmb) and isinstance(y, StateEmb):
            return self.goal_progress(y, x)
        return cos0(x.vec, y.vec)

    def flat(self, e: CapEmb) -> np.ndarray:
        """Single dense vector for ANN indexing: weighted, unit-normalised blocks.
        cos(flat(a), flat(b)) ~ weighted block cosines (see report, Sec. 5)."""
        parts = []
        o = self.w_overall
        for k, w in self.w_func.items():
            v = getattr(e, k)
            n = np.linalg.norm(v)
            parts.append(np.sqrt(o["func"] * w) * (v / n if n else v))
        for k, w in self.w_impl.items():
            v = getattr(e, k)
            n = np.linalg.norm(v)
            parts.append(np.sqrt(o["impl"] * w) * (v / n if n else v))
        parts.append(np.sqrt(o["qos"]) * self.qos_metric(e) / np.sqrt(6))
        return np.concatenate(parts)

    # ---------------------------------------------------------- goal layer
    def direct_alignment(self, c: CapEmb, goal: GoalEmb, state: Optional[StateEmb] = None):
        g = goal.vec
        unmet = np.where(g != 0, g, 0) if state is None else np.where((g != 0) & (state.vec != g), g, 0)
        gain = ((c.eff == unmet) & (unmet != 0)).sum()
        harm = ((c.eff == -g) & (g != 0)).sum()
        n = max(1, (g != 0).sum())
        return float((gain - harm) / n)

    def goal_relevance(self, goal: GoalEmb, state: Optional[StateEmb] = None,
                       caps: Optional[List[CapEmb]] = None, lam: float = 0.85):
        """Backward relevance propagation in vector space (NOT a plan search).

        need+/need- : atoms needed true / false.  A capability is relevant at depth t
        if one of its effects/outputs supplies a currently needed literal; its own
        (still unsatisfied) requirements then become needs for depth t+1.
        Score = lam**depth;  harm flags effects contradicting a goal literal."""
        caps = caps or list(self.caps.values())
        g = goal.vec
        s = state.vec if state is not None else None
        unmet = (g != 0) & ((s is None) | (s != g)) if s is not None else (g != 0)
        needP = (g > 0) & unmet
        needN = (g < 0) & unmet
        needD = np.zeros(len(self.port_keys), bool)
        depth, level = {}, 0
        while True:
            new = []
            for c in caps:
                if c.id in depth:
                    continue
                if ((c.eff > 0) & needP).any() or ((c.eff < 0) & needN).any() or \
                        ((c.out > 0) & needD).any():
                    new.append(c)
            if not new:
                break
            for c in new:
                depth[c.id] = level
                r = c.req()
                if s is not None:
                    r = np.where(s == r, 0, r)
                needP |= r > 0
                needN |= r < 0
                needD |= (c.inp >= 1) & (self.ctx_ports == 0)
            level += 1
        res = {}
        for c in caps:
            harm = bool(((c.eff == -g) & (g != 0)).any())
            d = depth.get(c.id)
            res[c.id] = dict(direct=self.direct_alignment(c, goal, state),
                             regressed=0.0 if (d is None or harm) else lam ** d,
                             depth=d, harm=harm)
        return res

    # --------------------------------------------------- operational layer
    def availability(self, e: CapEmb, t: Optional[float] = None, env=None) -> bool:
        ok = e.qext[0] >= 1
        if t is not None:
            ok = ok and e.qext[1] <= t <= e.qext[2]
        if env is not None:
            ev = np.zeros(len(self.res_names))
            for r in env:
                if r in self.ridx:
                    ev[self.ridx[r]] = 1
            ok = ok and bool((e.res <= ev).all())
        return bool(ok)

    def utility(self, e: CapEmb, w) -> float:
        """Lower is better.  w = weights over [time, money, res, energy, risk, unrel]."""
        return float(np.dot(w, self.qos_metric(e)))

    def global_violations(self, e: CapEmb):
        """Global constraints K (forbidden conjunctions of literals).

        certain  : every forbidden literal is *guaranteed* after running e
        possible : e asserts at least one forbidden literal and nothing in e's
                   guarantee rules the conjunction out (unsafe unless guarded)"""
        base = self.U.saturate(e.req())
        g = np.where(e.eff != 0, e.eff, base)
        certain, possible = [], []
        for k in self.p.global_constraints:
            f = self.U.from_lits(k["forbid"])
            nz = f != 0
            if (g[nz] == f[nz]).all():
                certain.append(k["id"])
            elif (e.eff[nz] == f[nz]).any() and not (g[nz] == -f[nz]).any():
                possible.append(k["id"])
        return dict(certain=certain, possible=possible)
