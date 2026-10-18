# Deliverable 4 — Technical Report
## Design of a Vector Embedding for Capability Composition
### Application Domain: Online Course Enrollment System

## 1. Problem Definition

This work investigates whether formally specified capabilities in an online
course enrollment system can be embedded into a vector space that preserves
functional relationships needed for compatibility and composition.

The system contains operations such as course selection, payment, enrollment,
notification, scholarship verification and alternative enrollment mechanisms.

The central composition is:

```text
SelectCourse → MakePayment → EnrollStudent → SendNotification
```

The objective is not to implement a planner. It is to represent the operations
and their relationships.

## 2. Design Requirements

The representation must support:

- distinct capability identity;
- state awareness;
- precondition-effect compatibility;
- input-output compatibility;
- similarity without confusing similarity with composability;
- atomic and composite capabilities;
- goal relevance;
- constraints and resources;
- cost, reliability and availability;
- consistency across several formally specified problems;
- reasonable computational and storage efficiency.

## 3. Related Embedding Approaches

### One-hot encoding

One-hot encoding is simple and interpretable, but it treats every symbol as
independent and provides weak support for graded similarity.

### Bag-of-features / multi-hot representation

A structured multi-hot representation naturally fits formal symbolic fields.
It is interpretable and deterministic but does not learn semantic relationships.

### Distributed neural embeddings

Neural embeddings can capture semantic similarity, but a generic text model
may treat two descriptions as similar even when their preconditions/effects are
not executable together.

### Proposed approach

This project combines structured multi-hot symbolic features with a compact
numeric operational block. The approach is problem-specific and transparent.

## 4. Proposed Representation

Each capability is

\[
C_i=(T_i,I_i,O_i,P_i,E_i,K_i,R_i,Q_i,Rel_i,A_i,M_i).
\]

The vector contains explicit blocks for type, preconditions, effects,
inputs, outputs, constraints, resources and mechanism. Operational attributes
are represented numerically.

The most important weights are assigned to effects and preconditions because
these determine state transformation and composability.

## 5. Mathematical Formulation

See Deliverable 1 for the full equations.

In summary:

\[
\phi_C(C)=Normalize([z_{semantic},q_{operational}]).
\]

State and goal vectors are built from the same state-variable vocabulary.

Similarity is cosine similarity:

\[
sim(x,y)=\frac{x^Ty}{||x||||y||}.
\]

Compatibility separately evaluates whether effects satisfy preconditions and
whether outputs can satisfy inputs.

## 6. Capability Composition Model

For

\[
C_1:S_0\rightarrow S_1,\quad C_2:S_1\rightarrow S_2
\]

a composition is valid when the effects of \(C_1\) satisfy the preconditions of
\(C_2\), together with required input-output dependencies.

For the enrollment system:

```text
SelectCourse
    effect: Course.selected = true

MakePayment
    precondition: Course.selected = true
    effect: Payment.status = SUCCESS

EnrollStudent
    precondition: Payment.status = SUCCESS
    effect: Enrollment.status = ENROLLED

SendNotification
    precondition: Enrollment.status = ENROLLED
    effect: Notification.sent = true
```

Therefore the four-step composition is valid.

## 7. Implementation

The implementation is written in Python using NumPy.

Core methods:

```python
encode_state(state)
encode_goal(goal)
encode_capability(capability)
compose(capabilities)
similarity(x, y)
compatibility(c1, c2)
```

The code is deterministic. No pretrained embedding model or external API is
required.

## 8. Experimental Methodology

### Experiment 1 — Capability compatibility

Compare:

```text
MakePayment → EnrollStudent
MakePayment → CancelCourse
```

The first pair is compatible because `MakePayment` produces
`Payment.status = SUCCESS`, which `EnrollStudent` requires.

The second is incompatible because `CancelCourse` requires
`Payment.status = FAILED`.

### Experiment 2 — Capability composition

Construct the four-capability enrollment composition and compare the composite
vector with each atomic capability vector.

### Experiment 3 — Alternative implementations

Compare `EnrollStudent` (DATABASE mechanism) with
`ManualEnrollStudent` (GUI mechanism). They have the same major effect but
different mechanisms and operational profiles.

### Experiment 4 — Irrelevant capabilities

Compare goal-related capabilities with `ViewCourseDetails`,
`CancelCourse`, and `ScholarshipVerification` for the regular enrollment goal.

### Experiment 5 — Operational attributes

Create controlled variants of `MakePayment` by changing execution time,
reliability and availability while preserving functional preconditions/effects.

### Experiment 6 — Consistency

Repeat composition/goal comparison across four formally specified problems in
the same application domain.

## 9. Results

Running

```bash
python src/run_experiments.py
```

produces:

- `experiment1_compatibility.csv`
- `experiment2_composition.csv`
- `experiment3_alternatives.csv`
- `experiment4_goal_relevance.csv`
- `experiment5_operational.csv`
- `experiment6_consistency.csv`
- `efficiency.csv`
- `capability_vectors.json`

The numerical values are generated by the implementation so that results remain
reproducible. In particular, the compatibility experiment is expected to give a
high score for `MakePayment -> EnrollStudent` and a low score for
`MakePayment -> CancelCourse`; the composition experiment should give positive
similarity between each atomic capability and the composite; the alternative
implementation experiment should show substantial functional similarity; and
the operational experiment should show that changing time/reliability/
availability changes the vector without destroying functional identity.

## 10. Analysis

The most important design decision is to keep similarity and compatibility
separate.

Two capabilities can have related effects yet fail to compose because a
required precondition is not satisfied. Conversely, two capabilities may be
compatible without being highly semantically similar.

The explicit effect/precondition block gives the representation direct access
to the functional dependency required for composition.

Alternative implementations demonstrate why mechanism should be represented
but not allowed to dominate functional identity.

Operational attributes are included in a controlled numeric block. This allows
cost, reliability and availability to influence similarity without replacing
the semantic structure.

## 11. Evaluation Against the Required Properties

| Property | Evaluation method |
|---|---|
| Capability representation | Distinct structured feature vectors |
| State relationship | State/goal condition vocabulary |
| Precondition-effect compatibility | Formal compatibility score |
| Input-output compatibility | Output/input type intersection |
| Composition | Weighted composite vector + aggregate operations |
| Goal relevance | Effect-goal match and vector similarity |
| Operational properties | Time/resource/money/risk/energy/reliability/availability block |
| Consistency | Four formal problems |
| Efficiency | Timed encoding and composition experiment |

## 12. Limitations

1. The vocabulary is constructed from the dataset, so unseen symbolic features
   require vocabulary extension.
2. The representation is not learned from a large corpus.
3. The compatibility score is a designed metric, not a learned probability.
4. A fixed-size vector can lose some ordering information in very long
   compositions.
5. Resource overlap is informative but not a complete resource feasibility model.

## 13. Conclusion

The proposed embedding gives a transparent vector representation of formal
capabilities while retaining the information needed for functional composition.
It distinguishes semantic resemblance from executable compatibility and includes
operational properties as explicit dimensions.

The Online Course Enrollment domain demonstrates atomic capabilities,
alternative implementations, irrelevant operations, operational variants and
multi-step compositions. The resulting experiments provide a basis for judging
whether a structured vector representation can preserve the relationships
needed for capability composition.
