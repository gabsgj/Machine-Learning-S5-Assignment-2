# Deliverable 2: System Implementation and API Guide

## 1. System Architecture Overview

The `capability-embedding` package provides a modular, production-ready Python framework for encoding, composing, and evaluating formal capabilities and applications in vector space.

```
capability_embedding/
├── core/                  # Formal domain models (State, Goal, Capability, Operations)
├── embedding/             # Coordinate registries, layout descriptors, algebraic vector operators
├── metrics/               # Decoupled similarity, composability, and goal relevance metrics
├── evaluation/            # Multi-objective Pareto frontier and latency/memory profiling
└── visualization/         # Publication-grade plotting utilities
```

---

## 2. Core API Reference

The primary API functions mandated by Section 9 (Deliverable 2) are exposed directly at the top level of `capability_embedding`:

### 2.1 `encode(entity)`
Polymorphic unified encoder supporting states, goals, atomic capabilities, and capability sequences.

```python
import capability_embedding as ce
from datasets.ecommerce import get_ecommerce_initial_state, get_ecommerce_goal, get_ecommerce_capabilities

# 1. Encode Application State
state = get_ecommerce_initial_state()
z_state = ce.encode(state)
print(f"State Vector Dimension: {len(z_state.raw)}, Type: {z_state.entity_type}")

# 2. Encode Goal Specification
goal = get_ecommerce_goal()
z_goal = ce.encode(goal)

# 3. Encode Capability
caps = get_ecommerce_capabilities()
c1 = caps["CreateOrder_API"]
z_c1 = ce.encode(c1)
print(f"Capability Latency: {z_c1.execution_time} ms, Reliability: {z_c1.reliability:.4f}")
```

### 2.2 `compose(capabilities, name=None)`
Constructs a composite representation either symbolically or algebraically in vector space.

```python
c1 = caps["CreateOrder_API"]
c2 = caps["MakePayment"]
c3 = caps["SendNotification"]

# Symbolic composition
c_comp = ce.compose([c1, c2, c3], name="CompletePurchasePipeline")
print(f"Composite Preconditions (Internal absorbed): {c_comp.preconditions}")
print(f"Composite Effects: {c_comp.effects}")
print(f"Cumulative Latency: {c_comp.quality.execution_time_ms} ms")

# Vector space direct composition
z1 = ce.encode(c1)
z2 = ce.encode(c2)
z3 = ce.encode(c3)
z_comp = ce.compose([z1, z2, z3])
print(f"Decoded Vector Latency: {z_comp.execution_time} ms, Reliability: {z_comp.reliability:.4f}")
```

### 2.3 `similarity(x, y, weights=None)`
Evaluates the similarity between two entities across functional, implementation, and operational dimensions.

```python
c_api = caps["CreateOrder_API"]
c_db = caps["CreateOrder_DB"]

z_api = ce.encode(c_api)
z_db = ce.encode(c_db)

# Full multi-faceted similarity
sim_score = ce.similarity(z_api, z_db)

# Isolated functional similarity (state effect transition)
func_sim = ce.functional_similarity(z_api, z_db)
print(f"Functional Equivalence: {func_sim:.4f}") # 1.0000

# Isolated mechanism similarity (API vs DB)
impl_sim = ce.mechanism_similarity(z_api, z_db)
print(f"Implementation Similarity: {impl_sim:.4f}") # Distinguishable (< 1.0)
```

### 2.4 `composability(c1, c2)`
Evaluates whether capability $c_1$ enables capability $c_2$ ($c_1 \to c_2$).

```python
c1 = caps["CreateOrder_API"] # Produces Order.exists = True
c2 = caps["MakePayment"]     # Requires Order.exists = True
c3 = caps["CancelCart"]      # Requires Order.exists = False

z1, z2, z3 = ce.encode(c1), ce.encode(c2), ce.encode(c3)

print("Composability C1 -> C2:", ce.composability(z1, z2)) # 0.7000 (Positive / Compatible)
print("Composability C1 -> C3:", ce.composability(z1, z3)) # -1.0000 (Negative / Conflict)
```

### 2.5 `goal_relevance(c, goal, initial_state=None)`
Measures the directional alignment of a capability's effects with the goal delta.

```python
z_goal = ce.encode(goal)
z_s0 = ce.encode(state)

print("C1 Goal Relevance:", ce.goal_relevance(z1, z_goal, z_s0)) # +0.4082 (Useful)
print("Tax Report Relevance:", ce.goal_relevance(ce.encode(caps["GenerateTaxAuditReport"]), z_goal, z_s0)) # 0.0000 (Irrelevant)
print("Reset Relevance:", ce.goal_relevance(ce.encode(caps["ResetOrderState"]), z_goal, z_s0)) # -1.0000 (Detrimental)
```

---

## 3. Subspace Layout and Coordinate Memory Alignment

The embedding space $\mathbb{R}^D$ is partitioned contiguously to guarantee zero-copy NumPy slicing:

```
[ 0 : Ds ]                 Precondition Values (p_i)
[ Ds : 2*Ds ]              Precondition Masks (m_P)
[ 2*Ds : 3*Ds ]            Effect Target Values (e_i)
[ 3*Ds : 4*Ds ]            Effect Modification Masks (m_E)
[ 4*Ds : 4*Ds + D_io ]     Input Token Hashes (z_in)
[ 4*Ds + D_io : 4*Ds + 2*D_io ] Output Token Hashes (z_out)
[ 4*Ds + 2*D_io : ... ]    Operational Quality Coordinates
                           (Latency, Cost, -ln(Rel), -ln(Avail), Risk, Resources)
[ ... : Total_D ]          Implementation Type One-Hot & Mechanism Signature
```

---

## 4. Computational Efficiency and Complexity

| Operation | Time Complexity | Space Complexity | Typical Execution Latency |
| :--- | :--- | :--- | :--- |
| `encode(State)` | $\mathcal{O}(|\text{vars}|)$ | $\mathcal{O}(D)$ | $28.4 \; \mu\text{s}$ |
| `encode(Goal)` | $\mathcal{O}(|\text{conditions}|)$ | $\mathcal{O}(D)$ | $31.2 \; \mu\text{s}$ |
| `encode(Capability)` | $\mathcal{O}(|\text{vars}| + |I| + |O|)$ | $\mathcal{O}(D)$ | $106.2 \; \mu\text{s}$ |
| `compose_embeddings` | $\mathcal{O}(D)$ | $\mathcal{O}(D)$ | $74.2 \; \mu\text{s}$ |
| `composability` | $\mathcal{O}(D_s + D_{\text{io}})$ | $\mathcal{O}(1)$ | $12.8 \; \mu\text{s}$ |
| `similarity` | $\mathcal{O}(D_s + D_{\text{impl}})$ | $\mathcal{O}(1)$ | $9.5 \; \mu\text{s}$ |
