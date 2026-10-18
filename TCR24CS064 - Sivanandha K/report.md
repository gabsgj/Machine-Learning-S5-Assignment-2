# Design of a Vector Embedding for Capability Composition

## PCCST503 – Assignment 2

---

## 1. Problem Definition

Modern software systems are composed of multiple executable capabilities such as APIs, database operations, GUI actions, functions, events, services, and computational operations. A larger task can therefore be represented as a sequence or composition of smaller capabilities.

The assignment considers an application model:

$$
A = (S,C,S_I,G,R,K)
$$

where:

* \(S\) = set of application states
* \(C\) = set of executable capabilities
* \(S_I\) = initial state
* \(G\) = goal state
* \(R\) = resources
* \(K\) = constraints

A capability contains information such as its type, inputs, outputs, preconditions, effects, resources, constraints, cost, reliability, availability, and execution mechanism.

The main objective of this assignment is to design and implement a problem-specific vector representation for states, goals, and executable capabilities. The representation should preserve important relationships between capabilities so that compatibility, composition, similarity, and goal relevance can be evaluated.

The assignment specifically requires experiments involving:

* Capability compatibility
* Capability composition
* Alternative implementations
* Irrelevant capabilities
* Operational attributes such as cost, reliability, availability, and risk

The assignment also requires the implementation to support functions for encoding states, goals, and capabilities, computing similarity, and composing capabilities.

---

## 2. Design Requirements

The proposed vector representation should satisfy the following requirements.

### 2.1 Capability Identity

Different capability types such as API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, and SERVICE should be distinguishable.

### 2.2 State Awareness

The representation should provide a way to represent the relevant properties of an application state.

### 2.3 Preconditions and Effects

A capability's preconditions determine when it can be executed, while its effects describe the resulting state changes.

### 2.4 Input-Output Compatibility

The output of one capability should be able to satisfy the input requirements of another capability.

### 2.5 Composition

Capabilities should be composable when the outputs and effects of one capability satisfy the inputs and preconditions of the next capability.

### 2.6 Goal Relevance

The representation should allow capabilities to be compared with a goal representation.

### 2.7 Operational Properties

The representation should include operational attributes such as:

* Cost
* Risk
* Reliability
* Availability

These requirements are derived from the required embedding properties and evaluation criteria specified in the assignment.

---

## 3. Related Embedding Approaches

Vector embeddings are commonly used to represent objects as numerical vectors so that mathematical operations such as similarity calculation can be performed.

For this assignment, however, simply applying an existing general-purpose embedding model is not sufficient. The assignment specifically requires the design and justification of a problem-specific representation that preserves capability relationships such as:

* Preconditions
* Effects
* Inputs
* Outputs
* Resources
* Operational properties
* Capability type

Therefore, a structured feature-based vector representation was selected.

The assignment permits either separate mappings for states, goals, and capabilities or a unified representation. A unified feature space was selected for this implementation.

The assignment also explicitly states that merely applying an existing embedding model is insufficient and that the solution should be studied, designed, justified, implemented, and evaluated.

---

## 4. Proposed Vector Representation

### 4.1 Overview

A fixed feature vocabulary is created to represent the important properties of the application domain.

Each state, goal, and capability is represented as a vector:

$$
x \in \mathbb{R}^{44}
$$

The final implementation contains **44 features**.

The features are grouped into the following categories:

1. Capability type
2. Inputs
3. Outputs
4. Preconditions
5. Effects
6. Resources
7. Execution mechanism
8. Cost
9. Risk
10. Reliability
11. Availability

The resulting vector is therefore a structured representation of the semantic and operational properties of a capability.

---

### 4.2 Capability Type Features

The following capability types are represented:

* API
* DATABASE
* GUI
* EVENT
* FUNCTION
* FILE
* COMPUTATION
* MESSAGE
* SERVICE

These correspond to the capability types identified in the assignment.

For example:

```text
type_API
type_DATABASE
type_GUI
type_EVENT
type_FUNCTION
```

A capability activates the feature corresponding to its type.

---

### 4.3 Input Features

Input-related features include:

```text
input_cart_id
input_order_id
input_payment_id
input_quantity
input_customer_id
```

These features represent the data required by a capability.

For example:

```text
CreateOrder
```

requires:

```text
cart_id
```

and therefore activates:

```text
input_cart_id
```

---

### 4.4 Output Features

Output features represent information produced by a capability.

The implementation includes:

```text
output_order_id
output_payment_id
output_notification
output_order_status
output_payment_status
```

For example, `CreateOrder` produces an `order_id`.

The assignment identifies input-output compatibility as an important relationship because the output of one capability may satisfy the input of another capability.

---

### 4.5 Preconditions

Preconditions describe conditions that must hold before a capability can execute.

The implementation represents conditions such as:

```text
precondition_authenticated
precondition_cart_exists
precondition_order_exists
precondition_order_not_exists
precondition_payment_pending
precondition_cart_items
precondition_payment_success
```

For example:

```text
CreateOrder
```

requires:

```text
cart_exists
cart_items
```

while:

```text
MakePayment
```

requires:

```text
order_exists
```

---

### 4.6 Effects

Effects represent the changes produced after executing a capability.

The implementation includes:

```text
effect_order_exists
effect_order_created
effect_payment_success
effect_notification_sent
effect_cart_cancelled
```

For example:

```text
CreateOrder
```

produces:

```text
order_exists
order_created
```

and:

```text
MakePayment
```

produces:

```text
payment_success
```

The assignment identifies precondition-effect relationships as an important requirement for determining capability applicability and state transitions.

---

### 4.7 Resources

Capabilities can require resources such as:

```text
resource_database
resource_network
resource_payment_gateway
resource_authentication
resource_filesystem
```

This allows the representation to distinguish capabilities based on their resource requirements.

---

### 4.8 Execution Mechanism

Execution mechanisms are represented using features such as:

```text
mechanism_POST
mechanism_INSERT
mechanism_CLICK
mechanism_EVENT
```

For example:

```text
CreateOrder
```

uses:

```text
POST
```

while:

```text
CreateOrderDatabase
```

uses:

```text
INSERT
```

---

### 4.9 Operational Attributes

The vector also contains numerical values for:

```text
cost
risk
reliability
availability
```

This allows operational properties to participate in the vector representation.

The assignment specifically requires operational properties to be considered during evaluation.

---

## 5. Mathematical Formulation

Let the feature vocabulary be:

$$
F = \{f_1,f_2,\ldots,f_{44}\}
$$

A capability \(C\) is represented by:

$$
E(C) = [x_1,x_2,\ldots,x_{44}]
$$

where each \(x_i\) represents one feature.

For categorical and boolean features:

$$
x_i =
\begin{cases}
1 & \text{if the feature is present}\\
0 & \text{otherwise}
\end{cases}
$$

Operational properties use their numerical values.

For example:

$$
x_{\text{cost}} = \text{cost}
$$

$$
x_{\text{risk}} = \text{risk}
$$

$$
x_{\text{reliability}} = \text{reliability}
$$

$$
x_{\text{availability}} = \text{availability}
$$

---

### 5.1 Similarity

Cosine similarity is used to compare two vectors.

$$
Similarity(A,B)
=
\frac{A\cdot B}
{\|A\|\|B\|}
$$

where:

* \(A\cdot B\) is the dot product
* \(\|A\|\) is the magnitude of vector \(A\)
* \(\|B\|\) is the magnitude of vector \(B\)

The similarity value increases when two vectors have similar active features.

The implementation returns 0 when one of the vectors has zero magnitude.

---

### 5.2 Compatibility

Vector similarity alone is not used to determine functional compatibility.

Instead, compatibility is explicitly checked using capability semantics.

For capabilities \(C_1\) and \(C_2\):

$$
Compatible(C_1,C_2)=1
$$

when:

$$
Inputs(C_2)\subseteq Outputs(C_1)
$$

and:

$$
Preconditions(C_2)\subseteq Effects(C_1)
$$

Otherwise:

$$
Compatible(C_1,C_2)=0
$$

This distinction is important because two capabilities can be similar without being composable.

The assignment specifically requires similarity and composability to be treated as different concepts.

---

## 6. Capability Composition Model

Capability composition is based on the relationship between outputs/effects of one capability and inputs/preconditions of the next capability.

For two capabilities:

$$
C_1 \rightarrow C_2
$$

the composition is valid when:

$$
Outputs(C_1) \supseteq Inputs(C_2)
$$

and:

$$
Effects(C_1) \supseteq Preconditions(C_2)
$$

The assignment defines composition in terms of satisfying the requirements of one capability using the results of another.

---

### 6.1 Example Composition

The implemented dataset contains the following chain:

```text
CreateOrder
      ↓
MakePayment
      ↓
SendNotification
```

#### Step 1: CreateOrder

Produces:

```text
order_id
order_exists
order_created
```

#### Step 2: MakePayment

Requires:

```text
order_id
order_exists
```

Therefore:

```text
CreateOrder → MakePayment
```

is compatible.

#### Step 3: SendNotification

Requires:

```text
payment_success
```

which is produced by:

```text
MakePayment
```

Therefore:

```text
MakePayment → SendNotification
```

is also compatible.

This creates a valid three-capability composition.

---

## 7. Implementation

The implementation is written in Python using NumPy.

The project provides the following main operations:

### `encode_state(state)`

Converts an application state into a 44-dimensional vector.

### `encode_goal(goal)`

Converts a goal into a 44-dimensional vector.

### `encode_capability(capability)`

Converts a capability into a 44-dimensional vector containing its structural and operational properties.

### `similarity(vector_a, vector_b)`

Calculates cosine similarity between two vectors.

### `compatibility(capability_a, capability_b)`

Checks input-output and precondition-effect compatibility.

### `compose(capabilities)`

Creates a composite capability from multiple capabilities and combines their operational attributes.

The implementation therefore supports the core operations required by the assignment.

---

## 8. Experimental Methodology

The assignment requires experiments covering capability compatibility, composition, alternative implementations, irrelevant capabilities, and operational attributes.

Seven experiments were performed.

### Experiment 1 — Capability Representation

Three capabilities were encoded:

* CreateOrder
* MakePayment
* CancelCart

The vector dimension and number of non-zero features were recorded.

---

### Experiment 2 — Capability Compatibility

The following capability pairs were tested:

```text
CreateOrder → MakePayment
CreateOrder → CancelCart
```

The first pair should be compatible, while the second should not be compatible because the required preconditions are not satisfied.

---

### Experiment 3 — Vector Similarity

The following comparisons were performed:

```text
CreateOrder vs CreateOrderDatabase
CreateOrder vs CancelCart
```

This tests whether the representation can capture similarity between capabilities.

---

### Experiment 4 — Alternative Implementations

Three implementations of the order-creation functionality were compared:

```text
API
DATABASE
GUI
```

The similarities between their vector representations were calculated.

---

### Experiment 5 — Irrelevant Capability

Capabilities were compared with the `CompletePurchase` goal.

The following comparisons were performed:

```text
CreateOrder vs CompletePurchase
CheckInventory vs CompletePurchase
```

This tests whether a relevant capability receives a greater similarity than an unrelated capability.

---

### Experiment 6 — Capability Composition

The following chain was tested:

```text
CreateOrder → MakePayment → SendNotification
```

Compatibility was checked between consecutive capabilities and a composite capability was created.

---

### Experiment 7 — Operational Attributes

The cost, risk, reliability, and availability of several capabilities were compared.

This demonstrates that operational properties are preserved in the representation and composition.

---

## 9. Results

The experiments produced the following results.

### 9.1 Experiment 1 — Capability Representation

```text
CreateOrder -> vector dimension = 44 , non-zero features = 14
MakePayment -> vector dimension = 44 , non-zero features = 14
CancelCart -> vector dimension = 44 , non-zero features = 9
```

All capabilities are represented using the same 44-dimensional vector space.

The different numbers of non-zero features reflect differences in the properties of each capability.

---

### 9.2 Experiment 2 — Capability Compatibility

```text
CreateOrder -> MakePayment : 1.0
CreateOrder -> CancelCart : 0.0
```

`CreateOrder → MakePayment` is compatible because:

* `CreateOrder` produces `order_id`
* `MakePayment` requires `order_id`
* `CreateOrder` produces `order_exists`
* `MakePayment` requires `order_exists`

Therefore, both input-output and precondition-effect requirements are satisfied.

`CreateOrder → CancelCart` is not compatible because `CancelCart` requires:

```text
order_not_exists
```

while `CreateOrder` produces:

```text
order_exists
```

Therefore, the required precondition is not satisfied.

---

### 9.3 Experiment 3 — Vector Similarity

```text
CreateOrder vs CreateOrderDatabase = 0.783
CreateOrder vs CancelCart = 0.436
```

The similarity between `CreateOrder` and `CreateOrderDatabase` is higher than the similarity between `CreateOrder` and `CancelCart`.

This is expected because `CreateOrder` and `CreateOrderDatabase` implement the same general functionality and share several structural properties.

The result demonstrates that the feature representation can capture meaningful similarity between capabilities.

---

### 9.4 Experiment 4 — Alternative Implementations

```text
API vs Database = 0.783
API vs GUI = 0.832
Database vs GUI = 0.782
```

The three implementations have relatively high similarity because they perform the same general order-creation task.

The differences arise from their capability type, resources, execution mechanisms, cost, risk, and reliability.

The highest similarity in this experiment is:

```text
API vs GUI = 0.832
```

while:

```text
API vs Database = 0.783
Database vs GUI = 0.782
```

This demonstrates that the representation can recognize common functionality while still preserving implementation-specific differences.

---

### 9.5 Experiment 5 — Irrelevant Capability

```text
CreateOrder vs CompletePurchase goal = 0.167
CheckInventory vs CompletePurchase goal = 0.0
```

`CreateOrder` has a non-zero similarity with the `CompletePurchase` goal because some of its represented features overlap with features represented in the goal.

`CheckInventory` has zero similarity with the goal because there are no overlapping active features in the current feature representation.

It is important to note that:

```text
0.167
```

is a cosine similarity value. It should **not** be interpreted as saying that `CreateOrder` completes exactly 16.7% of the goal.

Goal achievement requires semantic state transition and composition analysis rather than cosine similarity alone.

---

### 9.6 Experiment 6 — Capability Composition

```text
CreateOrder -> MakePayment compatibility = 1.0
MakePayment -> SendNotification compatibility = 1.0
Composite capability vector dimension = 44
Composite cost = 0.65
Composite risk = 0.17
Composite reliability = 0.941
Composite availability = 1.0
```

Both consecutive capability pairs are compatible.

The resulting composite capability remains in the same 44-dimensional vector space.

The operational attributes of the composite capability are:

```text
Cost = 0.65
Risk = 0.17
Reliability = 0.941
Availability = 1.0
```

The total cost is calculated by summing the costs of the individual capabilities.

The total risk is accumulated and limited to a maximum value of 1.0.

Reliability is calculated by multiplying the reliability values:

$$
0.99 \times 0.98 \times 0.97 = 0.941094
$$

which is represented as:

```text
0.941
```

Availability is:

$$
1.0 \times 1.0 \times 1.0 = 1.0
$$

---

### 9.7 Experiment 7 — Operational Attributes

The measured operational attributes were:

```text
CreateOrder : cost = 0.1 , risk = 0.05 , reliability = 0.99 , availability = 1.0

CreateOrderDatabase : cost = 0.08 , risk = 0.04 , reliability = 0.995 , availability = 1.0

CreateOrderGUI : cost = 0.2 , risk = 0.08 , reliability = 0.95 , availability = 1.0

MakePayment : cost = 0.5 , risk = 0.1 , reliability = 0.98 , availability = 1.0
```

These results show that different implementations of similar functionality can have different operational characteristics.

For example:

```text
CreateOrderDatabase
```

has lower cost and risk and higher reliability than:

```text
CreateOrderGUI
```

in the experimental dataset.

---

### 9.8 State and Goal Encoding

The implementation also encoded the initial state and the goal.

The results were:

```text
Initial state vector dimension = 44
Goal vector dimension = 44
CreateOrder vs initial state = 0.0
```

Both the initial state and goal use the same 44-dimensional feature space.

The zero similarity between `CreateOrder` and the initial state is a result of the current feature encoding and should not be interpreted as saying that `CreateOrder` cannot execute in the initial state.

The initial state actually contains the conditions required for `CreateOrder`, including:

```text
authenticated = true
cart_exists = true
cart_items = true
order_exists = false
```

The zero cosine similarity indicates a limitation of using the current unified feature mapping for direct capability-state similarity.

---

## 10. Analysis

### 10.1 Capability Representation

The representation successfully encodes different capability properties in a fixed 44-dimensional space.

The number of active features differs between capabilities, showing that the representation preserves differences in capability structure.

---

### 10.2 State and Goal Relationship

States and goals are encoded using the same feature space.

This provides a common representation framework for comparing application conditions with capability effects.

However, the zero similarity between `CreateOrder` and the initial state demonstrates that direct cosine similarity between a capability vector and a state vector is not sufficient for determining executability.

A semantic compatibility check is therefore more appropriate for deciding whether a capability can execute in a particular state.

---

### 10.3 Precondition-Effect Compatibility

The compatibility experiment successfully distinguishes between compatible and incompatible capability sequences.

The results:

```text
CreateOrder → MakePayment = 1.0
CreateOrder → CancelCart = 0.0
```

show that compatibility depends on actual functional requirements rather than only vector similarity.

This is an important property because two capabilities may have high vector similarity but still not be composable.

---

### 10.4 Input-Output Compatibility

The representation explicitly models inputs and outputs.

For example:

```text
CreateOrder
    output: order_id

MakePayment
    input: order_id
```

Therefore, the output of `CreateOrder` satisfies the corresponding input of `MakePayment`.

This provides the basis for constructing capability chains.

---

### 10.5 Capability Composition

The three-step sequence:

```text
CreateOrder
      ↓
MakePayment
      ↓
SendNotification
```

was successfully composed.

Both transitions achieved:

```text
compatibility = 1.0
```

The composite capability retained the same vector dimension and combined the operational attributes of its component capabilities.

This demonstrates that the representation can support construction of more complex functionality from smaller executable capabilities.

---

### 10.6 Alternative Implementations

The three order-creation implementations produced relatively high similarity values:

```text
API vs Database = 0.783
API vs GUI = 0.832
Database vs GUI = 0.782
```

This indicates that the representation captures their shared functionality.

At the same time, they remain distinguishable because the vectors include capability type and execution mechanism as separate features.

---

### 10.7 Goal Relevance

The comparison:

```text
CreateOrder vs CompletePurchase = 0.167
```

shows some overlap between a capability and the final goal.

In contrast:

```text
CheckInventory vs CompletePurchase = 0.0
```

shows no overlap in the current feature representation.

However, cosine similarity alone should not be treated as a complete goal-achievement measure. A capability may contribute to a goal indirectly through intermediate state transitions.

Therefore, goal relevance should ideally combine vector similarity with state-transition and composition reasoning.

---

### 10.8 Operational Properties

The representation includes cost, risk, reliability, and availability.

This enables capabilities to be compared not only by functionality but also by operational characteristics.

For example:

```text
CreateOrderDatabase
```

has:

```text
cost = 0.08
risk = 0.04
reliability = 0.995
```

while:

```text
CreateOrderGUI
```

has:

```text
cost = 0.20
risk = 0.08
reliability = 0.95
```

Therefore, the representation can support future capability-selection decisions where multiple implementations provide similar functionality but differ in operational properties.

---

## 11. Limitations

The proposed implementation satisfies the required experiments, but several limitations remain.

### 11.1 Fixed Feature Vocabulary

The current representation uses a manually defined feature vocabulary.

A new application domain may require additional features.

Therefore, the current implementation is domain-specific rather than universally applicable.

---

### 11.2 Limited Semantic Generalization

The representation treats features such as:

```text
order_id
payment_id
customer_id
```

as separate symbolic features.

It does not automatically understand deeper semantic relationships between these concepts.

---

### 11.3 Direct State-Capability Similarity

The result:

```text
CreateOrder vs initial state = 0.0
```

shows that cosine similarity is not sufficient to measure whether a capability is applicable to a state.

The current system handles functional applicability using explicit precondition and effect rules.

---

### 11.4 Simple Operational Aggregation

Composite cost is calculated by addition, reliability by multiplication, and risk by accumulation with an upper limit of 1.0.

These are reasonable simple rules for the experimental system, but real applications may require more sophisticated operational models.

---

### 11.5 No Learned Embedding

The proposed representation is manually designed rather than learned from a large dataset.

This was intentional because the assignment requires a problem-specific design rather than merely applying an existing embedding model.

---

### 11.6 Small Experimental Dataset

The experimental dataset contains a limited number of capabilities.

A larger dataset would be required for more extensive evaluation across different domains and capability structures.

---

## 12. Conclusion

This assignment presented the design and implementation of a problem-specific vector representation for formal states, goals, and executable capabilities.

A 44-dimensional feature-based vector space was designed to represent:

* Capability type
* Inputs
* Outputs
* Preconditions
* Effects
* Resources
* Execution mechanisms
* Cost
* Risk
* Reliability
* Availability

The implementation provides functions for:

```text
encode_state()
encode_goal()
encode_capability()
similarity()
compatibility()
compose()
```

The experimental results demonstrate that the proposed representation can distinguish capability types, represent alternative implementations, identify functional compatibility, support capability composition, and include operational attributes.

The compatibility experiments produced:

```text
CreateOrder → MakePayment = 1.0
CreateOrder → CancelCart = 0.0
```

and the composition experiment successfully constructed:

```text
CreateOrder → MakePayment → SendNotification
```

with:

```text
Composite cost = 0.65
Composite risk = 0.17
Composite reliability = 0.941
Composite availability = 1.0
```

The alternative implementation experiment also showed meaningful similarity:

```text
API vs Database = 0.783
API vs GUI = 0.832
Database vs GUI = 0.782
```

These results indicate that a structured, problem-specific vector representation can preserve useful relationships between executable capabilities while also supporting explicit compatibility and composition reasoning.

At the same time, the experiments show that vector similarity should not be treated as a replacement for semantic reasoning. In particular, capability-state applicability and goal achievement require explicit consideration of preconditions, effects, state transitions, and composition.

Overall, the proposed approach provides a simple and interpretable foundation for representing and composing executable capabilities in a vector space.


