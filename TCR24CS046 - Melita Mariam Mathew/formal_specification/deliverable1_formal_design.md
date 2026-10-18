# Deliverable 1: Formal Mathematical Specification of Vector Embedding for Capability Composition

**Author**: Melita Mariam Mathew  
**University Registration Number**: TCCR24CS046  
**Course**: Advanced Software Architecture / Capability Engineering  
**Assignment**: Assignment 2 — Design of a Vector Embedding for Capability Composition  

---

## 1. Formal Application Model

An application domain is formalized as a 6-tuple:
$$\mathcal{A} = (\mathcal{S}, \mathcal{C}, S_I, G, \mathcal{R}, \mathcal{K})$$

Where:
- $\mathcal{S}$: The application state space.
- $\mathcal{C} = \{C_1, C_2, \dots, C_N\}$: The finite set of available executable capabilities.
- $S_I \in \mathcal{S}$: The initial state of the application.
- $G$: The goal specification describing required target conditions.
- $\mathcal{R} = \{r_1, r_2, \dots, r_u\}$: The set of system resources (e.g., Database, Network, Payment Gateway).
- $\mathcal{K} = \{k_1, k_2, \dots, k_t\}$: The set of global invariants and policy constraints.

---

## 2. Formal Entity Representations

### 2.1 State Representation ($\mathcal{S}$)
A discrete application state $S \in \mathcal{S}$ is an assignment of values to an indexed set of $n$ state variables:
$$S = \{(x_1, v_1), (x_2, v_2), \dots, (x_n, v_n)\}, \quad x_k \in \mathcal{V}_{state}, \; v_k \in \text{Domain}(x_k)$$

Variables may be:
- Boolean: $v_k \in \{\text{True}, \text{False}\}$
- Numeric / Ordinal: $v_k \in \mathbb{R}$ or $\mathbb{Z}_{\ge 0}$
- Categorical / Enumerated: $v_k \in \Sigma_k$

### 2.2 Goal Representation ($G$)
A goal $G = \{g_1, g_2, \dots, g_m\}$ specifies a set of desired predicates over state variables. A state $S$ satisfies $G$ (denoted $S \models G$) if and only if:
$$\forall g_j \in G, \quad S \models g_j$$

### 2.3 Capability Representation ($C_i$)
Each capability $C_i \in \mathcal{C}$ is formalized as an 11-tuple:
$$C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)$$

Where:
1. **$T_i \in \mathcal{T}$**: Capability type, where $\mathcal{T} = \{\text{API}, \text{DATABASE}, \text{GUI}, \text{EVENT}, \text{FUNCTION}, \text{FILE}, \text{COMPUTATION}, \text{MESSAGE}, \text{SERVICE}\}$.
2. **$I_i = \{i_1, \dots, i_p\}$**: Input parameter signature, each $i_j = (\text{name}, \text{type}, \text{domain}, \text{required})$.
3. **$O_i = \{o_1, \dots, o_q\}$**: Output parameter signature, each $o_j = (\text{name}, \text{type}, \text{domain})$.
4. **$P_i = \{p_1, \dots, p_r\}$**: Precondition predicates. $C_i$ is applicable to state $S \iff S \models P_i$.
5. **$E_i = \{e_1, \dots, e_s\}$**: Effect assertions. State mutation operator: $C_i : S \mapsto S' = \text{Apply}(S, E_i)$.
6. **$K_i$**: Capability-specific operational constraints.
7. **$R_i \subseteq \mathcal{R}$**: Set of allocated system resources.
8. **$Q_i = (C_{time}, C_{money}, C_{resource}, C_{risk}, C_{energy}) \in \mathbb{R}_{\ge 0}^5$**: Operational cost vector.
9. **$Rel_i \in [0, 1]$**: Success probability (reliability).
10. **$A_i \in [0, 1]$**: Operational availability.
11. **$M_i$**: Execution mechanism descriptor (e.g., HTTP verb, endpoint route, table name, UI element ID).

---

## 3. Dual-Faceted Partitioned Vector Space (DF-PVS)

To avoid semantic collapse where distinct operational concepts (such as preconditions vs. effects, or functional equivalence vs. execution mechanisms) conflate, the embedding space is designed as a direct sum of orthogonal, semantically dedicated subspaces:

$$\mathcal{V} = \mathbb{R}^{d_{pre}} \oplus \mathbb{R}^{d_{eff}} \oplus \mathbb{R}^{d_{in}} \oplus \mathbb{R}^{d_{out}} \oplus \mathbb{R}^{d_{\Delta}} \oplus \mathbb{R}^{d_{mech}} \oplus \mathbb{R}^{d_{ops}} = \mathbb{R}^D$$

Where:
- $d_{pre} = d_{eff} = d_{\Delta} = d_{state} = |\mathcal{V}_{state}|$ (cardinality of known state variables).
- $d_{in} = d_{out} = d_{io} = |\mathcal{V}_{io}|$ (cardinality of I/O parameter vocabulary).
- $d_{mech} = |\mathcal{T}| + d_{extra}$ (one-hot type and structural execution flags).
- $d_{ops} = 6$ (latency, monetary cost, resource load, operational risk, log-reliability, availability).
- Total dimensionality: $D = 3 \cdot d_{state} + 2 \cdot d_{io} + d_{mech} + d_{ops}$.

---

## 4. Embedding Functions

### 4.1 State Embedding Function: $\phi_S : \mathcal{S} \to \mathbb{R}^{d_{state}}$
For state $S$ and state variable $x_k \in \mathcal{V}_{state}$ at index $k \in \{1, \dots, d_{state}\}$:
$$\phi_S(S)_k = \begin{cases}
+1.0 & \text{if } x_k = \text{True} \text{ or categorical positive} \\
-1.0 & \text{if } x_k = \text{False} \text{ or categorical negative} \\
\text{clamp}\left(\frac{v_k}{\text{scale}_k}, -1.0, 1.0\right) & \text{if } x_k \text{ is continuous / numeric} \\
0.0 & \text{if } x_k \text{ is uninstantiated / unknown in } S
\end{cases}$$

### 4.2 Goal Embedding Function: $\phi_G : G \to \mathbb{R}^{d_{state}}$
$$\phi_G(G)_k = \begin{cases}
+1.0 & \text{if } G \text{ asserts } x_k = \text{True} \\
-1.0 & \text{if } G \text{ asserts } x_k = \text{False} \\
\text{clamp}\left(\frac{v_k^*}{\text{scale}_k}, -1.0, 1.0\right) & \text{if } G \text{ asserts numeric target } v_k^* \\
0.0 & \text{if } x_k \text{ is unconstrained by } G
\end{cases}$$

### 4.3 Capability Embedding Function: $\phi_C : \mathcal{C} \to \mathbb{R}^D$
The vector embedding $\mathbf{c}_i = \phi_C(C_i)$ is partitioned as:
$$\mathbf{c}_i = \begin{bmatrix}
\mathbf{v}_{pre}(C_i) \\
\mathbf{v}_{eff}(C_i) \\
\mathbf{v}_{in}(C_i) \\
\mathbf{v}_{out}(C_i) \\
\mathbf{v}_{\Delta}(C_i) \\
\mathbf{v}_{mech}(C_i) \\
\mathbf{v}_{ops}(C_i)
\end{bmatrix} \in \mathbb{R}^D$$

1. **Precondition Subvector $\mathbf{v}_{pre} \in \mathbb{R}^{d_{state}}$**:
   $$[\mathbf{v}_{pre}(C_i)]_k = \begin{cases}
   +1.0 & \text{if } (x_k == \text{True}) \in P_i \\
   -1.0 & \text{if } (x_k == \text{False}) \in P_i \\
   0.0 & \text{otherwise}
   \end{cases}$$

2. **Effect Subvector $\mathbf{v}_{eff} \in \mathbb{R}^{d_{state}}$**:
   $$[\mathbf{v}_{eff}(C_i)]_k = \begin{cases}
   +1.0 & \text{if } (x_k := \text{True}) \in E_i \\
   -1.0 & \text{if } (x_k := \text{False}) \in E_i \\
   0.0 & \text{otherwise}
   \end{cases}$$

3. **Input Subvector $\mathbf{v}_{in} \in \mathbb{R}^{d_{io}}$**:
   Multi-hot binary indicator vector over required input names and types.

4. **Output Subvector $\mathbf{v}_{out} \in \mathbb{R}^{d_{io}}$**:
   Multi-hot binary indicator vector over produced output names and types.

5. **State Transition Delta Subvector $\mathbf{v}_{\Delta} \in \mathbb{R}^{d_{state}}$**:
   $$\mathbf{v}_{\Delta}(C_i) = \mathbf{v}_{eff}(C_i) - \mathbf{v}_{pre}(C_i)$$
   Encodes the net vector displacement in state space (analogous to the translation relation in TransE: $\phi_S(S') \approx \phi_S(S) + \mathbf{v}_{\Delta}(C)$).

6. **Mechanism Subvector $\mathbf{v}_{mech} \in \mathbb{R}^{d_{mech}}$**:
   One-hot type vector over $\mathcal{T}$ concatenated with execution property flags (e.g., HTTP verb, SQL command, UI element selector).

7. **Operational Subvector $\mathbf{v}_{ops} \in \mathbb{R}^6$**:
   $$\mathbf{v}_{ops}(C_i) = \begin{bmatrix}
   \frac{C_{time}}{C_{time}^{max}} \\
   \frac{C_{money}}{C_{money}^{max}} \\
   \frac{C_{resource}}{C_{resource}^{max}} \\
   C_{risk} \\
   -\ln(Rel_i) \\
   A_i
   \end{bmatrix}$$
   *Crucial mathematical insight*: Representing reliability as $-\ln(Rel_i)$ maps multiplicative reliability $Rel(C_1 \circ C_2) = Rel_1 \cdot Rel_2$ into a strictly additive metric space:
   $$-\ln(Rel_1 \cdot Rel_2) = -\ln(Rel_1) + (-\ln(Rel_2))$$

---

## 5. Formal Compatibility Measure

Given two capabilities $C_1$ and $C_2$, sequential compatibility assesses whether $C_2$ can validly execute following $C_1$ ($C_1 \to C_2$ or $C_2 \circ C_1$).

### 5.1 Directional State Alignment & Conflict Detection
Let $\mathbf{e}_1 = \mathbf{v}_{eff}(C_1)$ and $\mathbf{p}_2 = \mathbf{v}_{pre}(C_2)$. Let $\Omega(P_2) = \{k \mid |[\mathbf{p}_2]_k| > 0\}$ denote the set of active preconditions of $C_2$.

For each $k \in \Omega(P_2)$:
- **Satisfaction Match**: If $[\mathbf{e}_1]_k \cdot [\mathbf{p}_2]_k > 0$, effect $E_1$ directly fulfills precondition $P_2$.
- **Direct Conflict**: If $[\mathbf{e}_1]_k \cdot [\mathbf{p}_2]_k < 0$, effect $E_1$ establishes a state that violates precondition $P_2$ (e.g., $E_1$ sets $OrderExists = \text{True}$ while $P_2$ requires $OrderExists = \text{False}$).

We define:
$$\text{MatchScore}(C_1 \to C_2) = \frac{\sum_{k \in \Omega(P_2)} \mathbb{I}([\mathbf{e}_1]_k \cdot [\mathbf{p}_2]_k > 0)}{\max(1, |\Omega(P_2)|)}$$
$$\text{ConflictPenalty}(C_1 \to C_2) = \frac{\sum_{k \in \Omega(P_2)} \mathbb{I}([\mathbf{e}_1]_k \cdot [\mathbf{p}_2]_k < 0)}{\max(1, |\Omega(P_2)|)}$$

### 5.2 Input-Output Dataflow Coupling
Let $\mathbf{o}_1 = \mathbf{v}_{out}(C_1)$ and $\mathbf{i}_2 = \mathbf{v}_{in}(C_2)$. Let $\Omega(I_2) = \{j \mid [\mathbf{i}_2]_j > 0\}$:
$$\text{IOScore}(C_1 \to C_2) = \frac{\sum_{j \in \Omega(I_2)} \min([\mathbf{o}_1]_j, [\mathbf{i}_2]_j)}{\max(1, |\Omega(I_2)|)}$$

### 5.3 Unified Directional Compatibility Function
$$\text{Comp}(C_1 \to C_2) = \begin{cases}
-\text{ConflictPenalty}(C_1 \to C_2) & \text{if } \text{ConflictPenalty} > 0 \\
w_e \cdot \text{MatchScore}(C_1 \to C_2) + w_{io} \cdot \text{IOScore}(C_1 \to C_2) & \text{if } \text{MatchScore} > 0 \text{ or } |\Omega(P_2)| = 0 \\
w_{io} \cdot \text{IOScore}(C_1 \to C_2) \cdot 0.1 & \text{otherwise (independent)}
\end{cases}$$
Where $w_e = 0.6$ and $w_{io} = 0.4$.

**Property (Directional Asymmetry)**:
In general, $\text{Comp}(C_1 \to C_2) \neq \text{Comp}(C_2 \to C_1)$, correctly capturing that causality in execution pipelines is strictly directed.

---

## 6. Similarity vs. Composability

A core theoretical requirement (Section 6.1, Property 5 of Assignment PDF) is that **similarity and composability are orthogonal concepts**.

### 6.1 Functional Similarity
Measures whether two capabilities accomplish identical state modifications:
$$\text{Sim}_{func}(C_A, C_B) = \cos(\mathbf{v}_{eff}(C_A), \mathbf{v}_{eff}(C_B)) \cdot \left(\frac{1 + \cos(\mathbf{v}_{pre}(C_A), \mathbf{v}_{pre}(C_B))}{2}\right)$$

### 6.2 Mechanism Similarity
Measures whether two capabilities employ the same execution modality:
$$\text{Sim}_{mech}(C_A, C_B) = \cos(\mathbf{v}_{mech}(C_A), \mathbf{v}_{mech}(C_B))$$

### 6.3 Total Similarity
$$\text{Sim}_{total}(C_A, C_B) = \alpha \cdot \text{Sim}_{func}(C_A, C_B) + (1 - \alpha) \cdot \text{Sim}_{mech}(C_A, C_B), \quad \alpha \in [0, 1]$$

### 6.4 Key Distinction Table
| Property | $C_1 \to C_2$ (CreateOrder $\to$ MakePayment) | $C_1^{API}$ vs $C_1^{DB}$ (Alternative Implementations) |
| :--- | :--- | :--- |
| **Functional Similarity** | Low ($\approx 0.0$) | High ($= 1.0000$) |
| **Composability Score** | High ($= +0.8000$) | Low / Invalid ($0.0$) |
| **Pipeline Relation** | Sequential pipeline | Mutually exclusive alternatives |

---

## 7. Vector Composition Algebra

When composing two capabilities into a complex pipeline $C_{12} = C_2 \circ C_1$ (execute $C_1$, then $C_2$), the composite embedding $\mathbf{c}_{12} = \mathbf{c}_1 \odot \mathbf{c}_2$ is defined by component-wise closed algebraic operators:

1. **Composite Effects**:
   Effects of $C_2$ take precedence over $C_1$; non-overridden effects of $C_1$ persist:
   $$\mathbf{v}_{eff}(C_2 \circ C_1) = \mathbf{v}_{eff}(C_2) + (\mathbf{1} - |\text{sign}(\mathbf{v}_{eff}(C_2))|) \odot \mathbf{v}_{eff}(C_1)$$

2. **Composite Preconditions**:
   Preconditions of $C_1$ plus whatever preconditions of $C_2$ were not already established by $C_1$:
   $$[\mathbf{v}_{pre}(C_2 \circ C_1)]_k = \begin{cases}
   [\mathbf{v}_{pre}(C_1)]_k & \text{if } |[\mathbf{v}_{pre}(C_1)]_k| > 0 \\
   0.0 & \text{if } [\mathbf{v}_{eff}(C_1)]_k \cdot [\mathbf{v}_{pre}(C_2)]_k > 0 \text{ (fulfilled by } C_1) \\
   [\mathbf{v}_{pre}(C_2)]_k & \text{otherwise}
   \end{cases}$$

3. **Composite Inputs**:
   $$\mathbf{v}_{in}(C_2 \circ C_1) = \max\left(\mathbf{v}_{in}(C_1), \max\left(0, \mathbf{v}_{in}(C_2) - \mathbf{v}_{out}(C_1)\right)\right)$$

4. **Composite Outputs**:
   $$\mathbf{v}_{out}(C_2 \circ C_1) = \max(\mathbf{v}_{out}(C_1), \mathbf{v}_{out}(C_2))$$

5. **Composite State Delta**:
   $$\mathbf{v}_{\Delta}(C_2 \circ C_1) = \mathbf{v}_{eff}(C_2 \circ C_1) - \mathbf{v}_{pre}(C_2 \circ C_1)$$

6. **Composite Operational Vector**:
   $$\mathbf{v}_{ops}(C_2 \circ C_1) = \begin{bmatrix}
   \min(1.0, [\mathbf{v}_{ops}]_1^{(1)} + [\mathbf{v}_{ops}]_1^{(2)}) \\
   \min(1.0, [\mathbf{v}_{ops}]_2^{(1)} + [\mathbf{v}_{ops}]_2^{(2)}) \\
   \min(1.0, [\mathbf{v}_{ops}]_3^{(1)} + [\mathbf{v}_{ops}]_3^{(2)}) \\
   1.0 - (1 - [\mathbf{v}_{ops}]_4^{(1)})(1 - [\mathbf{v}_{ops}]_4^{(2)}) \\
   [\mathbf{v}_{ops}]_5^{(1)} + [\mathbf{v}_{ops}]_5^{(2)} \\
   \min([\mathbf{v}_{ops}]_6^{(1)}, [\mathbf{v}_{ops}]_6^{(2)})
   \end{bmatrix}$$

**Theorem (Homomorphism Property)**:
$$\phi_C(C_2 \circ C_1) \equiv \phi_C(C_1) \odot \phi_C(C_2)$$
The vector composition operator preserves the semantics of symbolic capability composition with exact closure ($L_2 = 0.0000$, $\text{Cosine} = 1.0000$).

---

## 8. Goal Relevance Formulation

Let $S$ be the current application state, and $G$ be the goal specification. The active goal dimensions are $\Omega(G) = \{k \mid |[\phi_G(G)]_k| > 0\}$.

The goal relevance of a capability $C$ (atomic or composite) is given by:
$$\text{Relevance}(C, G, S) = \frac{\sum_{k \in \Omega(G)} [\mathbf{v}_{eff}(C)]_k \cdot [\phi_G(G)]_k \cdot 2.0}{\sum_{k \in \Omega(G)} |[\phi_G(G)]_k| \cdot 2.0}$$

- If $C$'s effects satisfy all conditions in $G$: $\text{Relevance} = 1.0$.
- If $C$ satisfies a subset of $G$: $\text{Relevance} \in (0, 1)$.
- If $C$ affects variables outside $G$: $\text{Relevance} = 0.0$ (irrelevant).
- If $C$ negates a condition in $G$: $\text{Relevance} < 0.0$ (counterproductive/adversarial).
