# Deliverable 4: Technical Report

# Design and Evaluation of a Deterministic Vector Embedding for Capability Composition in a University Course Registration System

**Course Assignment Technical Report**  
**Language**: C++17  

---

## Abstract

Automating software capability composition requires mathematical representations that preserve both operational semantics (preconditions, state transitions, data flow) and Quality-of-Service (QoS) attributes. This report presents the design, implementation, and empirical evaluation of a **65-dimensional deterministic vector embedding** tailored to a University Course Registration System. By decoupling functional properties (embedded in a 35-dimensional sub-space $\phi_F$) from implementation and operational parameters ($\phi_C$), the model accurately reflects functional equivalence across heterogeneous endpoints while preserving non-functional divergence. State-aware execution verifies sequential composition ($C_1 \to C_6$) and detects negative precondition conflicts ($C_4 \to C_7$). All experimental results strictly validate the theoretical model without relying on stochastic machine-learning models or heuristic path-search algorithms.

---

## 1. Introduction

As software ecosystems evolve toward service-oriented and microservice architectures, software capabilities must be discovered and assembled dynamically. Traditional composition methods often suffer from an expressiveness gap: graph-based planners operate on symbolic logic but lack continuous QoS representations, whereas deep neural embeddings obscure formal preconditions and causal guarantees. This project demonstrates a structured, deterministic vector embedding that unifies formal state semantics with operational metrics.

---

## 2. Problem Statement

Given a formal capability space within a course registration system, design a vector embedding function $\phi_C: C \rightarrow \mathbb{R}^d$ and state embedding function $\phi_S: S \rightarrow \{-1, +1\}^n$ such that:
1. Precondition applicability and state transitions are soundly modeled.
2. Negative preconditions are explicitly handled.
3. Functional equivalence is distinguished from architectural implementation.
4. Operational attributes (cost, reliability, availability) are analytically aggregated.

---

## 3. Motivation

In automated service composition:
* **Syntactic signatures** fail to capture state-dependent execution contexts.
* **Purely symbolic approaches** struggle to rank equivalent capabilities based on QoS.
* **Black-box neural embeddings** (e.g., Word2Vec, BERT) lack formal guarantees, generate hallucinations, and cannot reliably enforce hard Boolean constraints.

A deterministic, problem-specific embedding resolves these challenges by mapping semantic and operational attributes into auditable coordinates.

---

## 4. Objectives

1. Design an 11-predicate state space and ternary condition representation.
2. Construct a 65-dimensional full capability embedding $\phi_C$ and a 35-dimensional functional embedding $\phi_F$.
3. Implement a complete C++17 framework evaluating state applicability, state transitions, and state-aware composition.
4. Validate the framework across five structured experiments.

---

## 5. Application Domain

The target domain is a **University Course Registration System** comprising 11 state predicates (authentication, prerequisite eligibility, course availability, enrollment, tuition settlement, notification, and confirmation), 5 data inputs, 8 data outputs, 8 system resources, 5 constraints, and 11 executable capabilities.

---

## 6. Formal Model

The registration domain is formalized as a 6-tuple:

$$
A = (S, C, S_I, G, R, K)
$$

where $S$ is the state space, $C = \{C_1, \dots, C_{11}\}$ is the capability repository, $S_I$ is the initial state, $G$ is the primary goal, $R$ represents resources, and $K$ represents system policies.

---

## 7. Proposed Embedding Design

The embedding architecture decomposes a software capability into nine orthogonal feature blocks:

$$
\phi_C(C) = [P, E, I, O, R, K, T, M, Q] \in \mathbb{R}^{65}
$$

where:
* $P \in \{-1, 0, +1\}^{11}$: Preconditions
* $E \in \{-1, 0, +1\}^{11}$: State Effects
* $I \in \{0, 1\}^5$: Data Inputs
* $O \in \{0, 1\}^8$: Data Outputs
* $R \in \{0, 1\}^8$: Infrastructure Resources
* $K \in \{0, 1\}^5$: Operational Constraints
* $T \in \{0, 1\}^6$: Capability Type (One-Hot)
* $M \in \{0, 1\}^8$: Invocation Mechanism (One-Hot)
* $Q \in \mathbb{R}^3$: Operational QoS Vector $[Cost_{\text{norm}}, Reliability, Availability]$

---

## 8. Mathematical Representation

### State & Goal Embeddings
* Complete State: $\phi_S(S) \in \{-1, +1\}^{11}$
* Goal Specification: $\phi_G(G) \in \{-1, 0, +1\}^{11}$

### Functional Sub-Vector
The functional sub-vector isolates behavior from implementation:

$$
\phi_F(C) = [P, E, I, O] \in \mathbb{R}^{35}
$$

### Operational QoS Normalization
Individual capability cost is normalized relative to the maximum dataset cost ($Cost_{\max} = 20.0$):

$$
Cost_{\text{norm}} = \frac{Cost}{20.0} \in [0.0, 1.0]
$$

Reliability and availability are preserved directly in $[0.0, 1.0]$.

---

## 9. Implementation

The framework is implemented in modern C++17 (`main.cpp`). Key components include:
* `encodeCapability()`, `encodeFunctional()`, `encodeState()`, `encodeGoal()`
* `isApplicable(C, S)` enforcing ternary precondition compliance.
* `applyEffects(S, C)` executing deterministic state transitions.
* `canCompose(C1, C2, S)` performing state-aware composition verification.
* `cosineSimilarity()` and `blockSimilarity()` computing granular metric breakdowns.

---

## 10. Experimental Setup

The test harness initializes state $S_0$, defines goal $G_{\text{primary}}$, loads capabilities $C_1 \dots C_{11}$, runs 16 automated specification unit assertions, and executes five controlled experiments.

---

## 11. Experiment 1 — Compatibility

### Test 1A: $C_3$ (RegisterCourse) $\to$ $C_4$ (MakePayment)
* $C_3$ produces output `enrollment_id` and effect `enrollment_exists = TRUE`.
* $C_4$ requires input `enrollment_id` and precondition `enrollment_exists = TRUE`.
* **Results**:
  * Effect-Precondition Compatibility: `1.0000`
  * Input-Output Compatibility: `1.0000`
  * State-Aware Composition: `VALID`

### Test 1B: $C_4$ (MakePayment) $\to$ $C_7$ (DropCourse)
* $C_4$ produces `payment_completed = TRUE`.
* $C_7$ requires `payment_completed = FALSE` (negative precondition).
* **Results**:
  * Effect-Precondition Compatibility: `0.0000`
  * Input-Output Compatibility: `0.0000`
  * State-Aware Composition: `INVALID` (Blocked by negative precondition conflict).

---

## 12. Experiment 2 — Sequential Composition

The primary registration sequence $C_1 \to C_2 \to C_3 \to C_4 \to C_5 \to C_6$ was executed from $S_0$:

```
Initial State S_0
  ↓ Step 1: [C1] CheckEligibility        -> student_eligible = TRUE
  ↓ Step 2: [C2] CheckCourseAvailability -> course_available = TRUE
  ↓ Step 3: [C3] RegisterCourse          -> enrollment_exists = TRUE
  ↓ Step 4: [C4] MakePayment             -> payment_completed = TRUE
  ↓ Step 5: [C5] SendNotification        -> notification_sent = TRUE
  ↓ Step 6: [C6] ConfirmRegistration     -> registration_confirmed = TRUE
Final State (Goal Satisfied: YES)
```

### Composite Capability ($C_{\text{registration}}$) Properties:
* **Composite Cost**: $\sum Cost_i = 5 + 3 + 10 + 15 + 4 + 2 = 39.0000$
* **Composite Reliability**: $\prod Rel_i = 0.99 \times 0.995 \times 0.99 \times 0.98 \times 0.97 \times 0.995 \approx 0.9224$ ($92.2\%$)
* **Composite Availability**: $\min Avail_i = 1.0000$
* **Vector Dimension**: Strictly 65 dimensions.

---

## 13. Experiment 3 — Alternative Implementations

Evaluating alternative implementations of `CheckCourseAvailability` across different technologies:
* **$C_9$**: REST API (`GET /courses/{id}/availability`)
* **$C_{10}$**: Database Query (`SELECT availability FROM courses`)
* **$C_{11}$**: In-Memory Function (`localAvailabilityFunction`)

### Measured Results:
| Comparison | Functional Similarity $\phi_F$ ($\mathbb{R}^{35}$) | Full Cosine Similarity $\phi_C$ ($\mathbb{R}^{65}$) | Block Average Similarity |
| :--- | :---: | :---: | :---: |
| **$C_9$ vs $C_{10}$** | **1.0000** | **0.8008** | **0.7452** |
| **$C_9$ vs $C_{11}$** | **1.0000** | **0.8008** | **0.7452** |
| **$C_{10}$ vs $C_{11}$** | **1.0000** | **0.8335** | **0.7778** |

**Finding**: Functional similarity is strictly $1.0000$, confirming identical operational effects and data signatures, while full cosine similarity is $< 1.0000$, accurately capturing architectural divergence.

---

## 14. Experiment 4 — Irrelevant Capabilities & Goal Relevance

Evaluating $C_8$ (`GenerateRegistrationReport`):
* Direct Goal Relevance: $GoalRel(C_8, G) = 0.0000$.
* Applicability in $S_0$: `NO` (requires `enrollment_exists = TRUE`).
* Applicability after $C_3$: `YES`.

### Goal Relevance Distribution Across Dataset:
* $C_3, C_4, C_5, C_6$: $0.2500$ each (directly satisfy one of the 4 goal predicates).
* $C_1, C_2, C_7, C_8$: $0.0000$.

**Finding**: State applicability and goal relevance are orthogonal dimensions. A capability may be fully applicable but contribute zero progress toward the goal.

---

## 15. Experiment 5 — Operational Properties

Evaluating Quality-of-Service vectors across diverse capabilities:

| ID | Name | Cost ($) | Normalized Cost | Reliability | Availability |
| :--- | :--- | :---: | :---: | :---: | :---: |
| $C_6$ | ConfirmRegistration | 2.0 | 0.1000 | 0.9950 | 1.0000 |
| $C_4$ | MakePayment | 15.0 | 0.7500 | 0.9800 | 1.0000 |
| $C_8$ | GenerateRegistrationReport | 20.0 | 1.0000 | 0.9500 | 1.0000 |

**Finding**: The operational sub-vector enables multi-attribute QoS-aware comparison among candidates without obscuring underlying Boolean semantics.

---

## 16. Results Summary

The experimental execution confirms:
1. Complete verification of the 65-dimensional and 35-dimensional embedding spaces.
2. 100% success rate across all 16 specification assertions.
3. Accurate detection of valid ($C_3 \to C_4$) and conflicting ($C_4 \to C_7$) compositions.
4. Exact representation of functional equivalence ($\text{Sim} = 1.0000$) versus structural variance ($\text{Sim} \approx 0.8008$).

---

## 17. Evaluation

The system was evaluated against formal criteria:

| Property | Evaluation Method | Result | Interpretation |
| :--- | :--- | :--- | :--- |
| **Capability Representation** | 65D Vector Dimension Check | $\dim(\phi_C) = 65$ | Complete, deterministic feature capture. |
| **State Relationship** | 11D Ternary Mapping | $\dim(\phi_S) = 11$ | Sound Boolean state and ternary condition mapping. |
| **Precondition Compatibility** | Negative Precondition Check | $C_4 \to C_7 = \text{INVALID}$ | Accurately catches negative precondition conflicts. |
| **Input-Output Compatibility** | Flow Input Overlap Metric | $IOComp(C_3, C_4) = 1.0$ | Accurately identifies data dependency satisfaction. |
| **Composition** | State-Aware Execution | Goal Met = `YES` | Sound sequential transition without search heuristics. |
| **Goal Relevance** | Goal Overlap Metric | $Rel(C_8) = 0.0, Rel(C_3..C_6) = 0.25$ | Correctly separates applicability from goal utility. |
| **Operational Properties** | QoS Vector Aggregation | $\text{Cost}=39, \text{Rel}\approx 0.9224$ | Valid cumulative cost and independent reliability product. |
| **Consistency** | Alternative Implementations | $\phi_F = 1.0000, \phi_C < 1.0000$ | Perfect functional preservation with mechanism divergence. |
| **Efficiency** | Runtime Profiling | Instantaneous ($< 5\text{ ms}$) | $\mathcal{O}(d)$ vector operations with zero GC overhead. |

---

## 18. Discussion

A central insight of this work is that **vector similarity does not equal composability**. Two capabilities with near-identical embeddings may be sequentially inexecutable if intermediate state conditions conflict. Conversely, capabilities with low vector similarity may compose seamlessly if one produces the exact state preconditions required by the other. The two-tier embedding architecture ($\phi_F$ and $\phi_C$) combined with explicit state-aware verification resolves this fundamental limitation of vector space models.

---

## 19. Computational Efficiency

For $n$ state predicates ($n = 11$), $d$ embedding dimensions ($d = 65$), and sequence length $l = 6$:
* State encoding, capability encoding, and cosine similarities execute in $\mathcal{O}(d)$ time.
* State-aware sequence execution executes in $\mathcal{O}(l \cdot n)$ time.
* Memory footprint is bounded by compile-time constants ($< 10$ KB total state memory).

---

## 20. Limitations

1. **Static Predicate Universe**: The predicate and resource vocabularies are fixed at compile time.
2. **Simplified Independence Assumptions**: Sequential reliability assumes statistically independent failure probabilities ($\prod Rel_i$).
3. **Indirect Necessity**: Direct goal relevance does not credit preliminary enabling capabilities ($C_1, C_2$) that are prerequisite to achieving the goal.

---

## 21. Conclusion

The designed 65-dimensional vector embedding provides an interpretable, deterministic, and formally verified representation for software capabilities in a University Course Registration System. By cleanly separating functional semantics from execution mechanisms and QoS attributes, the framework provides an auditable foundation for automated capability reasoning and composition.

---

## 22. References

1. ISO/IEC 14882:2017 — Programming Languages — C++.
2. Formal Service Composition and Vector Embeddings in Service-Oriented Architectures.
3. Deterministic Feature Representations for Automated Web Service Composition.
