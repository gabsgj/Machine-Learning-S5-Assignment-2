# SCE-128 Project Architecture

## 1. Formal layer

The application is represented as:

```text
A = (S, C, SI, G, R, K)
```

where `S` is the state space, `C` the capability set, `SI` the initial state, `G` the goal specification, `R` available resources, and `K` global constraints.

A capability is represented as:

```text
C = (T, I, O, P, E, K, R, Q, Reliability, Availability, M)
```

## 2. Embedding layer

The structured encoder creates a normalized 128-D vector with dedicated blocks for:

```text
function / type / input / output / precondition / effect /
constraint / resource / mechanism / operational
```

State and goal predicates share the underlying predicate representation so that state awareness and goal alignment can be evaluated.

## 3. Compatibility layer

Compatibility is directional:

```text
source effects       → target preconditions
source outputs       → target inputs
```

Exact symbolic matching is the authoritative compatibility mechanism. Vector similarity is reported as supporting evidence rather than as a replacement for formal logic.

## 4. Goal relevance layer

The final relevance score combines:

```text
semantic effect → goal alignment
+
exact goal-effect coverage
+
backward reachability through the formal capability graph
```

This is deliberately described as a hybrid embedding + symbolic score.

## 5. Composition layer

The learned composer receives:

```text
source vector
+
target vector
+
vector-derived directional relation features
```

It never receives a formal composite during prediction.

The independently encoded formal composite is used only as the target for evaluation.

## 6. Experiment architecture

```text
Phase 01  Dataset validation
    ↓
Phase 02  Compatibility
    ↓
Phase 03  Baseline composition
    ↓
Phase 04  Alternative implementations
    ↓
Phase 05  Goal relevance
    ↓
Phase 06  Operational attributes
    ↓
Phase 07  Leakage-free learned composition
    ↓
Phase 08  Final integrated evaluation
```

## 7. Why the architecture is intentionally hybrid

A pure cosine-similarity system cannot reliably express the directional logic of capability composition. The final design therefore combines a structured vector representation with explicit symbolic relations. This directly matches the assignment's distinction between similarity and composability.
