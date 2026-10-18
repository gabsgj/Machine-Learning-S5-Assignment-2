# Changelog

All notable changes to this project are documented here.

The project is currently organized as a small research/assignment prototype rather than a production software package.

---

## [0.3.0] — Project Organization

### Added

- Introduced a clean project directory structure:
  - `data/`
  - `experiments/`
  - `report/`
  - `results/`
  - `src/`
  - `tests/`
- Added `PROJECT_ARCHITECTURE.md`.
- Added a more detailed project `README.md`.
- Added this `CHANGELOG.md`.
- Added a dedicated `tests/` directory for future automated tests.

### Changed

- Moved formal application data into `data/`.
- Moved derived experimental datasets into `experiments/`.
- Moved report documents into `report/`.
- Moved experiment visualizations into `results/`.
- Moved the implementation into `src/`.

---

## [0.2.0] — Documentation and Presentation

### Added

- Polished technical report PDF.
- Editable DOCX version of the technical report.
- Polished formal embedding design PDF.
- Improved visual hierarchy, typography, equations, tables, callouts, headers, footers, and cover pages.

### Documentation

The report now explicitly documents:

- problem definition,
- design requirements,
- representation,
- mathematical formulation,
- compatibility,
- composition,
- implementation,
- experimental methodology,
- results,
- analysis,
- limitations,
- conclusion.

---

## [0.1.0] — Initial Assignment Implementation

### Added

- Structured Capability Embedding (SCE) baseline.
- State encoding.
- Goal encoding.
- Capability encoding.
- Capability similarity.
- Directed capability compatibility.
- Capability composition.
- Goal relevance.

### Added Dataset

- Formal application states.
- Goal specifications.
- Atomic capabilities.
- Compatibility labels.
- Operational attributes.

### Added Experiments

- Capability compatibility.
- Capability composition.
- Alternative implementations.
- Goal relevance.
- Operational attributes.

### Initial Results

The initial synthetic compatibility experiment achieved approximately:

```text
75% accuracy
```

The three-capability composition experiment produced approximately:

```text
0.917 cosine alignment
```

These results are treated as proof-of-concept measurements on the supplied synthetic dataset.

---

## Scope Notes

The project intentionally does not include:

- BFS,
- DFS,
- A*,
- D* Lite,
- LPA*,
- path search,
- replanning.

These belong to the planning/replanning context of Assignment 1 and are outside the stated scope of Assignment 2.

---

## Future Work

Potential future versions may include:

### 0.4.x

- Formal automated unit tests.
- More comprehensive experiment scripts.
- Larger synthetic datasets.
- Stronger logical predicate encoding.

### 0.5.x

- Learned embedding parameters.
- Larger capability-composition corpus.
- More rigorous train/validation/test splits.
- Learned compatibility classification.

### 1.0.x

- Comprehensive benchmark suite.
- Reproducible experiment runner.
- Statistical evaluation across multiple datasets.
- More advanced composition operators.
