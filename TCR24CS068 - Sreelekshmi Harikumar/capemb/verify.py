"""Property checks that tie the vector algebra to concrete semantics."""
from __future__ import annotations
import numpy as np
from . import semantics as S
from .embedding import CapabilityEmbedder, CapEmb, STRICT, CONFLICT


def _states(E: CapabilityEmbedder, req_vec, rng, n_random, n_witness):
    p = E.p
    out = [S.random_state(p, rng) for _ in range(n_random)]
    for _ in range(n_witness):
        out.append(E.U.decode_witness(req_vec, rng))
    return out


def check_apply_homomorphism(E, n_random=200, n_witness=20, seed=0):
    """phi(Apply(S,E)) == phi(S) (+) e   and   applicable <=> coverage==1."""
    rng = np.random.default_rng(seed)
    n = bad = n_app = 0
    for c in E.p.caps:
        e = E.caps[c.id]
        for s in _states(E, e.req(), rng, n_random, n_witness):
            sv = E.encode_state(s)
            ok_c = S.applicable(c, s)
            ok_v = E.is_applicable(sv, e)
            n += 1
            n_app += ok_c
            if ok_c != ok_v:
                bad += 1
                continue
            if ok_c:
                s2 = E.encode_state(S.apply(c, s)).vec
                if not np.array_equal(s2, E.apply(sv, e).vec):
                    bad += 1
    return dict(trials=n, applicable_trials=int(n_app), mismatches=bad)


def _sequential(E, chain_caps, s):
    for c in chain_caps:
        if not S.applicable(c, s):
            return False, None
        s = S.apply(c, s)
    return True, s


def random_chains(E, n, max_len, rng):
    ids = [c.id for c in E.p.caps]
    M = E.compat_matrix(ids)["label"]
    chains = []
    for k in range(n):
        L = int(rng.integers(2, max_len + 1))
        if k % 2 == 0:                                    # unconstrained
            chains.append([ids[i] for i in rng.choice(len(ids), L, replace=True)])
        else:                                             # guided by compat (non-conflict)
            cur = int(rng.integers(len(ids)))
            ch = [ids[cur]]
            for _ in range(L - 1):
                opts = [j for j in range(len(ids)) if M[cur, j] in (2, 3)]
                if not opts:
                    break
                cur = int(rng.choice(opts))
                ch.append(ids[cur])
            if len(ch) >= 2:
                chains.append(ch)
    return chains


def check_composition_semantics(E, n_chains=300, max_len=4, n_random=30, n_witness=10, seed=1):
    """For random chains: composite applicability and result == sequential execution."""
    rng = np.random.default_rng(seed)
    chains = random_chains(E, n_chains, max_len, rng)
    n = bad = n_valid = n_app = 0
    for ch in chains:
        comp = E.compose(ch)
        caps = [E.p.cap(i) for i in ch]
        n_valid += comp.valid
        sts = _states(E, comp.req(), rng, n_random, n_witness if comp.valid else 0)
        for s in sts:
            ok_s, s_end = _sequential(E, caps, s)
            sv = E.encode_state(s)
            ok_v = E.is_applicable(sv, comp)
            n += 1
            n_app += ok_s
            if ok_s != ok_v:
                bad += 1
                continue
            if ok_s and not np.array_equal(E.encode_state(s_end).vec, E.apply(sv, comp).vec):
                bad += 1
    return dict(chains=len(chains), valid_chains=int(n_valid), trials=n,
                applicable_trials=int(n_app), mismatches=bad)


def _blocks_equal(a: CapEmb, b: CapEmb):
    return all(np.allclose(x, y) for x, y in zip(a.blocks().values(), b.blocks().values()))


def check_associativity(E, n=400, seed=2):
    rng = np.random.default_rng(seed)
    ids = [c.id for c in E.p.caps]
    ok = valid_agree = 0
    n_valid = 0
    for _ in range(n):
        a, b, c = (E.caps[ids[i]] for i in rng.choice(len(ids), 3))
        left = E.compose2(E.compose2(a, b), c)
        right = E.compose2(a, E.compose2(b, c))
        valid_agree += left.valid == right.valid
        if left.valid and right.valid:
            n_valid += 1
            ok += _blocks_equal(left, right)
        elif left.valid == right.valid:
            ok += 1
    return dict(triples=n, valid_triples=n_valid, validity_agree=valid_agree, block_equal=ok)


def identity_cap(E) -> CapEmb:
    z = lambda x: np.zeros_like(x)
    c = next(iter(E.caps.values()))
    return CapEmb("ID", ("ID",), z(c.pre), z(c.grd), z(c.eff), z(c.inp), z(c.out), z(c.typ),
                  z(c.mech), z(c.res), z(c.qadd), np.array([1.0, 0.0, 24.0]))


def check_identity(E):
    I = identity_cap(E)
    ok = 0
    for c in E.caps.values():
        ok += _blocks_equal(E.compose2(I, c), c) and _blocks_equal(E.compose2(c, I), c)
    return dict(caps=len(E.caps), identity_ok=ok)


def monte_carlo_chain(E, chain_ids, n=200000, seed=3):
    """Simulate independent Bernoulli failures/risks to validate the QoS monoid."""
    rng = np.random.default_rng(seed)
    comp = E.compose(chain_ids)
    rel_hat = np.ones(n, bool)
    safe_hat = np.ones(n, bool)
    for i in chain_ids:
        c = E.p.cap(i)
        rel_hat &= rng.random(n) < c.reliability
        safe_hat &= rng.random(n) >= c.qos.get("risk", 0.0)
    return dict(reliability_vector=E.reliability(comp), reliability_mc=float(rel_hat.mean()),
                risk_vector=E.risk(comp), risk_mc=float(1 - safe_hat.mean()),
                time_ms=float(comp.qadd[0]), money=float(comp.qadd[1]))
