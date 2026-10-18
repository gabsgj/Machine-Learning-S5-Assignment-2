# Design of a Vector Embedding for Capability Composition

**Course:** PCCST503 — Assignment 2  
**Name:** Sreelekshmi Harikumar  
**Register No.:** TCR24CS068

---

## 1. What this project is

In an application (an online shop, a machine-learning pipeline, a loan process) the individual operations — *capabilities* such as
`CreateOrder`, `MakePayment`, `TrainModel` — need certain things beforehand, change the system, and take and produce data.
This project designs, implements and evaluates a **vector embedding** that represents formally specified **states, goals and capabilities**
so that a program can decide, using linear algebra:

| question | answered by |
|---|---|
| Which capability can run **directly after** which? | directed **compatibility** (precondition–effect and input–output) |
| Which capabilities are **alike** (substitutes)? | symmetric **similarity** |
| What is the capability obtained by **chaining** several? | **composition** (a composite is a capability in the same space) |
| Which capabilities **matter for a goal**? | **goal relevance** |
| How are **cost, reliability, availability, risk, resources, constraints** handled? | separate operational / guard blocks |

The central finding the assignment asks about: **similar ≠ composable**. `MakePayment_API` and `MakePayment_DB` have identical functional vectors
(similarity 1.0) yet cannot follow each other (compatibility: CONFLICT), while `CreateOrder → MakePayment` look different but chain perfectly.

**Representation name:** *TAPCE — Typed-Atom Partitioned Capability Embedding.*

**Scope.** The assignment excludes planners (BFS/DFS/A\*/D\* Lite/LPA\*). This project contains **no planner** and uses **no pre-trained model**.

This is a command-line Python library with an experiment script. It is **not a website or application**.

---

## 2. Deliverables

| # | Deliverable | Location |
|---|---|---|
| 1 | Formal embedding design (maths) | `DELIVERABLE_1_FORMAL_EMBEDDING_DESIGN.md` / `.pdf` |
| 2 | Implementation | `capemb/` and `DELIVERABLE_2_IMPLEMENTATION.md` |
| 3 | Experimental dataset | `datasets/*.json` and `DELIVERABLE_3_EXPERIMENTAL_DATASET.md` |
| 4 | Technical report (12 sections) | `DELIVERABLE_4_TECHNICAL_REPORT.md` / `.pdf` |
| – | Plain-language explanation + viva questions | `EXPLANATION.md` |
| – | Generated results and figures | `results/` |

---

## 3. Repository layout

```
.
├── README.md                                   this file
├── EXPLANATION.md                              plain-language walkthrough + 15 viva Q&A
├── DELIVERABLE_1_FORMAL_EMBEDDING_DESIGN.md/.pdf
├── DELIVERABLE_2_IMPLEMENTATION.md
├── DELIVERABLE_3_EXPERIMENTAL_DATASET.md
├── DELIVERABLE_4_TECHNICAL_REPORT.md/.pdf
├── capemb/                                     the embedding library
│   ├── __init__.py
│   ├── spec.py                                 formal model A=(S,C,S_I,G,R,K), capability 11-tuple, JSON loader
│   ├── atoms.py                                atom universe: grounding, saturation, state/goal vectors
│   ├── embedding.py                            CapabilityEmbedder: encode, compose, similarity, compat, relevance, operational views
│   ├── semantics.py                            concrete-value semantics + ground-truth oracles (evaluation only)
│   └── verify.py                               property checks (apply, composition, associativity, identity, QoS Monte-Carlo)
├── datasets/
│   ├── P0_assignment_minimal.json              exactly the C1/C2/C3 pattern of Experiment 1
│   ├── P1_ecommerce_checkout.json              14 capabilities (primary problem)
│   ├── P2_ml_pipeline.json                     15 capabilities
│   ├── P3_loan_approval.json                   13 capabilities
│   ├── build_datasets.py                       generates the four JSON files
│   └── make_dataset_doc.py                     generates DELIVERABLE_3 tables from the JSON
├── experiments/
│   └── run_all.py                              all experiments → results/
├── tests/
│   └── test_properties.py                      21 pytest tests
└── results/
    ├── RESULTS.md                              all tables (auto-generated)
    ├── results.json                            machine-readable results
    └── figures/                                fig1 … fig6 (PNG)
```

---

## 4. Installation

Requires **Python 3.10 or newer** (tested on 3.12 and 3.14). Check with `python --version`
(on macOS/Linux use `python3`; on Windows `py` also works).

```bash
pip install numpy scipy matplotlib pytest
```

---

## 5. How to run

Open a terminal **inside the project folder** (the one containing `capemb/`, `datasets/`, `experiments/`).

### 5.1 Run the tests
```bash
python -m pytest tests -q
```
Expected last line: `21 passed`.

### 5.2 Run all experiments (about 1 minute)
```bash
python experiments/run_all.py
```
It prints every result table and writes `results/RESULTS.md`, `results/results.json` and six figures in `results/figures/`.
The run is deterministic (fixed random seeds); only the timing figures in the *Efficiency* section depend on your machine.

### 5.3 (Optional) regenerate the datasets and dataset document
```bash
python datasets/build_datasets.py
python datasets/make_dataset_doc.py
```

### 5.4 Try the embedding yourself

Start Python (`python`) in the project folder and type:

```python
from capemb import load_problem, CapabilityEmbedder
E = CapabilityEmbedder(load_problem("datasets/P1_ecommerce_checkout.json"))

E.compat("CreateOrder", "CancelCart")["label_name"]             # 'CONFLICT'  an order now exists
E.compat("MakePayment_API", "SendNotification")["label_name"]   # 'STRICT'    payment provides everything it needs
E.compat("CreateOrder", "MakePayment_API")["label_name"]        # 'PARTIAL'   helps, but more is needed
E.similarity("MakePayment_API", "MakePayment_DB", "func")       # 1.0         same function ...
E.compat("MakePayment_API", "MakePayment_DB")["label_name"]     # 'CONFLICT'  ... but similar != composable

c = E.compose(["CreateOrder", "ValidatePaymentLimit", "MakePayment_API"])
c.valid                                                          # True
E.reliability(c)                                                 # 0.9935 (product of the three reliabilities)
exit()
```

Or save the same lines (with `print(...)`) in a file `demo.py` and run `python demo.py`.

---

## 6. The representation in brief

(Full mathematics: Deliverable 1.)

### 6.1 Atoms and ternary vectors
Every typed state variable is grounded into **atoms**: one per Boolean, one per enum value, and one per integer threshold `n ≥ c`
(thresholds are discovered automatically from the specification). A vector over atoms has entries **+1** (holds / must hold),
**−1** (does not hold / must not hold), **0** (unknown / unchanged).

* **State** → complete ±1 vector, `phi_S(S)`.
* **Goal** → ternary vector.
* **Transition** → `phi_S(Apply(S,E)) = phi_S(S) ⊕ e` (override).
* A capability is **applicable** in a state iff every non-zero entry of its requirement vector is matched.

### 6.2 A capability is a partitioned vector

| block | contents | composes by |
|---|---|---|
| `pre` | preconditions (ternary) | own preconditions + the second capability's preconditions not established by the first |
| `grd` | state-grounded constraints (ternary) | same rule as `pre` |
| `eff` | effects (ternary, full assignment of each variable) | last writer wins |
| `inp` | required (1) / optional (½) inputs over data kinds `name:type:domain` | inputs not produced inside the chain |
| `out` | outputs, closed under the domain hierarchy | union |
| `typ` | one-hot capability type | sum (bag) |
| `mech` | execution mechanism, hashed `key=value` tokens (64 buckets) | sum (bag) |
| `res` | resource requirements | union |
| `qadd` | time, money, resource cost, energy, hazard = −ln(1−risk), unreliability = −ln Rel | **sum** |
| `qext` | availability flag, window start, window end | min / max / min |

Dimension for the checkout problem: 206 floats (≈ 0.8 KB).

### 6.3 Three different measures

1. **Compatibility** (directed, `A → B`): compares what `A` guarantees (its effects plus the preconditions it did not overwrite) with what `B` requires, plus data availability.

   | label | meaning |
   |---|---|
   | `CONFLICT` | something `B` needs is made false by `A` |
   | `INDEPENDENT` | `A` contributes nothing `B` needs |
   | `PARTIAL` | `A` supplies part of what `B` needs |
   | `STRICT` | `A` alone establishes everything `B` needs |

   Computed with four matrix products (`compat_matrix`), optionally given a known state and available data (`context`).
2. **Similarity** (symmetric): weighted block cosines. `Sim = 0.70·Sim_func + 0.15·Sim_impl + 0.15·Sim_qos`. Used to find substitutes, **not** to decide chaining.
3. **Goal relevance**: direct alignment (effects hitting a goal literal) and **regressed relevance** (a backward fixed-point over needs; a *score*, not a plan search).

### 6.4 Composition
`compose([C1, C2, …, Cn])` builds `Cn ∘ … ∘ C1` block by block (table above). A composite lives in the same space, so it can be compared, composed again, and applied to a state.
Verified properties: **closure, associativity, identity element, soundness with respect to real execution**, and exact QoS composition
(reliability multiplies, time/money/energy add, availability windows intersect).

### 6.5 Why operational properties are kept separate
Cost, risk and reliability do **not** influence compatibility (a slow implementation is still compatible); they are used afterwards to **filter and rank** functionally acceptable candidates.
Tested: re-scaling all cost/reliability values 20 times never changed a compatibility label.

---

## 7. Python API

```python
E = CapabilityEmbedder(problem)

E.encode(state_dict | goal_list | capability | "CapabilityId")   # StateEmb / GoalEmb / CapEmb
E.compose([c1, c2, ...])                                          # composite CapEmb (.valid, .conflicts, .id)
E.similarity(x, y, mode="overall")                                # type-dispatched (see below)
E.similarity_report(a, b)                                         # dict(func, impl, qos, overall)
E.compat(a, b, ctx=None)                                          # directed compatibility of one pair
E.compat_matrix(list_of_caps, ctx=None)                           # all pairs
E.context(state_dict)                                             # known state + data available in the environment
E.apply(state, cap); E.is_applicable(state, cap); E.goal_progress(state, goal)
E.goal_relevance(goal, state)                                     # {cap: {direct, regressed, depth, harm}}
E.availability(cap, t=hour, env=[resources])                      # window + resource feasibility
E.utility(cap, weights)                                           # scalarised cost (lower = better)
E.reliability(cap); E.risk(cap)                                   # composed by monoid folds
E.global_violations(cap)                                          # {"certain": [...], "possible": [...]}
E.flat(cap)                                                       # single dense vector for indexing
```

`similarity(x, y)` dispatch: capability~capability → similarity; state~capability → applicability (coverage − conflict);
capability~goal → direct alignment; state~goal → goal progress.

---

## 8. Datasets

All problems are formal JSON (typed variables, initial state, goals, resources, global constraints, ports, capabilities with all 11 components).
Free-text descriptions are documentation only and are never read by the embedding.

| file | domain | capabilities | state variables | atoms | goals | purpose |
|---|---|---|---|---|---|---|
| `P0_assignment_minimal.json` | e-commerce (minimal) | 3 | 3 | 4 | 1 | the exact CreateOrder / MakePayment / CancelCart pattern |
| `P1_ecommerce_checkout.json` | e-commerce | 14 | 17 | 26 | 2 | primary problem for all experiments |
| `P2_ml_pipeline.json` | data / ML engineering | 15 | 14 | 17 | 2 | FILE / COMPUTATION, GPU resource, integer thresholds |
| `P3_loan_approval.json` | banking | 13 | 13 | 20 | 2 | SERVICE / MESSAGE, time window, numeric constraints |

Coverage: all nine capability types (API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE), Boolean / enum / integer variables,
a port-domain hierarchy, and every operational attribute. Ground truth is **not hand-written**: pair labels come from an exhaustive concrete-value oracle,
goal relevance from exhaustive search for irredundant goal-reaching sequences (used only to label data).

---

## 9. Experiments and headline results

Everything below is produced by `python experiments/run_all.py` and appears in `results/RESULTS.md`.

| # | Experiment | Result |
|---|---|---|
| 1 | **Capability compatibility** | CreateOrder→MakePayment **STRICT**; CreateOrder→CancelCart **CONFLICT**. Vector labels agree with the independent oracle on **548 / 548** ordered pairs (P1 182, P2 210, P3 156). Ablations (remove saturation / persistence / ports / all) drop accuracy to 0.80–0.99. |
| 1b | **Similarity vs composability** | AUC for "A can feed B": text similarity 0.65–0.68, flat-vector cosine 0.55–0.65, overall similarity 0.52–0.63, **directed compatibility 0.87–0.96**. |
| 2 | **Capability composition** | C123 = MakePayment_API ∘ ValidatePaymentLimit ∘ CreateOrder: 6 external preconditions (Order.exists and Payment.within_limit are established internally and disappear), reliability 0.9935, time 248 ms. **0 mismatches** vs step-by-step execution in 35 000+ trials; associativity 400/400 per problem; mean/sum pooling baselines reach only 0.81–0.87. |
| 3 | **Alternative implementations** | API / DB / GUI payment: `Sim_func = 1.00`, `Sim_impl ≈ 0`, flat vectors **not identical**, compatibility CONFLICT. Same-type/different-function control: `Sim_func` only 0.02–0.03. |
| 4 | **Irrelevant capabilities** | Regressed relevance F1 = 1.00 on 5 of 6 goals, 0.95 on one (false positive `DeclineLoan`); direct alignment 0.33–0.91. Goal-dependence works (extended goal makes `ReserveInventory`, `GenerateInvoice`, `DispatchShipment` relevant). |
| 5 | **Operational attributes** | Composed reliability/risk match a 200 000-run Monte-Carlo to 3–4 decimals; compatibility labels unchanged under random QoS re-scaling (20/20); availability windows, missing resources (no GPU) and guard constraints (loan amount > limit, role GUEST) behave as concrete semantics. |
| – | **Consistency** | Same code and weights on all three domains; compat accuracy 1.000, composition mismatches 0. |
| – | **Efficiency** | ≈ 0.8 KB per capability; all-pairs compatibility is two dense matrix products, O(N²·d); random-projection compression needs k ≈ 1024 for 99 % accuracy at d = 2000. Timings depend on your machine. |

### Figures (`results/figures/`)

| file | shows |
|---|---|
| `fig1_compat_vs_similarity.png` | directed compatibility labels / scores vs symmetric similarity, all pairs of P1 |
| `fig2_goal_relevance.png` | direct alignment vs regressed relevance per capability |
| `fig3_composition_blocks.png` | pre/eff blocks of C1, C2, C3 and the composite |
| `fig4_alternatives.png` | similarity components for alternative implementations vs different functions |
| `fig5_efficiency.png` | all-pairs time and random-projection accuracy |
| `fig6_operational.png` | functionally identical alternatives differ only in the operational block |

![Compatibility vs similarity](results/figures/fig1_compat_vs_similarity.png)
![Composition blocks](results/figures/fig3_composition_blocks.png)

---

## 10. Test suite (21 tests)

| test | what it proves |
|---|---|
| `test_apply_homomorphism` | `phi(Apply(S,E)) = phi(S) ⊕ e`; vector applicability = concrete applicability |
| `test_composition_equals_sequential_execution` | a composite vector behaves exactly like running the chain |
| `test_associativity_and_identity` | block-wise associativity, agreement of validity, identity element |
| `test_pair_labels_match_oracle` | all ordered-pair labels equal the exhaustive-valuation oracle |
| `test_assignment_experiment_1` | CreateOrder→MakePayment compatible, CreateOrder→CancelCart incompatible |
| `test_alternatives_same_function_different_implementation` | same function ⇒ `Sim_func = 1` but vectors not identical |
| `test_qos_independent_of_compat` | rescaling reliability never changes compatibility |
| `test_composite_reliability_is_product` | QoS monoid |
| `test_vector_state_goal_api` | state / goal / capability encode and similarity dispatch |

(Several are parametrised over the four problems, giving 21 test cases.)

---

## 11. Troubleshooting

| problem | fix |
|---|---|
| `ModuleNotFoundError: No module named 'capemb'` | your terminal is not inside the project folder; `cd` into the folder that contains `capemb/` |
| `ModuleNotFoundError: No module named 'numpy'` (or `matplotlib`, `scipy`, `pytest`) | run `pip install numpy scipy matplotlib pytest` |
| `python` not found | try `py` (Windows) or `python3` (macOS/Linux); reinstall Python with "Add to PATH" ticked |
| `UnicodeEncodeError: 'charmap' codec can't encode character '\u2218'` (Windows) | files must be written as UTF-8: in `experiments/run_all.py` the final `open(..., "w")` calls need `encoding="utf-8"`; or set `$env:PYTHONUTF8=1` (PowerShell) / `set PYTHONUTF8=1` (cmd) before running |
| `ImportError: DLL load failed ... An Application Control policy has blocked this file` (SciPy) | Windows security is blocking SciPy. SciPy is used for only one function, so remove the line `from scipy.stats import rankdata` in `experiments/run_all.py` and paste the replacement shown below |

NumPy-only replacement for `rankdata` (paste near the top of `experiments/run_all.py`, after the imports):

```python
def rankdata(a):
    a = np.asarray(a, float)
    order = np.argsort(a, kind="mergesort")
    srt = a[order]
    ranks = np.empty(len(a))
    i, n = 0, len(a)
    while i < n:
        j = i
        while j + 1 < n and srt[j + 1] == srt[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks
```

---

## 12. Limitations

(Details in the technical report, Section 11.)

1. **Designed, not learned.** Block weights (0.70 / 0.15 / 0.15 and within-block weights) are hand-set.
2. **Per-problem coordinates.** Each problem has its own atom universe; the *procedure* is consistent across problems, the coordinate space is not shared.
3. **Supported fragment.** Boolean / enum / integer variables (reals must be discretised); conjunctive conditions; deterministic assignment effects; no relative updates (`n += 1`) or conditional effects.
4. **Failure semantics.** Reliability is a probability stored beside the semantics; the state model assumes success; independence is assumed when composing reliability and risk.
5. **Goal relevance is a relaxation.** It is order-agnostic and ignores mutual exclusion between alternatives (observed false positive: `DeclineLoan` for a "disburse" goal).
6. **Data matching is by exact port name/type/domain**; semantically equivalent names are not matched.
7. **Small, hand-authored datasets** (13–15 capabilities each); the oracle shares the same formal specification.
8. **Baselines are lexical.** The text baseline is TF-IDF, not a pre-trained Word2Vec/BERT model.
9. **Compression is modest.** Random projection needs k ≈ 1024 for 99 % accuracy at d = 2000; sparse exact storage is preferable.
10. **Time-dependence** is a daily window only; replanning and dynamic changes are out of scope.

---
