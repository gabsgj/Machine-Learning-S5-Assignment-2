# 12 Dataset specification

The labeled dataset under `dataset/` is the ground truth the experiment suite measures against.
It contains three specification problems, each a labeled set of resolution, ranking, ambiguity
and compatibility cases over the five application sheets of `specs/app/`. This document defines
the structure, the meaning of every label, how the labels were frozen and how the experiments
consume them.

## 1. Why a dataset at all

The assignment asks for measurements, not demonstrations. A measurement needs a fixed input set
with known answers, so the repository ships its problems instead of generating them at
experiment time. Every label is machine checked: `core/tests/test_corpus.cpp` replays the whole
dataset against the real mapper and the real compatibility engine, so the suite fails if a
component change breaks a label, before any table in the report could silently become false.

## 2. Layout

```
dataset/
  README.md                          index of the three problems
  hospital_alias/problem.json        the acceptance problem: two registration vocabularies
  ecommerce_purchase/problem.json    the specification pattern problem
  document_processing/problem.json   the third domain problem
```

Requirement sheets live in `specs/app/requirements/`; the dataset references them by path, so a
requirement is authored exactly once. All paths are relative to the CareWeave Mini root.

## 3. Common fields

Every `problem.json` has:

- `problem_id`, `domain`, `description`: identity of the problem.
- `pool`: the application sheets that form the full candidate corpus of this problem (all five
  applications, 53 capabilities in total).
- `required_mappings`, `negative_cases`: requirement scoped against selected candidate sheets.
- `full_pool_cases`: requirement scoped against the whole pool.
- `ambiguity_cases`: twin injection cases.
- `compatibility_cases`: adjacent capability pairs for the symbolic engine.
- `equivalence_groups`: one logical operation offered as several execution personas.
- `name_pairs`: name level labels for the vocabulary experiment. Three kinds: `equivalent` (the
  names denote the same operation, `register_pat` against `Pat_reg`), `distinct` (the names
  denote different operations, including the same-prefix traps `Pat_reg` against `Pat_lookup`),
  and `mechanism` (the same operation reached through a different delivery persona whose names
  deliberately share no vocabulary, `place_order` against `checkout_form`; the operation level
  relation is pinned by an equivalence group, the name view is expected to stay apart).

## 4. Label kinds

### 4.1 Mapping expectation

| Label | Meaning | Machine check |
| --- | --- | --- |
| `selected` | the expected capability must win the selection, no ambiguity | best id in the expected set, `ambiguous` false |
| `resolved_by_kind` | the expected capability wins a near tie because the requirement's delivery kind singles it out | best id expected, `kindTieBreak` true, `ambiguous` false |
| `best_effort` | the expected capability is the closest sensible answer and needs field renaming | best id expected, no ambiguity |
| `rejected` | nothing must pass the threshold | `Selection::bestIndex` is -1 |

### 4.2 Full pool expectation

| Label | Meaning |
| --- | --- |
| `top1` | the expected capability is ranked first and the margin exceeds the ambiguity margin |
| `top1_with_ambiguity` | the expected capability is ranked first and a near tie is reported |
| `ambiguous` | the near tie is the correct outcome; the accepted top 1 ids are listed |

### 4.3 Compatibility expectation

The symbolic engine returns one of three verdicts, and the dataset labels all three:

- `compatible`: every precondition is entailed by the earlier effects, every mandatory input is
  bound, and no check is unknown.
- `uncertain`: the pair is not proven. The engine deliberately leaves state variables that the
  earlier effects do not write unconstrained, because another step of the pipeline may have
  written them; a precondition that is merely not established is unknown, not contradictory.
- `incompatible`: an effect actively contradicts a precondition (for example a cancellation
  writing `CANCELLED` where the later step requires `PAID`), a type mismatch, or a failed
  operational check.

The distinction matters for the report: an ordering the live modules reject at runtime (a
laboratory result before the sample) is uncertain statically and rejected with 409 dynamically,
and both facts are measured.

### 4.4 Ambiguity cases

An `inject` block clones a real capability, renames it slightly and adds it to the candidate
set. The resolver must report the near tie. The label lists both acceptable top 1 ids; guessing
one silently is a failure.

### 4.5 Equivalence groups

A group names one logical operation and its members across execution personas (API, DATABASE,
GUI, FILE, EVENT). The adaptation experiment synthesizes an adapter for every member and
compares the logical contracts; the conformance test only verifies that every member exists.

## 5. Calibration

The mapping threshold is 0.55, recalibrated in two measurement campaigns. Measured values:

- every intended mapping scores 0.7909 or above (the weakest accepted case is the best effort
  resolution of `register_pat` against the clinic application);
- unrelated capabilities of the corpus peak at 0.4092 (the document summary requirement against
  the audit policy computation), and the adversarial decoys of experiment 4 (capabilities that
  share a token with a requirement on purpose, for example `register_employee` against
  `register_pat`) reach 0.4962; a threshold of 0.45 could not separate those two hard decoys;
- the ambiguity margin is 0.05; near ties inside it are reported, and the delivery kind tie
  break resolves exactly the case where the requirement's kind singles out one candidate
  (`register_pat` against the alias application: 0.8346 over 0.7854, margin 0.0492).

The numbers above are also asserted by the conformance test and quoted per case in the dataset
notes, so this section cannot drift from the code without failing the suite.

## 6. How the experiments consume the dataset

- The vocabulary experiment (E1) uses `name_pairs` and the compatibility cases: measured name
  similarity against the name level labels (`equivalent` above `distinct`, `mechanism` pairs
  reported separately because a name view cannot see them), and the engine verdicts against the
  compatibility labels, including the high similarity low compatibility pairs.
- The composition experiment (E2) uses the application sheets and the compatibility cases as
  the seed for sequence tests, deltas and associativity.
- The adaptation experiment (E3) uses `equivalence_groups` and the `best_effort` mapping, where
  the synthesized adapter renames fields.
- The ranking experiment (E4) uses the `full_pool_cases` as the distractor evaluation:
  53 capabilities per requirement, precision@k, recall@k and mean reciprocal rank against the
  labeled top 1.
- The operational attributes experiment (E5) uses the quality, reliability, availability and
  resource fields of the application sheets, including the negative operational cases the
  labels imply.

## 7. Mirror

The dataset is mirrored into `assignment_2_submission/dataset/` for the submission copy of the
project; the two copies are identical and the mirror is performed by the bundling step of the
gateway tooling, not by hand.
