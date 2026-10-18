# Experiments and evaluation

Five experiments and one evaluation harness answer the questions the assignment poses. All of
them run against the shipped corpus (53 capabilities across the hospital, commerce and document
problems) and the three application problems in `dataset/`. Every assertion is executed:
an experiment that cannot produce its claimed property fails the run. Outputs are written as
JSON, CSV and Markdown into `experiments/out/`; this document quotes the frozen numbers from
those files.

Re-run everything:

```
sh scripts/run_experiments.sh
```

Timings vary by a few percent between runs; every other number below is stable.

## Experiment 1: compatibility (CreateOrder, MakePayment, CancelCart)

Pattern: the assignment's own triple in the commerce domain. Raw vector cosines between the
three capabilities are all close (create to cancel 0.7146, create to pay 0.7186, pay to cancel
0.7737), so similarity alone cannot separate them. The compatibility verdicts do:

| Pair | Vector score | Signed cosine | Verdict | Symbolic |
| --- | --- | --- | --- | --- |
| create -> pay | 1.0000 | 1.0000 | compatible | entailed |
| create -> cancel | 0.0000 | -1.0000 | incompatible | conflict |
| cancel -> create | 0.5000 | 0.0000 | uncertain | input unbound |

Dataset and metrics:

| Metric | Value |
| --- | --- |
| Adjacent pairs in the dataset | 17 |
| Verdicts reproduced | 17 of 17 |
| Symbolic accuracy | 1.0000 |
| Discrimination AUC (vector score) | 1.0000 |
| Raw cosine AUC | 0.7778 |
| Functional similarity AUC | 0.7738 |
| Name pair AUC (18 labelled name pairs) | 0.9846 |
| Equivalent name pairs | mean 0.7698, min 0.6369 |
| Distinct name pairs | mean 0.1890, max 0.6699 |
| Mechanism-only name pairs | max 0.0000 |
| Noise floor (decoys) | cosine mean 0.7090, max 0.7984; name similarity mean 0.0525, max 0.3686 |

Observation: the same functional operation delivered under a different name or mechanism is
recognized (name pair AUC 0.9846), while decoy capabilities stay below the working range. The
two incompatible orders are separated by sign, not by distance, which is why the signed
construction exists.

## Experiment 2: composition (C1 -> C2 -> C3)

Pattern: compose the triple and measure the composite against its members.

| Quantity | Two member composite | Three member composite |
| --- | --- | --- |
| Interface | `customer_id` | `customer_id` |
| Net delta | `Order.exists` | `Order.exists` |
| Time | 320 ms | 410 ms |
| Money | 0.5 | 0.5 |
| Risk | 0.0397 | 0.0493 |
| Reliability | 0.9702 | 0.9605 |

Relations: encoding the composite versus composing the encodings agrees to 0.9660; the
operation is associative to 0.9999999999999998. The composite's own compatibility check reports
the two member composite as not incompatible and the three member composite as incompatible,
because its second and third members contradict.

## Experiment 3: alternative implementations (API, DATABASE, GUI)

Pattern: the same logical operation delivered through different mechanisms. Four groups: legacy
registration with API, DATABASE and GUI members; canonical registration with API and GUI; order
placement with API and GUI; document uptake with FILE, GUI and EVENT. Adaptation records are
synthesized for every member pair: the alternate registry's API adaptation renames
`patient_mrn -> pat_no`, `full_name -> pat_name` and back, with the confidence of each match.

| Metric | Functional view | Implementation view |
| --- | --- | --- |
| Within operation (same function, different kind) | mean 0.9582 | mean 0.8330 |
| Cross operation | mean 0.6526 | mean 0.8485 |

Observation: the functional view keeps one operation's implementations together while the
implementation view pulls different mechanisms apart. A direct row interface is functionally the
registration; mechanically it is something else.

## Experiment 4: irrelevant capabilities

Pattern: a pool of 77 capabilities, 24 of them decoys from unrelated domains, and five
requirements with exactly one intended implementation each.

| Metric | Value |
| --- | --- |
| Mean reciprocal rank over the five requirements | 1.0000 |
| Weakest intended score | 0.8346 |
| Strongest decoy score | 0.4962 (DEC-RunPayroll) |

Observation: unrelated applications are separated by a wide band, not by a hair.

## Experiment 5: operational attributes

Pattern: all five operational attribute families (time, money, energy, resource and risk
costs, reliability, and availability) plus the weights themselves.

- Numeric toggles: 6 of 6 (each cost cap flips its verdict when the cap tightens).
- Availability window: opens at minute 480, open at 1019, closed at 200 and closed at 1020
  (the window is half open), closed on the weekend, and skipped when no time point is given.
- Resource and role checks: 8 checks; inventories pass when covering and fail when missing,
  and the enforce flags gate both instead of treating an empty inventory as "nothing available".
- Weight sweep: 21 settings; the smallest positive ambiguity margin observed is 0.0035. The
  default weights produce margin 0.0492 with `AR-PatReg` selected and the kind tie break active.

## Evaluation: the nine criteria

`experiments/out/evaluation.json` records one row per criterion with the measurement, the value
and a conclusion. Frozen values:

| # | Criterion | Frozen value |
| --- | --- | --- |
| 1 | Capability representation | 0 duplicate vectors; nearest neighbour mean 0.8385, max 0.9878 (the two registration capabilities across vocabularies) |
| 2 | State relationship | movement 1-cos 0.8948 for create, bitwise unchanged for payment; payment precondition alignment 0.1199 to 0.9865; cancel 0.9810 to 0.1414 |
| 3 | Precondition-effect compatibility | compatible pair vector score 1.0000 signed cosine 1.0000; incompatible pair 0.0000 and -1.0000; 17 of 17 dataset verdicts; decidable AUC 1.0000 |
| 4 | Input-output compatibility | 10 of 10 field rows bound; binding checks 3 pass, 14 unknown, 0 fail; the composite exposes `customer_id` |
| 5 | Composition | interface, net delta and attributes as in experiment 2; associativity 1.0000; two member self check not incompatible, three member self check incompatible |
| 6 | Goal relevance | 17 of 17 goal conditions writable; weakest best alignment 0.7246 (clinic visit) |
| 7 | Operational properties | 6 of 6 numeric toggles; the full window behaviour; inventories and roles as in experiment 5 |
| 8 | Consistency | 31 of 31 label checks reproduced; 53 of 53 vectors bitwise identical across runs; repeated scoring and checking identical |
| 9 | Efficiency | encode 236.1 us per capability; rank 2590.7 us per requirement against 53 capabilities; check 493.7 us per pair; 2072 bytes per capability and 109816 bytes for the corpus; 128 doubles per state vector; 328 term lexicon |

Raw counters behind the criteria: `associativity_cosine` 0.9999999999999998, `check_micros`
493.7, `discrimination_auc` 1.0, `encode_micros` 236.1, `label_checks` 31, `label_ok` 31,
`nearest_neighbour_max` 0.9878, `nearest_neighbour_mean` 0.8385, `rank_micros` 2590.7,
`state_move` 0.8948.

## Output files

| File | Content |
| --- | --- |
| `exp1_compatibility.{json,csv,md}` | pair verdicts, name pairs, noise floor, metrics |
| `exp2_composition.{json,csv,md}` | composites, relations, validity checks |
| `exp3_alternative_implementations.{json,csv,md}` | groups, adaptations, view metrics |
| `exp4_irrelevant_capabilities.{json,csv,md}` | pool, decoys, ranks |
| `exp5_operational_attributes.{json,csv,md}` | toggles, windows, resources, sweep |
| `evaluation.{json,csv,md}` | the nine criteria with measurements and raw counters |

## Scope note

The experiments, the evaluation and every number above stay inside the embedding, mapping,
adapter and runtime scope. The planner and the composer's search machinery are part of the
running system but are not exercised by any experiment, and gate G14 checks this mechanically:
no experiment source references the planner, and no experiment binary contains a planner
symbol.
