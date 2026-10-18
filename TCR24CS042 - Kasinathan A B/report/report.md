# Report: Design of a Vector Embedding for Capability Composition

---

## 1. Problem Definition

Modern software systems are increasingly composed of heterogeneous, independently deployable capabilities — REST APIs, database procedures, GUI flows, event handlers, and external services. Orchestrating these capabilities to achieve a high-level goal requires reasoning about two fundamental properties:

1. **Compatibility** — can capability *i* be immediately followed by capability *j*? This is a sequencing question: does executing *i* produce a world state in which *j* is permitted to run?
2. **Composability** — what is the collective behaviour of a chain *C₁→C₂→…→Cₙ*? Can this chain be treated as a single, abstract capability for higher-level planning?

The challenge addressed in this assignment is to design a **vector embedding** for formally specified states, goals, and capabilities such that:
- The embedding *preserves* compatibility — compatible sequential pairs produce high inner-product alignment between the effect vector of the predecessor and the precondition vector of the successor.
- The embedding *supports* composition — a composite capability can be derived algebraically from its constituents without running them.
- The embedding distinguishes **structural similarity** (do two capabilities look the same?) from **sequential compatibility** (can one enable the other?).

The embedding must be *custom-built* from domain knowledge; no off-the-shelf language model or neural network is used as the solution.

---

## 2. Design Requirements

| Requirement | Rationale |
|-------------|-----------|
| **Fixed-length vector** | Enables cosine similarity, dot products, and arithmetic composition without variable-length padding |
| **Deterministic encoding** | Same capability JSON always produces the same vector — essential for reproducibility |
| **Signed precondition/effect encoding** | +1/−1/0 allows the dot-product compatibility formula to detect both satisfaction *and* contradiction |
| **Separated availability and mechanism** | These are operational/implementation artefacts, not semantic descriptors; including them would pollute similarity scores |
| **Global cost normalisation** | Raw milliseconds and USD are not comparable; min-max normalisation across all domains makes cost a fair feature |
| **Reliability as a scalar** | Already in [0, 1] per the spec; multiplicative composition naturally degrades reliability along a chain |
| **Distinct similarity() and compatibility()** | The two functions must be able to disagree — two capabilities can be structurally similar yet sequentially incompatible |

---

## 3. Related Embedding Approaches

### 3.1 Word2Vec and Distributional Embeddings

Word2Vec (Mikolov et al., 2013) learns dense continuous embeddings by predicting surrounding context in a large corpus. Its key strength is capturing *semantic similarity* in a low-dimensional space where arithmetic relations emerge (king − man + woman ≈ queen). However:

- **Limitation for capabilities**: Word2Vec requires a large training corpus. Capability specifications are small, structured, and lack the distributional signal needed for unsupervised embedding.
- **Limitation for composition**: Vector addition is not a principled composition operator for state-transition semantics. Adding two capability vectors does not correctly propagate preconditions or model last-writer-wins effects.
- **Relevance**: Inspires the idea that embedding geometry should preserve semantic relationships, which this work achieves by aligning precondition/effect segments of the vector with the compatibility metric.

### 3.2 Knowledge-Graph Embeddings (TransE, RotatE)

Knowledge-graph embedding methods (Bordes et al., 2013; Sun et al., 2019) place entities and relations in a vector space such that `head + relation ≈ tail`. TransE and RotatE have been applied to represent workflow graphs and service compositions.

- **Strength**: Naturally models relational structure (e.g. *enables*, *conflicts-with*) and supports link prediction.
- **Limitation for capabilities**: These methods require a pre-built, fully enumerated relation graph. They cannot encode *new* capabilities zero-shot from their JSON specifications alone without retraining.
- **Limitation**: The relation between preconditions and effects is not a single fixed relation but a complex boolean function; simple translation or rotation operators cannot represent it faithfully.
- **Relevance**: Motivates the explicit representation of typed relations in the vector (effect → precondition compatibility uses a similar relational dot product).

### 3.3 Structured / Feature-Vector Encodings

Structured encodings (as used in classical AI planning — STRIPS, PDDL) represent states and actions as explicit sets of propositions. Feature-vector representations of PDDL actions for machine learning (Sievers et al., 2019) extract handcrafted features from action schemas.

- **Strength**: Fully interpretable, provably correct with respect to the planning semantics, zero-shot for new domains.
- **Limitation**: Traditional feature vectors do not capture *non-propositional* attributes (cost, reliability, resource usage) in a single unified vector.
- **Relevance**: This work directly extends the structured encoding approach by embedding the propositional state-transition semantics (preconditions and effects as ±1 vectors) and augmenting with operational features (type, IO, resources, cost, reliability) in a single concatenated representation.

### 3.4 Summary

| Method | Zero-shot | Composition | Interpretability | Compatibility Preservation |
|--------|-----------|-------------|-----------------|--------------------------|
| Word2Vec | No (needs corpus) | Approximate (addition) | Low | Indirect |
| KG Embeddings | No (needs graph) | No | Medium | Via link prediction |
| Structured (STRIPS) | Yes | Logical union | High | Exact (set semantics) |
| **This work** | **Yes** | **Algebraic** | **High** | **Exact (dot product)** |

---

## 4. Proposed Representation

Each capability is encoded as a **59-dimensional float vector** structured as a concatenation of semantically distinct segments:

```
v(cap) = [type_onehot | io_features | io_name_match | resource_multihot |
           cost_normalized | reliability | precondition_vector | effect_vector]
```

States and goals are encoded as **12-dimensional vectors** (the state-variable vocabulary of the domain), with +1 for True, −1 for False, 0 for absent.

The key design decision is to **separate** the state-transition semantics (precondition and effect segments, 24 of 59 dimensions) from the operational characteristics (type, IO, resources, cost, reliability, 35 of 59 dimensions). This allows:

- `compatibility()` to operate purely on the state-transition segment (ignoring operational details).
- `similarity()` to operate on the full vector (operational characteristics matter for structural closeness).
- The two functions to *disagree* as required — identical operational profiles but conflicting state transitions produce high similarity but negative compatibility.

---

## 5. Mathematical Formulation

### State and Goal Encoding

Let **V** = {v₁, v₂, …, v₁₂} be the ordered state-variable vocabulary of a domain.

For a state *s* or goal *g* (partial or complete assignment of boolean values):

$$\text{encode}(s)[i] = \begin{cases} +1 & \text{if } s(v_i) = \text{True} \\ -1 & \text{if } s(v_i) = \text{False} \\ 0 & \text{if } v_i \notin \text{dom}(s) \end{cases}$$

### Capability Encoding

For a capability *c* with type τ, inputs I, outputs O, resources R, cost *k*, reliability *ρ*, preconditions *P*, effects *E*:

$$\mathbf{v}(c) = [\underbrace{\mathbf{e}_\tau}_{\text{12-dim}} \;\|\; \underbrace{\phi_{\text{IO}}(I,O)}_{\text{4-dim}} \;\|\; \underbrace{\mu(I,O)}_{\text{1-dim}} \;\|\; \underbrace{\mathbf{r}(R)}_{\text{12-dim}} \;\|\; \underbrace{\hat{k}}_{\text{5-dim}} \;\|\; \underbrace{\rho}_{\text{1-dim}} \;\|\; \underbrace{\text{encode}(P)}_{\text{12-dim}} \;\|\; \underbrace{\text{encode}(E)}_{\text{12-dim}}]$$

Where:
- **e**_τ ∈ {0,1}¹² is a one-hot over 9 capability types (padded to 12)
- φ_IO(I, O) = [|I|/10, |O|/10, |I_req|/10, |I_opt|/10] (normalised IO counts)
- μ(I, O) = |names(I) ∩ names(O)| / |names(I)| (IO name overlap fraction)
- **r**(R) ∈ {0,1}¹² is a multi-hot over the 12-element global resource vocabulary
- k̂ = [(k_field − min_field) / (max_field − min_field)] for each of {time_ms, money, resource, risk, energy}
- ρ ∈ [0, 1] is the capability's declared reliability

### Similarity

$$\text{similarity}(x, y) = \frac{\mathbf{x} \cdot \mathbf{y}}{\|\mathbf{x}\| \|\mathbf{y}\|}$$

Cosine similarity over the full 59-dim vector. Measures representational closeness.

### Compatibility

$$\text{compatibility}(i, j) = \begin{cases} \dfrac{\text{encode}(E_i) \cdot \text{encode}(P_j)}{\sum_{d}|\text{encode}(P_j)[d]|} & \text{if } \sum_d|\text{encode}(P_j)[d]| > 0 \\ 0 & \text{otherwise} \end{cases}$$

Measures the fraction of *j*'s preconditions that are satisfied (rather than violated) by *i*'s effects.

- **+1.0**: every precondition of *j* is exactly satisfied by *i*'s effects
- **0.0**: *i*'s effects are orthogonal to *j*'s preconditions (or *j* has none)
- **−1.0**: *i*'s effects actively contradict every precondition of *j*

---

## 6. Capability Composition Model

Given an ordered chain *C₁→C₂→…→Cₙ* with encoded vectors **v**₁, …, **vₙ** and corresponding dicts d₁, …, dₙ, the composite capability vector **v**_∗ is constructed as:

### Type
Use the type one-hot of *C₁* (the chain's "entry point"):
$$\mathbf{v}_*[\text{type}] = \mathbf{v}_1[\text{type}]$$

### IO Features
Total inputs = sum of all capabilities' inputs; outputs = *Cₙ*'s outputs; required = *C₁*'s required inputs only (later required inputs are presumed satisfied internally).

### Resources
Element-wise maximum (logical union):
$$\mathbf{v}_*[\text{resource}] = \max_{i=1}^n \mathbf{v}_i[\text{resource}]$$

### Cost
Element-wise sum, clipped to [0, 1]:
$$\mathbf{v}_*[\text{cost}] = \min\!\left(\sum_{i=1}^n \mathbf{v}_i[\text{cost}],\; \mathbf{1}\right)$$

### Reliability
Product (independent failure assumption):
$$\rho_* = \prod_{i=1}^n \rho_i$$

### Precondition
Start from *C₁*'s precondition. Maintain a running accumulated effect **a** (initially **e**₁). For each subsequent *Cᵢ*:
- For each dimension *d* where *Cᵢ* has a precondition requirement that the accumulated effect does not yet satisfy: add that requirement to the composite precondition (if not already set).
- Update **a**: later effects overwrite earlier ones for non-zero dimensions.

$$P_*[d] = P_1[d] \text{ (base)} + \bigcup_{i \geq 2} \{P_i[d] : E_{<i}[d] \neq P_i[d] \text{ and } P_*[d] = 0\}$$

### Effect
Last-writer-wins (later capabilities overwrite earlier ones on conflict):
$$E_*[d] = E_n[d] \text{ if } E_n[d] \neq 0, \text{ else } E_{n-1}[d], \ldots$$

This correctly reflects that the final world state after the chain depends on the last capability that touched each variable.

---

## 7. Implementation

The implementation is entirely in Python 3 using only `numpy` and the standard library (`json`, `os`, `glob`).

**`src/encode.py`** is the core module containing all required functions. Constants `IDX_TYPE`, `IDX_IO`, `IDX_IOMATCH`, `IDX_RESOURCE`, `IDX_COST`, `IDX_RELY`, `IDX_PRECOND`, `IDX_EFFECT` define the exact slice boundaries, making the vector layout self-documenting and easy to modify.

**`src/compose.py`** provides higher-level utilities (`chain_capabilities`, `describe_vector`, `show_composition`) that simplify experiment scripts.

**`src/compatibility.py`** provides matrix-level utilities (`pairwise_compatibility_matrix`, `print_compatibility_table`, `rank_by_compatibility`) used across experiments.

The three domain JSON files under `data/` define 19 capabilities total (6 + 6 + 7) across three independently structured domains, each with its own state-variable vocabulary, initial state, and goal.

---

## 8. Experimental Methodology

Each experiment is a self-contained Python script (`experiments/exp*.py`) that:
1. Loads domain JSON files.
2. Calls `collect_cost_stats()` across all domains to fit normalisation.
3. Encodes capabilities using `encode_capability()`.
4. Applies the function under test.
5. Prints a formatted results table to stdout.

No GUI, no plotting, no interactive prompts. All random variation is avoided — the encoding is fully deterministic.

The three domains chosen cover distinct application contexts (e-commerce, library management, hotel hospitality) to avoid domain-specific bias in the resource vocabulary or capability type distribution.

---

## 9. Results

### Experiment 1 — Compatibility

| Pair | Compatibility | Similarity |
|------|--------------|-----------|
| CreateOrder → MakePayment | **+1.0000** | 0.2713 |
| CreateOrder → CancelCart | **−1.0000** | 0.5395 |
| MakePayment → ShipOrder | +1.0000 | 0.4157 |
| ShipOrder → SendNotification | 0.0000 | 0.1716 |

The hypothesis is confirmed: CreateOrder→MakePayment scores +1.0 (perfect satisfaction of all preconditions), while CreateOrder→CancelCart scores −1.0 (perfect contradiction). Crucially, the similarity scores do NOT mirror the compatibility scores — CreateOrder and CancelCart have *higher* similarity (0.54) than CreateOrder and MakePayment (0.27), because CancelCart and CreateOrder share the same API type, similar resources, and both touch `cart_active`.

### Experiment 2 — Composition

| | Similarity to Composite |
|-|------------------------|
| CreateOrder | 0.5958 |
| MakePayment | 0.6773 |
| ShipOrder | 0.5927 |

All similarities are in (0, 1) as required. Composite reliability = 0.9800 × 0.9500 × 0.9200 = **0.8565**, demonstrating correct multiplicative degradation.

### Experiment 3 — Alternative Implementations

| Pair | Similarity |
|------|-----------|
| API ↔ DATABASE | 0.8130 |
| API ↔ GUI | 0.8988 |
| DATABASE ↔ GUI | 0.7784 |

All pairs score HIGH (>0.77) but none reaches 1.0. The compatibility of all three with ShipOrder is **identically 1.0000** (effect vectors are the same), confirming that similarity and compatibility can disagree.

### Experiment 4 — Relevance Ranking (Hotel Domain)

| Rank | Capability | Effect-Goal Similarity |
|------|-----------|----------------------|
| 1 | CapturePayment | 0.5774 |
| 2 | CheckIn | 0.5774 |
| 3 | CheckOut | 0.4082 |
| 4–7 | SearchRooms, MakeReservation, OrderRoomService, CancelReservation | 0.0000 |

The goal-relevant capabilities rank at the top; unrelated capabilities score exactly 0.0 (orthogonal effects).

### Experiment 5 — Operational Scoring

With PayFine as predecessor:

| Variant | Compat | Reliability | Cost | Score (product) | Score (weighted) |
|---------|--------|------------|------|----------------|-----------------|
| HighRel_LowCost | 0.3333 | 0.99 | 0.056 | **0.3117** | **0.5182** |
| MedRel_MedCost | 0.3333 | 0.85 | 0.547 | 0.1283 | 0.3639 |
| LowRel_HighCost | 0.3333 | 0.70 | 0.880 | 0.0280 | 0.2373 |

Rankings agree for the PayFine predecessor. For the SearchCatalog predecessor (compatibility = 0 for all), the multiplicative formula collapses all scores to 0 while the weighted formula preserves discrimination — demonstrating a real difference between the two operational scoring formulations.

---

## 10. Analysis

### Correctness of Compatibility

The formula `dot(effect_i, precond_j) / |precond_j|₁` is equivalent to a *signed coverage ratio*: what fraction of *j*'s required conditions are produced (or violated) by *i*'s effects? This is geometrically equivalent to a cosine similarity restricted to the non-zero dimensions of *precond_j*, which is exactly what STRIPS planning compatibility requires.

### Distinctness of Similarity and Compatibility

Experiment 1 demonstrates concretely that CreateOrder and CancelCart are *more similar* (0.54) than CreateOrder and MakePayment (0.27), yet compatibility is −1.0 vs +1.0 respectively. This is because similarity considers the full 59-dim vector (both are API-type capabilities with similar IO and resource footprints) while compatibility looks only at the 12-dim effect/precondition overlap.

This separation is a deliberate design feature: a planner using compatibility to chain capabilities will not be confused by superficial structural similarity.

### Composition Invariants

The composed chain CreateOrder→MakePayment→ShipOrder correctly:
1. Inherits only CreateOrder's external preconditions (cart_active=T, cart_empty=F).
2. Accumulates effects: cart_active set to F, order_created=T, payment_pending later set to F, payment_complete=T, inventory_reserved=T, order_shipped=T.
3. Degrades reliability: 0.98 × 0.95 × 0.92 = 0.8565.
4. Each individual similarity with the composite is strictly less than 1.0.

### Goal Relevance

The goal-directed ranking correctly identifies that SearchRooms and CancelReservation are orthogonal or contradictory to the check-in/payment goal. CapturePayment and CheckIn rank highest because each exactly satisfies one of the three goal variables. CheckOut is partially relevant because it sets loyalty_points_credited=True (one of the three goal variables).

### Operational Scoring

The sensitivity table in Experiment 5 shows that lowering reliability from 0.99 to 0.70 costs approximately 0.12 in weighted operational score, while increasing cost from 0.05 to 0.80 costs approximately 0.15. The two trade-offs are therefore *roughly balanced* under the weighted formula, explaining why rankings can diverge when reliability and cost move in opposite directions.

---

## 11. Limitations

1. **Fixed 12-slot vocabulary.** The embedding is designed for domains with at most 12 boolean state variables. Larger domains require changing `NUM_STATE_VARS` and redefining all index constants. There is no automatic dimension discovery.

2. **Cross-domain incompatibility.** Precondition and effect segments occupy the same index positions (35–47 and 47–59) regardless of domain. Composing capabilities from different domains produces meaningless state-transition vectors unless a shared variable mapping is defined.

3. **Boolean-only state model.** Continuous or enumerated state variables (e.g., `queue_length`, `room_type`) cannot be encoded without extending the scheme to multi-value slots. The current ±1 encoding would misrepresent gradual state changes.

4. **Availability and temporal constraints excluded.** Time-windowed availability (`{"start": "09:00", "end": "21:00"}`) is stored outside the vector. Sequences that are compatible by state logic but temporally impossible (e.g., a service only available at night following one only available by day) are not detected.

5. **Cost normalisation is dataset-global.** `collect_cost_stats()` must be called over all known capabilities before any encoding. Streaming new capabilities incrementally can invalidate normalisation, requiring a full re-scan. Dynamic capabilities (e.g., costs updated at runtime) are not supported.

---

## 12. Conclusion

This work presents a custom, 59-dimensional vector embedding for formally specified software capabilities that simultaneously encodes:
- **State-transition semantics** (precondition and effect segments with ±1 encoding) — enabling an exact compatibility measure via the signed coverage dot product.
- **Operational characteristics** (type, IO counts, resources, cost, reliability) — enabling a meaningful similarity measure that captures structural resemblance independent of sequential fitness.

The embedding is *zero-shot* (no training data required), *deterministic* (same JSON always produces the same vector), and *algebraically composable* (chains can be merged into a single representative vector with correctness guarantees on precondition accumulation, last-writer-wins effects, summed costs, and multiplied reliability).

Five experiments confirm all major design claims:
- Compatibility correctly identifies and quantifies sequential fitness.
- Similarity correctly identifies structural resemblance and discriminates from compatibility.
- Composition correctly aggregates multi-step chains.
- Goal-directed relevance ranking correctly prioritises capabilities whose effects align with the goal.
- Operational scoring correctly integrates compatibility, reliability, and cost into a composite quality metric.

The primary limitation is the fixed vocabulary assumption (boolean variables, ≤12 per domain). Extending to continuous or categorical variables, and to cross-domain compositions, are natural directions for future work. A promising extension would be to use this structured encoding as a *feature input* to a learned model (e.g., a graph neural network over the capability-compatibility graph), exploiting the interpretable structure of the hand-designed embedding as an inductive bias.
