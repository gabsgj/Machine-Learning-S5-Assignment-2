# Deliverable 2 — Implementation

Language: **Python 3.12** (NumPy, SciPy, Matplotlib only; pytest for tests). No planner, no pre-trained model is used.

## 1. Layout

```
capemb/                      the embedding library
  spec.py                    formal model A=(S,C,S_I,G,R,K), capability 11-tuple, JSON loader
  atoms.py                   atom universe: grounding, saturation, state/goal vectors
  embedding.py               CapabilityEmbedder: encode / compose / similarity / compat /
                             goal relevance / operational views
  semantics.py               concrete-value semantics + ground-truth oracles (EVALUATION ONLY)
  verify.py                  property checks (apply, composition, associativity, identity, QoS Monte-Carlo)
datasets/
  build_datasets.py          generates the four JSON problems
  P0_assignment_minimal.json P1_ecommerce_checkout.json P2_ml_pipeline.json P3_loan_approval.json
experiments/run_all.py       every experiment of the assignment -> results/
tests/test_properties.py     21 tests (pytest)
results/                     RESULTS.md, results.json, run.log, figures/*.png
```

## 2. Quick start

```bash
pip install numpy scipy matplotlib pytest
python datasets/build_datasets.py        # (re)generate the datasets
python -m pytest tests -q                # 21 passed
python experiments/run_all.py            # ~1 min; writes results/
```

## 3. The required interface

```python
from capemb import load_problem, CapabilityEmbedder

problem = load_problem("datasets/P1_ecommerce_checkout.json")
E = CapabilityEmbedder(problem)

# --- encode(state | goal | capability) ------------------------------------
s  = E.encode(problem.init)            # StateEmb  (bipolar vector over atoms, length d_a)
g  = E.encode(problem.goal)            # GoalEmb   (ternary vector)
c1 = E.encode("CreateOrder")           # CapEmb    (blocks: pre, grd, eff, inp, out, typ, mech, res, qadd, qext)
c1.pre, c1.eff, c1.inp, c1.out         # numpy blocks
E.flat(c1)                             # single dense vector (203 dims for P1) for ANN indexing

# --- compose(capabilities) -------------------------------------------------
c123 = E.compose(["CreateOrder", "ValidatePaymentLimit", "MakePayment_API"])   # C3∘C2∘C1
c123.valid, c123.conflicts, c123.id    # validity flag, offending atoms, name
E.compose([c123, "SendNotification"])  # composites compose again (closure)

# --- similarity(x, y)  (type-dispatched) ----------------------------------
E.similarity("MakePayment_API", "MakePayment_DB")            # overall similarity (symmetric)
E.similarity("MakePayment_API", "MakePayment_DB", "func")    # or "impl" / "qos"
E.similarity(s, c1)    # state~capability : applicability  (coverage - conflict)
E.similarity(c1, g)    # capability~goal  : direct goal alignment
E.similarity(s, g)     # state~goal       : goal progress
E.similarity_report(a, b)   # dict(func, impl, qos, overall)

# --- directed compatibility (precondition-effect + input-output) ---------
r = E.compat("CreateOrder", "MakePayment_API")        # dict: label_name, score, cov, conflict, supply, covio, ...
ctx = E.context(problem.init)                         # known state + data available in the environment
E.compat("CreateOrder", "ValidatePaymentLimit", ctx)  # state-aware
M = E.compat_matrix(list_of_caps)                     # all pairs at once (matrix products)

# --- state transition in vector space ---------------------------------------
s2 = E.apply(s, c1);  E.is_applicable(s, c1);  E.goal_progress(s2, g)

# --- goal relevance & operational layer -----------------------------------
E.goal_relevance(g, s)                 # {cap: {direct, regressed, depth, harm}}
E.availability(c1, t=23, env=["Database"])        # window + resources
E.utility(c1, w=[.7,.1,.05,0,.05,.1])             # scalarised cost (lower = better)
E.reliability(c123), E.risk(c123)                 # composed by monoid folds
E.global_violations(c1)                           # {"certain": [...], "possible": [...]}
```

## 4. Key implementation points

* **One compat implementation.** `compat()` calls `compat_matrix()`; the matrix version computes
  `match`, `conflict`, `supply` with four matrix products on the dual-rail splits, so all-pairs cost is `O(N² d_a)` via BLAS.
* **Typed grounding.** `AtomUniverse` discovers integer cut-points automatically; assignments produce full group vectors so
  mutual exclusion and monotonicity never have to be remembered by the caller.
* **No hidden dependence on text.** `description` fields are only read by the TF-IDF *baseline* in `experiments/run_all.py`.
* **Determinism.** Mechanism hashing uses MD5 (not Python's randomised `hash`); experiments use fixed seeds.
* **Oracle isolation.** `capemb/semantics.py` re-implements preconditions/effects on *concrete values* and is imported only by
  `verify.py`, `tests/` and `experiments/`; the embedding never calls it.
* **Scope.** There is no planner. `goal_relevance` is a backward *score propagation* over vectors; the brute-force sequence
  search used to label ground truth for Exp. 4 lives in `semantics.py` and is evaluation-only.

## 5. Tests (what they prove)

| test | claim |
|---|---|
| `test_apply_homomorphism` | `phi(Apply(S,E)) = phi(S) ⊕ e` and vector applicability = concrete applicability |
| `test_composition_equals_sequential_execution` | composite vector behaves exactly like running the chain |
| `test_associativity_and_identity` | block-wise associativity, agreement of validity, identity element |
| `test_pair_labels_match_oracle` | all ordered-pair labels equal the exhaustive-valuation oracle |
| `test_assignment_experiment_1` | CreateOrder→MakePayment compatible, CreateOrder→CancelCart incompatible |
| `test_alternatives_...` | same function ⇒ `Sim_func=1`, but vectors not identical |
| `test_qos_independent_of_compat` | rescaling reliability never changes compatibility |
| `test_composite_reliability_is_product` | QoS monoid |
| `test_vector_state_goal_api` | state/goal/capability encode & similarity dispatch |
