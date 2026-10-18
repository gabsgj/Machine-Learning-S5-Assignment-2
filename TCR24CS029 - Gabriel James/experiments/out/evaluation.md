# Evaluation: the nine criteria

| # | property | measured value | conclusion |
| --- | --- | --- | --- |
| 1 | Capability representation | duplicate vectors 0; nearest neighbour mean 0.8385, max 0.9878 (CV-RegisterPatient / AR-RegisterPatient) | Yes: every capability has its own vector and even the closest pair keeps a visible distance. |
| 2 | State relationship | movement 1-cos 0.8948 for create, bitwise unchanged for payment; payment precondition alignment 0.1199 -> 0.9865; cancel precondition 0.9810 -> 0.1414 | Yes: capabilities and states share one condition space, so a precondition aligns with exactly the states that satisfy it. |
| 3 | Precondition-effect compatibility | C_1 -> C_2 compatible (vector score 1.0000, signed cosine 1.0000); C_1 -> C_3 incompatible (vector score 0.0000, signed cosine -1.0000); dataset verdicts 17 of 17 reproduced; decidable AUC 1.0000 | Yes: composable pairs are separated from contradictory ones, and the signed effects read as alignment and contradiction rather than as distance. |
| 4 | Input-output compatibility | bound 10 of 10 field rows; input-output check 3 pass, 14 unknown, 0 fail; composite exposes [customer_id] | Yes: dependencies are represented through named bindings, and what a caller must still supply is exactly what stays unbound. |
| 5 | Composition | interface [customer_id]; net delta Order.exists; time 320 ms, money 0.5, risk 0.0397, reliability 0.9702; associativity cosine 1.0000; self checks: two-member not incompatible, three-member incompatible | Yes: composites keep the caller interface, the net delta, the quality laws and the contradiction structure of their members. |
| 6 | Goal relevance | writable 17 of 17 goal conditions; weakest best alignment 0.7246 (hospital_clinic_visit.yaml) | Yes: a goal is expressed in the same condition space as the capabilities, and every goal condition is reachable by a named effect. |
| 7 | Operational properties | numeric toggles 6 of 6; window opens at 480, open at 1019, closed at 200 and at 1020 (half open), closed on the weekend, skipped without a time point; inventories pass when covering and fail when missing, enforce flags gate both | Yes: cost, risk, reliability, availability windows, resources and roles are represented and checked as first class context. |
| 8 | Consistency | label checks reproduced 31 of 31 (required, negative, full pool, ambiguity and compatibility cases); vectors bitwise identical 53 of 53; repeated scoring and checking identical | Yes: the same specification always produces the same numbers, and the labeled behaviour holds across the three problem domains. |
| 9 | Efficiency | encode 236.1 us per capability; rank 53 2590.7 us per requirement; check 493.7 us per pair; 259 doubles (2072 bytes) per capability, 109816 bytes for the corpus; state vectors 128 doubles; lexicon 328 terms | Everything runs offline in microseconds per operation with kilobyte sized vectors, so the representation fits the interactive tooling above it. |

## Measurement detail

- 1. **Capability representation**: nearest-neighbour full-vector cosine over the 53 capability corpus (53 by 52 pairs).
- 2. **State relationship**: state core movement when effects apply (and no movement for a capability without effects); alignment of the precondition's desired-condition form with the state before and after.
- 3. **Precondition-effect compatibility**: pattern pair verdicts and scores; the 17 frozen dataset verdicts; vector score AUC over the six decidable pairs.
- 4. **Input-output compatibility**: field assignment rows over the six required mappings; input-output check outcomes over the 17 dataset pairs; the composite interface.
- 5. **Composition**: compose the pattern members; quality laws; associativity of both bracketings; composite self check of the valid and the contradictory order.
- 6. **Goal relevance**: goal conditions writable by at least one capability across the five applications; best goal-to-effect alignment per application (both in the shared condition space).
- 7. **Operational properties**: six numeric attribute toggles (cap at the composed value against just past it); availability window arithmetic at five points plus the omitted control; resource and role inventories enforced and gated.
- 8. **Consistency**: replay of every dataset label through the real components; repeated encoding, scoring and checking for bitwise reproducibility.
- 9. **Efficiency**: wall clock means over repeated runs (5000 encodings, 100 rankings against the 53 candidate pool, 500 compatibility checks) and the storage arithmetic of the vectors.
