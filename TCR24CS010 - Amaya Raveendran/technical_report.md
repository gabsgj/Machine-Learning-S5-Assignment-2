# Technical Report

## 1. Problem Definition

The objective is to represent formally specified states, goals and executable
capabilities in a vector space for capability compatibility and composition.

The application is represented as:

A = (S, C, SI, G, R, K)

A capability contains type, inputs, outputs, preconditions, effects,
constraints, resources, cost, reliability, availability and execution
mechanism.

## 2. Design Requirements

The representation supports capability identity, state awareness,
precondition-effect compatibility, input-output compatibility, similarity,
composition, goal relevance and operational properties.

Similarity and composability are treated separately.

## 3. Related Embedding Approaches

Word2Vec represents semantic relationships using vectors, but ordinary word
embeddings do not directly represent formal preconditions and effects.

One-hot encoding is simple but does not represent relationships efficiently.

Learned neural embeddings can learn complex representations but require
suitable training data.

This project uses a structured feature embedding because the assignment
requires explicit functional relationships.

## 4. Proposed Representation

For a capability:

C = (T, I, O, P, E, K, R, Q, Rel, A, M)

The vector contains symbolic features for type, mechanism, inputs, outputs,
preconditions, effects, constraints and resources.

The final dimensions represent time, resource cost, monetary cost, risk,
energy, reliability, availability and composition depth.

A 128-dimensional vector is used.

## 5. Mathematical Formulation

Cosine similarity is:

sim(x,y) = (x . y) / (||x|| ||y||)

Compatibility first checks precondition satisfaction. If a required
precondition is not satisfied, compatibility is zero.

Otherwise:

Compat(C1,C2) = 0.7 ScoreEP + 0.3 ScoreIO

CreateOrder produces Order.exists=true.

MakePayment requires Order.exists=true.

CancelCart requires Order.exists=false.

Therefore CreateOrder -> MakePayment is compatible and
CreateOrder -> CancelCart is incompatible.

## 6. Capability Composition Model

For:

C1 : S0 -> S1

C2 : S1 -> S2

the composition is:

C2 o C1 : S0 -> S2

The experiment also constructs:

CreateOrder -> MakePayment -> SendNotification

The composite capability uses the inputs of the first capability, outputs of the
last capability, combined effects, constraints and resources, summed costs,
product reliability and joint availability.

## 7. Implementation

The implementation provides:

encode_state(state)
encode_goal(goal)
encode_capability(capability)
compose(capabilities)
similarity(x, y)
compatibility(c1, c2)

The symbolic features use deterministic hashing and the operational attributes
are stored explicitly in the vector.

## 8. Experimental Methodology

### Experiment 1

C1 = CreateOrder

C2 = MakePayment

C3 = CancelCart

The expected result is:

C1 -> C2 = compatible

C1 -> C3 = incompatible

### Experiment 2

The composite capability is:

CreateOrder -> MakePayment -> SendNotification

The composite vector is compared with the three component vectors.

### Experiment 3

CreateOrder is represented using API, database and GUI mechanisms.

### Experiment 4

UpdateInventory is used as an irrelevant capability for the specified goal.

### Experiment 5

Reliability, execution time and risk are changed to observe their effect on the
vector.

## 9. Results

The experiment program prints compatibility scores, composition similarities,
alternative implementation similarities, goal relevance and operational
attribute results.

The required compatibility test produces:

C1 -> C2 = 1.000

C1 -> C3 = 0.000

The three-step composition is also successfully encoded.

## 10. Analysis

The experiment shows that similarity and composability are different.

CreateOrder and MakePayment can be composed because the effect of CreateOrder
satisfies a MakePayment precondition.

CreateOrder and CancelCart cannot be directly composed because their state
conditions conflict.

The alternative implementations remain functionally related while retaining
different implementation features.

## 11. Limitations

The dataset is small and formally constructed for the experiment.

Feature hashing can produce collisions.

The condition parser handles simple symbolic conditions.

The embedding is designed rather than learned from a large dataset.

The composition vector uses deterministic aggregation.

## 12. Conclusion

The structured embedding represents states, goals and capabilities using
numerical vectors while explicitly testing functional compatibility.

The implementation supports capability encoding, similarity, compatibility,
composition, goal relevance and operational attributes.

The main result is that vector similarity alone should not be treated as proof
of composability. Preconditions, effects, inputs and outputs must also be
considered.
