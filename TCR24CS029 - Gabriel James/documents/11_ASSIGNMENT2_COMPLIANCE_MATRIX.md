# Assignment 2 compliance matrix

Every requirement of the assignment specification, mapped to where it is satisfied, with the
verdict. Verdicts are YES, PARTIAL or NO, and PARTIAL and NO entries state exactly what is
missing. Line references are repository relative.

## 1. Deliverables

| Deliverable | Verdict | Evidence |
| --- | --- | --- |
| 1, Formal embedding design (state, goal and capability representations; embedding function; similarity and compatibility measures; composition where applicable) | YES | `documents/03_EMBEDDING_DESIGN.md` (layouts, hash projections, score formulas), `core/include/careweave/embedding/blocks.hpp` (the dimension layout as code) |
| 2, Implementation with encode(state), encode(goal), encode(capability), compose(capabilities), similarity(x, y) | YES | `core/src/embedding/encoders.cpp` (the five interface operations), `core/src/composer/composer.cpp`, `core/tests/test_embedding.cpp` (8 cases, 159 checks) |
| 3, Experimental dataset: application problems with initial states, goals, atomic capabilities, compositions, constraints and operational attributes | YES | `dataset/hospital_alias`, `dataset/ecommerce_purchase`, `dataset/document_processing`; five application sheets and five requirement sheets in `specs/app/` over a 53 capability corpus; `documents/12_DATASET_SPEC.md` |
| 4, Technical report with exactly the twelve named sections, as Markdown, LaTeX and PDF | YES | `assignment_2_submission/report/REPORT.md`, `REPORT.tex`, `REPORT.pdf` |

## 2. Formal model

| Requirement | Verdict | Evidence |
| --- | --- | --- |
| Application model A = (S, C, S_I, G, R, K) | YES | `specs/app/*.yaml` declare state schema, initial state, goal, resources, constraints and capabilities; parsed by `core/src/spec/spec_parser.cpp` and validated against `specs/capability.schema.json` |
| Capability tuple with all nine declared types (API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE) | YES | `core/include/careweave/core/types.hpp` enum and parser; all nine are round tripped and embeddable; the corpus uses API, DATABASE, GUI, FILE and EVENT |
| Inputs and outputs with types, domains and optionality | YES | schema plus `test_types` and `test_corpus` |
| Preconditions and effects as typed conditions (=, !=, <, <=, >, >=, in) | YES | `core/src/compat/conditions.cpp`, `core/tests/test_compat_conditions.cpp` (13 cases, 69 checks) |
| Constraints K and resources R, enforced | YES | composer attributes, `Context` checks, `enforceResources` and `enforceRoles` gating, experiment 5 |
| Costs (time, money, energy, resource, risk) | YES | quality tuple in the schema; composed by the composer; exact caps in the compatibility context |
| Reliability and availability, including A_i(t) windows | PARTIAL | reliability product and half open weekly availability windows are implemented and measured (experiment 5, 6 of 6 toggles, full window behaviour); windows are weekday plus minutes only, so holidays or one-off closures are not representable |
| Capability composition C_1 o ... o C_n | YES | `core/src/composer/`, experiment 2 (interface, net delta, attributes; associativity 0.9999999999999998) |
| Goal specification and goal relevance | YES | goal conditions in sheets; evaluation criterion 6 (17 of 17 writable, weakest best alignment 0.7246) |

## 3. Embedding design problem requirements

| Requirement | Verdict | Where |
| --- | --- | --- |
| Capability identity | YES | nearest neighbour statistics (0 duplicates, mean 0.8385, max 0.9878) |
| State awareness | YES | state movement and alignment measurements (criterion 2) |
| Precondition-effect compatibility (E_i => P_j) | YES | signed cosine and entailment; 17 of 17 dataset verdicts |
| Input-output compatibility | YES | 10 of 10 field rows bound; 3 pass, 14 unknown, 0 fail |
| Similarity versus composability, kept apart | YES | separate functional view and verdicts; AUC 1.0 versus 0.7778 for raw cosine |
| Composition representation | YES | composite encoding versus composed encodings 0.9660 |
| Goal relevance | YES | goal vector, writable conditions and best alignment |
| Operational properties | YES | embedded blocks plus exact attribute enforcement (experiment 5) |

## 4. Required experiments

| Experiment | Verdict | Evidence |
| --- | --- | --- |
| 1, CreateOrder / MakePayment / CancelCart compatibility | YES | `experiments/src/exp1_compatibility.cpp`; 17 pairs; verdicts 17 of 17; discrimination AUC 1.0 |
| 2, composition of C_1 -> C_2 -> C_3 | YES | `experiments/src/exp2_composition.cpp`; composite interface, delta and attributes; validity checks |
| 3, API / DATABASE / GUI alternative implementations | YES | `experiments/src/exp3_alternative_implementations.cpp`; four groups with 2 to 3 members and synthesized adaptations |
| 4, irrelevant capabilities | YES | `experiments/src/exp4_irrelevant_capabilities.cpp`; pool 77, decoys 24, mean reciprocal rank 1.0 |
| 5, all five operational attributes | YES | `experiments/src/exp5_operational_attributes.cpp`; toggles, windows, inventories, 21 setting weight sweep |

## 5. Evaluation criteria

| Criterion | Verdict | Frozen measurement |
| --- | --- | --- |
| Capability representation | YES | 0 duplicate vectors; nearest neighbour mean 0.8385, max 0.9878 |
| State relationship | YES | movement 0.8948 for create, bitwise unchanged for payment |
| Precondition-effect compatibility | YES | compatible 1.0000 signed 1.0000; incompatible 0.0000 signed -1.0000; decidable AUC 1.0000 |
| Input-output compatibility | YES | 10 of 10 bound; 0 failed checks |
| Composition | YES | composite interface and net delta; associativity 1.0000 |
| Goal relevance | YES | 17 of 17 writable; weakest alignment 0.7246 |
| Operational properties | YES | 6 of 6 toggles; full window behaviour; inventories and roles pass and fail as specified |
| Consistency | YES | 31 of 31 label checks; 53 of 53 vectors bitwise identical; repeat runs identical |
| Efficiency | YES | encode 236.1 us, rank 2590.7 us, check 493.7 us; 2072 bytes per capability |

## 6. Scope

| Requirement | Verdict | Evidence |
| --- | --- | --- |
| The planner stays out of the graded scope: no experiment references it | YES | gate G14: no planner references in `experiments/`, no planner symbols in any experiment binary (checked by the acceptance script) |
| The report stays within the embedding, mapping, adapter and runtime scope | YES | `assignment_2_submission/report/REPORT.md` sections 7 to 10; the plan view in the dashboard carries an explicit out of scope note |
| Three application problems from distinct domains | YES | hospital alias, commerce purchase, document processing |

## 7. Honest gaps

- Availability modelling stops at weekly windows (section 2).
- The interface verification includes a manual headless browser pass with pasted evidence
  (`documents/05_UI_WALKTHROUGH.md`); it is not wired into `verify_all.sh` because the script
  must run on machines without a browser installation. The automated layers (pytest UI routes
  and the live HTTP endpoint checks) do run in every acceptance pass.
- The report PDF is produced locally with a LaTeX toolchain; the Markdown and LaTeX sources are
  the portable forms.
- The concept lexicon is curated (328 terms) rather than learned; adding a term is a one line
  change documented in the developer guide. Vocabulary outside the lexicon still connects
  through shared tokens, as the alias experiment shows, but not through learned synonymy.
