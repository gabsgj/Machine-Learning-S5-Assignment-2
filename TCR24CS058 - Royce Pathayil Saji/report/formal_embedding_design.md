# Formal Embedding Design: Partitioned Structured Dense Vector (PSD-160)

**Course:** PCCST503: Advanced Software Engineering and Systems Design  
**Assignment:** Assignment 2: Design of a Vector Embedding for Capability Composition  
**Student Name:** Royce P Saji  
**Registration ID:** TCR24CS058  
**Roll No:** 57  
**GitHub Repository:** [https://github.com/Royce1415/capability_embedding](https://github.com/Royce1415/capability_embedding)  

---

## 1. Application Model

Following the formal specification of the assignment, an enterprise software environment is defined as a tuple:

$$\mathcal{A} = (S, C, S_I, G, R, K)$$

where:
- **$S$ (State Space):** The set of all possible world configurations. A specific state $s \in S$ is a mapping of domain state variables to concrete valuations, representing the condition of the application at a specific point in execution.
- **$C$ (Capability Space):** The set of all atomic executable operations, services, APIs, and functions available within the software environment: $C = \{C_1, C_2, \dots, C_n\}$.
- **$S_I$ (Initial State):** The known concrete state of the environment prior to the invocation of any capability sequence ($S_I \in S$).
- **$G$ (Goal Specification):** A set of target conditions and predicate constraints that must hold true upon task completion ($G \subseteq S$).
- **$R$ (System Resources):** Shared or exclusive computational, system, and hardware entities required during capability execution (for example: databases, payment gateways, network bandwidth, and hardware tokens).
- **$K$ (System Constraints):** Invariant operational rules, business logic boundaries, or execution limits that must not be violated throughout any state transition.

---

## 2. Capability Model

Each capability $C_i \in C$ represents a discrete executable unit modeled as an 11-tuple:

$$C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, \text{Rel}_i, A_i, M_i)$$

Each component is formally defined as follows:

1. **$T_i$ (Capability Type):** The architectural execution paradigm of the capability. Valid types defined in the system include `API`, `DATABASE`, `GUI`, `EVENT`, `FUNCTION`, `FILE`, `COMPUTATION`, `MESSAGE`, `SERVICE`, and `COMPOSITE`.
2. **$I_i$ (Input Parameters):** A typed list of input data requirements: $I_i = \{(name, type, required)\}$.
3. **$O_i$ (Output Parameters):** A typed list of output data structures produced upon successful execution: $O_i = \{(name, type)\}$.
4. **$P_i$ (Preconditions):** Logical propositions over application state variables that must evaluate to true immediately before invocation: $P_i = \{(var, op, val)\}$.
5. **$E_i$ (Effects):** Discrete state transformations produced upon completion. Effects define transitions on state variables: $E_i = \{(var, op, val)\}$.
6. **$K_i$ (Capability Constraints):** Local operational boundaries and guard conditions governing execution (for example: transaction amount limits or minimum inventory thresholds).
7. **$R_i$ (Resource Requirements):** Computational or external resources required during execution, annotated as shared or exclusive access.
8. **$Q_i$ (Operational Quality / Cost Vector):** Quantitative operational consumption metrics: $Q_i = (t_i, m_i, r_i, \text{risk}_i, e_i)$, representing execution latency in milliseconds, direct monetary cost in dollars, computing resource cost units, failure risk probability in $[0, 1]$, and energy consumption units.
9. **$\text{Rel}_i$ (Reliability):** The probability that the capability completes without internal runtime failure when all preconditions are met: $\text{Rel}_i \in [0.0, 1.0]$.
10. **$A_i$ (Availability):** The probability or operational readiness of the capability being reachable at invocation time: $A_i \in [0.0, 1.0]$.
11. **$M_i$ (Execution Mechanism):** Concrete protocol, endpoint, or dispatch metadata (for example: HTTP method, URL endpoint, SQL query pattern, or event topic).

---

## 3. Vector Representation Architecture: PSD-160

To represent capabilities in a continuous metric space while preserving functional, data-flow, and operational semantics, we define the **Partitioned Structured Dense 160-dimensional vector space** ($\mathbb{R}^{160}$).

Rather than projecting heterogeneous capability attributes into an unconstrained latent space where logical polarities and data types become entangled, PSD-160 allocates fixed, dedicated sub-vectors (slices) to each formal component of the capability tuple.

The overall vector $v(C) \in \mathbb{R}^{160}$ has a fixed length of 160 dimensions, laid out as follows:

| Block Index | Slice Range | Sub-Vector | Dimension | Mathematical Purpose |
|:---:|:---:|:---|:---:|:---|
| 0 | `[0:16]` | Mechanism & Type ($M, T$) | 16 | Encodes execution paradigm and protocol signature |
| 1 | `[16:40]` | Inputs ($I$) | 24 | Encodes required and optional input data fields |
| 2 | `[40:64]` | Outputs ($O$) | 24 | Encodes generated output data structures |
| 3 | `[64:96]` | Preconditions ($P$) | 32 | Encodes logical conditions required prior to execution |
| 4 | `[96:128]` | Effects ($E$) | 32 | Encodes state transformations produced by execution |
| 5 | `[128:140]` | Constraints ($K$) | 12 | Encodes local execution boundaries and guard expressions |
| 6 | `[140:152]` | Resources ($R$) | 12 | Encodes shared and exclusive system resource dependencies |
| 7 | `[152:160]` | Operational ($Q, \text{Rel}, A$) | 8 | Encodes normalized operational costs, reliability, and availability |

Total dimension: $16 + 24 + 24 + 32 + 32 + 12 + 12 + 8 = 160$.

---

## 4. Shared Condition Space ($\mathbb{R}^{32}$)

A critical design requirement is that environmental states $S$, goal conditions $G$, capability preconditions $P$, and capability effects $E$ must reside in the exact same geometric subspace to permit direct algebraic comparisons. 

We define a canonical 32-dimensional condition space $\mathbb{R}^{32}$ that deterministically maps logical propositions without random hashing.

### 4.1 Boolean State Predicates (Dimensions 0 to 7)

Boolean variables are mapped using signed polarity:
- Value is `True`: coordinate is set to $+1.0$
- Value is `False`: coordinate is set to $-1.0$
- Variable is unmentioned / neutral: coordinate is set to $0.0$

The canonical variable mappings are:
- Index 0: `User.authenticated`
- Index 1: `Cart.exists`
- Index 2: `Cart.locked`
- Index 3: `Order.exists`
- Index 4: `Inventory.available`
- Index 5: `Inventory.reserved`
- Index 6: `Notification.sent`
- Index 7: `Order.archived`

Signed polarity provides an important geometric property: if capability $C_1$ produces `Order.exists = True` ($+1.0$) and capability $C_2$ requires `Order.exists = False` ($-1.0$), the inner product is:

$$(+1.0) \times (-1.0) = -1.0$$

This negative inner product immediately flags a logical contradiction in vector space.

### 4.2 Categorical State Predicates (Dimensions 8 to 18)

Discrete categorical variables are encoded via disjoint one-hot coordinate groups:
- **`Payment.status` (Indices 8 to 11):**
  - Index 8: `NOT_STARTED`
  - Index 9: `PENDING`
  - Index 10: `SUCCESS`
  - Index 11: `REFUNDED`
- **`Order.status` (Indices 12 to 14):**
  - Index 12: `NONE`
  - Index 13: `CREATED`
  - Index 14: `COMPLETED`
- **`User.role` (Indices 15 to 16):**
  - Index 15: `CUSTOMER`
  - Index 16: `ADMIN`
- **`Cart.status` (Indices 17 to 18):**
  - Index 17: `ACTIVE`
  - Index 18: `CANCELLED`

### 4.3 Numerical State Predicates (Dimensions 19 to 22)

Numerical variables are assigned pairs of coordinates encoding normalized magnitude and relational operator direction:
- **`Cart.item_count`:**
  - Index 19: Normalized magnitude $\min(1.0, \max(0.0, \text{value} / 10.0))$
  - Index 20: Operator direction ($+1.0$ for $>$ or $\ge$, $-1.0$ for $<$ or $\le$, $0.0$ for $=$)
- **`quantity`:**
  - Index 21: Normalized magnitude $\min(1.0, \max(0.0, \text{value} / 10.0))$
  - Index 22: Operator direction ($+1.0$ for $>$ or $\ge$, $-1.0$ for $<$ or $\le$, $0.0$ for $=$)

Indices 23 to 31 are reserved for domain extensions.

---

## 5. Data-Flow Representation ($\mathbb{R}^{24}$)

Inputs ($I$) and Outputs ($O$) share a 24-dimensional typed data space:
- Canonical schema fields occupy indices 0 to 10:
  - 0: `cart_id`
  - 1: `order_id`
  - 2: `payment_id`
  - 3: `payment_method`
  - 4: `cancelled_cart_id`
  - 5: `notification_id`
  - 6: `inventory_txn_id`
  - 7: `archive_id`
  - 8: `refund_id`
  - 9: `reservation_id`
  - 10: `sku`
- Indices 11 to 23 are reserved for dynamic or custom parameters.

### Activation Values:
- **Input vector $v(I)$:** Coordinate is $1.0$ if the parameter is required, and $0.5$ if the parameter is optional.
- **Output vector $v(O)$:** Coordinate is $1.0$ if the output parameter is produced by the capability.

---

## 6. Operational Quality Representation ($\mathbb{R}^8$)

Slice `[152:160]` encodes 8 normalized operational and non-functional quality attributes:

1. **Index 152 ($t_{\text{norm}}$):** Normalized execution latency: $\min(1.0, t / 1000.0\text{ ms})$
2. **Index 153 ($m_{\text{norm}}$):** Normalized monetary cost: $\min(1.0, m / \$0.10)$
3. **Index 154 ($r_{\text{norm}}$):** Normalized computing resource cost: $\min(1.0, r / 5.0\text{ units})$
4. **Index 155 ($\text{risk}$):** Inherent failure risk probability clamped to $[0.0, 1.0]$
5. **Index 156 ($e_{\text{norm}}$):** Normalized energy consumption: $\min(1.0, e / 10.0\text{ units})$
6. **Index 157 ($u_{\text{rel}}$):** Unreliability penalty: $1.0 - \text{Rel}$
7. **Index 158 ($u_{\text{avail}}$):** Unavailability penalty: $1.0 - A$
8. **Index 159 ($c_{\text{comp}}$):** Mean composite cost penalty: $\frac{t_{\text{norm}} + m_{\text{norm}} + r_{\text{norm}} + \text{risk} + u_{\text{rel}}}{5.0}$

By encoding penalties ($1 - \text{Rel}$ and $1 - A$), a perfectly reliable, fully available, zero-cost capability produces an all-zero operational vector. Higher values consistently represent greater cost or operational risk.

---

## 7. Similarity Metrics

### 7.1 Safe Cosine Similarity

Standard cosine similarity is undefined when either vector has zero magnitude. We implement safe cosine similarity:

$$\text{cos}(a, b) = \begin{cases} 
1.0 & \text{if } \|a\| = 0 \text{ and } \|b\| = 0 \\
0.0 & \text{if } \|a\| = 0 \text{ xor } \|b\| = 0 \\
\frac{a \cdot b}{\|a\| \|b\| + \epsilon} & \text{otherwise}
\end{cases}$$

where $\epsilon = 10^{-9}$ prevents division by numerical underflow.

### 7.2 Weighted Functional Capability Similarity

Symmetric capability similarity combines block-wise cosine similarities using normalized functional weights:

$$\text{Sim}(C_1, C_2) = \sum_{b \in \mathcal{B}} w_b \cdot \text{cos}(v(C_1)_b, v(C_2)_b)$$

where $\mathcal{B} = \{\text{effect}, \text{pre}, \text{input}, \text{output}, \text{constraint}, \text{resource}, \text{ops}, \text{mech}\}$ and the weights are configured as:

$$w_{\text{effect}} = 0.25, \quad w_{\text{pre}} = 0.20, \quad w_{\text{input}} = 0.10, \quad w_{\text{output}} = 0.10$$
$$w_{\text{constraint}} = 0.10, \quad w_{\text{resource}} = 0.10, \quad w_{\text{ops}} = 0.10, \quad w_{\text{mech}} = 0.05$$

Notice that the weights sum exactly to:

$$0.25 + 0.20 + 0.10 + 0.10 + 0.10 + 0.10 + 0.10 + 0.05 = 1.00$$

Functional effects and preconditions account for $45\%$ of the similarity weight, ensuring that capabilities performing identical state transitions remain highly similar even when implemented via different mechanisms.

---

## 8. Goal Relevance

The relevance of a capability $C$ to a target goal state $G$ is determined by how effectively the capability's effects satisfy the target goal conditions:

$$\text{GoalRel}(C, G) = \begin{cases} 
0.0 & \text{if } \|v(G)\|^2 = 0 \\
\frac{\max(0.0, v(C)_E \cdot v(G))}{\|v(G)\|^2} & \text{otherwise}
\end{cases}$$

where $v(C)_E \in \mathbb{R}^{32}$ is the capability's effect sub-vector and $v(G) \in \mathbb{R}^{32}$ is the goal condition vector. Capabilities producing contradictory effects yield non-positive dot products and are clamped to $0.0$.

---

## 9. Capability Compatibility and Execution Gating

Compatibility evaluates whether capability $C_1$ (producer) can directly hand off its outputs and post-state to capability $C_2$ (consumer). Unlike similarity, compatibility is strictly directional:

$$\text{Compat}(C_1 \to C_2) \ne \text{Compat}(C_2 \to C_1)$$

### 9.1 Continuous Vector Alignment

Vector compatibility evaluates two directional handoffs:

1. **Effect to Precondition Alignment ($\text{Align}_{EP}$):**
   $$\text{Align}_{EP}(C_1 \to C_2) = \begin{cases} 
   1.0 & \text{if } \|v(C_2)_P\|^2 = 0 \\
   \frac{v(C_1)_E \cdot v(C_2)_P}{\|v(C_2)_P\|^2} & \text{otherwise}
   \end{cases}$$

2. **Output to Input Alignment ($\text{Align}_{OI}$):**
   $$\text{Align}_{OI}(C_1 \to C_2) = \begin{cases} 
   1.0 & \text{if } \|v(C_2)_I\|^2 = 0 \\
   \frac{v(C_1)_O \cdot v(C_2)_I}{\|v(C_2)_I\|^2} & \text{otherwise}
   \end{cases}$$

3. **Composite Vector Compatibility Score ($\text{Comp}_{vec}$):**
   $$\text{Comp}_{vec}(C_1 \to C_2) = 0.6 \cdot \text{Align}_{EP} + 0.4 \cdot \text{Align}_{OI}$$

4. **Execution Compatibility Score ($\text{Comp}_{exec}$):**
   $$\text{Comp}_{exec}(C_1 \to C_2) = A_1 \cdot A_2 \cdot \text{Comp}_{vec}(C_1 \to C_2)$$

### 9.2 Two-Tier Compatibility Architecture

A central principle of our design is the separation of **continuous vector compatibility** from **formal executable compatibility**:

1. **Continuous Metric Layer:** Provides smooth gradient signals for indexing, searching, and ranking candidate transitions.
2. **Formal Validation Gate:** Ensures runtime safety by enforcing non-negotiable discrete constraints. A handoff $C_1 \to C_2$ is declared formally compatible if and only if all five rules pass:
   - **Rule 1 (Threshold):** $\text{Comp}_{exec}(C_1 \to C_2) \ge 0.70$.
   - **Rule 2 (Input Completeness):** Every required input in $I_2$ is present in $O_1$.
   - **Rule 3 (Type Conformance):** The schema type of every matched input matches the produced output type.
   - **Rule 4 (Precondition Satisfaction):** Every precondition in $P_2$ is satisfied by effects in $E_1$.
   - **Rule 5 (Non-Contradiction):** Zero effects in $E_1$ contradict any precondition in $P_2$.
   - **Rule 6 (Availability):** Both $A_1 > 0$ and $A_2 > 0$.

---

## 10. Capability Composition Model

Given an ordered sequence of capabilities $[C_1, C_2, \dots, C_n]$, sequential composition constructs a unified composite capability:

$$C_{1:n} = C_1 \circ C_2 \circ \dots \circ C_n$$

The composition pipeline executes eight concrete steps:

1. **Adjacent Verification:** Every adjacent transition $C_i \to C_{i+1}$ must pass formal compatibility validation.
2. **External Preconditions:** A precondition of downstream capability $C_j$ ($j > 1$) is external if and only if it is not satisfied by any prior effect $E_k$ ($k < j$).
3. **External Inputs:** An input of downstream capability $C_j$ ($j > 1$) is external if and only if it is not supplied by any prior output $O_k$ ($k < j$).
4. **Terminal Outputs:** The outputs of the final capability $C_n$ are exposed as the composite's public outputs ($O_{\text{comp}} = O_n$).
5. **Effect Accumulation with Override:** All effects are merged chronologically. If multiple capabilities modify the same state variable, the later capability overrides the earlier one.
6. **Constraint Union:** $K_{\text{comp}} = \bigcup_{i=1}^n K_i$.
7. **Resource Union:** $R_{\text{comp}} = \bigcup_{i=1}^n R_i$.
8. **Operational Aggregation:**
   - Total latency: $t_{\text{comp}} = \sum_{i=1}^n t_i$
   - Total monetary cost: $m_{\text{comp}} = \sum_{i=1}^n m_i$
   - Total resource cost: $r_{\text{comp}} = \sum_{i=1}^n r_i$
   - Total energy consumption: $e_{\text{comp}} = \sum_{i=1}^n e_i$
   - Composite risk: $\text{risk}_{\text{comp}} = 1.0 - \prod_{i=1}^n (1.0 - \text{risk}_i)$
   - Composite reliability: $\text{Rel}_{\text{comp}} = \prod_{i=1}^n \text{Rel}_i$
   - Composite availability: $A_{\text{comp}} = \prod_{i=1}^n A_i$

The resulting composite object $C_{1:n}$ is an instance of the standard `Capability` tuple, allowing it to be directly re-encoded into $\mathbb{R}^{160}$ using the same encoder function and composed hierarchically.
