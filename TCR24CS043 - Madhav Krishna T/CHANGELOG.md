# Changelog

## Final cleaned package — SCE-128 v2.1

- Removed obsolete phase-specific prototype programs (`exp*`, `*_v2`, old smoke programs).
- Renamed runnable programs to explicit `phase01`–`phase08` names.
- Renamed ambiguous implementation modules for clarity (`data_models.py`, `final_model.py`, `learned_composer.py`, `formal_composition.py`).
- Added shared evaluation utilities.
- Added a single `run_all.py` entry point.
- Expanded final terminal output so each experiment reports its purpose, key metrics, methodological notes, and artifact paths.
- Preserved v1.1 baseline results for controlled comparison with v2.1.
- Preserved the leakage-free learned composition methodology.
- Added a final project smoke test through `python -m src`.

## Methodological preservation

No numerical result was deliberately altered during the cleanup. The cleanup changes naming, organization, documentation, and reproducibility tooling rather than changing the frozen final model design.
