# Assignment 2 – Vector Embedding for Capability Composition

Course: PCCST503 · Author: Shima Shamsudheen · Roll No: 77

A problem-specific vector embedding for formally specified states, goals and
capabilities, with compatibility checking, composition, goal relevance and
operational attributes.

## How to run

```bash
pip install numpy pandas matplotlib
python main.py
```

Set `SHOW_PLOTS=0` to run without opening plot windows.
Expected ending of the output: `All experiments completed.`

## Design in brief

| Space | Dimension (Problem 1) | Content |
|---|---|---|
| Condition space | 11 | States and goals: +1 true, -1 false, 0 unknown |
| Capability space | 53 | Weighted blocks: preconditions, effects, inputs, outputs, mechanism, resources |
| Operational vector | 4 | cost/10, reliability, availability, 1 - risk (kept separate) |

- **Similarity:** cosine similarity of capability vectors (functional resemblance).
- **Compatibility:** logic (effects satisfy preconditions), input/output, availability and
  non-redundancy checks. Similarity and compatibility are deliberately separate.
- **Composition:** block algebra for C2 ∘ C1, applied recursively for n capabilities.
- **Goal relevance:** progress of a capability's effects on the unmet goal literals.

## Files

| File | Description |
|---|---|
| `main.py` | Embedding system and all experiments (Deliverables 1–2 implementation) |
| `experimental_dataset.json` | Formal problems: states, goals, capabilities (Deliverable 3) |
| `compatibility_results.csv` | Similarity and compatibility for all capability pairs |
| `operational_results.csv` | Cost, reliability, availability, risk, resources |
| `cost_comparison.png` | Cost and reliability comparison |
| `similarity_vs_compatibility.png` | Similarity vs compatibility heatmaps |
| `goal_relevance.png` | Goal relevance ranking |
| `Technical_Report.pdf` / `.docx` | Technical report (Deliverable 4) |

## Experiments covered

1. Capability compatibility (CreateOrder → MakePayment / CancelCart / SendNotification)
2. Capability composition (three-step composite)
3. Alternative implementations (API / database / GUI)
4. Irrelevant capabilities and goal relevance
5. Operational attributes (cost, reliability, risk, resources, availability, constraints)

Plus: state awareness, similarity vs compatibility, consistency on a second problem
(file-processing pipeline) and efficiency measurements.