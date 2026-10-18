# Embedding design

This document is Deliverable 1 of Assignment 2: the formal embedding design, its justification,
and the evidence that the eight required properties hold. Every number quoted here is produced
by the frozen experiment output in `experiments/out/` and reproducible with
`sh scripts/run_experiments.sh`.

## 1. The design problem

Applications are modelled as state machines over named variables, capabilities as typed tuples
(inputs, outputs, preconditions, effects, constraints, resources, quality, reliability and
availability), and goals as conditions on the final state. The design problem is to represent
capabilities, states and goals as functions into a vector space such that:

1. Capability identity: functionally different capabilities are distinguishable.
2. State awareness: a capability's relationship to the states it operates on is captured.
3. Precondition-effect compatibility: relationships such as `E_i => P_j` are captured.
4. Input-output compatibility: one capability's outputs satisfying another's inputs is captured.
5. Similarity and composability: functional resemblance is represented separately from
   composability, and the two never collapse into one number.
6. Composition: `C_i o C_j` and longer chains have a meaningful representation.
7. Goal relevance: the relationship between a capability and a goal is captured.
8. Operational properties: cost, reliability, availability, constraints and resources are
   represented appropriately, which may mean separately from the semantic vector.

## 2. Design decisions

Three embeddings, one shared sub-space:

```
phi_S : S -> R^128     state
phi_G : G -> R^128     goal
phi_C : C -> R^259     capability
```

The shared sub-space is the 64 dimensional condition space: the first block of the state and
the goal, and the precondition and effect blocks of the capability, all project their variables
and values through the same hash function into the same 64 dimensions (40 text dimensions plus
24 structured dimensions). This is what makes a cosine between a precondition and an effect, or
between an effect and a goal condition, meaningful: the two sides talk about the same variable
names in the same dimensions.

The capability vector is partitioned exactly as the assignment asks, and the grouping is
functional:

```
phi_C(C) = [ type(9) ; mech(16) ; in(32) ; out(32) ; pre(64) ; eff(64) ;
             delta(16) ; resources(16) ; quality(8) ; reliability(1) ; availability(1) ]
```

- The functional view is the mean of the precondition, effect, delta, input and output blocks.
  Two capabilities that do the same thing through different mechanisms stay close here.
- The implementation view is the mean of the type, mechanism, resources and quality blocks.
  The same functional capability delivered as an API, a database row interface or a GUI screen
  moves apart here, which is what experiment 3 measures.

Operational attributes are represented twice on purpose: embedded (so similarity and ranking
can see them) and exactly (so constraints can be enforced by comparison, not by cosine). A cost
cap is a comparison; no cosine can make it exact.

## 3. Text and structured features

All text (capability names, descriptions, field names, domains, variable names, string values)
is turned into features deterministically:

1. Tokenization splits on non-alphanumerics and on camel case and digit boundaries, so
   `register_patient`, `RegisterPatient` and `register patient` share tokens.
2. A curated concept table maps synonym sets to canonical concepts (`mrn`, `patient`, `client`
   all map to the concept `patient`), so vocabularies drift without losing the semantic link.
3. Each token contributes its concept, itself, and its character n-grams with weights; term
   frequencies are damped logarithmically and capped. Weights are scaled by a small inverse
   document frequency lexicon computed from the shipped corpus, so ubiquitous tokens (like
   `api` or `id`) count less than distinctive ones.
4. Features are projected with a signed count sketch: each feature lands on four slots with
   independent signs. A feature present on both sides adds coherently; collisions carry random
   signs and average out. This keeps short field names from picking up spurious cosine in a
   small dimension.

Condition blocks add structured features next to the text: the variable identity is signed by
the value (`Patient.admitted = true` and `Patient.admitted = false` point in opposite
directions), the operator is one-hot hashed, the exact value is a token, and numeric values add
a damped magnitude feature. The signed variable term is what makes epistemic states such as
`E_i => P_j` and its negation distinguishable instead of merely dissimilar.

The same signed construction is used for effects, which yields the two quantities the
compatibility engine needs:

```
coverage(pre_j, eff_i)  mean best per-variable identity cosine in [0,1]
signedCosine            cos(signedEff_i, signedPre_j) in [-1,1]
vectorScore             coverage * 0.5 * (1 + signedCosine)
```

A positive signed cosine means the effects point towards the later preconditions; a negative
one means they point away (an order created against a precondition that requires it cancelled),
and the vector score collapses to 0. The symbolic engine (typed entailment over the abstract
domain, input-output binding, operational checks) runs in parallel and the report carries both
verdicts, which is the separation required by property 5.

State and goal vectors reserve 32 dimensions for value magnitudes and 32 for variable presence
masks, which is what the state movement measurement (property 2) reads: an effect that flips a
boolean moves the state vector by 1 minus the cosine, while a payment capability that touches
none of the four clinic flags leaves the state vector bitwise unchanged.

## 4. Composition

A composite capability is a first class value: `compose(C_i, C_j)` merges inputs, outputs,
effects and cost, applies the reliability product `Rel_i * Rel_j` and the risk union
`1 - (1 - r_i)(1 - r_j)`, and removes preconditions satisfied by the earlier member. Encoding
the composite and composing the encodings agree to a cosine of 0.966; the operation is
associative to 0.9999999999999998. A composite's self compatibility is checked in experiment 2:
a two member composite is not reported incompatible, while a three member composite whose
second and third members contradict (create, pay, cancel) is.

## 5. Representation of the operational attributes

| Attribute | In the vector | Exactly enforced |
| --- | --- | --- |
| Time, money, energy, resource costs | quality block (8 dimensions) | `Context.maxTimeMs`, `maxMoney`, `maxEnergy`, `maxResource` composed caps |
| Risk | quality block | `Context.maxRisk`, composed as a risk union |
| Reliability | reliability block (1 dimension) | `Context.minReliability`, composed as a product |
| Availability (always / window) | availability block (1 dimension) | window evaluation `A_i(t)` with weekday and minutes after midnight |
| Constraints (K) | not embedded | typed condition checks against the post state |
| Resources and roles | resources block (16 dimensions) | inventory and role checks gated by their enforce flags |

The availability window is half open: opening minute inside, closing minute outside; a missing
time point skips the check instead of guessing; the weekend falls outside a weekday window.

## 6. The eight required properties, with evidence

| Property | Where the design answers it | Frozen evidence |
| --- | --- | --- |
| 1. Capability identity | partitioned vector, signed condition features | 0 duplicate vectors in 53 capabilities; nearest neighbour mean cosine 0.8385, max 0.9878 (the two registration capabilities in different vocabularies) |
| 2. State awareness | shared condition space, state value and coverage blocks | 1-cos movement 0.8948 for create; bitwise unchanged for payment; payment precondition alignment 0.1199 to 0.9865 after the create effect, cancel 0.9810 to 0.1414 |
| 3. Precondition-effect compatibility | signed effect vector, coverage, symbolic entailment | create to pay compatible (vector score 1.0000, signed cosine 1.0000), create to cancel incompatible (0.0000, -1.0000); 17 of 17 dataset verdicts reproduced; decidable cases AUC 1.0000 |
| 4. Input-output compatibility | input and output blocks, field matching | bound 10 of 10 field rows; 3 pass, 14 unknown, 0 fail binding checks; composite exposes `customer_id` |
| 5. Similarity is not composability | functional view reported next to the verdict | vector score AUC 1.0 against 0.7778 for raw cosine and 0.7778 for functional similarity on the compatibility set; symbolic engine 17 of 17 |
| 6. Composition | algebraic compose, re-encoded composite | composite interface, net delta and attributes; associativity 0.9999999999999998; algebraic vs re-encoded 0.9660 |
| 7. Goal relevance | goal vector and best alignment | 17 of 17 goal conditions writable by at least one capability; weakest best alignment 0.7246 on the clinic visit sheet |
| 8. Operational properties | quality, reliability, availability blocks plus exact attribute vector | numeric toggles 6 of 6; window opens 480, open 1019, closed 200 and 1020, closed on the weekend, skipped without a time point; inventories pass when covering and fail when missing |

## 7. Efficiency and storage

| Quantity | Value |
| --- | --- |
| Encode one capability | 236.1 microseconds |
| Rank one requirement against 53 capabilities | 2590.7 microseconds |
| Compatibility check of one pair | 493.7 microseconds |
| Capability vector | 259 doubles, 2072 bytes |
| Corpus of 53 capabilities | 109816 bytes |
| State and goal vector | 128 doubles each |
| Concept lexicon | 328 terms |

## 8. Limitations

- The hash projection is not learned: semantically close but lexically unrelated terms only
  connect through the curated concept table (a one-line change per term, documented in
  `documents/10_DEVELOPER_GUIDE.md`), not through training data.
- Small blocks trade dimension count for collision noise. The 16 text dimensions in each IO
  block are the measured lower bound that still separates `track_id` from `mrn`; shrinking them
  raises the projection noise floor like `1 / sqrt(dims)`.
- Sub-block concatenation makes cross-block cosines meaningless by construction. Only
  same-dimension, same-seed blocks compare (enforced by `Blocks::blocksComparable`), and the
  views report which blocks they average.
- Availability beyond weekly windows (holidays, one-off closures) is not representable; the
  window language is weekday plus minutes plus an always switch.
- The signed value projection is monotone but not order preserving beyond `tanh`; a cost of 500
  and a cost of 5000 are close, and exact comparisons for constraints live in the attribute
  vector on purpose.
