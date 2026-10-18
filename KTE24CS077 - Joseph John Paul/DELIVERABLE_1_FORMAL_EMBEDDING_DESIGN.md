# Deliverable 1: Formal Embedding Design for Capability Composition

**University Course Registration System**  
**Author / Student Implementation Documentation**  
**Language / Target**: C++17  

---

## 1. Introduction

In modern distributed software architectures and service-oriented systems, software capabilities (services, APIs, functions, database queries) must be dynamically discovered, evaluated, and composed to satisfy high-level operational goals. Traditional capability composition relies either on purely syntactic signature matching or heavyweight state-space planning algorithms. 

This document defines a **problem-specific, deterministic, and interpretable vector embedding** designed to capture both the functional semantics (preconditions, effects, inputs, outputs) and operational non-functional characteristics (execution mechanisms, underlying resources, constraints, cost, reliability, and availability) of software capabilities within a **University Course Registration System**.

---

## 2. Problem Definition

Given an application domain characterized by formal states, operational constraints, and target goals, the problem is to construct a fixed-dimensional vector representation that:
1. Preserves state applicability semantics ($S \models P_C$).
2. Preserves state transitions ($S' = \text{Apply}(S, E_C)$).
3. Distinguishes functional equivalence from implementation divergence.
4. Models operational Quality-of-Service (QoS) attributes.
5. Enables state-aware sequential capability composition without relying on black-box neural networks or external embeddings.

---

## 3. Formal Application Model

The domain is formally defined as a 6-tuple:

$$
A = (S, C, S_I, G, R, K)
$$

where:
* $S$: The formal state space over a fixed set of domain predicates.
* $C$: The repository of executable capabilities $\{C_1, C_2, \dots, C_{11}\}$.
* $S_I \in S$: The initial state of the registration system.
* $G$: The target goal specification.
* $R$: The set of system infrastructure resources.
* $K$: The set of system policies and validity constraints.

---

## 4. State Representation

A complete state $S \in S$ is represented by a valuation over exactly **11 Boolean state predicates** in a fixed order:

| Index | State Predicate Name | Semantic Meaning |
| :---: | :--- | :--- |
| `0` | `student_authenticated` | Student identity is verified via authentication service. |
| `1` | `student_exists` | Student record exists in the institutional database. |
| `2` | `student_eligible` | Student satisfies academic and administrative prerequisites. |
| `3` | `course_exists` | Course catalog entry is valid and recognized. |
| `4` | `course_available` | Course has open seats and is scheduled for registration. |
| `5` | `registration_open` | Active registration semester window is open. |
| `6` | `enrollment_exists` | Student has an active enrollment hold / reservation. |
| `7` | `payment_completed` | Tuition / registration fees are settled. |
| `8` | `notification_sent` | Registration receipt and timetable notification delivered. |
| `9` | `registration_confirmed` | Registration is locked and finalized in records. |
| `10` | `registration_report_generated` | Administrative audit report generated on file system. |

For complete states:

$$
S[i] \in \{\text{true}, \text{false}\}
$$

---

## 5. Goal Representation

A goal $G$ expresses desired predicate valuations over the same 11-predicate vocabulary. Unlike complete states, goals often leave irrelevant predicates unspecified. Hence, goals use ternary logic:

$$
G[i] \in \{-1, 0, +1\}
$$

where:
* $+1$: Predicate must evaluate to `TRUE`.
* $-1$: Predicate must evaluate to `FALSE`.
* $0$: Predicate is irrelevant to the goal.

The primary registration goal is:

$$
G_{\text{primary}} = [0, 0, 0, 0, 0, 0, +1, +1, +1, +1, 0]
$$

Goal satisfaction condition:

$$
S \models G \iff \forall i \in [0, 10], \quad (G[i] = +1 \implies S[i] = \text{true}) \land (G[i] = -1 \implies S[i] = \text{false})
$$

---

## 6. Capability Representation

Each capability $C \in C$ is defined as a structured entity:

$$
C = \langle \text{id}, \text{name}, \text{type}, P, E, I, O, R, K, M, Q \rangle
$$

where:
* $P \in \{-1, 0, +1\}^{11}$: Preconditions.
* $E \in \{-1, 0, +1\}^{11}$: Effects.
* $I \in \{0, 1\}^5$: Required data inputs.
* $O \in \{0, 1\}^8$: Produced data outputs.
* $R \in \{0, 1\}^8$: Consumed/required system resources.
* $K \in \{0, 1\}^5$: Enforced policies/constraints.
* $T \in \{0, 1\}^6$: One-hot capability type.
* $M \in \{0, 1\}^8$: One-hot mechanism.
* $Q = [Cost_{\text{norm}}, \text{Reliability}, \text{Availability}] \in \mathbb{R}^3$: Operational vector.

### Why Ternary Logic is Necessary
Binary representation ($\{0, 1\}$) cannot distinguish between:
1. "Requires predicate to be FALSE" (negative precondition, e.g., `payment_completed == false` for `DropCourse`).
2. "Predicate is irrelevant / unconstrained" (value $0$).

Therefore, ternary encoding ($\{-1, 0, +1\}$) is mathematically mandatory for precondition and effect vectors.

---

## 7. Input and Output Representation

* **Input Vocabulary ($I \in \{0, 1\}^5$)**:
  `0: student_id`, `1: course_id`, `2: enrollment_id`, `3: payment_details`, `4: registration_details`.
* **Output Vocabulary ($O \in \{0, 1\}^8$)**:
  `0: eligibility_status`, `1: availability_status`, `2: enrollment_id`, `3: payment_receipt`, `4: notification_id`, `5: confirmation_id`, `6: drop_confirmation`, `7: registration_report`.

---

## 8. Resource Representation

* **Resource Vocabulary ($R \in \{0, 1\}^8$)**:
  `0: StudentDatabase`, `1: CourseDatabase`, `2: RegistrationDatabase`, `3: AuthenticationService`, `4: PaymentGateway`, `5: Network`, `6: NotificationService`, `7: FileSystem`.

---

## 9. Constraint Representation

* **Constraint Vocabulary ($K \in \{0, 1\}^5$)**:
  `0: authentication_required`, `1: registration_period_required`, `2: positive_payment`, `3: valid_student`, `4: valid_course`.

---

## 10. Capability Type Representation

* **Capability Types ($T \in \{0, 1\}^6$, One-Hot)**:
  `0: API`, `1: DATABASE`, `2: FUNCTION`, `3: SERVICE`, `4: COMPUTATION`, `5: GUI`.

---

## 11. Mechanism Representation

* **Mechanism Channels ($M \in \{0, 1\}^8$, One-Hot)**:
  `0: MECH_LOCAL_FUNCTION` (In-memory logic: `EligibilityFunction`, `ConfirmationFunction`, `localAvailabilityFunction`)  
  `1: MECH_SQL_DATABASE_QUERY` (SQL queries: `DatabaseQuery`, `SELECT availability FROM courses`)  
  `2: MECH_REST_POST_REGISTRATION` (`POST /registration`)  
  `3: MECH_REST_POST_PAYMENT` (`POST /payment`)  
  `4: MECH_REST_GET_AVAILABILITY` (`GET /courses/{id}/availability`)  
  `5: MECH_NOTIFICATION_SERVICE` (`NotificationService`)  
  `6: MECH_REST_DELETE_REGISTRATION` (`DELETE /registration`)  
  `7: MECH_REPORT_GENERATOR` (`ReportGenerator`)  

---

## 12. Operational Representation

The operational vector $Q(C) \in \mathbb{R}^3$ models Quality-of-Service attributes:

$$
Q(C) = [Cost_{\text{norm}}, Reliability, Availability]
$$

where:
* $Cost_{\text{norm}} = \frac{Cost}{20.0} \in [0.0, 1.0]$ (normalized by the maximum individual capability cost $Cost_{\max} = 20.0$).
* $Reliability \in [0.0, 1.0]$: Probability of successful execution.
* $Availability \in [0.0, 1.0]$: Service uptime ratio.

---

## 13. State Embedding $\phi_S$

$$
\phi_S : S \rightarrow \{-1, +1\}^{11}
$$

$$
\phi_S(S)[i] = \begin{cases} +1.0 & \text{if } S[i] = \text{true} \\ -1.0 & \text{if } S[i] = \text{false} \end{cases}
$$

---

## 14. Goal Embedding $\phi_G$

$$
\phi_G : G \rightarrow \{-1, 0, +1\}^{11}
$$

$$
\phi_G(G)[i] = static\_cast<double>(G[i])
$$

---

## 15. Functional Capability Embedding $\phi_F$

The functional embedding captures **what** a capability achieves, independent of implementation:

$$
\phi_F(C) = [P, E, I, O] \in \mathbb{R}^{35}
$$

$$
\dim(\phi_F) = 11 + 11 + 5 + 8 = 35
$$

---

## 16. Full Capability Embedding $\phi_C$

The full capability embedding concatenates functional and non-functional feature blocks:

$$
\phi_C(C) = [P, E, I, O, R, K, T, M, Q] \in \mathbb{R}^{65}
$$

$$
\dim(\phi_C) = 11 + 11 + 5 + 8 + 8 + 5 + 6 + 8 + 3 = 65
$$

```
+-------------------------------------------------------------------------------------------------------+
|                                  Full Capability Embedding phi_C (65 dims)                           |
+-----------+-----------+---------+---------+-----------+-------------+----------+-------------+--------+
|   P (11)  |   E (11)  |  I (5)  |  O (8)  |   R (8)   |    K (5)    |  T (6)   |    M (8)    |  Q (3) |
| Preconds  |  Effects  |  Inputs | Outputs | Resources | Constraints | Type 1hot| Mech. 1-hot | QoS    |
+-----------+-----------+---------+---------+-----------+-------------+----------+-------------+--------+
|                                    Functional Embedding phi_F (35 dims)                              |
+-------------------------------------------------------------------------------------------------------+
```

---

## 17. Similarity Measures

### Cosine Similarity
For any two vectors $A, B \in \mathbb{R}^d$:

$$
Sim(A, B) = \begin{cases} 
\frac{A \cdot B}{\|A\| \|B\|} & \text{if } \|A\| > 0 \land \|B\| > 0 \\
1.0 & \text{if } \|A\| = 0 \land \|B\| = 0 \\
0.0 & \text{otherwise}
\end{cases}
$$

### Block-Level Similarity
To prevent high-dimensional blocks from overwhelming smaller ones:

$$
Sim_{\text{overall}}(C_1, C_2) = \frac{1}{9} \sum_{X \in \{P, E, I, O, R, K, T, M, Q\}} Sim(X(C_1), X(C_2))
$$

---

## 18. Compatibility Measures

### Direct Effect-Precondition Compatibility
Measures the fraction of $C_2$'s preconditions directly supplied by $C_1$'s effects:

$$
Comp_{EP}(C_1, C_2) = \frac{|\{i \mid P_2[i] \neq 0 \land E_1[i] = P_2[i]\}|}{|\{i \mid P_2[i] \neq 0\}|}
$$

### Input-Output Compatibility
Measures data-flow coupling:

$$
IOComp(C_1, C_2) = \frac{O(C_1) \cdot I_{\text{flow}}(C_2)}{|I_{\text{flow}}(C_2)|}
$$

For $C_3 \to C_4$, $C_3$ outputs `enrollment_id` and $C_4$ requires `enrollment_id`, yielding $IOComp = 1.0$.

---

## 19. State-Aware Applicability

A capability $C$ is applicable in state $S$ if and only if $S$ satisfies all preconditions $P_C$:

$$
Applicable(C, S) \iff \forall i \in [0, 10]: \begin{cases} 
P_C[i] = +1 \implies S[i] = \text{true} \\
P_C[i] = -1 \implies S[i] = \text{false} \\
P_C[i] = 0 \implies \text{true}
\end{cases}
$$

---

## 20. State Transition

Applying capability $C$ to state $S$ yields new state $S'$:

$$
S' = \text{Apply}(S, E_C)
$$

where:

$$
S'[i] = \begin{cases}
\text{true} & \text{if } E_C[i] = +1 \\
\text{false} & \text{if } E_C[i] = -1 \\
S[i] & \text{if } E_C[i] = 0
\end{cases}
$$

---

## 21. Capability Composition

Composition is **state-aware** rather than vector addition. The sequential pair $C_1 \to C_2$ is valid in state $S$ if and only if:

$$
Applicable(C_1, S) \land Applicable(C_2, \text{Apply}(S, E_1))
$$

```mermaid
graph LR
    S0((State S0)) -->|C1 CheckEligibility| S1((State S1))
    S1 -->|C2 CheckCourseAvail| S2((State S2))
    S2 -->|C3 RegisterCourse| S3((State S3))
    S3 -->|C4 MakePayment| S4((State S4))
    S4 -->|C5 SendNotification| S5((State S5))
    S5 -->|C6 ConfirmRegistration| S6((State S6 |= Goal))
```

---

## 22. Goal Relevance

The direct goal relevance $GoalRel(C, G)$ measures how many required goal predicates are produced by $C$:

$$
GoalRel(C, G) = \frac{|\{i \mid G[i] \neq 0 \land E_C[i] = G[i]\}|}{|\{i \mid G[i] \neq 0\}|}
$$

For the 4-predicate primary goal, each of $C_3, C_4, C_5, C_6$ achieves exactly 1 goal condition ($GoalRel = 0.25$). Enabling capabilities ($C_1, C_2$) have direct goal relevance of $0.0$, illustrating that direct goal relevance is orthogonal to execution necessity.

---

## 23. Mathematical Summary

| Entity | Symbol | Target Domain | Dimension |
| :--- | :---: | :---: | :---: |
| State Vector | $\phi_S(S)$ | $\{-1, +1\}^{11}$ | 11 |
| Goal Vector | $\phi_G(G)$ | $\{-1, 0, +1\}^{11}$ | 11 |
| Functional Vector | $\phi_F(C)$ | $\mathbb{R}^{35}$ | 35 |
| Full Capability Vector | $\phi_C(C)$ | $\mathbb{R}^{65}$ | 65 |
| Composite Capability Vector | $\phi_C(C_{\text{comp}})$ | $\mathbb{R}^{65}$ | 65 |

---

## 24. Design Rationale

1. **Interpretable Coordinates**: Every dimension has an exact, human-auditable semantic meaning.
2. **Separation of Concerns**: $\phi_F$ evaluates functional interchangeability, while $\phi_C$ evaluates implementation and QoS compatibility.
3. **Deterministic & Self-Contained**: No stochastic training, drift, or black-box embeddings.

---

## 25. Limitations

1. **Fixed Vocabulary Size**: Expanding predicates or inputs requires structural re-indexing.
2. **Discrete State Assumptions**: Continuous resource quantities (e.g., remaining seat counts) are abstracted into discrete Booleans (`course_available`).
3. **Orthogonal Similarity**: High cosine similarity between capabilities does not imply composability; composability strictly depends on state-aware transitions.
