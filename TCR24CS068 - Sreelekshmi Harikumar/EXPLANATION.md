# Explanation — what the assignment asks, and what was built

This file explains the assignment and my solution in plain language, then gives viva-style questions and answers.

---

## Part A — The assignment in plain language

### A1. The big picture

* In **Assignment 1** you searched for a *path* of actions that gets a system from a start state to a goal state.
* In **Assignment 2** you stop caring about the path-finding and ask: **how do I describe the individual actions (capabilities) as vectors of numbers** so that a computer can tell:
  1. which capability can run **after** which (compatibility),
  2. which capabilities are **alike** (similarity),
  3. what you get when you **chain** several into one bigger capability (composition),
  4. which capabilities **matter for a goal** (relevance),
  5. how to treat **cost, reliability, availability, constraints, resources**.

### A2. The Word2Vec analogy

Word2Vec puts *words* in a space where *meaning* is geometry (king − man + woman ≈ queen).
Here you put *capabilities* in a space where **function is geometry**: what a capability needs, what it changes, what data it takes and gives.
The twist the assignment stresses: *similar ≠ composable*. `MakePayment_API` and `MakePayment_DB` are very similar, but you cannot run one right after the other (the payment is already done). `CreateOrder` and `MakePayment` look different, but they chain perfectly.

### A3. Vocabulary

| term | meaning | example |
|---|---|---|
| state | values of all state variables | `Order.exists=false`, `Cart.item_count=3` |
| goal | conditions that should become true | `Payment.status=SUCCESS` |
| capability | reusable operation | `CreateOrder` |
| precondition | must hold before running | `Cart.item_count>0` |
| effect | what changes afterwards | `Order.exists=true` |
| input / output | data in / data out | needs `cart_id`, gives `order_id` |
| constraint | extra restriction | `role in {CUSTOMER, ADMIN}` |
| composition | chain C1 then C2 as one capability | `CompletePurchase = MakePayment ∘ CreateOrder` |

### A4. What you must deliver

1. **Formal design** (maths): how states/goals/capabilities become vectors, similarity/compatibility, composition.
2. **Implementation**: `encode(state)`, `encode(goal)`, `encode(capability)`, `compose(...)`, `similarity(x,y)`.
3. **Dataset**: formal problems (states, goals, capabilities, constraints, costs…).
4. **Report**: 12 sections.
5. **Five experiments**: compatibility, composition, alternative implementations, irrelevant capabilities, operational attributes.

**Not required (explicitly out of scope):** any planner/search algorithm (A\*, D\* Lite…). My solution has none.

---

## Part B — My solution in plain language

### B1. The core idea in one paragraph

Turn every yes/no fact about the system into one coordinate ("atom"), e.g. `Order.exists`, `Payment.status=SUCCESS`, `Cart.item_count>=1`.
Then a **state** is a list of +1/−1 (true/false); a **precondition** is a list with +1 (must be true), −1 (must be false), 0 (don't care);
an **effect** is a list saying what becomes true (+1) or false (−1), 0 = unchanged. Because every part lives on the *same* coordinates,
"does the effect of A satisfy the precondition of B?" is just a **dot product**.

### B2. What each part of a capability becomes

| capability component | in the vector |
|---|---|
| preconditions $P$ | `pre` block (ternary) |
| constraints $K$ | `grd` block (ternary, same coordinates) |
| effects $E$ | `eff` block (ternary) |
| inputs / outputs | `inp` / `out` blocks over data kinds (name:type:domain), outputs also set their "parent domain" |
| type $T$ | `typ` one-hot (low weight) |
| mechanism $M$ | `mech` hashed bag of "key=value" (separate from the main meaning) |
| resources $R$ | `res` 0/1 vector |
| cost, risk, reliability | `qadd` — numbers that **add** when chained (reliability stored as −ln Rel so that probabilities multiply by adding) |
| availability | `qext` — available?, window start/end |

### B3. The three different "measurements"

1. **Compatibility (directed, A → B).** Compare A's *guarantee* (its effects plus what it already required) with B's *requirements*.
   Result: `CONFLICT` (something B needs is made false), `INDEPENDENT` (A does nothing for B), `PARTIAL` (A helps but B needs more), `STRICT` (A provides everything B needs).
2. **Similarity (symmetric).** Compare like with like: effects with effects, inputs with inputs, mechanisms with mechanisms…
   Used to find *substitutes*, not to decide chaining.
3. **Goal relevance.** Start from the unmet goal conditions, walk *backwards*: which capabilities supply them, what do those need, who supplies *that*…
   This finds capabilities that matter indirectly (like `CreateOrder` for a notification goal). It is a score propagation, **not** a path search.

### B4. Composition — the heart of the assignment

Chain `X` then `Y` and compute the vector of the chain directly:

* **preconditions** = X's preconditions + only those of Y that X did *not* establish,
* **effects** = X's effects overwritten by Y's effects,
* **inputs** = data needed from outside only; **outputs** = all outputs,
* **cost/time/money** add; **reliability** multiplies (adds in −ln); **availability** windows intersect.

The chain is itself a capability in the same space, so you can compose again. I proved/tested that it is associative, has an identity, and
behaves **exactly** like running the steps (0 mismatches in more than 35 000 random trials against a concrete simulator).
Averaging the vectors instead gives only 81–87 % agreement.

### B5. How the solution was checked (no hand-waving)

* An **independent oracle** re-implements the meaning of preconditions/effects on concrete values (true/false, enum names, integers) and labels every ordered pair of capabilities: the vector method agrees on **all 548 pairs**.
* **Ablations** (remove saturation / persistence / ports) show each ingredient is needed (accuracy drops to 0.80–0.99).
* **Baseline**: a text (TF-IDF) similarity cannot predict compatibility (AUC ≈ 0.65 vs 0.87–0.96 for the directed measure).
* **Property tests** (21, pytest): apply, composition, associativity, identity, QoS composition.
* Experiments on **three domains** (e-commerce, ML pipeline, loans) plus the exact C1/C2/C3 example from the assignment.

### B6. Honest limitations (say these in the viva before they are asked)

* The vector is **designed from the specification, not learned**; weights are hand-chosen.
* Supports Boolean/enum/**integer** variables and conjunctive conditions; no relative updates (`n += 1`), reals must be discretised.
* Goal relevance ignores order and mutual exclusion (one false positive: `DeclineLoan`).
* Datasets are small and written by me; each problem has its own coordinate system.
* The text baseline is TF-IDF, not a real Word2Vec/BERT.

---

## Part C — How to read the project

| if you want to… | open |
|---|---|
| see the maths | `DELIVERABLE_1_FORMAL_EMBEDDING_DESIGN.md` |
| use the code | `DELIVERABLE_2_IMPLEMENTATION.md`, `capemb/embedding.py` |
| see the data | `DELIVERABLE_3_EXPERIMENTAL_DATASET.md`, `datasets/*.json` |
| read the results and discussion | `DELIVERABLE_4_TECHNICAL_REPORT.md` (PDF included) |
| re-run everything | `python experiments/run_all.py` |
| check correctness | `python -m pytest tests -q` |

Suggested order to learn it: A → B1/B2 → open `capemb/atoms.py` → `embedding.py::compose2` and `compat_matrix` → run `experiments/run_all.py` and read `results/RESULTS.md`.

---

## Part D — Viva questions and answers

**Q1. Why not just use Word2Vec / a sentence encoder?**
They embed *meaning from text*. Compatibility is a logical relation (effect satisfies precondition) and is directed; a text embedding is symmetric and approximate.
Measured: the lexical baseline predicts composability with AUC ≈ 0.65, the directed measure 0.87–0.96. Also the assignment says capabilities are given formally, and "merely applying an existing model is not sufficient".

**Q2. What is an "atom"?** A Boolean proposition derived from a state variable: one per Boolean, one per enum value, and one per threshold `n ≥ c` for integers (thresholds found automatically from the spec).

**Q3. Why ternary (−1/0/+1)?** Because a condition has three possibilities: must be true, must be false, don't care. The same encoding serves goals, preconditions, and effects (unchanged = 0), so dot products mean "agree minus disagree".

**Q4. What is "saturation" and why is it needed?** It adds implied facts: if `Payment.status=SUCCESS` then all other statuses are false; if `count>=5` then `count>=1`. Without it the vector misses conflicts and matches (ablation: accuracy 0.95–0.96 on P1/P3).

**Q5. Why does A's own precondition count ("persistence")?** If A needs `Order.exists=true` and doesn't change it, `Order.exists=true` is still true after A. Ignoring this is the biggest single error source (P1 accuracy 0.80).

**Q6. How do you show similar ≠ composable?** `MakePayment_API` vs `_DB`: functional similarity 1.00, yet compatibility CONFLICT. And `CreateOrder` vs `CancelCart` have the same similarity as `CreateOrder` vs `MakePayment` (0.25 vs 0.23) but opposite compatibility. AUC of similarity for predicting composability ≈ 0.52–0.68.

**Q7. How is a composite represented, and how does it relate to its parts?** Block-wise (see B4). It is *not* the average of the parts — pre-conditions satisfied inside the chain disappear, effects are last-writer-wins, costs add. It lives in the same space and composes again. Verified associative, with an identity, and equal to real execution.

**Q8. Where do type and mechanism go?** In their own low-weight blocks that affect only *implementation* similarity (15 % of overall). They never affect compatibility or validity, so an API and a DB implementation can have identical functional vectors without being identical overall.

**Q9. Why store reliability as −ln(Rel)?** So that a chain's reliability, a *product*, becomes a *sum* — the same operation as time and money; checked against a 200 000-run Monte-Carlo simulation.

**Q10. Do cost/reliability influence compatibility?** No by design (principle of non-leakage): a slow implementation is still compatible. Tested: rescaling all QoS values 20 times never changed any compatibility label. They are used afterwards to *rank or filter* candidates.

**Q11. How do you handle availability, resources and constraints?** Availability = flag + time window (composite = intersection); resources = set (composite = union; infeasible if the environment lacks one); constraints = a guard block in the same atom space as preconditions (so a violated policy blocks applicability but can also be *established* by another capability).

**Q12. Is goal relevance a planner?** No. It is a backward score propagation over vectors (a fixed point of "who supplies what is needed"). It does not enumerate or return sequences. A brute-force search is used only offline to create ground-truth labels for evaluation.

**Q13. What does 100 % accuracy mean? Is it too good?** It means the vector method preserves the semantics defined by the specification (checked by an independent concrete-value oracle). It is expected for an exact, designed representation; the ablations show weaker variants do drop. It does not prove generality beyond the supported fragment, and the datasets are small.

**Q14. What are the computational costs?** About 0.8 KB and 15 µs per capability; all-pairs compatibility is two dense matrix products, O(N² d). 4 000 capabilities with 2 000 atoms take about 2.4 s. Random projection can compress further but needs k≈1 000 for 99 % accuracy, so the exact sparse form is preferable.

**Q15. What would you do next?** Learn the block weights from data, extend to relative numeric updates and conditional effects, handle semantic port matching (e.g. via ontologies or learned embeddings of port names), model failure and partial effects, and test on externally authored specifications.
