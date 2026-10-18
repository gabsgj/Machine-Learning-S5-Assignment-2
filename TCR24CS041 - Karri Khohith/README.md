# Vector Embedding for Capability Composition

**PCCST503 – Assignment 2**

**Submitted by:** KHOHITH  
**Register Number:** TCR24CS041

## 1. Objective

This project develops a problem-specific vector representation for formally specified software capabilities. The representation is designed to preserve functional relationships needed for:

- state and goal representation
- directional precondition/effect compatibility
- input/output compatibility
- capability composition
- functional and implementation similarity
- goal relevance
- operational/QoS attributes such as latency, cost, risk and reliability

This is an independent implementation inspired by the assignment specification. The implementation, examples, datasets, experiments and report have been organized and written for this submission.

## 2. Core idea

A capability is represented by structured feature blocks instead of one undifferentiated semantic vector:

`state preconditions | state effects | inputs | outputs | type | resources | QoS`

The resulting vector supports both symmetric measurements (such as similarity) and directional measurements (such as whether the effect of one capability satisfies the precondition of another).

## 3. Capability model

Each capability contains:

- name
- type
- preconditions
- effects
- inputs
- outputs
- resources
- latency
- monetary cost
- risk
- energy
- reliability
- availability
- mechanism

## 4. Compatibility

For `A -> B`, compatibility combines:

1. **Precondition-effect compatibility**: effects of A satisfy requirements of B.
2. **Input-output compatibility**: outputs of A can supply inputs of B.

The score is directional, so `A -> B` can differ from `B -> A`.

## 5. Composition

Sequential composition combines capabilities while:

- retaining requirements that are not internally satisfied
- merging state effects in execution order
- removing intermediate inputs already produced by an earlier capability
- accumulating operational costs
- multiplying reliability
- combining required resources

Reliability is stored using `-log(reliability)` so independent reliability penalties become additive.

## 6. Included application domains

Three domains are included:

### E-Commerce
Register user -> create order -> make payment -> reserve stock -> send confirmation

### Cloud DevOps
Checkout -> lint -> test -> build image -> push image -> deploy -> health check

### Healthcare
Verify patient -> record vitals -> run lab test -> diagnose -> authorize prescription -> dispense medicine

## 7. Experiments

The experiment runner evaluates:

1. Directional capability compatibility
2. Sequential composition and associativity
3. Alternative implementations
4. Goal-relevance screening
5. QoS and reliability preservation

Run everything with:

```bash
python run_assignment.py
```

Run unit tests:

```bash
pytest -q
```

## 8. Project structure

```text
capability_embedding_khohith/
├── capembed/
│   ├── __init__.py
│   ├── model.py
│   ├── encoder.py
│   ├── metrics.py
│   └── composition.py
├── datasets/
│   ├── ecommerce.json
│   ├── devops.json
│   └── healthcare.json
├── experiments/
│   └── run_experiments.py
├── figures/
├── tests/
│   └── test_capembed.py
├── report/
│   └── TECHNICAL_REPORT.md
├── requirements.txt
└── run_assignment.py
```

## 9. Student

**KHOHITH — TCR24CS041**
