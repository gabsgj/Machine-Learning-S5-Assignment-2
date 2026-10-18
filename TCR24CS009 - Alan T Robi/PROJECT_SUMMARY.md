# Project Summary - Vector Embedding for Capability Composition


**Project Name**: Hybrid Structured Capability Embedding System  
**Status**: Fully Implemented, Verified, and Benchmark Tested  

---

## 1. What Was Implemented

A complete, runnable Python system for formal capability vector representation, state/goal encoding, directional compatibility reasoning, sequence composition, and baseline evaluation:

- **Formal Dataset**: 25 capabilities in `data/capabilities.json` matching $C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)$.
- **Data Models**: `Capability`, `InputSpec`, `OutputSpec`, `CostSpec` (`src/capability.py`), `State`, `Goal` (`src/state.py`).
- **Encoder Engine**: `CapabilityEncoder` ($D=167$ structured vector), `CapabilityPCAEncoder` ($d=16$ dense embedding) in `src/encoder.py`.
- **Predicate Canonicalization**: Shared `canonicalize_predicate` (`src/utils.py`) unifying predicate syntax across states, goals, preconditions, and effects (e.g. `Order.exists=true` $\equiv$ `OrderExists=true`).
- **Similarity & Compatibility**: Cosine similarity (`src/similarity.py`), directional compatibility `compatibility(c1, c2)` (`src/compatibility.py`).
- **Composition Engine**: `compose(capabilities)` (`src/composition.py`).
- **Evaluation Framework**: Textual/Flat baselines & metrics (`src/evaluation.py`).
- **Experiment Suite**: 5 comprehensive experiments in `experiments/`.
- **Unit Test Suite**: 8 automated tests in `tests/test_core.py`.
- **Documentation & Report**: `README.md`, `technical_report.md`, `requirements.txt`.

---

## 2. Proposed Embedding Idea

The system uses a **Hybrid Structured Capability Embedding**. The vector is constructed by concatenating multi-hot symbolic feature sub-vectors with Min-Max normalized operational attributes:

$$\mathbf{V}(C_i) = [ \mathbf{V}_{type} \mid \mathbf{V}_{inputs} \mid \mathbf{V}_{outputs} \mid \mathbf{V}_{preconditions} \mid \mathbf{V}_{effects} \mid \mathbf{V}_{constraints} \mid \mathbf{V}_{resources} \mid \mathbf{V}_{mechanism} \mid \mathbf{V}_{operational} ]$$

A key scientific principle of this system is that **Similarity $\neq$ Composability**. Similarity is measured via vector cosine angle, while Composability is evaluated directionally using Effect-Precondition and Output-Input satisfaction metrics with hard contradiction checks.

---

## 3. Key Equations

1. **Formal Capability Model**:
   $$C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)$$
2. **Cosine Similarity**:
   $$\text{Similarity}(\mathbf{x}, \mathbf{y}) = \frac{\mathbf{x} \cdot \mathbf{y}}{\|\mathbf{x}\|_2 \|\mathbf{y}\|_2}$$
3. **Directional Compatibility**:
   $$\text{Compat}(C_1, C_2) = w_1 \cdot \text{Match}_{EP}(E_1, P_2) + w_2 \cdot \text{Match}_{OI}(O_1, I_2)$$
4. **Composite Reliability & Availability**:
   $$Rel_{comp} = \prod_{k=1}^n Rel_k, \quad A_{comp} = \min_{k=1}^n A_k$$

---

## 4. Experiments Performed & Major Measured Findings

1. **Experiment 1 (Compatibility)**:
   - `CreateOrder` $\to$ `MakePayment`: Effect-Precond Match = **1.0**, Output-Input Match = **0.5**, Compatibility Score = **0.8** $\to$ **Compatible**.
   - `CreateOrder` $\to$ `CancelCart`: Effect-Precond Match = **0.0**, Output-Input Match = **0.0**, Compatibility Score = **0.0**, Contradiction = `True` $\to$ **Incompatible**.
   - Pairwise Classification (12-pair evaluation dataset): Proposed F1 = **0.8333** vs Flat Baseline F1 = **0.2500**.
2. **Experiment 2 (Composition)**:
   - Composite `CompletePurchase` constructed for $SendNotification \circ MakePayment \circ CreateOrder$.
   - Similarity $V(C_{comp})$ vs $V(CreateOrder) = \mathbf{0.6052}$, $V(MakePayment) = \mathbf{0.5173}$, $V(SendNotification) = \mathbf{0.4197}$.
   - Linear Vector Addition approximation similarity = **0.7153**.
3. **Experiment 3 (Alternative Implementations)**:
   - `CreateOrder` (API) vs `CreateOrderDatabase` (DB) vs `CreateOrderGUI` (GUI).
   - Functional Sub-space Similarity = **1.0000** (identical effects), Type Sub-space Sim = **0.0000**, Mechanism Sub-space Similarity = **0.0000**, Resource Sub-space Sim = **0.7071** (API vs DB) and **0.5000** (API vs GUI), Full Vector Similarity = **0.7404** (API vs DB) and **0.7176** (API vs GUI).
4. **Experiment 4 (Irrelevant Capabilities)**:
   - Target Goal $G$: `orderexists=true`, `paymentstatus=success`, `notificationsent=true`.
   - Relevant capabilities (`CreateOrder`, `MakePayment`, `SendNotification`): Formal Goal Relevance = **0.3333**, Vector Similarity to Goal Vector = **0.1183 - 0.2310**.
   - Auxiliary capability (`GenerateInvoice`): Formal Goal Relevance = **0.0000**, Vector Similarity to Goal Vector = **0.1235** (shares preconditions with goal state space).
   - Irrelevant capabilities (`AddToCart`, `UpdateProfile`, `CreateWishlist`, `GenerateUserReport`): Formal Goal Relevance = **0.0000**, Vector Similarity to Goal Vector = **0.0000**.
5. **Experiment 5 (Operational Attributes)**:
   - `MakePaymentPremium` (50ms, \$0.025, risk=0.005) vs `MakePaymentDiscount` (300ms, \$0.003, risk=0.10).
   - Functional Sub-space Sim = **1.0000**, Operational Sub-space Sim = **0.7608**, Full Vector Sim = **0.8174**.

### Efficiency & Storage Benchmarks
- Structured Vector Dimension $D$: **167**
- Dense PCA Dimension $d$: **16** (86.31% explained variance ratio: 0.8630760578)
- Encoding Speed: **0.0242 ms** per capability (or **24.2 microseconds / μs**)
- Compatibility Speed: **0.0043 ms** per pair (or **4.3 microseconds / μs**)
- Storage Size: **1,336 bytes** (structured) / **128 bytes** (16D dense float64)

---

## 5. Limitations

1. Vocabulary requires domain feature extraction across dataset capabilities.
2. Predicate parser currently handles equality and numeric inequalities ($=, >, <, \ge, \le$).
3. Unstructured text inputs must first be formatted into formal JSON capability tuples.

---

## 6. Commands to Reproduce Everything

```bash
# Install dependencies
pip install -r requirements.txt

# Run automated unit tests
python -m unittest discover -s tests -v

# Run master experiment runner
python experiments/run_experiments.py
```
