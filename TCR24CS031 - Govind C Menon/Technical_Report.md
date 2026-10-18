# Deliverable 4: Technical Report

**Course:** PCCST503 – Machine Learning  
**Assignment 2:** Design of a Vector Embedding for Capability Composition – Formal Representations, Compatibility, and Compositional Reasoning  
**Application domain of the implementation:** E-commerce order fulfilment (terminal/CLI-based Python project)

> **Source of the numbers.** Every numerical value in this report was taken from the final project files (`results/experiment_results.csv`, `results/metrics_summary.csv`, the plots in `plots/`) and cross-checked against a fresh run of `python main.py`. All scores are deterministic and reproduced exactly on re-execution; only the wall-clock latencies in the efficiency measurements vary between runs (see Sections 9.7 and 11). Where an older `REPORT_CONTENT.md` disagreed with the current implementation, the current implementation and result files were used.

---

## 1. Problem Definition

### 1.1 Motivation

Modern software systems are assembled from many executable units: REST endpoints, database operations, GUI actions, message-queue publishers, file generators and computations. To automate the discovery, matching and chaining of such units, a program must be able to answer questions such as:

* *Which capabilities can run in the current application state?*
* *Can the result of capability $C_i$ be consumed by capability $C_j$?*
* *Which capabilities contribute to a stated goal, and which are irrelevant?*
* *Are two differently implemented capabilities functionally interchangeable, and how do they differ in cost, reliability and risk?*

A natural idea is to place capabilities in a vector space so that geometric operations (dot products, projections, distances) can answer these questions quickly and uniformly. The difficulty is that the questions above concern **formal contracts** (what must hold before execution, what holds afterwards, what data flows in and out), not the resemblance of descriptions.

### 1.2 Why ordinary semantic similarity is not sufficient

Ordinary semantic similarity (for example, cosine similarity between text embeddings of capability descriptions, or between generic feature vectors) measures *resemblance*. Composability, however, is a *directed, logical* relationship: $C_i \to C_j$ is valid only if the state produced by $C_i$ satisfies the preconditions of $C_j$ and the data produced by $C_i$ can supply the inputs of $C_j$. Resemblance is symmetric and says nothing about this relationship. Two facts measured in the implemented system illustrate the gap:

* `CreateOrder` and `CancelCart` have a **high** cosine similarity (**0.6164**) but `CreateOrder → CancelCart` is **incompatible**, because `CreateOrder` sets `Order.exists := True` and `Cart.locked := True` while `CancelCart` requires `Order.exists == False` and `Cart.locked == False`.
* `CreateOrder` and `MakePayment` have a **very low** cosine similarity (**0.0754**) but `CreateOrder → MakePayment` is **compatible** (compatibility score 0.6833), because the effect of the first capability establishes preconditions of the second and its output (`order_id`) is an input of the second.

A representation that is used for capability composition therefore has to expose precondition, effect, input and output structure explicitly, and compatibility must be computed by a function that respects that structure rather than by similarity alone.

### 1.3 Definitions used in this report

| Term | Definition (as implemented) |
|-------------|---------------------------------------------------------------------------------------|
| **Application state** | A set of variable/value pairs $S=\{(x_1,v_1),\dots,(x_n,v_n)\}$, e.g. `Cart.exists = True`, `Order.status = "CREATED"`. Implemented by the `State` class; the initial state of the e-commerce application has 14 variables. |
| **Goal** | A set of desired state conditions $G=\{g_1,\dots,g_m\}$, each of the form *variable operator value*. The implemented goal has three conditions: `Order.exists == True`, `Payment.status == SUCCESS`, `Notification.sent == True`. Implemented by the `Goal` class. |
| **Capability** | An executable unit specified by a formal tuple of type, inputs, outputs, preconditions, effects, constraints, resources, quality attributes, reliability, availability and an execution mechanism (Section 5.3). Implemented by the `Capability` class; the dataset contains 15 capabilities. |
| **Capability compatibility** | A directed relation $C_i \to C_j$ that holds when the effects/outputs of $C_i$ support the preconditions/inputs of $C_j$ and no effect of $C_i$ contradicts a precondition of $C_j$. Implemented by `CompatibilityEngine`, which returns both a numeric score and a Boolean decision. |
| **Capability composition** | The construction of a composite capability $C_{comp}=C_n\circ\dots\circ C_1$ from a validated sequence, with aggregated inputs, outputs, preconditions, effects, resources, constraints and operational properties. Implemented by `CompositionEngine` and `CompositeCapability`. |

### 1.4 Central objective

The central objective of the project is to design and evaluate a **structured, deterministic vector embedding** of states, goals and capabilities (a 108-dimensional capability vector, 17-dimensional state and goal vectors) that:

1. keeps different capabilities distinguishable,
2. reflects the state conditions a capability needs and produces,
3. supports a compatibility function that separates composable from non-composable pairs and distinguishes composability from similarity,
4. supports the construction and vector representation of composite capabilities,
5. exposes goal relevance, alternative implementations, and operational properties (cost, reliability, availability, time, risk).

The implemented system realises this objective in a single domain (e-commerce order fulfilment) and evaluates it with five experiments and nine evaluation criteria (Sections 8–10).

---

## 2. Design Requirements

The representation was required to satisfy the ten requirements below. For each requirement, the table states what it means and how the implementation addresses it. The measured outcome is reported in Section 9 and discussed in Section 10.

| # | Requirement | Meaning | How the implementation addresses it |
|---|--------------|----------------------|-------------------------------------------------------------|
| R1 | **Identity preservation** | Different capabilities must have different representations. | Each capability is encoded through nine subspaces (type, inputs, outputs, preconditions, effects, resources, constraints, operational attributes, mechanism). Identity is checked in `evaluate_identity_distinction`: all 105 pairs of the 15 capabilities are compared and the number of pairs with (near-)identical vectors (distance $<10^{-6}$) is counted. |
| R2 | **State awareness** | The representation must reflect the state conditions required and produced by a capability. | Preconditions and effects are encoded in 17-dimensional subspaces aligned slot-by-slot with a 17-dimensional **state** encoding (`StateEmbedder`) and **goal** encoding (`GoalEmbedder`). Effects are encoded as a signed state-change vector $\Delta S$. `evaluate_state_relationship` compares the empirical change of the encoded state after executing `CreateOrder` with its effect subspace. |
| R3 | **Precondition–effect compatibility** | Determine whether the effects of $C_i$ establish the preconditions of $C_j$. | `CompatibilityEngine` combines (a) a symbolic contradiction check between effects and preconditions, (b) a vector score $S_{E\to P}$ computed from the effect subspace of $C_i$ and the precondition subspace of $C_j$, and (c) a state-simulation score $S_{state}$. |
| R4 | **Input–output compatibility** | Determine whether the outputs of $C_i$ supply the inputs of $C_j$. | Inputs and outputs share one 17-slot data-entity vocabulary; $S_{O\to I}$ measures the fraction of the required input mass of $C_j$ that is covered by the outputs of $C_i$. |
| R5 | **Distinguish similarity from composability** | High similarity must not imply compatibility, and vice versa. | Cosine similarity (`cosine_similarity`) and compatibility (`CompatibilityEngine.evaluate`) are separate functions. Experiment 1 reports both for the same pairs. |
| R6 | **Capability composition** | Build complex capabilities from simpler ones and represent them in the same space. | `CompositionEngine.compose` validates a sequence, aggregates inputs, preconditions, effects, resources, constraints and operational properties, and returns a `CompositeCapability` that is encoded by the same `CapabilityEmbedder` (Experiment 2). |
| R7 | **Goal relevance** | Identify which capabilities contribute to a goal. | `compute_goal_relevance` combines symbolic goal coverage (60 %) with vector alignment between the effect subspace and the goal-gap vector (40 %) (Experiment 4). |
| R8 | **Operational properties** | Represent cost, time, resource use, risk, reliability and availability. | A dedicated 6-dimensional operational subspace with bounded normalisation; composition rules for each attribute; Experiment 5 varies the attributes of `MakePayment`. |
| R9 | **Deterministic and consistent encoding** | The same capability must always yield the same vector. | The encoder is a fixed, rule-based function with a fixed feature catalogue (`EmbeddingSchema`); there are no learned parameters and no randomness. `evaluate_consistency` encodes `CreateOrder` three times and measures the maximum absolute difference. |
| R10 | **Computational efficiency** | Encoding and comparison must be cheap. | The vector has 108 float64 entries (864 bytes); encoding, similarity, compatibility and composition are timed in `evaluate_efficiency` (1000 iterations each). |

---

## 3. Related Embedding Approaches

This section reviews representation approaches that are relevant to describing states, goals and capabilities, and relates each to the requirements of Section 2. The review is conceptual; the project itself does not use any of the learned models mentioned below.

### 3.1 Symbolic (logical) representations

Classical planning formalisms such as STRIPS describe an action by a precondition list and add/delete lists over propositions, and planning theory builds on this model [1, 2]. Service-description languages such as OWL-S similarly describe inputs, outputs, preconditions and effects of web services [3].

*Advantages:* exact and unambiguous; precondition–effect reasoning is direct; state transitions are well defined.  
*Limitations:* symbolic matching is discrete (all-or-nothing); there is no native notion of graded closeness, no continuous operational attributes, and no uniform geometric operations for ranking, clustering or nearest-neighbour search.

### 3.2 One-hot and structured (multi-hot / feature-engineered) representations

A one-hot vector marks exactly one category; a multi-hot vector marks several. Structured feature vectors place hand-chosen, interpretable features in fixed positions.

*Advantages:* deterministic, interpretable, cheap, no training data needed; individual dimensions can be inspected and combined arithmetically.  
*Limitations:* the vocabulary is fixed in advance; naive concatenation does not by itself encode logical relationships, so additional structure (signs, alignment of subspaces) and a separate compatibility function are needed; high dimensionality for large vocabularies.

### 3.3 Semantic vector embeddings (text-based)

Word- and sentence-level embeddings (for instance Word2Vec [4], BERT [5] and Sentence-BERT [6]) map text to dense vectors whose geometry reflects distributional similarity.

*Advantages:* capture semantic relatedness of descriptions; handle open vocabulary; useful when only natural-language descriptions exist.  
*Limitations for this problem:* cosine similarity reflects resemblance, not logical satisfaction of preconditions or data dependencies; negation and exact state values (`Order.exists == False` versus `== True`) can be nearly invisible; numeric operational attributes are not represented faithfully; the vectors are not directly interpretable per component; they typically require pretrained models and, for fine-tuning, labelled data.

### 3.4 Distributed representations in general

Distributed representations spread a concept over many dimensions so that similar concepts share features [7]. They generalise well and support graded similarity, but individual dimensions have no fixed meaning, so contract-level questions (is a *specific* precondition satisfied?) are not answerable by inspection of the vector.

### 3.5 Graph / relational representations

Knowledge-graph embeddings such as TransE [8] and graph neural networks such as GCNs [9] represent entities and relations in a graph (for example, capability → *produces* → data type, capability → *requires* → state condition).

*Advantages:* relational structure is explicit; multi-hop dependencies can be represented; structure can be learned from data.  
*Limitations:* require a (usually large) graph and a training procedure; the learned geometry of relations (e.g., translation) does not by itself guarantee logical entailment of preconditions; numeric attributes and exact state values need extra machinery.

### 3.6 Compositional representations

Compositional schemes build the representation of a whole from its parts using a binding/aggregation operator, for example tensor-product representations [10] and holographic reduced representations [11].

*Advantages:* structured objects (role–filler pairs) have a systematic vector form; composites can be built from components by a defined operation.  
*Limitations:* binding operators increase dimensionality or introduce noise; the operator must be chosen to match the semantics of *sequential execution*, which is not simple superposition.

### 3.7 Summary and justification of the chosen approach

| Approach | Exact contract reasoning | Graded / geometric operations | Interpretable dimensions | Needs training data | Fit to this assignment |
|-----------------|:-----------:|:-----------:|:-----------:|:-----------:|-------------------------------|
| Symbolic | Yes | No | Yes | No | Good for logic, no vector space |
| One-hot / structured | Partial (needs design) | Yes | Yes | No | Good, if structure is designed carefully |
| Semantic text embeddings | No | Yes | No | Pretrained model | Captures resemblance, not composability |
| Distributed (general) | No | Yes | No | Usually | Weak for contract-level questions |
| Graph / relational | Partial | Yes | Partial | Yes | Plausible, but needs a graph and training |
| Compositional (binding) | Partial | Yes | Partial | No | Relevant for composites, but heavier |

The project therefore adopts a **structured vector representation**: a fixed catalogue of interpretable features is partitioned into nine subspaces, state-dependent subspaces (preconditions, effects) are aligned with the state and goal encodings, and a separate compatibility function operates on those subspaces together with symbolic checks. This choice is appropriate for the assignment because (i) the assignment concerns *formally specified* capabilities, so the features can be derived directly from the formal model; (ii) it preserves the ability to inspect and test each requirement (identity, state, compatibility, composition, goal, operations) subspace by subspace; (iii) it is deterministic and cheap; and (iv) it requires no training data.

**Statement on pretrained models.** The uploaded implementation depends only on `numpy`, `pandas` and `matplotlib` (`requirements.txt`). It does **not** use BERT, Word2Vec, transformers or any other pretrained or learned model; those approaches appear in this section only as related work.

---

## 4. Proposed Representation

### 4.1 Overview

The implemented capability encoder $\phi_C$ (class `CapabilityEmbedder` in `embedding.py`) maps a capability to a fixed vector of **108 dimensions**, obtained by concatenating nine subspaces:

$$
\mathbf v = \big[\;\mathbf v_{type}\;|\;\mathbf v_{in}\;|\;\mathbf v_{out}\;|\;\mathbf v_{pre}\;|\;\mathbf v_{eff}\;|\;\mathbf v_{res}\;|\;\mathbf v_{con}\;|\;\mathbf v_{ops}\;|\;\mathbf v_{mech}\;\big]\in\mathbb R^{108}
$$

The total is computed in code as the sum of the subspace dimensions and equals 108 (it is printed by `main.py` and stored in `metrics_summary.csv` as `embedding_dimension = 108`). States and goals are encoded separately into 17-dimensional vectors that are aligned slot-by-slot with the precondition and effect subspaces.

### 4.2 Subspace table

| Component | Purpose | Index range | Dimension |
|--------------|------------------------------------------------------------|:----------:|---------:|
| Type | One-hot capability type $T_i$ (API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE) | 0–8 | 9 |
| Input | Data entities required by the capability ($I_i$); 1.0 = required, 0.5 = optional | 9–25 | 17 |
| Output | Data entities produced by the capability ($O_i$) | 26–42 | 17 |
| Preconditions | Signed state conditions required before execution ($P_i$) | 43–59 | 17 |
| Effects | Signed state change $\Delta S$ produced by execution ($E_i$) | 60–76 | 17 |
| Resources | Normalised resource requirements ($R_i$): Database, PaymentGateway, Network, EmailService, FileSystem, GPU, AuthToken, AudioDevice | 77–84 | 8 |
| Constraints | Domain constraints active for the capability ($K_i$): authenticated_user, valid_inventory, cart_has_items, transaction_limit, rate_limit, valid_recipient, db_connection_pool | 85–91 | 7 |
| Operational | Normalised cost, execution time, resource cost, risk, reliability, availability | 92–97 | 6 |
| Mechanism | One-hot execution mechanism $M_i$ (FUNCTION_CALL, REST_API, MESSAGE_QUEUE, DATABASE_INSERT, MICROSERVICE, FILE_IO, UI_COMPONENT, BATCH_JOB, AUDIO_STREAM, GUI_INTERACTION) | 98–107 | 10 |
| **Total** | | 0–107 | **108** |

(The index ranges are the slice boundaries computed by the encoder: $9+17+17+17+17+8+7+6+10=108$.)

```text
 idx:   0-8   9-25    26-42   43-59   60-76    77-84  85-91  92-97  98-107
      +------+-------+-------+-------+--------+------+------+------+---------+
      | type | input | output|  pre  | effect | res  | con  | ops  |  mech   |
      |  9   |  17   |  17   |  17   |   17   |  8   |  7   |  6   |   10    |
      +------+-------+-------+-------+--------+------+------+------+---------+
                                total = 108
```

### 4.3 Encoding of each subspace

* **Type ($\mathbb R^{9}$).** One-hot over the nine formal capability types.
* **Input ($\mathbb R^{17}$) and Output ($\mathbb R^{17}$).** Both use the same 17-entry data-entity vocabulary (`cart_id`, `order_id`, `payment_details`, `payment_receipt`, `customer_id`, `user_id`, `report_type`, `report_file`, `user_profile`, `profile_data`, `inventory_status`, `notification_payload`, `notification_receipt`, `auth_token`, `invoice_pdf`, `audio_stream`, `track_id`). Inputs take the value 1.0 (required) or 0.5 (optional); outputs take 1.0. A shared vocabulary is what allows an output of one capability to be compared with an input of another.
* **Precondition ($\mathbb R^{17}$) and Effect ($\mathbb R^{17}$).** Both are aligned with the 17-entry state-condition vocabulary (`User.authenticated`, `User.role:ADMIN`, `User.role:CUSTOMER`, `Cart.exists`, `Cart.item_count_positive`, `Cart.locked`, `Order.exists`, `Order.status:CREATED`, `Order.status:PAID`, `Payment.status:NOT_STARTED`, `Payment.status:SUCCESS`, `Inventory.available`, `Invoice.generated`, `Notification.sent`, `Profile.updated`, `Report.generated`, `Music.playing`). Categorical variables are expanded into one slot per value (for example `Order.status:CREATED`).
  * *Preconditions:* $+1$ if the slot must be true, $-1$ if it must be false, $0$ if unconstrained (`Cart.item_count > 0` activates the slot `Cart.item_count_positive`).
  * *Effects:* $+1$ if execution makes the slot true, $-1$ if it makes it false (or deletes it), $0$ if unaffected. When `Order.status` or `Payment.status` is set to a value, the other tracked values of that variable (`CREATED`/`PAID`, `NOT_STARTED`/`SUCCESS`) receive $-0.5$ to indicate that they cease to hold.
* **Resources ($\mathbb R^{8}$).** Entry $= \min(1,\ \text{quantity}/2)$ for each required resource.
* **Constraints ($\mathbb R^{7}$).** Binary indicator for each constraint name present in the capability.
* **Operational ($\mathbb R^{6}$).** Bounded, normalised attributes in the order $[\tilde c,\ \tilde t,\ \tilde r,\ \rho,\ Rel,\ A]$:
  * $\tilde c=\ln(1+c)/\ln(1+c_{max})$ with $c_{max}=1.0$ (monetary cost, clipped to $[0,1]$),
  * $\tilde t=t/t_{max}$ with $t_{max}=2000$ ms (execution time, clipped),
  * $\tilde r=r/r_{max}$ with $r_{max}=10$ (resource cost, clipped),
  * $\rho$ = risk, $Rel$ = reliability, $A$ = availability (already in $[0,1]$).

  The energy cost stored in the model (`QualityAttributes.energy_cost`) is aggregated during composition but is **not** part of the 6-dimensional operational subspace.
* **Mechanism ($\mathbb R^{10}$).** One-hot over the ten execution-mechanism categories.

### 4.4 State and goal encodings

`StateEmbedder` and `GoalEmbedder` map a state or goal to $\mathbb R^{17}$, using the same 17 state-condition slots as the precondition/effect subspaces:

* a state slot is $+1$ if the corresponding condition holds in the state, $-1$ if the variable is defined and the condition does not hold, and $0$ if the variable is not defined;
* a goal slot is $+1$ for a required positive condition, $-1$ for a required negative condition, $0$ for unconstrained slots.

Because the three vectors (state, precondition, effect) and the goal share one coordinate system, state applicability, state transitions and goal gaps can be computed with elementary vector operations.

### 4.5 Functional and operational sub-vectors

Two derived sub-vectors are used in the experiments:

* the **functional sub-vector** = inputs ⊕ outputs ⊕ preconditions ⊕ effects (68 dimensions), used to test whether two capabilities do the same thing;
* the **operational sub-vector** = resources ⊕ constraints ⊕ operational attributes (21 dimensions).

---

## 5. Mathematical Formulation

### 5.1 Application model

The formal application model is

$$
A=(S,\ C,\ S_I,\ G,\ R,\ K)
$$

(implemented by the `Application` dataclass), where:

* $S$ — the **state space**: a state is a set of variable/value pairs $S=\{(x_1,v_1),\dots,(x_n,v_n)\}$. In the implementation the state space schema has 14 variables (e.g. `Cart.item_count`, `Order.status`, `Payment.status`).
* $C$ — the set of **capabilities** (15 in the dataset).
* $S_I$ — the **initial state** (`SI_InitialOrderState`: authenticated customer, cart with 3 unlocked items, no order, payment not started, inventory available, and so on).
* $G$ — the **goal**: a set of desired state conditions $G=\{g_1,\dots,g_m\}$, each $g_k$ being *variable operator value* (operators `==`, `!=`, `>`, `<`, `>=`, `<=`, `in`). Here $m=3$.
* $R$ — the **available resources** of the application (7 resources, e.g. Database, PaymentGateway, Network).
* $K$ — the **global constraints** (3: `authenticated_user`, `valid_inventory`, `cart_non_empty`).

A state satisfies a goal, $S\models G$, if every condition $g_k$ evaluates to true in $S$. A condition on a variable that is absent from the state evaluates to false.

### 5.2 State and goal representation

A **state** is represented by variable/value conditions. An atomic condition $p=(x,\ \circ,\ v)$ holds in $S$ if $x$ is defined and $S(x)\circ v$. A **goal** is a set of such conditions describing the desired state, e.g.

$$
G=\{\ \text{Order.exists}==\text{True},\ \ \text{Payment.status}==\text{SUCCESS},\ \ \text{Notification.sent}==\text{True}\ \}.
$$

### 5.3 Capability model

Each capability is the tuple

$$
C_i=(T_i,\ I_i,\ O_i,\ P_i,\ E_i,\ K_i,\ R_i,\ Q_i,\ Rel_i,\ A_i,\ M_i)
$$

* $T_i$ — type, $T_i\in\{\text{API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE}\}$.
* $I_i$ — inputs, each $(name,\ data\_type,\ domain,\ required)$.
* $O_i$ — outputs, each $(name,\ data\_type,\ domain)$.
* $P_i$ — preconditions, each *variable operator value*; $S\models P_i$ means the capability can execute in $S$.
* $E_i$ — effects, each *variable := value* with operation SET, INCREMENT, DECREMENT or DELETE; they define the transition $S'=\mathrm{Apply}(S,E_i)$.
* $K_i$ — capability-specific constraints (name, expression, type).
* $R_i$ — resource requirements (name, type, quantity). (The implementation keeps resource requirements as a separate component $R_i$; the vector has a dedicated resource subspace for it.)
* $Q_i=(C_{time},C_{resource},C_{money},C_{risk},C_{energy})$ — quality/cost attributes.
* $Rel_i\in[0,1]$ — reliability; $A_i\in[0,1]$ — availability.
* $M_i$ — execution mechanism (type, endpoint/target, protocol/action), e.g. `REST_API`, `POST /api/v1/payments`.

A capability can execute on $S$ iff $S\models P_i$; execution yields $S'=\mathrm{Apply}(S,E_i)$ (`Capability.can_execute_on`, `Capability.execute`).

### 5.4 Encoding functions

Three encoders are implemented:

$$
\phi_S: S\to\mathbb R^{17}\quad(\texttt{encode\_state}),\qquad
\phi_G: G\to\mathbb R^{17}\quad(\texttt{encode\_goal}),\qquad
\phi_C: C\to\mathbb R^{108}\quad(\texttt{encode\_capability}).
$$

The capability encoder is the concatenation of the nine subspace encoders:

$$
\phi_C(C_i)=\big[\ \mathbf v_{type}\,|\,\mathbf v_{in}\,|\,\mathbf v_{out}\,|\,\mathbf v_{pre}\,|\,\mathbf v_{eff}\,|\,\mathbf v_{res}\,|\,\mathbf v_{con}\,|\,\mathbf v_{ops}\,|\,\mathbf v_{mech}\ \big].
$$

For the state-aligned slots $k=1,\dots,17$:

$$
\phi_S(S)_k=\begin{cases}+1 & \text{condition of slot }k\text{ holds in }S\\ -1 & \text{variable defined, condition does not hold}\\ 0 & \text{variable undefined}\end{cases}
\qquad
\phi_G(G)_k=\begin{cases}+1 & \text{slot required true}\\ -1 & \text{slot required false}\\ 0 & \text{unconstrained.}\end{cases}
$$

The operational subspace is

$$
\mathbf v_{ops}=\Big[\ \tfrac{\ln(1+C_{money})}{\ln(1+c_{max})},\ \ \tfrac{C_{time}}{t_{max}},\ \ \tfrac{C_{resource}}{r_{max}},\ \ C_{risk},\ \ Rel,\ \ A\ \Big],
$$

with each entry clipped to $[0,1]$ and $c_{max}=1$, $t_{max}=2000$ ms, $r_{max}=10$.

### 5.5 Similarity function

The similarity function is cosine similarity,

$$
\mathrm{sim}(\mathbf x,\mathbf y)=\frac{\mathbf x\cdot\mathbf y}{\lVert\mathbf x\rVert_2\,\lVert\mathbf y\rVert_2},
$$

with the implementation returning $0$ if either norm is below $10^{-12}$ and clipping the result to $[-1,1]$. It is symmetric and is used for: pairwise capability similarity (Experiment 1, Experiment 3, identity evaluation), component–composite comparison (Experiment 2), the functional sub-vector comparison (Experiment 3, 5), and vector alignment inside goal relevance (Experiment 4). **It is not used to decide compatibility.**

### 5.6 Compatibility function

For a directed pair $C_i\to C_j$ and an optional context state $S$, the engine computes three component scores and a conflict check.

**Conflict check (symbolic).** A conflict exists if some effect $e\in E_i$ with operation SET and some precondition $p\in P_j$ refer to the same variable and (i) $p$ requires `==` a value different from the value set by $e$, or (ii) $p$ requires `!=` the value set by $e$.

**Effect → precondition score.** With $\mathbf e=\mathbf v_{eff}(C_i)$ and $\mathbf p=\mathbf v_{pre}(C_j)$:

$$
S_{E\to P}=\begin{cases}
1 & \text{if } P_j=\varnothing\ (\lVert\mathbf p\rVert_1=0)\\[2pt]
0 & \text{if } \sum_k\max(0,-e_kp_k)>0\ \ (\text{direct contradiction})\\[2pt]
\min\!\Big(1,\ \dfrac{\sum_k\max(0,\,e_kp_k)}{\lVert\mathbf p\rVert_1}\Big) & \text{otherwise.}
\end{cases}
$$

**Input → output score.** With $\mathbf o=\mathbf v_{out}(C_i)$ and $\mathbf u=\mathbf v_{in}(C_j)$:

$$
S_{O\to I}=\frac{\sum_k\min(o_k,u_k)}{\sum_k u_k}\quad(=1\text{ if }C_j\text{ has no inputs}).
$$

**State score.** If a context state $S$ is given, the intermediate state is $S'=\mathrm{Apply}(S,E_i)$ and $S_{state}$ is the fraction of preconditions $P_j$ that hold in $S'$ ($=1$ if all hold). If no context state is given, $S_{state}=1$ when there is no conflict and $0$ otherwise.

**Overall score and decision.**

$$
\mathrm{Compat}(C_i,C_j)=\begin{cases}0 & \text{if any conflict exists}\\ w_1S_{E\to P}+w_2S_{O\to I}+w_3S_{state} & \text{otherwise,}\end{cases}
$$

with $(w_1,w_2,w_3)=(0.50,\,0.30,\,0.20)$.

The Boolean decision is *compatible* iff there is no conflict and ($S_{E\to P}>0$ or $P_j=\varnothing$); when a context state is supplied, it additionally requires that $C_i$ is executable in $S$ and that $S'\models P_j$. The compatibility score is **directed** ($C_i\to C_j\ne C_j\to C_i$), unlike cosine similarity.

### 5.7 Composition formulas

For a sequence $C_1,\dots,C_n$ (validated pairwise for consecutive compatibility, with state simulation when an initial state is given), the composite $C_{comp}=C_n\circ\dots\circ C_1$ has:

* **Inputs:** every input of $C_k$ whose name is not produced as an output by $C_1,\dots,C_{k-1}$.
* **Outputs:** the union of all outputs.
* **Preconditions:** every precondition of $C_k$ that is not already established by an earlier SET effect on the same variable with the required value.
* **Effects (net):** for each variable, the effect of the **last** capability that sets it.
* **Resources:** union by name, with quantities summed. **Constraints:** union by name.
* **Operational properties:**

$$
\begin{aligned}
C_{money}&=\sum_k C_{money,k}, & C_{time}&=\sum_k C_{time,k},\\
C_{resource}&=\sum_k C_{resource,k}, & C_{energy}&=\sum_k C_{energy,k},\\
C_{risk}&=1-\prod_k(1-C_{risk,k}), & Rel&=\prod_k Rel_k,\qquad A=\prod_k A_k.
\end{aligned}
$$

* **Type and mechanism:** the composite is typed `SERVICE`, with mechanism type `COMPOSITE_PIPELINE`.

The composite vector is $\phi_C(C_{comp})$, i.e. the **same** encoder is applied to the synthesised composite capability.

### 5.8 Goal relevance

Let $U=\{g\in G:\ S\not\models g\}$ be the unmet goal conditions in $S$. If $U=\varnothing$ the relevance is 1. Otherwise

$$
\mathrm{GR}(C_i,G,S)=0.60\cdot\underbrace{\frac{\lvert\{g\in U:\ \mathrm{Apply}(S,E_i)\models g\}\rvert}{\lvert U\rvert}}_{\text{symbolic goal coverage}}\;+\;0.40\cdot\underbrace{\max\!\big(0,\ \mathrm{sim}(\mathbf v_{eff}(C_i),\ \Delta\mathbf g)\big)}_{\text{vector alignment}},
$$

where the goal-gap vector is $\Delta g_k=\max(0,\ \phi_G(G)_k-\phi_S(S)_k)$ on the slots constrained by the goal ($\phi_G(G)_k\neq0$) and $0$ elsewhere. The vector alignment is $0$ when either vector has norm below $10^{-6}$. The score is therefore a **combination** of symbolic coverage and vector alignment, not a pure vector similarity.

### 5.9 Operational similarity

Operational differences between capability variants are measured by the Euclidean distance between operational subspaces,

$$
d_{ops}(C_a,C_b)=\lVert\mathbf v_{ops}(C_a)-\mathbf v_{ops}(C_b)\rVert_2,
$$

and are contrasted with the cosine similarity of the functional sub-vectors and of the full 108-dimensional vectors.

---

## 6. Capability Composition Model

### 6.1 The composed pipeline

The implemented composition is

$$
\texttt{CompletePurchase}=\texttt{SendNotification}\circ\texttt{MakePayment}\circ\texttt{CreateOrder},
$$

executed in the order **CreateOrder → MakePayment → SendNotification**. The contracts of the three components, as defined in `dataset.py`, are:

| Capability | Type | Inputs | Outputs | Preconditions | Effects |
|-------------|--------|----------------|--------------|------------------------|-------------------------|
| `CreateOrder` | FUNCTION | `cart_id` | `order_id` | `Cart.exists == True`, `Cart.item_count > 0`, `Cart.locked == False` | `Order.exists := True`, `Order.status := CREATED`, `Cart.locked := True` |
| `MakePayment` | API | `order_id`, `payment_details` | `payment_receipt` | `Order.exists == True`, `Order.status == CREATED`, `Payment.status == NOT_STARTED` | `Payment.status := SUCCESS`, `Order.status := PAID` |
| `SendNotification` | MESSAGE | `order_id`, `notification_payload` (optional) | `notification_receipt` | `Payment.status == SUCCESS`, `Notification.sent == False` | `Notification.sent := True` |

### 6.2 Step-by-step composition

1. **Validate consecutive pairs.** `validate_sequence` evaluates `CreateOrder → MakePayment` and `MakePayment → SendNotification` with the compatibility engine, simulating the state after each step. Both pairs are compatible (Section 9.2).
2. **Check preconditions along the state trajectory** (starting from the initial state $S_I$):

   | After step | `Order.exists` | `Order.status` | `Cart.locked` | `Payment.status` | `Notification.sent` |
   |---|---|---|---|---|---|
   | $S_I$ | False | NONE | False | NOT_STARTED | False |
   | `CreateOrder` | True | CREATED | True | NOT_STARTED | False |
   | `MakePayment` | True | PAID | True | SUCCESS | False |
   | `SendNotification` | True | PAID | True | SUCCESS | **True** |

   Each capability's preconditions hold in the state produced by its predecessor, and the final state satisfies all three goal conditions (`Order.exists`, `Payment.status == SUCCESS`, `Notification.sent`).
3. **Compatibility between consecutive capabilities.**
   * `CreateOrder → MakePayment`: the effects establish `Order.exists == True` and `Order.status == CREATED`; `Payment.status == NOT_STARTED` already holds in the initial state; the output `order_id` supplies one of the two required inputs (`payment_details` is supplied externally).
   * `MakePayment → SendNotification`: the effect `Payment.status := SUCCESS` establishes the first precondition of `SendNotification`; `Notification.sent == False` holds in the state. The pairwise input check finds no match, because `SendNotification` requires `order_id`, which was produced earlier by `CreateOrder` rather than by `MakePayment`. The pairwise check therefore only sees consecutive capabilities; the composite construction (next step) accounts for outputs produced anywhere earlier in the sequence.
4. **Aggregate inputs.** Inputs not produced earlier in the sequence remain external: `cart_id`, `payment_details`, `notification_payload`. The input `order_id` is internal because `CreateOrder` produces it.
5. **Aggregate outputs.** `order_id`, `payment_receipt`, `notification_receipt`.
6. **Aggregate preconditions.** Preconditions not established by earlier effects remain: `Cart.exists == True`, `Cart.item_count > 0`, `Cart.locked == False`, `Payment.status == NOT_STARTED`, `Notification.sent == False`. (`Order.exists == True` and `Order.status == CREATED` are established internally; `Payment.status == SUCCESS` is established by `MakePayment`.)
7. **Aggregate effects (net).** Five net effects: `Order.exists := True`, `Order.status := PAID` (the later effect overrides `CREATED`), `Cart.locked := True`, `Payment.status := SUCCESS`, `Notification.sent := True`.
8. **Aggregate resources and constraints.** Resources: Database (1), PaymentGateway (1), Network (2, summed from `MakePayment` and `SendNotification`), EmailService (1). Constraints: `cart_has_items`, `transaction_limit`, `valid_recipient`.
9. **Aggregate operational attributes.**

   | Attribute | Rule | Calculation | Result |
   |---|---|---|---:|
   | Monetary cost | sum | $0.01+0.10+0.005$ | 0.1150 |
   | Execution time (ms) | sum | $80+250+40$ | 370.0 |
   | Resource cost | sum | $2+4+1$ | 7.0 |
   | Risk | $1-\prod(1-\rho_k)$ | $1-(0.95)(0.90)(0.99)$ | 0.1536 |
   | Reliability | product | $0.99\times0.97\times0.995$ | 0.95550 |
   | Availability | product | $1.0\times0.99\times1.0$ | 0.99000 |

10. **Construct the composite capability.** A `CompositeCapability` named `CompletePurchase` is created, of type `SERVICE`, mechanism `COMPOSITE_PIPELINE`, with `composition_method = "SEQUENTIAL"`, and keeps the ordered list of its component capabilities.

### 6.3 Vector representation of the composite

The composite is encoded with the same encoder, $\phi_C(\texttt{CompletePurchase})\in\mathbb R^{108}$ (Euclidean norm 4.8955). Its subspaces reflect the aggregated contract: the input subspace marks `cart_id` and `payment_details` (1.0) and `notification_payload` (0.5); the output subspace marks the three outputs; the precondition subspace carries the five remaining preconditions; the effect subspace carries the net transition (`Order.status:PAID` $+1$ with `Order.status:CREATED` $-0.5$, `Payment.status:SUCCESS` $+1$ with `NOT_STARTED` $-0.5$, `Order.exists`, `Cart.locked`, `Notification.sent` $+1$); the operational subspace is $[0.157,\,0.185,\,0.700,\,0.154,\,0.956,\,0.990]$. The type subspace has `SERVICE` active. **The mechanism subspace of the composite is the zero vector**, because `COMPOSITE_PIPELINE` is not one of the ten mechanism categories in the feature catalogue (this is visible in Figure 3A and is discussed in Section 11).

### 6.4 Similarity versus composability

Similarity and composability answer different questions:

* **Similarity** is a symmetric, graded measure of how alike two vectors are: $\mathrm{sim}(\mathbf x,\mathbf y)=\mathrm{sim}(\mathbf y,\mathbf x)$.
* **Composability** is a directed, contract-based relationship: $C_i\to C_j$ requires $E_i$ to support $P_j$, the outputs of $C_i$ to cover the inputs of $C_j$, and no contradiction between them.

Two capabilities may therefore have a high vector similarity but be incompatible because their preconditions, effects, inputs or outputs do not satisfy the required relationships. Four pairs measured in the implemented system show this (cosine similarity from the full 108-dimensional vectors; compatibility score from `CompatibilityEngine`):

| Pair | Cosine similarity | Compatibility score | Compatible? | Reason |
|---------------------------|---------:|----------:|:--------:|------------------------------------------|
| `CreateOrder` → `CancelCart` | 0.6164 | 0.0000 | No | Effects contradict preconditions (`Order.exists`, `Cart.locked`) |
| `CreateOrder` → `CreateOrder` | 1.0000 | 0.0000 | No | `Cart.locked := True` contradicts `Cart.locked == False` |
| `CreateOrderAPI` → `CreateOrderDatabase` | 0.7634 | 0.0000 | No | Same contradiction; identical functional sub-vector (1.0000) but not sequentially composable |
| `CreateOrder` → `MakePayment` | 0.0754 | 0.6833 | Yes | Effects and outputs establish preconditions and inputs |

In addition, composability is directional: `MakePayment → CreateOrder` has the same cosine similarity (0.0754) as `CreateOrder → MakePayment` but a compatibility score of 0.2000 and a *not compatible* decision, and sequence validation rejects the sequence [`MakePayment`, `CreateOrder`].

---

## 7. Implementation

### 7.1 Module overview

The project is a terminal-based Python program (dependencies: `numpy`, `pandas`, `matplotlib`). Its modules are:

| Module | Purpose |
|------------|----------------------------------------------------------------------------------------|
| `models.py` | **Formal data structures** (dataclasses/enums): `CapabilityType`, `InputSpec`, `OutputSpec`, `Precondition` (with `evaluate`), `Effect` (with `apply`), `Constraint`, `Resource`, `QualityAttributes`, `ExecutionMechanism`, `State` (with `satisfies_preconditions`, `apply_effects`, `satisfies_goal`), `Goal`, `Capability` (with `can_execute_on`, `execute`), `CompositeCapability`, and `Application` $=(S,C,S_I,G,R,K)$. |
| `embedding.py` | **Vector encoding.** `EmbeddingSchema` (the fixed feature catalogue), `CapabilityEmbedder` (nine subspace encoders, `encode_capability`, `get_subspaces`, `get_functional_subvector`, `get_operational_subvector`), `StateEmbedder`, `GoalEmbedder`, `cosine_similarity`, and `compute_goal_relevance`. |
| `compatibility.py` | **Compatibility checking.** `CompatibilityEngine.evaluate` returns a `CompatibilityResult` (overall score, $S_{E\to P}$, $S_{O\to I}$, $S_{state}$, satisfied/unmet preconditions, satisfied/missing inputs, conflicts, explanation); `compute_compatibility_matrix` evaluates all ordered pairs. |
| `composition.py` | **Composition.** `CompositionEngine.validate_sequence`, `compose` (aggregation of contract and operational properties; returns `CompositeCapability`) and `compare_composition_vectors` (component–composite similarity analysis). |
| `dataset.py` | **Dataset construction/export.** `build_ecommerce_application` builds the e-commerce application (initial state, goal, resources, global constraints and 15 capabilities); `export_dataset` writes `data/capabilities.json` and `data/capabilities.csv`. |
| `experiments.py` | **Experimental evaluation.** `ExperimentRunner` runs the five experiments, prints results to the terminal, records rows for `results/experiment_results.csv`. |
| `evaluation.py` | **Evaluation metrics.** `EvaluationSuite` computes the nine evaluation criteria and writes the summary data frame used for `results/metrics_summary.csv`. |
| `visualization.py` | **Plot generation.** `Visualizer` creates four matplotlib figures in `plots/` (capability similarity, compatibility matrix, composition comparison, operational attributes). |
| `main.py` | **Pipeline driver.** Builds the application, instantiates the engines, runs the experiments and evaluation, exports CSVs, generates the plots, and prints terminal output. |

The dataset contains 15 capabilities: the core purchase flow (`CreateOrder`, `MakePayment`, `SendNotification`), supporting and incompatible capabilities (`CancelCart`, `CheckInventory`, `GenerateInvoice`), unrelated capabilities (`UpdateProfile`, `GenerateReport`, `PlayMusic`), three alternative implementations of order creation (`CreateOrderAPI`, `CreateOrderDatabase`, `CreateOrderGUI`), and three operational variants of payment (`MakePayment_Economy`, `MakePayment_Enterprise`, `MakePayment_HighCost_LowRel`).

### 7.2 Execution flow

```text
Capability Dataset                (dataset.py: 15 capabilities, 14-variable state, 3-condition goal)
       ↓
Formal Models                     (models.py: State, Goal, Capability, Application)
       ↓
Embedding Generation              (embedding.py: 108-D capability, 17-D state/goal vectors)
       ↓
Similarity / Compatibility        (embedding.py: cosine;  compatibility.py: E→P, O→I, state)
       ↓
Capability Composition            (composition.py: validate, aggregate, encode composite)
       ↓
Goal Relevance / Operational      (embedding.py: goal relevance; experiments.py: operational variants)
Analysis
       ↓
Evaluation                        (evaluation.py: nine criteria)
       ↓
Terminal Results + CSV Results + Plots
   (stdout)   (results/*.csv)   (plots/*.png)
```

`main.py` executes five numbered stages: (1) initialise the formal application model and export the dataset; (2) set up the embedding, compatibility and composition engines and print the subspace dimensions; (3) run the five experiments; (4) run the evaluation suite and print the nine criteria; export the CSV files; (5) generate the four plots. The terminal output, the CSV files and the plots together constitute the demonstration mechanism of the project.

---

## 8. Experimental Methodology

All experiments use the e-commerce application built by `dataset.py` (initial state with 14 variables; goal with 3 conditions; 15 capabilities) and the engines configured in `main.py` (compatibility weights $w_{E\to P}=0.50$, $w_{O\to I}=0.30$, $w_{state}=0.20$). The encoding is deterministic, so each experiment is a single evaluation rather than a repeated random trial.

### 8.1 Experiment 1 – Compatibility

**Capabilities.** $C_1=$ `CreateOrder`, $C_2=$ `MakePayment`, $C_3=$ `CancelCart`.  
**Expected relationship.** `CreateOrder → MakePayment` should be compatible (the effects of `CreateOrder` establish `Order.exists` and `Order.status == CREATED`, and `order_id` feeds `MakePayment`). `CreateOrder → CancelCart` should be incompatible (`CancelCart` requires `Order.exists == False` and `Cart.locked == False`, which `CreateOrder` contradicts).  
**Evaluation.** Both pairs are evaluated with `CompatibilityEngine.evaluate` using the initial state as context. The compatibility score, its three components, the Boolean decision, and the cosine similarity of the two capability vectors are reported, so that compatibility can be compared with similarity for the same pairs.

### 8.2 Experiment 2 – Composition

**Pipeline.** `CreateOrder → MakePayment → SendNotification`, composed into `CompletePurchase` with the initial state as context for validation.  
**Evaluation.** The composite is built by `CompositionEngine.compose` (Section 6.2) and evaluated on (i) the aggregated contract (inputs, outputs, preconditions, net effects); (ii) the aggregated operational properties (cost, time, reliability, availability) compared with the expected sum/product of the component values; (iii) the cosine similarity of the composite vector to each component vector and to the component sum vector. In addition, the `EvaluationSuite` checks that the aggregated cost and reliability match the expected sum and product and that the composite has at least three net effects.

### 8.3 Experiment 3 – Alternative implementations

**Capabilities.** Three implementations of the same order-creation function: `CreateOrderAPI` (type API, mechanism `REST_API`), `CreateOrderDatabase` (type DATABASE, mechanism `DATABASE_INSERT`), `CreateOrderGUI` (type GUI, mechanism `GUI_INTERACTION`). All three have the same inputs, outputs, preconditions and effects as `CreateOrder`, but differ in type, resources, constraints, mechanism and operational attributes (e.g. execution time 120 ms / 35 ms / 250 ms; monetary cost 0.03 / 0.005 / 0.00).  
**Evaluation.** For each pair, two similarities are computed: (a) **functional similarity**, the cosine similarity of the functional sub-vectors (inputs, outputs, preconditions, effects), and (b) **overall similarity**, the cosine similarity of the full 108-dimensional vectors. The expected pattern is a functional similarity near 1 with an overall similarity that is lower because type, resources, constraints, mechanism and operational attributes differ.

### 8.4 Experiment 4 – Goal relevance

**Goal.** `Order.exists == True`, `Payment.status == SUCCESS`, `Notification.sent == True`, evaluated in the initial state (all three conditions unmet).  
**Candidates.** Eight capabilities: `CreateOrder`, `MakePayment`, `SendNotification` (labelled relevant), `GenerateInvoice`, `CheckInventory` (labelled semi-relevant), and `UpdateProfile`, `GenerateReport`, `PlayMusic` (labelled irrelevant). The labels are the experiment's own categories.  
**Method.** The implementation uses a **combination** of symbolic and vector information (Section 5.8): the score is 0.60 × *symbolic goal coverage* (fraction of unmet goal conditions satisfied after applying the capability's effects) + 0.40 × *vector alignment* (cosine similarity between the capability's effect subspace and the goal-gap vector, floored at 0). It is therefore neither a pure vector similarity nor a pure symbolic match. The terminal output reports the combined score together with its two components.

### 8.5 Experiment 5 – Operational attributes

**Variants (all of type API with the same functional contract as `MakePayment`).** `MakePayment` (baseline), `MakePayment_Economy`, `MakePayment_Enterprise`, `MakePayment_HighCost_LowRel`.  
**Attributes represented.** Monetary cost, reliability, availability, execution time, resource cost and risk (the six components of the operational subspace; the energy cost is stored in the model but not embedded).  
**Evaluation.** For each variant, the operational-subspace Euclidean distance from the baseline and the full-vector cosine similarity to the baseline are computed; the evaluation suite additionally compares the functional sub-vector similarity (expected $\approx1$ because the contract is unchanged) with the operational distance. The question is whether changes in operational attributes change the embedding, and how strongly.

### 8.6 Evaluation protocol (nine criteria)

In addition to the experiments, `EvaluationSuite` computes nine criteria over the whole dataset or selected capability pairs: (1) identity distinction, (2) state relationship, (3) compatibility separation, (4) input–output compatibility, (5) composition fidelity, (6) goal relevance, (7) operational sensitivity, (8) consistency/determinism, (9) computational efficiency. Their definitions are those implemented in `evaluation.py`; the results are in Section 9.7. Efficiency timings use `time.perf_counter` with 1000 iterations per operation.

---

## 9. Results

All values below are the current outputs of the final project (terminal output of `python main.py`, `results/experiment_results.csv`, `results/metrics_summary.csv`, and the plots in `plots/`).

### 9.1 Dataset and encoding configuration

| Item | Value |
|----------------------------------------------------------------------|-----------------------------:|
| Capabilities in the dataset | 15 |
| State variables in the initial state | 14 |
| Goal conditions | 3 |
| Capability embedding dimension | 108 |
| Subspace dimensions (type / input / output / pre / eff / res / con / ops / mech) | 9 / 17 / 17 / 17 / 17 / 8 / 7 / 6 / 10 |
| Memory per vector (float64) | 864 bytes |

### 9.2 Experiment 1 – Compatibility results

| Source | Target | Compatibility Score | $S_{E\to P}$ | $S_{O\to I}$ | $S_{state}$ | Similarity | Result |
|-------------|-------------|-------------:|--------:|--------:|--------:|----------:|----------------------|
| CreateOrder | MakePayment | 0.6833 | 0.6667 | 0.5000 | 1.0000 | 0.0754 | Compatible |
| CreateOrder | CancelCart | 0.0000 | 0.0000 | 0.0000 | 0.3333 | 0.6164 | Incompatible (2 conflicts) |

* `CreateOrder → MakePayment`: satisfied preconditions `Order.exists == True` and `Order.status == CREATED` (from the effects of `CreateOrder`); satisfied input `order_id`. Unmet by the effect of `CreateOrder` alone: `Payment.status == NOT_STARTED` (holds in the initial state, hence $S_{state}=1$) and the input `payment_details` (external). Score: $0.50\times0.6667+0.30\times0.50+0.20\times1.0=0.6833$.
* `CreateOrder → CancelCart`: conflicts detected: `Order.exists := True` vs. required `Order.exists == False`, and `Cart.locked := True` vs. required `Cart.locked == False`. The overall score is set to 0 and the pair is incompatible, although the vectors are fairly similar (0.6164).

For the stateless pair evaluation used by the evaluation suite (no context state), `CreateOrder → MakePayment` yields the same score (0.6833). The matrix in Figure 2 uses the initial state as context (see below).

**Figure 1** shows the pairwise cosine similarities of eleven capabilities.

![](plots/capability_similarity.png){ width=88% }

**Figure 1: Pairwise capability cosine-similarity matrix in the 108-dimensional space.** The three order-creation implementations (`CreateOrder`, `CreateOrderAPI`, `CreateOrderDatabase`) form the most similar group (0.76–0.78); `CancelCart` is also highly similar to `CreateOrder` (0.62), while `MakePayment` is nearly orthogonal to `CreateOrder` (0.08).

**Figure 2** shows the directed compatibility score and the Boolean decision for seven capabilities, computed with the initial state as context.

![](plots/compatibility_matrix.png){ width=100% }

**Figure 2: Compatibility matrix of evaluated capability pairs (left: weighted score; right: Boolean decision), evaluated against the initial state.** Because a context state is supplied, a pair is *compatible* only if the source capability is itself executable in the initial state and the intermediate state satisfies the target's preconditions. In this matrix only `CreateOrder → MakePayment` is marked compatible (score 0.68). For example, `MakePayment → SendNotification` has a non-zero score (0.45) but is marked incompatible here because `MakePayment` is not executable in the initial state; the same pair is accepted when it is checked inside the sequential composition (Section 9.3) or without a context state (Section 9.7, Table 9.7b).

### 9.3 Experiment 2 – Composition results

**Composite capability `CompletePurchase`** (CreateOrder → MakePayment → SendNotification):

| Property | Value |
|----------------------|------------------------------------------------------------------------------|
| Aggregated inputs | `cart_id`, `payment_details`, `notification_payload` |
| Aggregated outputs | `order_id`, `payment_receipt`, `notification_receipt` |
| Aggregated preconditions | `Cart.exists == True`, `Cart.item_count > 0`, `Cart.locked == False`, `Payment.status == NOT_STARTED`, `Notification.sent == False` |
| Net effects (5) | `Order.exists := True`, `Order.status := PAID`, `Cart.locked := True`, `Payment.status := SUCCESS`, `Notification.sent := True` |
| Pairwise validation | `CreateOrder → MakePayment`: compatible, 0.6833; `MakePayment → SendNotification`: compatible, 0.4500 ($S_{E\to P}=0.5$, $S_{O\to I}=0.0$, $S_{state}=1.0$) |

**Operational properties of the composite:**

| Property | Components | Composite |
|------------------------------|---------------------------------------------|------------------------:|
| Monetary cost | 0.01 + 0.10 + 0.005 | 0.1150 |
| Execution time (ms) | 80 + 250 + 40 | 370.0 |
| Resource cost | 2 + 4 + 1 | 7.0 |
| Risk | $1-(0.95\cdot0.90\cdot0.99)$ | 0.1536 |
| Reliability | 0.99 × 0.97 × 0.995 | 0.95550 |
| Availability | 1.0 × 0.99 × 1.0 | 0.99000 |

**Composite-to-component similarity** (cosine similarity between $\phi_C(C_{comp})$ and the indicated vector):

| Comparison | Cosine similarity |
|---|---:|
| Composite vs. `CreateOrder` | 0.5190 |
| Composite vs. `MakePayment` | 0.5162 |
| Composite vs. `SendNotification` | 0.4372 |
| Composite vs. component sum vector $\sum_k\phi_C(C_k)$ | 0.7396 |
| Composite vs. component average vector | 0.7396 |

(The sum and average vectors differ only by a scalar factor, so their cosine similarity with the composite is identical.)

**Figure 3** compares subspace magnitudes of the components and the composite, and the component–composite alignment.

![](plots/composition_comparison.png){ width=100% }

**Figure 3: Composition comparison between component vectors and the composite `CompletePurchase` vector.** (A) Euclidean norm of each subspace for the three components and the composite; the composite has larger norms in the input, output, precondition, effect, resource and constraint subspaces (it aggregates more items) and a zero mechanism subspace. (B) Cosine similarity of the composite with each component (0.519, 0.516, 0.437) and with the average/sum component vector (0.740).

**Supplementary: per-subspace cosine similarity between the composite and each component** (computed with the project's `get_subspaces` extractor; not printed by `main.py`):

| Subspace | CreateOrder | MakePayment | SendNotification |
|----------------------------|-----------------------:|-----------------------:|-----------------------:|
| type | 0.000 | 0.000 | 0.000 |
| input | 0.667 | 0.471 | 0.149 |
| output | 0.577 | 0.577 | 0.577 |
| precondition | 0.775 | 0.258 | 0.316 |
| effect | 0.237 | 0.674 | 0.426 |
| resource | 0.378 | 0.802 | 0.802 |
| constraint | 0.577 | 0.577 | 0.577 |
| operational | 0.937 | 0.982 | 0.908 |
| mechanism | 0.000 | 0.000 | 0.000 |

### 9.4 Experiment 3 – Alternative implementation results

| Implementation Pair | Functional Similarity | Overall Similarity |
|---|---:|---:|
| CreateOrderAPI vs CreateOrderDatabase | 1.0000 | 0.7634 |
| CreateOrderAPI vs CreateOrderGUI | 1.0000 | 0.7915 |
| CreateOrderDatabase vs CreateOrderGUI | 1.0000 | 0.7856 |

**Supplementary: per-subspace cosine similarity within these pairs** (project's `get_subspaces` extractor; not printed by `main.py`):

| Pair | input | output | pre | eff | type | resource | constraint | mechanism | operational |
|----------------------|-------:|-------:|-------:|-------:|-------:|---------:|---------:|--------:|--------:|
| API vs Database | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.577 | 0.000 | 0.000 | 0.996 |
| API vs GUI | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.516 | 0.000 | 0.000 | 0.998 |
| Database vs GUI | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.990 |

The overall similarity (0.76–0.79) is below the functional similarity (1.0) because the type, constraint and mechanism subspaces are orthogonal for the three variants and the resource subspaces differ, while the 68 functional dimensions are identical.

### 9.5 Experiment 4 – Goal relevance results

Goal: `Order.exists == True`, `Payment.status == SUCCESS`, `Notification.sent == True` (initial state: none satisfied).

| Capability | Category (experiment label) | Relevance Score | Symbolic Coverage | Vector Alignment |
|--------------------|--------------------|--------------:|---------------------:|----------------------:|
| SendNotification | Relevant | 0.4309 | 0.3333 | 0.5774 |
| MakePayment | Relevant | 0.3461 | 0.3333 | 0.3651 |
| CreateOrder | Relevant | 0.3281 | 0.3333 | 0.3203 |
| GenerateInvoice | Semi-relevant | 0.0000 | 0.0000 | 0.0000 |
| CheckInventory | Semi-relevant | 0.0000 | 0.0000 | 0.0000 |
| UpdateProfile | Irrelevant | 0.0000 | 0.0000 | 0.0000 |
| GenerateReport | Irrelevant | 0.0000 | 0.0000 | 0.0000 |
| PlayMusic | Irrelevant | 0.0000 | 0.0000 | 0.0000 |

Mean relevance of the three relevant capabilities: 0.3684; of the three irrelevant capabilities: 0.0000; gap: 0.3684. Each relevant capability satisfies exactly one of the three unmet goal conditions (symbolic coverage 1/3). The values are, for example, $0.6\times0.3333+0.4\times0.5774=0.4309$ for `SendNotification`.

### 9.6 Experiment 5 – Operational results

| Variant | Cost ($) | Reliability | Availability | Execution Time (ms) | Risk | Operational distance from baseline | Similarity (full vector) |
|------------------------|-------:|---------:|---------:|---------:|------:|--------------:|---------------:|
| MakePayment (baseline) | 0.10 | 0.970 | 0.99 | 250.0 | 0.10 | 0.0000 | 1.0000 |
| MakePayment_Economy | 0.01 | 0.920 | 0.95 | 300.0 | 0.15 | 0.2498 | 0.9978 |
| MakePayment_Enterprise | 0.15 | 0.999 | 1.00 | 100.0 | 0.02 | 0.1646 | 0.9991 |
| MakePayment_HighCost_LowRel | 0.50 | 0.800 | 1.00 | 500.0 | 0.30 | 0.5700 | 0.9887 |

The evaluation suite reports a functional sub-vector similarity of 1.0000 between `MakePayment_HighCost_LowRel` and `MakePayment`; the same value is obtained for the other two variants when the project's `get_functional_subvector` is applied to them.

**Figure 4** shows the operational attributes of the four variants and their effect on the embedding.

![](plots/operational_attributes.png){ width=100% }

**Figure 4: Operational attributes of the `MakePayment` variants and their effect on the embedding.** (A) Cost–reliability positions with bubble size = execution time and colour = risk; (B) Euclidean distance of the operational subspace from the baseline (0.250, 0.000, 0.165, 0.570); (C) execution time and resource cost; (D) functional sub-vector similarity (constant at 1.0) compared with the full-vector cosine similarity (0.998, 1.000, 0.999, 0.989).

### 9.7 Overall evaluation

**Summary of the nine criteria** (`results/metrics_summary.csv`):

| # | Criterion | Metric | Measured value | Reported flag |
|---|---------------|--------------------------------------|--------------------|------------------------|
| 1 | Identity | Capabilities / pairs compared | 15 / 105 | |
| | | Identical-representation pairs | 0 | `identity_preserved = True` |
| | | Min / mean / max pairwise cosine distance | 0.0009 / 0.7017 / 0.9357 | |
| 2 | State relationship | `CreateOrder` applicable in $S_I$ | True | |
| | | `MakePayment` applicable in $S_I$ / after `CreateOrder` | False / True | |
| | | Alignment (cosine) of empirical encoded state change and effect subspace | 0.9608 | `state_awareness_verified = True` (threshold 0.85) |
| 3 | Compatibility separation | Mean score, 4 labelled-compatible pairs | 0.4833 | |
| | | Mean score, 4 labelled-incompatible pairs | 0.1500 | |
| | | Separation margin | 0.3333 | `perfect_separation = False` |
| 4 | Input–output compatibility | Overlap `CreateOrder` outputs → `MakePayment` inputs | 1.0 | |
| | | Overlap `PlayMusic` outputs → `MakePayment` inputs | 0.0 | `data_dependency_detected = True` |
| 5 | Composition fidelity | Cost / reliability aggregation correct | True / True | |
| | | Net effects in composite | 5 | |
| | | Composite vs. component sum vector | 0.7396 | `composition_valid = True` |
| 6 | Goal relevance | Mean relevant / mean irrelevant / gap | 0.3684 / 0.0000 / 0.3684 | `goal_discrimination_accurate = True` |
| 7 | Operational sensitivity | Functional similarity (std vs. high-cost variant) | 1.0000 | |
| | | Operational distance: std vs. high-cost / std vs. economy | 0.5700 / 0.2498 | `operational_sensitivity_verified = True` (distance > 0.10 and functional similarity > 0.99) |
| 8 | Consistency | Max run-to-run difference over 3 encodings | 0.0 | `consistency_verified = True` |
| 9 | Efficiency | Dimension / memory per vector | 108 / 864 bytes | |
| | | Encoding / similarity / compatibility / composition latency (µs) | 35.64 / 7.57 / 111.14 / 29.44 | |
| | | Throughput (embeddings per second) | 28 055 | |

(The efficiency latencies above are those stored in the shipped `metrics_summary.csv`. A fresh execution of `main.py` produced 31.94 / 6.17 / 98.49 / 26.35 µs and 31 313 embeddings/s; all other values in this table were reproduced exactly.)

**Table 9.7b – Pairs used for the compatibility-separation criterion** (stateless evaluation, no context state; cosine similarity from the 108-dimensional vectors):

| Labelled as | Source → Target | Compat. score | $S_{E\to P}$ | $S_{O\to I}$ | Decision | Cosine similarity |
|-----------|------------------------------|---------:|-------:|-------:|:-------------------:|-----------:|
| compatible | CreateOrder → MakePayment | 0.6833 | 0.6667 | 0.5000 | Compatible | 0.0754 |
| compatible | MakePayment → SendNotification | 0.4500 | 0.5000 | 0.0000 | Compatible | 0.2637 |
| compatible | MakePayment → GenerateInvoice | 0.6000 | 0.5000 | 0.5000 | Compatible | 0.3332 |
| compatible | CheckInventory → CreateOrder | 0.2000 | 0.0000 | 0.0000 | **Incompatible** | 0.3974 |
| incompatible | CreateOrder → CancelCart | 0.0000 | 0.0000 | 0.0000 | Incompatible (2 conflicts) | 0.6164 |
| incompatible | SendNotification → MakePayment | 0.2000 | 0.0000 | 0.0000 | Incompatible | 0.2637 |
| incompatible | UpdateProfile → MakePayment | 0.2000 | 0.0000 | 0.0000 | Incompatible | 0.1746 |
| incompatible | PlayMusic → MakePayment | 0.2000 | 0.0000 | 0.0000 | Incompatible | 0.2166 |

(The per-pair scores in this table were obtained by evaluating the same pairs with the project's own `CompatibilityEngine`; the suite itself prints only the means. Mean of the first four scores: 0.4833; of the last four: 0.1500, matching `metrics_summary.csv`.)

**Note on the columns of `experiment_results.csv`.** The CSV uses one common schema for all experiments, so some columns are re-used or filled with constants: for Experiment 3, `compatibility_score` holds the *functional* similarity and `goal_relevance` is the constant 0.5; for Experiment 4, `similarity` holds the vector alignment and `compatibility_score` the symbolic coverage, and `compatible` means relevance $>0.3$; for Experiments 2 and 5, `compatibility_score` and `goal_relevance` are the constant 1.0 and are not computed measurements. Only the values reported in Sections 9.2–9.6 above are computed quantities.

---

## 10. Analysis

### 10.1 Identity preservation

The results indicate that all 15 capabilities receive distinct representations: no pair of the 105 pairs has an identical vector, and the mean pairwise cosine distance is 0.7017. The weakest point is that some pairs are nearly identical: the smallest distance (0.0009) occurs between `MakePayment` and `MakePayment_Enterprise`, whose contracts are identical and which differ only in operational values. The identity criterion as implemented (distance $\geq10^{-6}$) is therefore a weak test; it shows that vectors are not identical, but it does not show that the distances are large enough to be robust against noise. This closeness is consistent with the design intent in Experiment 5 (same function, different operational profile), but it also means that identity in the sense of "clearly separable" is not established for such variants by this metric.

### 10.2 State awareness

The evaluation shows that applicability and state change are represented consistently: `CreateOrder` is applicable in $S_I$, `MakePayment` is not, and `MakePayment` becomes applicable after `CreateOrder` executes. The alignment of 0.9608 between the encoded state change and the effect subspace of `CreateOrder` exceeds the threshold of 0.85 used by the suite, which suggests that the effect subspace is a good approximation of the encoded state change. The alignment is below 1 because the effect encoding assigns $-0.5$ to the displaced status value `Order.status:PAID`, whereas the empirical state change is 0 on that slot (the order was never `PAID` before). The test examines one capability only, so it should be read as an illustration rather than a general measurement of state awareness.

### 10.3 Compatibility and the imperfect separation

Experiment 1 demonstrates the intended behaviour on the two required pairs: `CreateOrder → MakePayment` is accepted (0.6833) and `CreateOrder → CancelCart` is rejected (0.0000, with two explicit conflicts).

The aggregate separation result is, however, **not perfect**. The mean score of the labelled-compatible pairs (0.4833) is higher than that of the labelled-incompatible pairs (0.1500), a margin of 0.3333, but `perfect_separation` is `False`. Table 9.7b shows why: (i) the pair `CheckInventory → CreateOrder`, which the suite labels as compatible, receives a score of 0.2000 and a *not compatible* decision, because the single effect of `CheckInventory` (`Inventory.available := True`) does not establish any of the three preconditions of `CreateOrder` (`Cart.exists`, `Cart.item_count > 0`, `Cart.locked == False`), and no output of `CheckInventory` feeds `CreateOrder`; the label reflects the intuitive workflow order, whereas the engine tests logical support; (ii) three pairs labelled incompatible (`SendNotification → MakePayment`, `UpdateProfile → MakePayment`, `PlayMusic → MakePayment`) have a non-zero score of 0.2000 even though the Boolean decision is *incompatible*; this value is the constant contribution of the state term ($0.20\times1.0$) when no conflict is found and no context state is supplied; (iii) the strict criterion `min(compatible) > max(incompatible)` therefore fails (0.2000 is not greater than 0.2000). In terms of Boolean decisions, 3 of the 4 labelled-compatible pairs and 4 of the 4 labelled-incompatible pairs are classified as labelled (7 of 8 pairs). The observed results suggest that the Boolean decision is more discriminative than the numeric score, and that the numeric score has a floor of 0.2 for non-conflicting but unrelated pairs. This is a limitation of the current score design and has not been adjusted.

A further observation concerns the Boolean rule. Without a context state it accepts a pair if the effects support at least *some* of the target's preconditions ($S_{E\to P}>0$); for `CreateOrder → MakePayment` the precondition `Payment.status == NOT_STARTED` is not established by the effects, yet the pair is accepted. With a context state (Figure 2), the rule is stricter and also requires that the source is executable in that state, which is why `MakePayment → SendNotification` is accepted in the stateless evaluation and inside the sequential composition but rejected in the single-step matrix evaluated at $S_I$. The two modes answer different questions and should not be compared directly.

### 10.4 Input–output relationships

The input–output overlap is 1.0 for `CreateOrder → MakePayment` and 0.0 for `PlayMusic → MakePayment`, which demonstrates that the shared data-entity vocabulary can express data dependencies. In the compatibility score the corresponding $S_{O\to I}$ is only 0.5 for `CreateOrder → MakePayment` because `MakePayment` also requires `payment_details`, which no earlier capability produces. The result for `MakePayment → SendNotification` ($S_{O\to I}=0$) shows a limitation of a purely pairwise input check: the required input `order_id` was produced two steps earlier. The composition engine handles this correctly (it treats `order_id` as an internal data flow), but the pairwise score does not.

### 10.5 Capability composition

The evaluation shows that the composition rules are implemented as specified: cost and reliability aggregation match the expected sum (0.1150) and product (0.95550), the composite has five net effects, and its remaining preconditions are exactly those not established by the pipeline. This criterion, however, tests the aggregation arithmetic and the contract construction; it does not establish that the composite vector is a faithful *geometric* summary of its parts. The composite vector has moderate cosine similarity with each component (0.4372–0.5190) and 0.7396 with the sum/average vector. The per-subspace comparison shows why the similarity is not higher: the composite's type is `SERVICE` while no component has that type (type similarity 0), the composite's mechanism subspace is zero because `COMPOSITE_PIPELINE` is outside the mechanism catalogue, and the effect subspace of the composite reflects net effects (e.g. `PAID` rather than `CREATED`). The results therefore suggest that the composite is representable in the same space, but that the choice of type and mechanism encoding for composites limits how closely the composite vector tracks its components.

### 10.6 Goal relevance

The experiment demonstrates a separation between goal-contributing capabilities (0.3281–0.4309) and the others (0.0). All three relevant capabilities score below 0.5, because each satisfies only one of three unmet conditions (symbolic coverage 1/3): the score measures *direct, single-step* goal contribution. Consequences visible in the results: (i) `CreateOrder`, a necessary prerequisite for payment, receives the lowest relevance of the three; (ii) `GenerateInvoice` and `CheckInventory`, which the experiment labels semi-relevant, receive exactly 0.0, the same as the irrelevant capabilities, so the score does not separate "indirectly helpful" from "unrelated"; (iii) the gap of 0.3684 is large relative to the score range of the relevant group, but the absolute scores are modest. The ordering among the relevant capabilities is also influenced by the vector-alignment term, which depends on the geometry of the effect subspace (for instance `SendNotification` has a single-slot effect vector that aligns more strongly with the goal-gap vector than `CreateOrder`, whose effect vector also has non-zero entries outside the goal gap, namely `Cart.locked` and the `Order.status` slots), rather than on the contribution of the capability to the plan.

### 10.7 Alternative implementations

The functional sub-vectors of `CreateOrderAPI`, `CreateOrderDatabase` and `CreateOrderGUI` are identical (similarity 1.0000), while the full-vector similarities are 0.7634–0.7915. The experiment demonstrates that the representation can express "same function, different mechanism": the difference lies in the type, resource, constraint, mechanism and operational subspaces. At the same time, an overall similarity of 0.76–0.79 is of the same order as that of `CreateOrder` with the functionally conflicting `CancelCart` (0.6164), which shows that the full-vector similarity alone cannot distinguish functionally equivalent alternatives from functionally conflicting capabilities; the functional sub-vector (and the compatibility function) is needed for that. Also note that the three variants are functionally identical but *not* composable in sequence (Section 6.4).

### 10.8 Operational attributes

The operational subspace responds to changes in cost, time, risk, reliability and availability: distances from the baseline range from 0.1646 (`Enterprise`) to 0.5700 (`HighCost_LowRel`) and identify `MakePayment_HighCost_LowRel` as the variant that differs most from the baseline. However, the effect on the **full-vector cosine similarity** is small (0.9887–0.9991), because the six operational entries are a small part of the 108-dimensional vector and the remaining subspaces are identical. The observed results suggest that operational differences are clearly visible in the operational sub-vector but are strongly diluted in the full-vector cosine. Operational comparisons should therefore be made on the operational sub-vector (or with an explicit weighting), not on the overall similarity. It should also be noted that the operational distance is not ordered by "quality": `Enterprise` (better on reliability, availability and time, but more expensive) is closer to the baseline (0.1646) than `Economy` (0.2498), simply because the distance is symmetric and magnitude-based; it measures *difference*, not *preference*.

### 10.9 Similarity versus composability

The experiments consistently support the central distinction. Cosine similarity ranks `CreateOrder` closest to its own alternatives and to `CancelCart` (0.62), and nearly orthogonal to `MakePayment` (0.08), whereas compatibility accepts `MakePayment` and rejects `CancelCart` and `CreateOrder` itself (similarity 1.0, compatibility 0.0). Furthermore, compatibility is directional (`MakePayment → CreateOrder` is rejected although the similarity is the same). These results indicate that similarity should not be used as a proxy for composability in this representation. They also show that the vector subspaces (effect, precondition, input, output) *support* the compatibility computation, but the final decision relies on the symbolic conflict check and the state simulation as well; the contribution of the vectors alone is partial.

### 10.10 Computational efficiency and determinism

Encoding a capability costs about 32–36 µs, a cosine similarity about 6–8 µs, a compatibility evaluation about 98–111 µs and a composition about 26–29 µs in the two measured executions; a vector occupies 864 bytes. These figures suggest that the approach is lightweight at the scale of this dataset, with the caveat that they are single-machine measurements that differ between executions and were obtained on 15 capabilities only. The consistency check (maximum difference 0.0 over three encodings) is expected for a rule-based encoder without random components, so it confirms the absence of nondeterminism rather than providing a statistical result.

---

## 11. Limitations

1. **Handcrafted, rule-based encoding.** All subspace layouts and encoding rules were designed by hand; there are no learned parameters. The representation cannot adapt to data, and its quality depends on the design choices (e.g. the $-0.5$ convention for displaced status values, the clipping and normalisation bounds).
2. **Fixed 108-dimensional representation and predefined vocabularies.** The dimensions follow from fixed catalogues (9 types, 17 data entities, 17 state slots, 8 resources, 7 constraints, 10 mechanisms, 6 operational entries). Entities, state variables, resources or constraints outside these catalogues cannot be represented (the encoder silently ignores unknown names). Adding a new domain or variable changes the dimensionality.
3. **Domain dependence and limited dataset.** All experiments use a single e-commerce domain with 15 capabilities, one initial state and one goal. The results do not show how the representation behaves for other domains, larger capability sets, or different goals.
4. **Limited experimental scale and labelled pairs.** The compatibility-separation criterion uses only four labelled-compatible and four labelled-incompatible pairs, and the labels themselves are specified by the experimenter; one of them (`CheckInventory → CreateOrder`) is not reproduced by the engine (Section 10.3). No statistical analysis is possible at this scale.
5. **Manually specified symbolic relationships.** Compatibility depends on a symbolic conflict check and a state simulation in addition to the vectors; effects, preconditions and conflict conditions are provided by hand in the capability definitions. The conflict check covers only SET effects against `==` and `!=` preconditions.
6. **Limits of vector similarity for logical compatibility.** The experiments show that cosine similarity cannot decide composability; in turn, the compatibility score is a weighted heuristic (weights 0.50/0.30/0.20 chosen by the authors, not tuned) with a floor of 0.2 for non-conflicting pairs and a lenient stateless Boolean rule (partial support suffices). It is not a proof of executability.
7. **Pairwise compatibility is local.** The pairwise input–output check considers only consecutive capabilities; it does not account for data produced earlier in a longer pipeline (Section 10.4).
8. **Goal relevance is single-step.** The score measures the direct contribution of one capability's effects to unmet goal conditions; it does not model multi-step dependencies, so prerequisites and auxiliary capabilities receive low or zero relevance.
9. **Composite encoding gaps.** The composite is typed `SERVICE` and uses mechanism `COMPOSITE_PIPELINE`, which is outside the mechanism catalogue, so the composite's mechanism subspace is zero; composition is purely sequential (no branching, parallelism or loops).
10. **Operational attributes are partially embedded and diluted.** The energy cost is not part of the operational subspace; aggregation rules assume independent success and serial availability; operational differences have little effect on the full-vector cosine (Section 10.8).
11. **Evaluation criteria are partly weak or threshold-based.** The identity criterion only checks that vectors are not identical; the state-awareness verdict uses a threshold (0.85) chosen by the authors; the composition check verifies the aggregation arithmetic; the determinism flag is a fixed constant in the code supported by a three-encoding comparison.
12. **Machine-dependent runtime measurements.** Latencies and throughput depend on the machine, Python/NumPy versions and system load; two executions of the same code produced different values (e.g. encoding 35.64 µs vs. 31.94 µs).
13. **Terminal/CSV-based demonstration.** The project is executed from the command line; results are read from terminal output, CSV files and static plots, which limits interactive exploration of the embedding space.

---

## 12. Conclusion

This report addressed the problem of representing formally specified application states, goals and executable capabilities in a vector space so that compatibility, composition, goal relevance, alternative implementations and operational properties can be analysed, and in which semantic similarity is not mistaken for composability. The implemented solution is a deterministic, rule-based **108-dimensional structured capability embedding** composed of nine subspaces (type 9, input 17, output 17, precondition 17, effect 17, resource 8, constraint 7, operational 6, mechanism 10), with 17-dimensional state and goal encodings aligned to the precondition and effect subspaces. The formal model consists of the application tuple $A=(S,C,S_I,G,R,K)$ and the capability tuple $C_i=(T_i,I_i,O_i,P_i,E_i,K_i,R_i,Q_i,Rel_i,A_i,M_i)$.

Compatibility is computed by a directed function that combines a symbolic conflict check, an effect-to-precondition vector score, an output-to-input score and a state-simulation score with weights 0.50, 0.30 and 0.20. Composition builds a composite capability by aggregating contracts and operational properties (sums for cost, time and resources, a product for reliability and availability, a union model for risk) and encodes it with the same encoder. Goal relevance combines symbolic goal coverage with vector alignment to the goal gap (0.60/0.40). Operational attributes are represented in a bounded six-dimensional subspace.

The experiments gave the following findings. `CreateOrder → MakePayment` is compatible (0.6833, cosine similarity 0.0754) and `CreateOrder → CancelCart` is incompatible (0.0000, cosine similarity 0.6164). The composition `CreateOrder → MakePayment → SendNotification` yields a composite with five net effects, cost 0.1150, execution time 370 ms, reliability 0.95550 and availability 0.99000, and a vector with cosine similarity 0.4372–0.5190 to its components and 0.7396 to the component sum. The three order-creation alternatives have functional similarity 1.0000 and overall similarity 0.7634–0.7915. Relevant capabilities scored 0.3281–0.4309 while the others scored 0.0000 (gap 0.3684). Operational variants of `MakePayment` have operational distances of 0.1646–0.5700 from the baseline but full-vector similarities of 0.9887–0.9991. In the nine-criterion evaluation, identity (0 identical pairs), state relationship (alignment 0.9608), input–output dependency, composition fidelity, goal discrimination, operational sensitivity and determinism were reported as satisfied, while compatibility separation was **not perfect** (mean 0.4833 vs. 0.1500; `perfect_separation = False`).

The limitations are that the encoding is handcrafted with fixed vocabularies, the study covers a single domain and a small set of capabilities, pairwise checks and goal relevance are local, the composite's mechanism and type encoding is limited, the operational effect is diluted in the full vector, and runtime figures are machine-dependent. Within these limits, the results suggest that a structured, partitioned vector representation together with a separate compatibility function can support capability composition reasoning for the evaluated domain, with similarity and composability treated as distinct notions.

---

## References

[1] R. E. Fikes and N. J. Nilsson, "STRIPS: A new approach to the application of theorem proving to problem solving," *Artificial Intelligence*, vol. 2, no. 3–4, pp. 189–208, 1971.

[2] M. Ghallab, D. Nau and P. Traverso, *Automated Planning: Theory and Practice*, Morgan Kaufmann, 2004.

[3] D. Martin et al., "OWL-S: Semantic Markup for Web Services," W3C Member Submission, 2004.

[4] T. Mikolov, K. Chen, G. Corrado and J. Dean, "Efficient estimation of word representations in vector space," arXiv:1301.3781, 2013.

[5] J. Devlin, M.-W. Chang, K. Lee and K. Toutanova, "BERT: Pre-training of deep bidirectional transformers for language understanding," in *Proc. NAACL-HLT*, 2019 (arXiv:1810.04805).

[6] N. Reimers and I. Gurevych, "Sentence-BERT: Sentence embeddings using Siamese BERT-networks," in *Proc. EMNLP-IJCNLP*, 2019.

[7] G. E. Hinton, J. L. McClelland and D. E. Rumelhart, "Distributed representations," in *Parallel Distributed Processing*, vol. 1, MIT Press, 1986.

[8] A. Bordes, N. Usunier, A. Garcia-Durán, J. Weston and O. Yakhnenko, "Translating embeddings for modeling multi-relational data," in *Advances in Neural Information Processing Systems 26 (NIPS)*, 2013.

[9] T. N. Kipf and M. Welling, "Semi-supervised classification with graph convolutional networks," in *Proc. ICLR*, 2017 (arXiv:1609.02907).

[10] P. Smolensky, "Tensor product variable binding and the representation of symbolic structures in connectionist systems," *Artificial Intelligence*, vol. 46, no. 1–2, pp. 159–216, 1990.

[11] T. A. Plate, "Holographic reduced representations," *IEEE Transactions on Neural Networks*, vol. 6, no. 3, pp. 623–641, 1995.
