# Deliverable 3: Experimental Dataset Investigation & Search Audit

## 1. Objective of Investigation
According to the assignment specification (Deliverables §9 and Scope §3–4):
> *"Scour the internet first for a dataset that matches our requirements. If not found, then create an experimental dataset. Construct or use formally specified application problems containing initial states, goal specifications, atomic capabilities, capability compositions, relevant constraints, and operational attributes."*

The required capability representation is a comprehensive 11-tuple:
$$C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)$$
operating on a formally specified state space:
$$S = \{(x_1, v_1), (x_2, v_2), \dots, (x_n, v_n)\}$$
with explicit goal conditions:
$$G = \{g_1, \dots, g_m\}$$
and multi-modal execution mechanisms:
$$T_i \in \{\text{API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE}\}$$
accompanied by 5-dimensional operational cost profiles $Q_i = (C_{time}, C_{resource}, C_{money}, C_{risk}, C_{energy})$, reliability $Rel_i \in [0, 1]$, and availability $A_i \in \{0, 1\}$.

---

## 2. Comprehensive Survey of Existing Public Datasets

We performed an exhaustive literature and repository search across four major paradigms in automated service composition and AI planning:

### 2.1 OWLS-TC (OWL-S Test Collection v4.0)
- **Source**: Semantic Web service retrieval test collection maintained by DFKI / University of Saarland / CMU.
- **Coverage**: ~1,080 web service profiles across 9 domains (Economy, Education, Medical, Food, Travel, Communication, Simulation, Weapon, Geography).
- **Format**: OWL-S XML ontologies with IOPE (Inputs, Outputs, Preconditions, Effects expressed in SWRL/KIF).
- **Gap Analysis**:
  - **No Multi-Sector Execution Mechanisms ($T_i, M_i$)**: OWLS-TC exclusively represents WSDL/SOAP-grounded web services. It completely lacks Database operations (SQL queries/inserts), GUI interactions (button clicks/form submits), event handlers, local computations, or system message buses.
  - **No Discrete/Continuous Application State Variables ($S, S_I$)**: OWLS-TC preconditions and effects refer to ontological concepts in description logic rather than structured discrete/continuous state variables (e.g., `Order.exists=True`, `Cart.item_count=3`, `Payment.status=SUCCESS`).
  - **Missing Operational Cost Vector ($Q_i$)**: Does not provide monetary cost, compute resource cost, risk factor, or energy footprint.
  - **Static / Archaic Tooling**: Relies on Jena / OWL-DL reasoning engines from 2007–2010 that are incompatible with modern vectorized machine learning embeddings.

### 2.2 WSC (Web Service Challenge 2008 & 2009 Benchmarks)
- **Source**: IEEE International Conference on e-Business Engineering (ICEBE) WSC datasets.
- **Coverage**: Synthetic repositories ranging from 150 to 8,000 services structured as DAGs of type transformations.
- **Format**: XML taxonomy schemas and service parameter definitions.
- **Gap Analysis**:
  - **Pure I/O Matching, No Preconditions or Effects ($P_i, E_i$)**: WSC models services purely as typed inputs transforming into typed outputs (type-matching DAG). There are no state conditions or world state updates.
  - **No State Awareness ($S, G$)**: No application state space $S$ or goal state predicates.
  - **No Execution Mechanism ($M_i$) or Type Diversity ($T_i$)**: All nodes are generic web services.

### 2.3 QoS-WSC & QWS Dataset (Al-Masri & Mahmoud)
- **Source**: Real-world Web service quality measurements (QWS dataset, 2,507 services measured over 10 QoS metrics).
- **Coverage**: Response time, availability, throughput, reliability, latency, successability.
- **Gap Analysis**:
  - **Pure QoS with No Semantics**: Contains strictly numerical performance telemetry. It contains zero functional semantics: no inputs, outputs, preconditions, effects, or state variables.
  - Cannot evaluate functional compatibility or capability composition.

### 2.4 International Planning Competition (IPC) PDDL Benchmarks
- **Source**: IPC Classical & Temporal Planning domains (Logistics, Rovers, Satellite, Blocksworld, Gripper).
- **Format**: PDDL (Planning Domain Definition Language) domain and problem files.
- **Gap Analysis**:
  - **No Heterogeneous Execution Mechanisms**: Actions in PDDL are abstract operators without type $T_i \in \{\text{GUI, DB, API, EVENT}\}$, endpoints, or mechanism metadata $M_i$.
  - **Oversimplified Metrics**: Typically only supports single unit-action cost or metric-time, missing multidimensional $Q_i = (C_{time}, C_{res}, C_{money}, C_{risk}, C_{energy})$, reliability probabilities $Rel_i \in [0, 1]$, and availability flags.

### 2.5 Modern Tool Datasets (ToolBench, APIBench, RestBench)
- **Source**: LLM agent tool-use datasets (Guan et al., Qin et al., 2023–2024).
- **Format**: OpenAPI / Swagger JSON schemas and natural language instruction prompts.
- **Gap Analysis**:
  - **Designed for Text LLMs, Not Formal Mathematical Embeddings**: Focuses on prompt-in-context argument generation rather than formal mathematical state representations $S$, preconditions $P_i$, and effects $E_i$.
  - Lacks ground truth composition validation, formal reliability attributes, and algebraic composition vectors.

---

## 3. Summary Comparison Matrix

| Dataset / Benchmark | $T_i$ (Types) | $I_i, O_i$ | $P_i, E_i$ | $S, S_I, G$ | $Q_i$ (5D Cost) | $Rel_i, A_i$ | $M_i$ (Mechanism) | Conforms to Spec? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **OWLS-TC v4.0** | Only Service | Yes | DL/SWRL | No | No | No | Only WSDL | **No** |
| **WSC 2008/2009** | None | Yes | No | No | No | No | None | **No** |
| **QWS / QoS-WSC** | None | No | No | No | Partial | Yes | None | **No** |
| **IPC PDDL** | None | No | Predicates | Predicates | 1D only | No | None | **No** |
| **ToolBench** | Only API | Schemas | No | No | No | No | REST only | **No** |
| **Assignment Spec** | **9 Types** | **Yes** | **Yes** | **Yes** | **5-tuple** | **Yes** | **Multi-Modal** | **Required** |

---

## 4. Conclusion & Decision to Construct the Experimental Dataset
Because **no existing public dataset** satisfies the formal specification of the problem-specific 11-tuple $C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)$ and the Cartesian/stateful application model $A = (S, C, S_I, G, R, K)$, we proceed to **create a rigorous, multi-domain experimental benchmark suite** directly fulfilling Deliverable 3:

1. **`ecommerce_benchmark.json`**:
   The primary application domain formulated in the assignment text (User auth, cart management, inventory verification, order creation, payment gateway, notification dispatch, order cancellation).
2. **`cloud_devops_benchmark.json`**:
   A realistic systems engineering domain (VPC networking, VM provisioning, block storage attachment, container deployment, service health checks, metrics monitoring, alert emission).
3. **`fintech_kyc_benchmark.json`**:
   A regulated financial workflows domain (Customer KYC verification, risk scoring, AML screening, ledger debit/credit, clearing and instant settlement).
4. **`alternative_implementations.json`**:
   Explicit multi-modal variants (API, Database, and GUI implementations) designed specifically to evaluate Experiment 3.
