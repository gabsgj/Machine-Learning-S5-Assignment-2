# PCCST503 Machine Learning Assignment 2
## Deliverable 1: Formal Embedding Design for Capability Composition

**Topic:** Structured Feature-Based Vector Embedding for Capability Composition  
**Domain:** E-Commerce Workflow and Transaction Processing  
**Author:** Student Implementation  

---

## 1. Executive Summary

This document specifies the mathematical foundation of a structured, feature-based vector embedding for representing formal states, goals, and capabilities in an enterprise e-commerce system. Unlike semantic word embeddings (such as Word2Vec or BERT) that capture textual co-occurrence, this embedding explicitly encodes causal state preconditions, state-transforming effects, component types, input/output port interfaces, and operational quality attributes (QoS). The resulting representations preserve algebraic compositional semantics and enable linear-time verification of capability compatibility, sequence composition, and goal alignment.

---

## 2. Formal Application Model

According to Section 3 of the PCCST503 Assignment 2 specification, a formal application is modeled as a 6-tuple:

$$\mathcal{A} = (\mathcal{S}, \mathcal{C}, S_I, G, \mathcal{R}, \mathcal{K})$$

Where:
* **$\mathcal{S}$ (State Space):** The set of all possible state valuations over a predefined finite universe of state variables $X = \{x_0, x_1, \dots, x_{d-1}\}$.
* **$\mathcal{C}$ (Capability Library):** The finite set of available executable operations $\{C_1, C_2, \dots, C_n\}$.
* **$S_I \in \mathcal{S}$ (Initial State):** The ground valuation of the system before any capability execution occurs.
* **$G$ (Goal Specification):** A set of desired state conditions $\{g_1, g_2, \dots, g_m\}$ required for task completion.
* **$\mathcal{R}$ (Available Resources):** The set of shared system infrastructure components (e.g., databases, message brokers, payment gateways).
* **$\mathcal{K}$ (Global Constraints):** Invariant safety and policy rules that must hold throughout execution.

---

## 3. State and Goal Representation

### 3.1. Canonical State Variable Basis
We define an ordered basis of $d = 11$ canonical boolean state variables:

| Index $k$ | Variable Name | Formal Description |
| :---: | :--- | :--- |
| **0** | `authenticated` | Customer identity and session validity verified |
| **1** | `customer_exists` | Registered customer record located in persistent store |
| **2** | `cart_exists` | Active shopping cart session initialized |
| **3** | `cart_has_items` | Cart contains at least one purchasable line item |
| **4** | `inventory_available` | Stock quantities validated and reserved |
| **5** | `order_exists` | Formal order entity instantiated |
| **6** | `order_created` | Order record state flagged as CREATED |
| **7** | `payment_success` | Transaction funds captured successfully |
| **8** | `notification_sent` | Customer confirmation dispatch completed |
| **9** | `order_cancelled` | Cart or order marked as cancelled/abandoned |
| **10** | `shipment_dispatched`| Courier label generated and shipment released |

### 3.2. State Embedding Function $\phi_S(S)$
States describe concrete valuations of all system variables. We apply a bipolar encoding:

$$\phi_S : \mathcal{S} \to \{-1, +1\}^d$$

$$\phi_S(S)_k = \begin{cases} +1.0 & \text{if } x_k = \text{true in } S \\ -1.0 & \text{if } x_k = \text{false in } S \end{cases}$$

For the standard initial state $S_I$ where the user is authenticated with an active cart containing items and available inventory, but no order or payment has yet been executed:
$$\phi_S(S_I) = [+1.0, +1.0, +1.0, +1.0, +1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0]^T$$

### 3.3. Goal Embedding Function $\phi_G(G)$
A goal specification $G$ defines a partial valuation over state variables. Variables not referenced in $G$ are "don't care" variables:

$$\phi_G : G \to \{-1, 0, +1\}^d$$

$$\phi_G(G)_k = \begin{cases} +1.0 & \text{if } G \text{ requires } x_k = \text{true} \\ -1.0 & \text{if } G \text{ requires } x_k = \text{false} \\ 0.0 & \text{if variable } x_k \text{ is unconstrained by } G \end{cases}$$

For the canonical purchase goal $G = \{\text{order\_exists}=\text{true}, \text{payment\_success}=\text{true}, \text{notification\_sent}=\text{true}\}$:
$$\phi_G(G) = [0.0, 0.0, 0.0, 0.0, 0.0, +1.0, 0.0, +1.0, +1.0, 0.0, 0.0]^T$$

---

## 4. Formal Capability Model

A capability is modeled as an 11-tuple according to Section 4 of the specification:

$$C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, \text{Rel}_i, A_i, M_i)$$

Where:
* $T_i \in \{\text{API}, \text{DATABASE}, \text{GUI}, \text{EVENT}, \text{FUNCTION}, \text{SERVICE}\}$: Architectural mechanism type.
* $I_i = \{i_1, \dots, i_p\}$: Input port specifications, where $i_j = (\text{name}, \text{type}, \text{domain}, \text{required})$.
* $O_i = \{o_1, \dots, o_q\}$: Output port specifications, where $o_j = (\text{name}, \text{type}, \text{domain})$.
* $P_i = \{p_1, \dots, p_r\}$: Causal precondition predicates required to execute $C_i$.
* $E_i = \{e_1, \dots, e_s\}$: State transformation effects produced by $C_i$.
* $K_i$: Capability-specific runtime constraints.
* $R_i$: Resource dependencies.
* $Q_i = (C_{\text{time}}, C_{\text{money}}, C_{\text{resource}}, C_{\text{risk}})$: Quality of Service (QoS) operational costs.
* $\text{Rel}_i \in [0, 1]$: Execution reliability (success probability).
* $A_i \in \{0, 1\}$: Current component availability.
* $M_i$: Execution mechanism details (e.g., URI route, SQL template).

---

## 5. Structured Capability Vector Embedding $\phi_C(C)$

The vector representation of a capability maps $C_i$ into a continuous/discrete vector space $\mathbb{R}^D$ where $D = 36$:

$$\phi_C : \mathcal{C} \to \mathbb{R}^{36}$$

The 36 dimensions are partitioned into five orthogonal semantic blocks:

$$\phi_C(C) = \big[ \mathbf{p}(C) \;\parallel\; \mathbf{e}(C) \;\parallel\; \mathbf{t}(C) \;\parallel\; \mathbf{io}(C) \;\parallel\; \mathbf{q}(C) \big]$$

### 5.1. Precondition Sub-vector $\mathbf{p}(C) \in \{-1, 0, +1\}^{11}$ (Indices 0–10)
$$\mathbf{p}(C)_k = \begin{cases} +1.0 & \text{if } C \text{ requires } x_k = \text{true} \\ -1.0 & \text{if } C \text{ requires } x_k = \text{false} \\ 0.0 & \text{if } C \text{ places no condition on } x_k \end{cases}$$

### 5.2. Effect Sub-vector $\mathbf{e}(C) \in \{-1, 0, +1\}^{11}$ (Indices 11–21)
$$\mathbf{e}(C)_k = \begin{cases} +1.0 & \text{if } C \text{ sets } x_k \leftarrow \text{true} \\ -1.0 & \text{if } C \text{ sets } x_k \leftarrow \text{false} \\ 0.0 & \text{if } C \text{ leaves } x_k \text{ unchanged} \end{cases}$$

### 5.3. Capability Type One-Hot Sub-vector $\mathbf{t}(C) \in \{0, 1\}^6$ (Indices 22–27)
Represented over the basis $\{\text{API}, \text{DATABASE}, \text{GUI}, \text{EVENT}, \text{FUNCTION}, \text{SERVICE}\}$:
$$\mathbf{t}(C)_j = \begin{cases} 1.0 & \text{if } T(C) = \text{Type}_j \\ 0.0 & \text{otherwise} \end{cases}$$

### 5.4. Interface Port Feature Sub-vector $\mathbf{io}(C) \in [0, 1]^2$ (Indices 28–29)
$$\mathbf{io}(C) = \left[ \min\left(1.0, \frac{|I(C)|}{5.0}\right), \min\left(1.0, \frac{|O(C)|}{5.0}\right) \right]$$

### 5.5. Operational Quality Sub-vector $\mathbf{q}(C) \in [0, 1]^6$ (Indices 30–35)
Deterministic linear normalization bounds raw values into $[0, 1]$, covering all required operational attributes:
$$\mathbf{q}(C) = \left[ \min\left(1.0, \frac{C_{\text{time}}}{1000.0}\right), \min\left(1.0, \frac{C_{\text{money}}}{1.0}\right), \min\left(1.0, \frac{C_{\text{resource}}}{10.0}\right), C_{\text{risk}}, \text{Rel}, A \right]$$

---

## 6. Mathematical Operations

### 6.1. Cosine Similarity $\text{Sim}(\mathbf{u}, \mathbf{v})$
Measures vector alignment (functional and operational resemblance):

$$\text{Sim}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2 + \epsilon}, \quad \epsilon = 10^{-12}$$

Properties:
* Symmetric: $\text{Sim}(\mathbf{u}, \mathbf{v}) = \text{Sim}(\mathbf{v}, \mathbf{u})$
* Reflexive: $\text{Sim}(\mathbf{u}, \mathbf{u}) = 1.0$ for non-zero vectors
* Safe for zero-vectors: Returns $0.0$ if $\|\mathbf{u}\| < \epsilon$ or $\|\mathbf{v}\| < \epsilon$.

### 6.2. Precondition-Effect Compatibility $\text{Comp}(C_1, C_2)$
Evaluates whether executing $C_1$ causally enables or conflicts with $C_2$:

$$\text{Comp}(C_1, C_2) = \begin{cases} 1.0 & \text{if } \|\mathbf{p}(C_2)\|_2^2 = 0 \\ \dfrac{\mathbf{e}(C_1) \cdot \mathbf{p}(C_2)}{\|\mathbf{p}(C_2)\|_2^2} & \text{otherwise} \end{cases}$$

Interpretation:
* $\mathbf{+1.0000}$: All preconditions of $C_2$ that intersect with $C_1$'s effects are satisfied.
* $\mathbf{0.0000}$: Neutral / uncoupled relationship ($C_1$'s effects neither enable nor conflict with $C_2$).
* $\mathbf{-1.0000}$: Causal conflict ($C_1$ actively produces effects contrary to $C_2$'s requirements).

### 6.3. Input-Output Interface Compatibility $\text{IOComp}(C_1, C_2)$
Measures whether the produced outputs of $C_1$ satisfy the required input arguments of $C_2$:

$$\text{IOComp}(C_1, C_2) = \begin{cases} 1.0 & \text{if } |I_{\text{req}}(C_2)| = 0 \\ \dfrac{|\{i \in I_{\text{req}}(C_2) \mid \exists o \in O(C_1) : \text{name}(o) = \text{name}(i) \land \text{type}(o) = \text{type}(i)\}|}{|I_{\text{req}}(C_2)|} & \text{otherwise} \end{cases}$$

### 6.4. Goal Relevance $\text{Relevance}(C, G)$
Measures direct alignment between capability effects and desired goal criteria:

$$\text{Relevance}(C, G) = \mathbf{e}(C) \cdot \phi_G(G) = \sum_{k=0}^{d-1} \mathbf{e}(C)_k \cdot \phi_G(G)_k$$

A positive score indicates direct goal advancement; zero indicates goal irrelevance.

---

## 7. Capability Composition Model

Given capabilities $C_1$ and $C_2$, sequential composition $C_{12} = C_2 \circ C_1$ denotes executing $C_1$ followed by $C_2$.

### 7.1. Composed Preconditions
Preconditions of $C_1$ are preserved, plus any preconditions of $C_2$ not already satisfied by $C_1$'s effects:
$$P(C_2 \circ C_1) = P(C_1) \cup \left\{ p \in P(C_2) \mid \neg \exists e \in E(C_1) : \text{var}(e) = \text{var}(p) \land \text{val}(e) = \text{expected}(p) \right\}$$

### 7.2. Composed Effects
Effects of $C_1$ are applied, and subsequent effects of $C_2$ update or overwrite them:
$$E(C_2 \circ C_1) = E(C_2) \cup \left\{ e_1 \in E(C_1) \mid \neg \exists e_2 \in E(C_2) : \text{var}(e_1) = \text{var}(e_2) \right\}$$

### 7.3. Composed Inputs and Outputs
* Inputs: $I(C_2 \circ C_1) = I(C_1) \cup \left\{ i \in I(C_2) \mid \neg \exists o \in O(C_1) : \text{name}(i) = \text{name}(o) \land \text{type}(i) = \text{type}(o) \right\}$
* Outputs: $O(C_2 \circ C_1) = O(C_2) \cup O(C_1)$

### 7.4. Operational Attribute Aggregation
* **Time:** Additive: $C_{\text{time}}(C_{12}) = C_{\text{time}}(C_1) + C_{\text{time}}(C_2)$
* **Money:** Additive: $C_{\text{money}}(C_{12}) = C_{\text{money}}(C_1) + C_{\text{money}}(C_2)$
* **Resource:** Additive: $C_{\text{resource}}(C_{12}) = C_{\text{resource}}(C_1) + C_{\text{resource}}(C_2)$
* **Risk:** Cumulative probability of failure avoidance:
  $$\text{Risk}(C_{12}) = 1.0 - \big(1.0 - \text{Risk}(C_1)\big)\big(1.0 - \text{Risk}(C_2)\big)$$
* **Reliability:** Multiplicative:
  $$\text{Rel}(C_{12}) = \text{Rel}(C_1) \times \text{Rel}(C_2)$$
* **Availability:** Conjunctive:
  $$A(C_{12}) = A(C_1) \land A(C_2)$$

### 7.5. Composite Vector Encoding Invariant
The resulting composite entity $C_{12}$ is encoded using the exact same function $\phi_C(C_{12}) \in \mathbb{R}^{36}$ as atomic capabilities, ensuring inductive compositional closure.
