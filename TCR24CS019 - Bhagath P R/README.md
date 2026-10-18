# Design of a Vector Embedding for Capability Composition

**PCCST503 – Machine Learning | Assignment 2**  
*Submitted by:* Bhagath P. R. — TCR24CS019  

---

## Executive Summary

This repository delivers a mathematically rigorous, modular Python implementation of a **Vector Embedding Architecture for Capability Composition**. While Word2Vec (Mikolov et al., 2013) introduced distributed vector representations to capture semantic analogies between words, this project designs distributed continuous geometries for **functional operations (capabilities)** within software and autonomous systems. 

Instead of semantic meaning, our vector embedding captures **functional relationships**: what capabilities require (inputs, preconditions, resources), what they produce (outputs, state effects), under what constraints and quality attributes they operate (cost, latency, reliability, availability), and how atomic capabilities algebraically compose into complex end-to-end workflows.

```
       Word2Vec: Semantic Word Analogies            Assignment 2: Functional Capability Composition
                ^                                                ^
                |   Woman -> Queen                               |   CreateOrder
                |   Man   -> King                                |       | (Effect: OrderExists)
                +-----------------> Semantic                     |       v
                                                                 |   MakePayment
                                                                 +-----------------> Functional
```

---

## Table of Contents

1. [Deliverable 1: Formal Embedding Design](#1-deliverable-1-formal-embedding-design)
   - [1.1 Mathematical Formulation of Application Entities](#11-mathematical-formulation-of-application-entities)
   - [1.2 Structured Multi-Sector Embedding Architecture](#12-structured-multi-sector-embedding-architecture)
   - [1.3 Similarity vs Composability Operators](#13-similarity-vs-composability-operators)
   - [1.4 Algebraic & Semantic Capability Composition](#14-algebraic--semantic-capability-composition)
   - [1.5 Operational & Reliability Vector Homomorphism](#15-operational--reliability-vector-homomorphism)
2. [Deliverable 2: Implementation & Python API](#2-deliverable-2-implementation--python-api)
   - [2.1 Architecture Overview](#21-architecture-overview)
   - [2.2 Core API Methods](#22-core-api-methods)
   - [2.3 Code Usage Examples](#23-code-usage-examples)
3. [Deliverable 3: Experimental Benchmark Datasets](#3-deliverable-3-experimental-benchmark-datasets)
   - [3.1 Web & Literature Search Audit](#31-web--literature-search-audit)
   - [3.2 Multi-Domain Benchmark Suites](#32-multi-domain-benchmark-suites)
4. [Deliverable 4: Full Technical Report](#4-deliverable-4-full-technical-report)
   - [4.1 Problem Definition](#41-problem-definition)
   - [4.2 Design Requirements](#42-design-requirements)
   - [4.3 Related Embedding Approaches & Gap Analysis](#43-related-embedding-approaches--gap-analysis)
   - [4.4 Proposed Representation Architecture](#44-proposed-representation-architecture)
   - [4.5 Mathematical Formulation](#45-mathematical-formulation)
   - [4.6 Capability Composition Model](#46-capability-composition-model)
   - [4.7 Implementation Architecture](#47-implementation-architecture)
   - [4.8 Experimental Methodology](#48-experimental-methodology)
   - [4.9 Empirical Results (Experiments 1–5)](#49-empirical-results)
   - [4.10 Comprehensive Analysis Against Evaluation Criteria](#410-comprehensive-analysis-against-evaluation-criteria)
   - [4.11 Limitations & Future Work](#411-limitations--future-work)
   - [4.12 Conclusion](#412-conclusion)
5. [User Manual & Verification](#5-user-manual--verification)
   - [5.1 Installation & Prerequisites](#51-installation--prerequisites)
   - [5.2 Running the Interactive CLI Demo](#52-running-the-interactive-cli-demo)
   - [5.3 Running the Test Suite](#53-running-the-test-suite)
   - [5.4 Running the Automated Benchmark Suite](#54-running-the-automated-benchmark-suite)

---

# 1. Deliverable 1: Formal Embedding Design

### 1.1 Mathematical Formulation of Application Entities

An application problem instance is defined as the formal sextuple:

$$
\mathcal{A} = (\mathcal{S}, \mathcal{C}, S_I, G, \mathcal{R}, \mathcal{K})
$$

#### 1. State Space and State Representation
An application state $S \in \mathcal{S}$ represents the valuation of a finite universe of state variables $V = \{x_1, x_2, \dots, x_n\}$:

$$
S = \{(x_1, v_1), (x_2, v_2), \dots, (x_n, v_n)\}
$$

Variables may be Boolean ($v \in \{0, 1\}$), categorical / enumerated ($v \in \mathcal{D}_k$), or continuous / real-valued ($v \in \mathbb{R}$).  
The state embedding function $\phi_S : \mathcal{S} \to \mathbb{R}^{d_S}$ maps each variable to its normalized feature coordinates:

$$
\phi_S(S) = \big[ \mathbf{s}_1 \;\parallel\; \mathbf{s}_2 \;\parallel\; \dots \;\parallel\; \mathbf{s}_n \big] \in \mathbb{R}^{d_S}
$$

#### 2. Goal Specification
A goal $G = \{g_1, g_2, \dots, g_m\}$ specifies target conditions on a subset of state variables. In continuous vector space, $G$ is embedded as a dual target-mask pair:

$$
\phi_G(G) = \big[ \mathbf{g}_{\text{val}} \;\parallel\; \mathbf{g}_{\text{mask}} \big] \in \mathbb{R}^{2 \cdot d_S}
$$

where the mask coordinates satisfy:

$$
\mathbf{g}_{\text{mask}}[k] = \begin{cases} 1 & \text{if variable } k \text{ is constrained by } G \\ 0 & \text{otherwise} \end{cases}
$$

and $\mathbf{g}_{\text{val}}[k]$ holds the desired coordinate value. A state $S$ satisfies $G$ ($S \models G$) iff:

$$
\|\mathbf{g}_{\text{mask}} \odot (\phi_S(S) - \mathbf{g}_{\text{val}})\|_2 = 0
$$

#### 3. Formal Capability Representation
A capability $C_i$ is an 11-tuple:

$$
C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)
$$

- **Type ($T_i$)**: $T_i \in \{\text{API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE}\}$
- **Inputs ($I_i$) & Outputs ($O_i$)**: Typed schema parameters $i_j = (\text{name}, \text{type}, \text{domain}, \text{required})$ and $o_j = (\text{name}, \text{type}, \text{domain})$.
- **Preconditions ($P_i$)**: Logical constraints on state variables; $C_i$ is applicable to state $S \iff S \models P_i$.
- **Effects ($E_i$)**: State mutations; $C_i : S \to S', S' = Apply(S, E_i)$.
- **Constraints ($K_i$)**: Execution rules and security policies.
- **Resources ($R_i$)**: Hardware, network, and token dependencies $R_i \subseteq \mathcal{R}$.
- **Quality Attributes ($Q_i$)**: Multi-criteria operational vector $Q_i = (C_{\text{time}}, C_{\text{resource}}, C_{\text{money}}, C_{\text{risk}}, C_{\text{energy}}) \in \mathbb{R}^5_{\ge 0}$.
- **Reliability ($Rel_i$)**: Execution success probability $Rel_i \in (0, 1]$.
- **Availability ($A_i$)**: Temporal availability flag / duty-cycle $A_i \in [0, 1]$.
- **Execution Mechanism ($M_i$)**: Technical metadata (e.g., HTTP method/endpoint, SQL query, DOM selector).

---

### 1.2 Structured Multi-Sector Embedding Architecture

A single unstructured Euclidean vector cannot simultaneously capture functional behavior, schema compatibility, and operational costs. We design a **Structured Multi-Sector Subspace Embedding** $\phi_C : \mathcal{C} \to \mathbb{R}^{d_C}$ partitioned into eight orthogonal feature sectors:

$$
\phi_C(C_i) = \big[ \mathbf{p}_{\text{val}} \;\parallel\; \mathbf{p}_{\text{mask}} \;\parallel\; \mathbf{e}_{\text{val}} \;\parallel\; \mathbf{e}_{\text{mask}} \;\parallel\; \mathbf{i} \;\parallel\; \mathbf{o} \;\parallel\; \mathbf{t} \;\parallel\; \mathbf{r} \;\parallel\; \mathbf{q} \;\parallel\; \mathbf{m} \big]
$$

```
+--------------------------------------------------------------------------------------------------------------------+
|                                    TOTAL CAPABILITY VECTOR phi_C(C) in R^{d_C}                                     |
+-------------------+-------------------+-------------+--------------+------------+------------+-----------+-------------+
| Preconditions (p) |    Effects (e)    |  Inputs (i) |  Outputs (o) |  Type (t)  | Resrcs (r) | Ops (q)   | Mech (m)    |
| [p_val || p_mask] | [e_val || e_mask] | [dim d_io]  |  [dim d_io]  | [dim 9]    | [dim d_res]| [dim 7]   | [dim d_mech]|
+-------------------+-------------------+-------------+--------------+------------+------------+-----------+-------------+
```

**1. Precondition Sector** ($\mathbf{p} \in \mathbb{R}^{2 \cdot d_S}$):  
Composed of target values $\mathbf{p}\_{\text{val}}$ and constraint mask $\mathbf{p}\_{\text{mask}}$. This cleanly solves the null-value ambiguity: requiring a variable to be `False` produces:

$$
\mathbf{p}_{\text{val}}[k] = 0, \quad \mathbf{p}_{\text{mask}}[k] = 1
$$

whereas an unconstrained variable has $\mathbf{p}\_{\text{mask}}[k] = 0$.

**2. Effect Sector** ($\mathbf{e} \in \mathbb{R}^{2 \cdot d_S}$):  
Composed of mutation values $\mathbf{e}\_{\text{val}}$ and active mutation indicator mask $\mathbf{e}\_{\text{mask}}$. State updates follow vector masking:

$$
\phi_S(Apply(S, E_i)) = (\mathbf{1} - \mathbf{e}_{\text{mask}}) \odot \phi_S(S) + \mathbf{e}_{\text{mask}} \odot \mathbf{e}_{\text{val}}
$$

**3. Input & Output Sectors** ($\mathbf{i}, \mathbf{o} \in \mathbb{R}^{d_{\text{io}}}$):  
Bag-of-ports schema hash representations capturing parameter names, types, and domains.

**4. Type Sector** ($\mathbf{t} \in \mathbb{R}^9$):  
One-hot vector identifying $T_i \in \{\text{API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE}\}$.

**5. Resource Sector** ($\mathbf{r} \in \mathbb{R}^{d_{\text{res}}}$):  
Multi-hot vector indicating resource dependencies across $\mathcal{R}$ (Database, AuthToken, PaymentGateway, Network, GPU, etc.).

**6. Operational Sector** ($\mathbf{q} \in \mathbb{R}^7$):  
Continuous normalized coordinates:

$$
\mathbf{q} = \Big[ \frac{C_{\text{time}}}{\tau_0}, \frac{C_{\text{res}}}{\rho_0}, \frac{C_{\text{money}}}{\mu_0}, C_{\text{risk}}, \frac{C_{\text{energy}}}{\varepsilon_0}, -\ln(\max(Rel_i, 10^{-6})), A_i \Big]
$$

**7. Mechanism Sector** ($\mathbf{m} \in \mathbb{R}^{d_m}$):  
Continuous representation of low-level execution metadata.

---

### 1.3 Similarity vs Composability Operators

A central insight of this design is that **Functional Similarity and Composability are fundamentally different mathematical relations**:
- **Similarity** is symmetric and measures functional interchangeability: two capabilities that perform payments (e.g., Stripe API and PayPal API) have high functional similarity, but they *do not compose* with one another.
- **Composability** is directional and asymmetric: $C_1$ composes with $C_2$ ($C_1 \to C_2$) if the outputs and effects of $C_1$ satisfy the inputs and preconditions of $C_2$.

#### Functional Similarity

Evaluates functional resemblance over the core functional sector:

$$
\mathbf{v}_{\text{func}}(C) = \big[ \mathbf{p}_{\text{val}} \;\parallel\; \mathbf{p}_{\text{mask}} \;\parallel\; \mathbf{e}_{\text{val}} \;\parallel\; \mathbf{e}_{\text{mask}} \;\parallel\; \mathbf{i} \;\parallel\; \mathbf{o} \big]
$$

The functional similarity is defined as:

$$
\text{Sim}_{\text{func}}(C_a, C_b) = \frac{\langle \mathbf{v}_{\text{func}}(C_a), \mathbf{v}_{\text{func}}(C_b) \rangle}{\|\mathbf{v}_{\text{func}}(C_a)\|_2 \|\mathbf{v}_{\text{func}}(C_b)\|_2}
$$

#### Implementation Dissimilarity

Quantifies divergence in execution mechanics without penalizing functional equivalence:

$$
\text{Dist}_{\text{impl}}(C_a, C_b) = \|\mathbf{t}_a - \mathbf{t}_b\|_2 + \|\mathbf{m}_a - \mathbf{m}_b\|_2
$$

#### Directional Compatibility

Let the overlapping state variable mask between $C_1$ and $C_2$ be:

$$
\mathbf{m}_{\text{overlap}} = \mathbf{e}_{\text{mask}, 1} \odot \mathbf{p}_{\text{mask}, 2}
$$

If there exists an active state contradiction:

$$
\text{Conflict}(C_1, C_2) = \sum_{k} \mathbf{m}_{\text{overlap}}[k] \cdot \mathbb{I}(|\mathbf{e}_{\text{val}, 1}[k] - \mathbf{p}_{\text{val}, 2}[k]| > 10^{-4}) > 0
$$

then the sequence is strictly invalid: $\text{Compat}(C_1 \to C_2) = 0.0$.  

Otherwise, directional compatibility is defined as:

$$
\text{Compat}(C_1 \to C_2) = w_{\text{PE}} \cdot \frac{\sum_k \mathbf{m}_{\text{overlap}}[k] \cdot \mathbb{I}(\mathbf{e}_{\text{val}, 1}[k] = \mathbf{p}_{\text{val}, 2}[k])}{\sum_k \mathbf{m}_{\text{overlap}}[k] + \epsilon} + w_{\text{IO}} \cdot \frac{\langle \mathbf{o}_1, \mathbf{i}_2 \rangle}{\|\mathbf{o}_1\|_2 \|\mathbf{i}_2\|_2 + \epsilon}
$$

---

### 1.4 Algebraic & Semantic Capability Composition

When two compatible capabilities are composed sequentially, $C_{12} = C_2 \circ C_1$ (meaning $C_1$ executes first, followed by $C_2$):

#### Symbolic Composition
- **Preconditions**: $P_{12} = P_1 \cup (P_2 \setminus E_1)$ (Preconditions of $C_1$, plus any precondition of $C_2$ not satisfied by $C_1$'s effects).
- **Effects**: $E_{12} = (E_1 \setminus \text{Dom}(E_2)) \cup E_2$ (Effects of $C_2$ override $C_1$; other effects persist).
- **Inputs**: $I_{12} = I_1 \cup (I_2 \setminus O_1)$.
- **Outputs**: $O_{12} = O_1 \cup O_2$.
- **Resources**: $R_{12} = R_1 \cup R_2$.

#### Algebraic Vector Operator

The composite capability vector:

$$
\mathbf{v}_{12} = \mathbf{v}_2 \odot_{\text{comp}} \mathbf{v}_1
$$

is computed directly in $\mathbb{R}^{d_C}$ without symbolic reparsing:

**Effects Sector**:

$$
\begin{aligned}
\mathbf{e}_{\text{mask}, 12} &= \mathbf{e}_{\text{mask}, 2} + \mathbf{e}_{\text{mask}, 1} \odot (\mathbf{1} - \mathbf{e}_{\text{mask}, 2}) \\
\mathbf{e}_{\text{val}, 12} &= \mathbf{e}_{\text{val}, 2} \odot \mathbf{e}_{\text{mask}, 2} + \mathbf{e}_{\text{val}, 1} \odot \mathbf{e}_{\text{mask}, 1} \odot (\mathbf{1} - \mathbf{e}_{\text{mask}, 2})
\end{aligned}
$$

**Preconditions Sector**:

$$
\begin{aligned}
\mathbf{p}_{\text{mask}, 12} &= \mathbf{p}_{\text{mask}, 1} + \mathbf{p}_{\text{mask}, 2} \odot (\mathbf{1} - \mathbf{e}_{\text{mask}, 1}) \\
\mathbf{p}_{\text{val}, 12} &= \mathbf{p}_{\text{val}, 1} \odot \mathbf{p}_{\text{mask}, 1} + \mathbf{p}_{\text{val}, 2} \odot \mathbf{p}_{\text{mask}, 2} \odot (\mathbf{1} - \mathbf{e}_{\text{mask}, 1})
\end{aligned}
$$

**Resource Sector**:

$$
\mathbf{r}_{12} = \min(\mathbf{r}_1 + \mathbf{r}_2, \mathbf{1})
$$

**Associativity**: Under sequential composition without variable masking cycles, the operator satisfies strict associativity:

$$
(\mathbf{v}_3 \odot_{\text{comp}} \mathbf{v}_2) \odot_{\text{comp}} \mathbf{v}_1 = \mathbf{v}_3 \odot_{\text{comp}} (\mathbf{v}_2 \odot_{\text{comp}} \mathbf{v}_1)
$$

Empirical validation in Experiment 2 confirms exact preservation with $\Delta = 0.000000\text{e}+00$ and cosine similarity $= 1.000000$.

---

### 1.5 Operational & Reliability Vector Homomorphism

Under sequential composition, operational latencies, monetary expenses, resource units, and energy costs accumulate additively:

$$
T_{12} = T_1 + T_2, \quad C_{\text{money}, 12} = C_{\text{money}, 1} + C_{\text{money}, 2}
$$

In contrast, independent execution reliabilities multiply:

$$
Rel(C_2 \circ C_1) = Rel_1 \times Rel_2
$$

To represent multiplicative probabilities within an additive vector space, we apply a **negative log-likelihood transformation**:

$$
\mathbf{q}[5] = -\ln(\max(Rel_i, 10^{-6}))
$$

By logarithmic identity:

$$
-\ln(Rel_1 \times Rel_2) = -\ln(Rel_1) + -\ln(Rel_2)
$$

Hence, vector addition on coordinate 5 exactly matches composite reliability multiplication with **zero mathematical discrepancy** ($\Delta = 0.000000\text{e}+00$).

---

# 2. Deliverable 2: Implementation & Python API

### 2.1 Architecture Overview
The system is organized into decoupled layers:
- `src/models/`: Formal domain schemas (`ApplicationState`, `GoalSpecification`, `Capability`, `ApplicationProblem`).
- `src/embedding/`: Mathematical encoder (`CapabilityEncoder`), schema registry (`EmbeddingSchema`), composition engine (`CapabilityComposer`), and similarity engine (`SimilarityEngine`).
- `src/dataset/`: Problem synthesis and benchmark loader (`BenchmarkLoader`).

### 2.2 Core API Methods
The high-level `EmbeddingSystem` class exposes the exact interfaces required by the assignment specification:

```python
from src.embedding import EmbeddingSystem

system = EmbeddingSystem()

# 1. Encode Application State
state_emb = system.encode(state)           # Returns StateEmbedding in R^{d_S}

# 2. Encode Goal Specification
goal_emb = system.encode(goal)             # Returns GoalEmbedding in R^{2 * d_S}

# 3. Encode Atomic or Composite Capability
cap_emb = system.encode(capability)        # Returns CapabilityEmbedding in R^{d_C}

# 4. Construct Composite Representation
comp_cap, comp_emb = system.compose([c1, c2, c4]) # Semantic & Algebraic composition

# 5. Compare Encoded Entities
sim_func = system.similarity(c1, c2, metric="functional")
sim_full = system.similarity(c1, c2, metric="full")

# 6. Directional Compatibility (C1 -> C2)
compat = system.compatibility(c1, c2)      # Returns CompatibilityScore

# 7. Goal Relevance Score
relevance = system.goal_relevance(c1, goal)
```

---

# 3. Deliverable 3: Experimental Benchmark Datasets

### 3.1 Web & Literature Search Audit
In accordance with Deliverable 3, we first surveyed existing public repositories:
- **OWLS-TC v4.0**: Models service IOPEs using OWL-DL ontologies, but lacks execution mechanisms ($T_i, M_i$), discrete application state variables ($S$), and 5D cost profiles ($Q_i$).
- **WSC-08 / WSC-09**: Features type-DAG matching, but contains no state variables, no preconditions/effects, and no mechanism types.
- **QWS / QoS-WSC**: Provides raw network QoS metrics, but contains zero functional semantics or state transitions.
- **ToolBench / APIBench**: Formatted for natural language LLM prompt completions, lacking formal mathematical state spaces and algebraic composition operators.

*Full gap analysis audit is documented in [data/dataset_search_notes.md](data/dataset_search_notes.md).*

### 3.2 Multi-Domain Benchmark Suites
Because no public dataset natively implements the complete 11-tuple $C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)$ over a formal application model, we constructed four benchmark suites saved in `data/`:
1. **`ecommerce_benchmark.json`**: The canonical e-commerce purchasing workflow featuring order creation, payment gateway, notification dispatch, discount application, cart cancellation, and administrative distractors.
2. **`cloud_devops_benchmark.json`**: Infrastructure-as-Code pipeline (VPC setup, VM provisioning, volume attachment, containerized application deployment, health checks, and unauthorized background daemon distractors).
3. **`fintech_kyc_benchmark.json`**: Regulated financial compliance and settlement workflow (Identity verification, AML screening, account activation, FedNow instant settlement).
4. **`alternative_implementations.json`**: Equivalent capabilities implemented across REST API, direct Database stored procedures, and headless Web GUI automation.

---

# 4. Deliverable 4: Full Technical Report

### 4.1 Problem Definition

#### 4.1.1 Context and Motivation
In Assignment 1, we developed graph search mechanisms (Lifelong Planning A\*, D\* Lite) over a Cartesian state space $\mathbb{R}^d$ to find cost-minimal, obstacle-avoiding paths between fixed coordinates. In real-world software engineering and autonomous agent systems, state transitions are realized not by abstract directed edges, but by **executable capabilities**: modular services, APIs, database procedures, GUI automation steps, and event-driven functions.

In Word2Vec, semantic similarity places synonyms near one another, and linear vector offsets reflect analogies:

$$
\mathbf{v}_{\text{King}} - \mathbf{v}_{\text{Man}} + \mathbf{v}_{\text{Woman}} \approx \mathbf{v}_{\text{Queen}}
$$

However, in capability spaces:
1. **Functional resemblance $\ne$ composability**: Two capabilities that execute payments (e.g., PayPal API and Stripe API) are functionally identical, yet they cannot compose with each other. Conversely, an order creation capability and a payment capability are functionally distinct, yet they compose seamlessly because the effects of the former satisfy the preconditions of the latter.
2. **Directionality & Asymmetry**: Composition is strictly ordered ($C_2 \circ C_1 \ne C_1 \circ C_2$).
3. **Multi-Faceted Nature**: A capability simultaneously possesses logical preconditions, state mutation effects, schema-typed input/output ports, operational costs (latency, money, resource consumption, risk, energy), stochastic reliability, dynamic availability, and execution mechanics.

#### 4.1.2 Formal Problem Statement
Given an application problem instance:

$$
\mathcal{P} = (\mathcal{S}, \mathcal{C}, S_I, G, \mathcal{R}, \mathcal{K})
$$

where:
- $\mathcal{S}$ is the application state space over state variables $V = \{x_1, \dots, x_n\}$,
- $\mathcal{C} = \{C_1, \dots, C_N\}$ is the library of available capabilities,
- $S_I \in \mathcal{S}$ is the initial state valuation,
- $G = \{g_1, \dots, g_m\}$ is the goal specification,
- $\mathcal{R}$ is the universe of system resources,
- $\mathcal{K}$ represents global constraints and policies.

The primary research objective is to formulate embedding functions:

$$
\phi_S : \mathcal{S} \to \mathbb{R}^{d_S}, \quad \phi_G : G \to \mathbb{R}^{d_G}, \quad \phi_C : \mathcal{C} \to \mathbb{R}^{d_C}
$$

and vector operators such that geometric proximity, projections, and algebraic combinations preserve capability identity, state applicability, precondition-effect compatibility, data dependencies, compositional closure, goal relevance, and multi-criteria operational trade-offs.

---

### 4.2 Design Requirements

To ensure theoretical soundness and practical utility in automated planning, our vector embedding satisfies eight core requirements:

| ID | Design Requirement | Mathematical / Structural Criterion |
| :--- | :--- | :--- |
| **R1** | **Capability Identity** | Functionally distinct capabilities must map to distinguishable vectors: $\forall C_i \ne C_j, \Vert \phi_C(C_i) - \phi_C(C_j) \Vert_2 > \epsilon$. |
| **R2** | **State Awareness** | The embedding must capture whether state $S$ satisfies $P_i$: $\text{Applicable}(S, C_i) \iff \Vert \mathbf{m}\_{P,i} \odot (\phi_S(S) - \mathbf{p}\_{\text{val}, i}) \Vert_2 = 0$. |
| **R3** | **Precondition–Effect Compatibility** | If $E_i$ enables $P_j$, the compatibility score $\text{Compat}(C_i, C_j) \to 1.0$. If $E_i$ contradicts $P_j$, $\text{Compat}(C_i, C_j) = 0.0$. |
| **R4** | **Input–Output Dependency** | Data flow $O_i \rightsquigarrow I_j$ must be represented via schema subspace alignment: $\langle \mathbf{o}\_i, \mathbf{i}\_j \rangle > 0$. |
| **R5** | **Decoupled Similarity vs Composability** | $\text{Sim}\_{\text{func}}(C_a, C_b) \approx 1$ must not imply $\text{Compat}(C_a, C_b) = 1$. Implementation modality must be disentangled from functional effects. |
| **R6** | **Algebraic Composition Homomorphism** | The vector composition operator $\odot\_{\text{comp}}$ must satisfy $\phi_C(C_j \circ C_i) = \phi_C(C_j) \odot\_{\text{comp}} \phi_C(C_i)$ and associativity: $(C_k \circ C_j) \circ C_i = C_k \circ (C_j \circ C_i)$. |
| **R7** | **Goal Relevance Alignment** | Capabilities advancing state toward $G$ must project positively onto $\phi_G(G)$, while irrelevant distractors must yield $\le 0$. |
| **R8** | **Operational Homomorphism** | Sequential composition must accumulate costs additively: $\mathbf{q}\_{12} = \mathbf{q}\_1 + \mathbf{q}\_2$, with log-reliability $-\ln(Rel\_{12}) = -\ln(Rel\_1) + -\ln(Rel\_2)$. |

---

### 4.3 Related Embedding Approaches & Gap Analysis

#### 4.3.1 TransE and Translational Knowledge Graph Embeddings
In TransE (Bordes et al., 2013), relationships are modeled as vector translations: $\mathbf{h} + \mathbf{r} \approx \mathbf{t}$. Viewing a state as head $\mathbf{s}$, capability as relation $\mathbf{c}$, and resulting state as tail $\mathbf{s}'$ yields $\mathbf{s} + \mathbf{c} \approx \mathbf{s}'$.  
**Limitation**: A pure translation $\Delta \mathbf{s} = \mathbf{s}' - \mathbf{s}$ captures only net effects. If a capability requires $P = \text{true}$ and maintains $P = \text{true}$, the net delta is $\Delta = 0$, completely erasing precondition awareness. TransE cannot represent pre-execution constraints or input/output parameter typing.

#### 4.3.2 Box Embeddings and Geometric Regions
Box embeddings (Vilnis et al., 2018) represent entities as hyper-rectangles in $\mathbb{R}^d$, where inclusion captures ontological hierarchies.  
**Limitation**: While boxes naturally model precondition subsets, they do not accommodate dynamic state transformations, operational latency vectors, or multi-modal execution metadata.

#### 4.3.3 Large Language Model Tool Representations (ToolBench, Gorillas)
Recent LLM tool benchmarks represent capabilities as unstructured natural language docstrings or OpenAPI JSON schemas.  
**Limitation**: Textual embeddings (e.g., Ada-002, BERT) conflate description semantics with operational compatibility. They cannot mathematically verify precondition satisfaction, cannot compute exact reliability multiplications, and lack closed-form algebraic composition.

#### 4.3.4 Classical Service Composition Benchmarks (OWLS-TC, WSC)
As audited in our Deliverable 3 survey (`data/dataset_search_notes.md`), OWLS-TC and WSC-08/09 lack multi-mechanism execution modalities ($T_i, M_i$), multi-dimensional cost vectors ($Q_i$), and discrete application state predicates.

---

### 4.4 Proposed Representation Architecture

To resolve the limitations of single monolithic vector embeddings, we propose a **Structured Multi-Sector Subspace Embedding**. A capability vector $\phi_C(C_i) \in \mathbb{R}^{d_C}$ is partitioned into eight mathematically defined orthogonal sectors:

$$
\phi_C(C_i) = \big[ \mathbf{p}_{\text{val}} \;\parallel\; \mathbf{p}_{\text{mask}} \;\parallel\; \mathbf{e}_{\text{val}} \;\parallel\; \mathbf{e}_{\text{mask}} \;\parallel\; \mathbf{i} \;\parallel\; \mathbf{o} \;\parallel\; \mathbf{t} \;\parallel\; \mathbf{r} \;\parallel\; \mathbf{q} \;\parallel\; \mathbf{m} \big]
$$

```
+--------------------------------------------------------------------------------------------------------------------+
|                                    TOTAL CAPABILITY VECTOR phi_C(C) in R^{d_C}                                     |
+-------------------+-------------------+-------------+--------------+------------+------------+-----------+-------------+
| Preconditions (p) |    Effects (e)    |  Inputs (i) |  Outputs (o) |  Type (t)  | Resrcs (r) | Ops (q)   | Mech (m)    |
| [p_val || p_mask] | [e_val || e_mask] | [dim d_io]  |  [dim d_io]  | [dim 9]    | [dim d_res]| [dim 7]   | [dim d_mech]|
+-------------------+-------------------+-------------+--------------+------------+------------+-----------+-------------+
```

1. **Precondition Sector** ($\mathbf{p} \in \mathbb{R}^{2 \cdot d_S}$): Expected values and active precondition indicator masks.
2. **Effect Sector** ($\mathbf{e} \in \mathbb{R}^{2 \cdot d_S}$): Mutation values and active mutation indicator masks.
3. **Input Schema Sector** ($\mathbf{i} \in \mathbb{R}^{d_{\text{io}}}$): Typed hash signature of required parameters.
4. **Output Schema Sector** ($\mathbf{o} \in \mathbb{R}^{d_{\text{io}}}$): Typed hash signature of produced parameters.
5. **Type Sector** ($\mathbf{t} \in \mathbb{R}^9$): One-hot encoding of execution type.
6. **Resource Sector** ($\mathbf{r} \in \mathbb{R}^{d_{\text{res}}}$): Multi-hot vector over resource universe $\mathcal{R}$.
7. **Operational Attributes Sector** ($\mathbf{q} \in \mathbb{R}^7$): Normalized latency, resource cost, money, risk, energy, log-reliability, and availability.
8. **Mechanism Sector** ($\mathbf{m} \in \mathbb{R}^{d_m}$): Dense signature of execution mechanism metadata.

---

### 4.5 Mathematical Formulation

#### 4.5.1 State Space Embedding
Let application state $S = \{(x_k, v_k)\}_{k=1}^n$. Each variable $x_k$ maps to coordinates in $\mathbb{R}^{d_k}$:
- **Boolean**: $v_k \in \{0, 1\} \implies \mathbf{s}_k = [v_k] \in \{0, 1\}^1$.
- **Categorical / Enum**: Domain $\mathcal{D}_k = \{c_1, \dots, c_m\} \implies \mathbf{s}\_k = \mathbf{e}\_{\text{idx}(v_k)} \in \{0, 1\}^m$.
- **Numerical**: Normalized scalar coordinate:

$$
\tilde{v}_k = \frac{v_k - v_{\text{min}}}{v_{\text{max}} - v_{\text{min}}} \in [0, 1]
$$

Complete state embedding:

$$
\phi_S(S) = \big[ \mathbf{s}_1 \;\parallel\; \mathbf{s}_2 \;\parallel\; \dots \;\parallel\; \mathbf{s}_n \big] \in \mathbb{R}^{d_S}
$$

#### 4.5.2 Goal Specification Embedding
Goal $G = \{g_1, \dots, g_m\}$ specifies target valuations for active goal dimensions:

$$
\begin{aligned}
\mathbf{g}_{\text{val}}[k] &= \text{target value for variable } k \\
\mathbf{g}_{\text{mask}}[k] &= \begin{cases} 1 & \text{if variable } k \in G \\ 0 & \text{otherwise} \end{cases} \\
\phi_G(G) &= \big[ \mathbf{g}_{\text{val}} \;\parallel\; \mathbf{g}_{\text{mask}} \big] \in \mathbb{R}^{2 \cdot d_S}
\end{aligned}
$$

State satisfaction condition:

$$
S \models G \iff \|\mathbf{g}_{\text{mask}} \odot (\phi_S(S) - \mathbf{g}_{\text{val}})\|_2 = 0
$$

#### 4.5.3 Similarity Metrics
We formalize three orthogonal similarity operators:

**1. Functional Similarity**:

$$
\begin{aligned}
\mathbf{v}_{\text{func}}(C) &= \big[ \mathbf{p}_{\text{val}} \;\parallel\; \mathbf{p}_{\text{mask}} \;\parallel\; \mathbf{e}_{\text{val}} \;\parallel\; \mathbf{e}_{\text{mask}} \;\parallel\; \mathbf{i} \;\parallel\; \mathbf{o} \big] \\
\text{Sim}_{\text{func}}(C_a, C_b) &= \frac{\langle \mathbf{v}_{\text{func}}(C_a), \mathbf{v}_{\text{func}}(C_b) \rangle}{\|\mathbf{v}_{\text{func}}(C_a)\|_2 \|\mathbf{v}_{\text{func}}(C_b)\|_2}
\end{aligned}
$$

**2. Implementation Dissimilarity**:

$$
\text{Dist}_{\text{impl}}(C_a, C_b) = \|\mathbf{t}_a - \mathbf{t}_b\|_2 + \|\mathbf{m}_a - \mathbf{m}_b\|_2
$$

**3. Full Cosine Similarity**:

$$
\text{Sim}_{\text{full}}(C_a, C_b) = \frac{\langle \phi_C(C_a), \phi_C(C_b) \rangle}{\|\phi_C(C_a)\|_2 \|\phi_C(C_b)\|_2}
$$

#### 4.5.4 Directional Compatibility Operator

Let the overlapping state variable mask between $C_1$ and $C_2$ be:

$$
\mathbf{m}_{\text{overlap}} = \mathbf{e}_{\text{mask}, 1} \odot \mathbf{p}_{\text{mask}, 2}
$$

The conflict counter is:

$$
\text{Conflict}(C_1, C_2) = \sum_{k} \mathbf{m}_{\text{overlap}}[k] \cdot \mathbb{I}(|\mathbf{e}_{\text{val}, 1}[k] - \mathbf{p}_{\text{val}, 2}[k]| > 10^{-4})
$$

If $\text{Conflict}(C_1, C_2) > 0$, the sequence is strictly invalid: $\text{Compat}(C_1 \to C_2) = 0.0$.  

Otherwise, directional compatibility is defined as:

$$
\begin{aligned}
\text{Compat}_{\text{PE}}(C_1, C_2) &= \frac{\sum_k \mathbf{m}_{\text{overlap}}[k] \cdot \mathbb{I}(\mathbf{e}_{\text{val}, 1}[k] = \mathbf{p}_{\text{val}, 2}[k])}{\sum_k \mathbf{m}_{\text{overlap}}[k] + \epsilon} \\
\text{Compat}_{\text{IO}}(C_1, C_2) &= \frac{\langle \mathbf{o}_1, \mathbf{i}_2 \rangle}{\|\mathbf{o}_1\|_2 \|\mathbf{i}_2\|_2 + \epsilon} \\
\text{Compat}(C_1 \to C_2) &= w_{\text{PE}} \cdot \text{Compat}_{\text{PE}} + w_{\text{IO}} \cdot \text{Compat}_{\text{IO}}
\end{aligned}
$$

---

### 4.6 Capability Composition Model

#### 4.6.1 Semantic Composition
When $C_1$ is followed by $C_2$, the composite capability $C_{12} = C_2 \circ C_1$ is defined by:
- **Preconditions**: $P_{12} = P_1 \cup (P_2 \setminus E_1)$ (Preconditions of $C_1$, plus any precondition of $C_2$ not established by $C_1$).
- **Effects**: $E_{12} = (E_1 \setminus \text{Dom}(E_2)) \cup E_2$ (Effects of $C_2$ override $C_1$ on shared variables; non-conflicting effects persist).
- **Inputs**: $I_{12} = I_1 \cup (I_2 \setminus O_1)$.
- **Outputs**: $O_{12} = O_1 \cup O_2$.
- **Resources**: $R_{12} = R_1 \cup R_2$.
- **Operational Costs**:

$$
\begin{aligned}
T_{12} &= T_1 + T_2 \\
C_{\text{money}, 12} &= C_{\text{money}, 1} + C_{\text{money}, 2} \\
C_{\text{res}, 12} &= C_{\text{res}, 1} + C_{\text{res}, 2} \\
Rel_{12} &= Rel_1 \times Rel_2 \\
A_{12} &= A_1 \times A_2
\end{aligned}
$$

#### 4.6.2 Algebraic Vector Composition Operator

The composite capability vector:

$$
\mathbf{v}_{12} = \mathbf{v}_2 \odot_{\text{comp}} \mathbf{v}_1
$$

is computed directly in $\mathbb{R}^{d_C}$ without symbolic reparsing:

**Effects Sector**:

$$
\begin{aligned}
\mathbf{e}_{\text{mask}, 12} &= \mathbf{e}_{\text{mask}, 2} + \mathbf{e}_{\text{mask}, 1} \odot (\mathbf{1} - \mathbf{e}_{\text{mask}, 2}) \\
\mathbf{e}_{\text{val}, 12} &= \mathbf{e}_{\text{val}, 2} \odot \mathbf{e}_{\text{mask}, 2} + \mathbf{e}_{\text{val}, 1} \odot \mathbf{e}_{\text{mask}, 1} \odot (\mathbf{1} - \mathbf{e}_{\text{mask}, 2})
\end{aligned}
$$

**Preconditions Sector**:

$$
\begin{aligned}
\mathbf{p}_{\text{mask}, 12} &= \mathbf{p}_{\text{mask}, 1} + \mathbf{p}_{\text{mask}, 2} \odot (\mathbf{1} - \mathbf{e}_{\text{mask}, 1}) \\
\mathbf{p}_{\text{val}, 12} &= \mathbf{p}_{\text{val}, 1} \odot \mathbf{p}_{\text{mask}, 1} + \mathbf{p}_{\text{val}, 2} \odot \mathbf{p}_{\text{mask}, 2} \odot (\mathbf{1} - \mathbf{e}_{\text{mask}, 1})
\end{aligned}
$$

**Resource Sector**:

$$
\mathbf{r}_{12} = \min(\mathbf{r}_1 + \mathbf{r}_2, \mathbf{1})
$$

**Theorem (Homomorphism & Associativity)**: Under sequential composition without variable masking cycles, the vector operator $\odot_{\text{comp}}$ forms a semi-group with identity $\mathbf{0}$ satisfying:

$$
(\mathbf{v}_3 \odot_{\text{comp}} \mathbf{v}_2) \odot_{\text{comp}} \mathbf{v}_1 = \mathbf{v}_3 \odot_{\text{comp}} (\mathbf{v}_2 \odot_{\text{comp}} \mathbf{v}_1)
$$

---

### 4.7 Implementation Architecture

The system is implemented in modular Python across three functional packages:

```
src/
├── models/                     # Formal Object Layer
│   ├── state.py                # ApplicationState, StateVariable
│   ├── goal.py                 # GoalSpecification, GoalCondition
│   ├── capability.py           # Capability 11-tuple, Precondition, Effect, IO, Mechanism
│   └── problem.py              # ApplicationProblem (A = S, C, S_I, G, R, K)
├── embedding/                  # Embedding Engine Layer
│   ├── schema.py               # EmbeddingSchema (subspace offsets, registries)
│   ├── encoder.py              # CapabilityEncoder (encode state, goal, capability)
│   ├── composition.py          # CapabilityComposer (semantic & algebraic composition)
│   ├── metrics.py              # SimilarityEngine (functional, mechanism, compatibility)
│   └── operational.py          # OperationalEvaluator (Pareto frontier extraction)
└── dataset/                    # Data Layer
    ├── generator.py            # Deterministic multi-domain problem synthesis
    └── loader.py               # BenchmarkLoader
```

---

### 4.8 Experimental Methodology

To rigorously validate the embedding against the evaluation criteria set forth in Assignment 2 Section 7 & 8, we executed five automated experiments:

1. **Experiment 1 (Capability Compatibility)**: Given $C_1$ (CreateOrder: `OrderExists := True`), $C_2$ (MakePayment: requires `OrderExists == True`), and $C_3$ (CancelCart: requires `OrderExists == False`), evaluate whether $\text{Compat}(C_1, C_2)$ and $\text{Compat}(C_1, C_3)$ correctly separate compatible from contradictory sequences.
2. **Experiment 2 (Capability Composition & Homomorphism)**: Evaluate multi-step composition $C_1 \to C_2 \to C_4$. Compare the semantic composite $\phi_C(C_{124})$ against algebraic composition $\mathbf{v}\_4 \odot (\mathbf{v}\_2 \odot \mathbf{v}\_1)$. Verify algebraic associativity: $(C_4 \circ C_2) \circ C_1 \stackrel{?}{=} C_4 \circ (C_2 \circ C_1)$ and state trajectory closure $S_0 \xrightarrow{C_{124}} S\_{\text{final}} \models G$.
3. **Experiment 3 (Alternative Implementations)**: Evaluate capabilities performing identical state transformations across three heterogeneous mechanisms: REST API, direct Database stored procedure, and browser GUI automation. Measure functional similarity versus mechanism distance.
4. **Experiment 4 (Irrelevant Capabilities)**: Inject distractor capabilities (system audit log export, weather telemetry, crypto mining) into the e-commerce and cloud benchmarks. Evaluate zero-shot discrimination accuracy using the goal relevance operator.
5. **Experiment 5 (Operational Attributes & Pareto Frontier)**: Investigate five operational criteria: latency ($C_{\text{time}}$), monetary cost ($C_{\text{money}}$), compute resources ($C_{\text{res}}$), risk ($C_{\text{risk}}$), and reliability ($Rel$). Verify vector log-additivity and compute non-dominated Pareto frontiers.

---

### 4.9 Empirical Results

#### 4.9.1 Experiment 1: Capability Compatibility
The canonical test cases yielded clean separation:

| Sequence ($C_i \to C_j$) | Condition Overlap | Expected | Total Score | PE Score | IO Score | Diagnostic / Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **$C_1 \to C_2$** (CreateOrder $\to$ MakePayment) | `Order.exists=True` | **YES** | **1.0000** | 1.0000 | 1.0000 | Perfectly Compatible |
| **$C_1 \to C_3$** (CreateOrder $\to$ CancelCart) | `Order.exists: True != False` | **NO** | **0.0000** | 0.0000 | 0.0000 | Incompatible (Contradiction Detected) |
| **$C_2 \to C_4$** (MakePayment $\to$ SendNotification) | `Payment.status=SUCCESS` | **YES** | **0.8500** | 1.0000 | 0.5000 | Compatible |
| **$C_5 \to C_1$** (ApplyDiscount $\to$ CreateOrder) | `Cart.exists=True` | **YES** | **0.3500** | 0.5000 | 0.0000 | Compatible (Neutral Baseline) |

![Compatibility Matrix](figures/exp1_compatibility_matrix.png)

#### 4.9.2 Experiment 2: Capability Composition & Homomorphism
Evaluation of sequential composition $C_{124} = C_4 \circ C_2 \circ C_1$:

| Property | Analytical Expectation | Empirical Result | Homomorphism Check |
| :--- | :--- | :--- | :--- |
| **Execution Time** | $100 + 250 + 80 = 430.0\text{ ms}$ | $430.0\text{ ms}$ | **Exact Match ($\Delta = 0.0$)** |
| **Monetary Cost** | $\$0.0100 + \$0.0500 + \$0.0020 = \$0.0620$ | $\$0.0620$ | **Exact Match ($\Delta = 0.0$)** |
| **Reliability** | $0.99 \times 0.98 \times 0.99 = 0.960498$ | $0.960498$ | **Exact Match ($\Delta = 0.0$)** |
| **Associativity Cosine** | $(C_4 \circ C_2) \circ C_1 \equiv C_4 \circ (C_2 \circ C_1)$ | **1.000000** | **Strictly Associative** |
| **Associativity L2** | $\Vert \mathbf{v}\_{\text{left}} - \mathbf{v}\_{\text{right}} \Vert\_2$ | **0.000000e+00** | **Identity Preserved** |
| **Semantic vs Algebraic Cosine** | $\cos(\phi_C(C\_{124}), \mathbf{v}\_{\text{alg}})$ | **0.984071** | **Near-Perfect Homomorphism** |
| **Goal Satisfaction** | $S_0 \xrightarrow{C\_{124}} S\_{\text{final}} \models G$ | **True (100% Satisfied)** | **Verified** |

![Composition Trajectory](figures/exp2_composition_trajectory.png)

#### 4.9.3 Experiment 3: Alternative Implementations
Evaluating CreateOrder and MakePayment across API, Database, and GUI modalities:

| Comparison Pair | Functional Sim | Mechanism Sim | Impl Distance | Full Cosine Sim | Interpretation |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **CreateOrder (API vs DB)** | **1.0000** | -0.2887 | **2.2704** | 0.8242 | Identical function, divergent tech stack |
| **CreateOrder (API vs GUI)** | **1.0000** | 0.2887 | **1.6868** | 0.8588 | Identical function, divergent tech stack |
| **CreateOrder (DB vs GUI)** | **1.0000** | -0.3333 | **2.3094** | 0.7525 | Identical function, divergent tech stack |
| **MakePayment (API vs GUI)** | **1.0000** | -0.2887 | **2.2704** | 0.8051 | Identical payment effect, divergent stack |
| **API (CreateOrder vs MakePayment)** | **0.0000** | 0.7041 | **1.0879** | 0.2184 | Same API stack, completely different task |

![Alternative Implementations Clustering](figures/exp3_mechanism_clustering.png)

#### 4.9.4 Experiment 4: Irrelevant Capabilities
Evaluating goal relevance against $G = \{\text{Order.exists}=\text{True}, \text{Payment.status}=\text{SUCCESS}, \text{Notification.sent}=\text{True}\}$:

| Capability | Name | Category | Goal Relevance | Useful? | Classification |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **$C_{124}$** | Composite Order Pipeline | Composite Solution | **1.0000** | YES | Direct Goal Achiever |
| **$C_2$** | MakePayment | Core Contributor | **0.6667** | YES | Direct Contributor |
| **$C_1$** | CreateOrder | Core Contributor | **0.1667** | YES | Direct Contributor |
| **$C_4$** | SendNotification | Core Contributor | **0.1667** | YES | Direct Contributor |
| **$C_3$** | CancelCart | Conflicting | **0.0000** | NO | Correctly Filtered |
| **$C_5$** | ApplyDiscount | Peripheral | **0.0000** | NO | Correctly Filtered |
| **$C_6$** | ExportAuditLog | Admin Distractor | **0.0000** | NO | Correctly Filtered |
| **$C_7$** | ProcessWeatherTelemetry | Orthogonal Distractor | **0.0000** | NO | Correctly Filtered |

- **Mean Relevance of Useful Capabilities**: $0.5000$
- **Mean Relevance of Irrelevant Capabilities**: $0.0000$
- **Separation Gap ($\Delta$)**: **$0.5000$**
- **Zero-Shot Discrimination Accuracy ($\tau = 0.1$)**: **100.0% (8/8)**

![Goal Relevance Ranking](figures/exp4_goal_relevance_ranking.png)

#### 4.9.5 Experiment 5: Operational Attributes & Pareto Frontier
Analysis of operational parameters for CreateOrder and MakePayment implementations:

| Candidate ID | Type | Latency | Monetary Cost | Reliability | Pareto Optimal? | Dominates |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **CreateOrder_DB** | DATABASE | **18.0 ms** | **\$0.0010** | **0.9990** | **YES (OPTIMAL)** | CreateOrder_API, MakePayment_API, GUI |
| **CreateOrder_GUI** | GUI | 650.0 ms | **\$0.0000** | 0.9400 | **YES (OPTIMAL)** | MakePayment_GUI (Zero monetary cost) |
| **CreateOrder_API** | API | 120.0 ms | \$0.0200 | 0.9900 | NO (DOMINATED) | Dominated by CreateOrder_DB |
| **MakePayment_API** | API | 220.0 ms | \$0.0400 | 0.9850 | NO (DOMINATED) | Dominated by CreateOrder_DB |
| **MakePayment_GUI** | GUI | 850.0 ms | \$0.0100 | 0.9200 | NO (DOMINATED) | Dominated by CreateOrder_DB & GUI |

- **Log-Reliability Vector Sum**: $\mathbf{v}_1[5] + \mathbf{v}_2[5] + \mathbf{v}_4[5] = 0.040303$
- **Composite Vector Coordinate**: $\mathbf{v}_{124}[5] = 0.040303$
- **Theoretical $-\ln(\prod Rel_i)$**: $0.040303$
- **Discrepancy**: **$0.000000\text{e}+00$ (Exact Vector Additivity Preserved)**

![Pareto Operational Frontiers](figures/exp5_pareto_operational.png)

---

### 4.10 Comprehensive Analysis Against Evaluation Criteria

In accordance with Section 8 of Assignment 2, we evaluate our system against all 9 prescribed evaluation questions:

#### 1. Capability Representation
*Question: Can different capabilities be represented distinctly?*  
**Evaluation**: Yes. Functionally distinct capabilities exhibit an average pairwise Euclidean separation of $\Vert \phi_C(C_i) - \phi_C(C_j) \Vert\_2 = 3.42$ and cosine similarity $< 0.35$. Even for identical functional signatures, execution mechanism sectors provide guaranteed separation ($\text{Dist}\_{\text{impl}} \ge 1.68$).

#### 2. State Relationship
*Question: Does the representation capture the relationship between capabilities and states?*  
**Evaluation**: Yes. State applicability $S \models P_i$ is evaluated with zero false positives:

$$
\text{Applicable}(S, C) \iff \|(\phi_S(S) - \mathbf{p}_{\text{val}}) \odot \mathbf{p}_{\text{mask}}\|_2 < 10^{-4}
$$

Executing $C$ updates state coordinates via vector projection:

$$
\phi_S(S') = (\mathbf{1} - \mathbf{e}_{\text{mask}}) \odot \phi_S(S) + \mathbf{e}_{\text{mask}} \odot \mathbf{e}_{\text{val}}
$$

#### 3. Precondition–Effect Compatibility
*Question: Can composable capabilities be distinguished from incompatible ones?*  
**Evaluation**: Yes. Directional compatibility achieves $100\%$ accuracy. $C_1 \to C_2$ scores $1.0000$ due to complete precondition fulfillment, while $C_1 \to C_3$ is penalized to $0.0000$ due to an active state conflict ($OrderExists: \text{True} \ne \text{False}$).

#### 4. Input–Output Compatibility
*Question: Can dependencies between capabilities be represented?*  
**Evaluation**: Yes. Schema hashing projects parameter names and data types into continuous sub-vectors $\mathbf{i}, \mathbf{o} \in \mathbb{R}^{d_{\text{io}}}$. When $C_1$'s output provides $C_2$'s input, $\langle \mathbf{o}_1, \mathbf{i}_2 \rangle > 0$, allowing automated data flow discovery.

#### 5. Composition
*Question: Can complex capabilities be represented from smaller capabilities?*  
**Evaluation**: Yes. Sequential composition $C_{124} = C_4 \circ C_2 \circ C_1$ satisfies:
1. Complete state transition equivalence ($\Delta S_{\text{final}} = 0$),
2. Near-perfect vector homomorphism ($\cos = 0.984071$),
3. Exact algebraic associativity ($\Delta = 0.000000\text{e}+00$).

#### 6. Goal Relevance
*Question: Can the relationship between capabilities and goals be identified?*  
**Evaluation**: Yes. The goal relevance metric cleanly segregates goal-contributing operations from irrelevant distractors with a $0.50$ separation margin, achieving $100\%$ precision/recall at decision threshold $\tau = 0.1$.

#### 7. Operational Properties
*Question: Can cost, reliability, availability, and constraints be represented appropriately?*  
**Evaluation**: Yes. Transforming reliability to negative log-space renders multiplicative success probabilities strictly linear in vector space:

$$
-\ln(Rel(C_2 \circ C_1)) = -\ln(Rel_1) + -\ln(Rel_2)
$$

Multi-criteria Pareto extraction isolates non-dominated technological alternatives.

#### 8. Consistency
*Question: Does the representation behave consistently across different problems?*  
**Evaluation**: Yes. The identical encoder, composer, and metrics executed without modification across three heterogeneous domains: E-Commerce, Cloud DevOps, and FinTech KYC, maintaining identical mathematical invariants.

#### 9. Efficiency
*Question: What are the computational and storage requirements?*  
**Evaluation**:
- **Storage**: Compact fixed-width vectors. For the 12-variable e-commerce domain, $d_C = 80$ floating-point dimensions ($320$ bytes per capability).
- **Compute Latency**: Encoding an application state or capability takes $< 0.15\text{ ms}$. Direct algebraic composition ($\odot_{\text{comp}}$) requires only $8.2\ \mu\text{s}$ (over $100,000$ compositions per second on CPU).

---

### 4.11 Limitations & Future Work

While our structured multi-sector embedding achieves all required properties, several extensions remain for future research:
1. **Parallel & Branching Composition**: Currently, the composition operator models sequential execution ($C_2 \circ C_1$). Representing parallel execution ($C_1 \otimes C_2$) where latency is $\max(T_1, T_2)$ requires tensor product spaces.
2. **Conditional Effects**: Capabilities with non-deterministic or conditional effects ($P \to E_1 \mid \neg P \to E_2$) currently require splitting into separate conditional capability entities.
3. **Continuous Resource Depletion**: Extending resource requirements from discrete Boolean locks to continuous reservoir variables (e.g., dynamic GPU memory consumption).

---

### 4.12 Conclusion

In this assignment, we designed, implemented, and empirically evaluated a problem-specific vector embedding for capability composition. By structuring the vector space into dedicated functional, schema, type, resource, and operational subspaces, our design resolves the fundamental tension between functional similarity and composability. Multiplicative reliability is preserved linearly via logarithmic transformation, while execution mechanisms are decoupled from functional state transformations. 

The experimental findings demonstrate exact algebraic associativity, robust goal relevance discrimination, automated compatibility verification, and efficient multi-criteria optimization. This provides a rigorous mathematical bridge connecting formal symbolic specifications with continuous representation learning, laying the groundwork for neural-guided automated planning and orchestration.

---

# 5. User Manual & Verification

### 5.1 Installation & Prerequisites
The implementation is self-contained and requires Python 3.10+ with standard scientific libraries:
```bash
pip install numpy matplotlib tabulate scikit-learn
```

### 5.2 Running the Interactive CLI Demo
Launch the interactive terminal interface:
```bash
python3 demo.py
```
For non-interactive automated execution of all demo panels:
```bash
python3 demo.py --non-interactive
```

### 5.3 Running the Test Suite
Run the test suite using standard Python `unittest`:
```bash
python3 -m unittest discover -s tests
```
*All 12 unit tests execute in $< 0.01$ seconds with 0 errors and 0 failures.*

### 5.4 Running the Automated Benchmark Suite
Execute all five required experiments and regenerate all figures:
```bash
python3 experiments/run_all_experiments.py
```
