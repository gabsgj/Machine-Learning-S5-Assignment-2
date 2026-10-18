
# Assignment 2: Design of a Vector Embedding for Capability Composition

**Student:** Dilshath P. K.  
**Project:** Capability Embedding for Functional Composition  
**Language:** Python  
**Libraries:** NumPy, Pandas, Scikit-learn

## 1. Problem Definition

Modern applications consist of reusable operations called capabilities. These capabilities have inputs, outputs, preconditions, effects, constraints, resource requirements, and operational properties.

The objective of this project is to design and implement a numerical vector representation for application states, goals, and capabilities. The representation should help distinguish functionally similar capabilities from capabilities that can actually be composed.

The project uses an online purchase application as its example domain. The main capabilities are CreateOrder, MakePayment, SendNotification, CancelCart, and UpdateUserProfile.

## 2. Design Requirements

The proposed system should:

- Encode application states, goals, and capabilities as vectors.
- Represent capability inputs, outputs, preconditions, effects, resources, and execution types.
- Measure similarity between encoded capabilities.
- Determine compatibility using precondition-effect relationships.
- Construct composite capabilities from atomic capabilities.
- Identify capabilities relevant to a specified goal.
- Consider cost, reliability, and availability.
- Evaluate the system using formally specified experiments.

## 3. Related Embedding Approaches

### 3.1 One-Hot Encoding

One-hot encoding assigns a separate numerical position to each category. It is simple and interpretable but does not naturally represent relationships between different categories.

### 3.2 TF-IDF

TF-IDF represents documents using the importance of terms. It is useful for text similarity but does not directly establish whether one capability satisfies another capability's preconditions.

### 3.3 Word2Vec

Word2Vec learns distributed vector representations from word contexts. It captures semantic relationships but requires suitable training data and does not directly guarantee formal capability compatibility.

### 3.4 Graph-Based Representation

A graph can represent dependencies between capabilities. An edge can connect a capability that produces a condition to another capability that requires it. Graphs are useful for dependency reasoning but need additional numerical representations for vector similarity.

### 3.5 Proposed Approach

This project uses a custom structured feature embedding with numerical operational attributes. Formal compatibility is evaluated separately using preconditions and effects.

This hybrid approach is explainable, computationally inexpensive, and suitable for a small formally specified application.

## 4. Proposed Representation

A capability is represented as:

C = (T, I, O, P, E, K, R, Q, Rel, A, M)

where:

- T: capability type
- I: inputs
- O: outputs
- P: preconditions
- E: effects
- K: constraints
- R: required resources
- Q: operational quality attributes
- Rel: reliability
- A: availability
- M: execution mechanism

The implementation extracts features from the capability name, type, inputs, outputs, preconditions, effects, and resources. Cost, reliability, and availability are stored in dedicated numerical dimensions.

The implementation uses a 128-dimensional vector.

## 5. Mathematical Formulation

### 5.1 Capability Embedding

Let C represent a capability and let d = 128 be the vector dimension.

The embedding function is:

φC(C) = [x1, x2, ..., xd] ∈ R^d

Categorical and symbolic features are mapped into vector positions using a deterministic SHA-256 hash. Numerical operational attributes are placed in the final three dimensions.

The resulting vector is:

φC(C) = [f1, f2, ..., f125, cost, reliability, availability]

This is a compact feature representation, not a trained semantic embedding.

### 5.2 State Embedding

A state consists of variable-value pairs:

S = {(x1, v1), (x2, v2), ..., (xn, vn)}

The state encoder maps each pair to a numerical feature representation.

φS(S) ∈ R^128

### 5.3 Goal Embedding

A goal is a set of desired conditions:

G = {g1, g2, ..., gm}

The goal encoder maps each condition to a numerical feature representation:

φG(G) ∈ R^128

### 5.4 Similarity

Cosine similarity is used to compare capability vectors:

Sim(u, v) = (u · v) / (||u|| ||v||)

A larger value indicates greater alignment between the represented features. Similarity does not, by itself, establish composability.

### 5.5 Compatibility

Capability Ci is compatible with capability Cj when the effects of Ci satisfy the preconditions of Cj.

For a simple equality-based model:

Comp(Ci, Cj) = matched preconditions / total preconditions of Cj

If every precondition is satisfied, the compatibility score is 1. Otherwise, the score is less than 1.

The current implementation checks direct equality matches. It does not yet evaluate inequalities, variable substitutions, or complex logical expressions.

### 5.6 Composition

For capabilities C1, C2, ..., Cn, the composite capability is represented as:

C* = Cn ◦ ... ◦ C2 ◦ C1

The implementation uses:

- Preconditions from the first capability
- Inputs from the first capability
- Effects from the last capability
- Outputs from the last capability
- The union of required resources
- The sum of operational costs
- The product of reliability values
- The product of availability values

These rules assume sequential execution and successful completion of all constituent operations. A production system would also need intermediate-state validation and failure-handling logic.

## 6. Capability Composition Model

The example purchase workflow is:

CreateOrder → MakePayment → SendNotification

CreateOrder produces Order.exists = true. MakePayment requires Order.exists = true and produces Payment.status = SUCCESS. SendNotification requires Payment.status = SUCCESS and produces Notification.sent = true.

The resulting composite capability is CompletePurchase.

Its desired final effects are:

- Order.exists = true
- Payment.status = SUCCESS
- Notification.sent = true

This composition is valid when the intermediate conditions and all required inputs are satisfied.

## 7. Implementation

The project is implemented in Python using the following modules:

- `src/embedding.py`: encodes states, goals, and capabilities and computes cosine similarity.
- `src/compatibility.py`: evaluates precondition-effect compatibility.
- `src/composition.py`: constructs composite capabilities.
- `data/dataset.py`: defines the experimental capabilities.
- `main.py`: executes the experiments and saves CSV results.

NumPy is used for numerical vectors, Pandas for result tables, and Scikit-learn for cosine similarity.

The experiments are executed using:

`python main.py`

## 8. Experimental Methodology

Five experiments are considered.

### Experiment 1: Capability Compatibility

CreateOrder is compared with MakePayment and CancelCart.

Expected behaviour:

- CreateOrder → MakePayment: compatible
- CreateOrder → CancelCart: incompatible

The compatibility function checks whether the effects of the first capability satisfy the preconditions of the second.

### Experiment 2: Capability Composition

CreateOrder, MakePayment, and SendNotification are composed into a single composite capability.

The experiment examines the resulting inputs, preconditions, outputs, effects, resources, cost, reliability, and vector dimension.

### Experiment 3: Alternative Implementations

Three implementations are considered:

- CreateOrderAPI
- CreateOrderDatabase
- CreateOrderGUI

They share similar inputs, outputs, preconditions, and effects but use different execution mechanisms and resources.

The experiment compares their vector similarity to investigate whether functional resemblance can coexist with implementation differences.

### Experiment 4: Irrelevant Capabilities

The target goal requires order creation, successful payment, and notification delivery.

Capabilities are checked for direct matches with the goal conditions. UpdateUserProfile should be irrelevant to the specified purchase goal, while capabilities producing the requested conditions should be considered relevant.

This experiment measures direct relevance, not complete workflow relevance.

### Experiment 5: Operational Attributes

Two payment service alternatives are compared.

PaymentServiceA:
- Cost: 0.10
- Reliability: 0.99
- Availability: 1

PaymentServiceB:
- Cost: 0.02
- Reliability: 0.90
- Availability: 1

The experiment demonstrates that services with similar functional behaviour may have different operational properties.

## 9. Results and Analysis

The program generates CSV files for compatibility, alternative implementations, goal relevance, and operational attributes.

The compatibility experiment should identify the direct dependency between CreateOrder and MakePayment and reject the direct dependency between CreateOrder and CancelCart under the supplied preconditions.

The composition experiment constructs a composite capability with accumulated cost and combined reliability and availability.

The alternative implementation experiment reports cosine similarity values for each pair of implementations. These scores depend on the encoded features and should be interpreted as feature similarity rather than proof of functional equivalence.

The goal relevance experiment identifies direct matches between capability effects and goal conditions. It does not yet perform backward dependency analysis.

The operational experiment records the differences in cost, reliability, and availability between payment service alternatives.

Actual numerical similarity scores and execution outputs should be inserted after running the implementation.

## 10. Evaluation

### Capability Representation

The implementation encodes multiple capability properties into a fixed-length numerical vector. Functionally different capabilities may share some features, but their vectors are not guaranteed to be unique.

### State Relationship

States and goals are represented as vectors. However, the current implementation does not directly evaluate whether a capability is applicable to a state or whether its effects transform the state into a desired state.

### Precondition-Effect Compatibility

Direct equality-based matching provides a simple compatibility score. More complex logical constraints require an improved evaluator.

### Input-Output Compatibility

Input and output names are included in capability vectors. However, explicit type and domain compatibility is not fully implemented. This remains an area for improvement.

### Composition

The system constructs composite representations from multiple capabilities. Full validity requires checking all intermediate dependencies, input availability, constraints, and state transitions.

### Goal Relevance

Direct goal-condition matching identifies some relevant capabilities. Indirect relevance through a chain of capabilities is not fully evaluated.

### Operational Properties

Cost, reliability, and availability are represented numerically. Cost is accumulated by summation, while reliability and availability are combined multiplicatively under an independence assumption.

### Consistency

The hash-based symbolic features are deterministic for the same feature strings. Hash collisions are possible, and vectors are not guaranteed to preserve all functional relationships.

### Efficiency

Encoding a capability involves processing its symbolic features and constructing a fixed-size vector. Storage for each embedding is proportional to the vector dimension. Compatibility checking depends on the number of preconditions.

## 11. Limitations and Future Work

The proposed implementation has several limitations:

1. Hash-based feature mapping can cause collisions.
2. The embedding is not trained from examples or learned from execution data.
3. Cosine similarity does not guarantee semantic or functional equivalence.
4. Compatibility currently supports direct equality matching rather than full logical reasoning.
5. Input and output data types and domains are not formally unified.
6. The composite operation does not fully validate intermediate states or constraints.
7. Goal relevance checks direct effects rather than complete dependency chains.
8. Operational values are not normalized or weighted according to a defined optimization objective.
9. Reliability multiplication assumes independent capability failures.
10. Dynamic availability, retries, and failure recovery are not modelled.

Future work could introduce typed symbolic features, explicit transition validation, normalized operational metrics, dependency graphs, learned embeddings, and more extensive test datasets.

## 12. Conclusion

This project presents a simple structured vector representation for application capabilities, states, and goals. It combines numerical feature encoding with a separate formal compatibility check and a composition operation.

The experiments investigate capability compatibility, composite construction, alternative implementations, goal relevance, and operational properties.

The main finding is that vector similarity and functional compatibility represent different relationships. A useful capability-composition system therefore benefits from combining vector representations with explicit precondition-effect reasoning.

The implementation provides a starting point for further research into representing reusable application operations and constructing complex functionality from simpler capabilities.
