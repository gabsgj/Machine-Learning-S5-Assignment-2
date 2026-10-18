# Dataset: labeled specification problems

Three problems with ground truth labels, replayed by the experiment suite against the real
components (the mapper, the compatibility engine, the encoders). Every label in this directory
was frozen from a verified run of those components, not written by hand: the measured scores are
quoted in the notes of each case, and `core/tests/test_corpus.cpp` replays the dataset so a component
change that breaks a label fails the test suite before the report is rewritten.

## Problems

| Problem | Domain | What it covers |
| --- | --- | --- |
| `hospital_alias/` | hospital | The same registration in two vocabularies, a row write and a screen; near ties, twin injection and full pool ranking over all 53 capabilities |
| `ecommerce_purchase/` | ecommerce | The specification pattern application: checkout requirement, screen persona, full pool run and a foreign domain rejection |
| `document_processing/` | documents | The third domain: summary requirement, intake in three personas, ordering cases around parsing |

## Case kinds

- `required_mappings`: requirement sheet, candidate sheets, expected selection. The expectation
  is one of `selected`, `resolved_by_kind` (a near tie decided by the requested delivery kind),
  `best_effort` (the closest sensible answer needs field renaming) or `rejected`.
- `negative_cases`: requirements that must stay below the calibrated threshold.
- `full_pool_cases`: the requirement against all capabilities of the five applications.
  Expectations `top1`, `top1_with_ambiguity` and `ambiguous`; these drive the precision and rank
  metrics of the evaluation experiment.
- `ambiguity_cases`: a synthetic twin cloned from a real capability and injected into the pool.
  The resolver must report the near tie instead of guessing.
- `compatibility_cases`: adjacent capability pairs checked with the symbolic compatibility
  engine. Expectations `compatible`, `uncertain` (established enough to run but with a binding
  the engine cannot prove) and `incompatible` (a precondition contradicted by the earlier
  effects or the initial state).
- `equivalence_groups`: one logical operation offered as several execution personas; the
  adaptation experiment synthesizes an adapter per member of the group.
- `name_pairs`: name level labels `equivalent`, `distinct` and `mechanism` for the vocabulary
  experiment. A `mechanism` pair is the same operation through a different delivery persona; its
  names deliberately share no vocabulary, so the label documents that name similarity is the
  wrong instrument for it and that the operation equality is pinned elsewhere (the equivalence
  groups).

## Requirements

The requirement sheets live in `specs/app/requirements/` and use the same formal language as
every other sheet, so the dataset references them by path rather than duplicating them.
