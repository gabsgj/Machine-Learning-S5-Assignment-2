# Assignment 2 - Embedding Design

## 1. Proposed Approach

The project uses a structured feature-based vector representation.

The objective is not to use a general-purpose Word2Vec representation, but to design a representation specifically for formal states, goals, and executable capabilities.

## 2. State Embedding

A state is represented as a collection of variable-value pairs.

Example:

    cart_status = ACTIVE
    order_status = CREATED

The state encoder converts these symbolic values into a fixed-dimensional numerical vector.

The current implementation produces a 64-dimensional state vector.

## 3. Goal Embedding

A goal consists of conditions that should be satisfied by a state.

Example:

    confirmation_sent = YES

The goal encoder uses the same structured feature principle and produces a 64-dimensional vector.

## 4. Capability Embedding

A capability is represented using:

    Type
    Inputs
    Outputs
    Preconditions
    Effects
    Constraints
    Resources
    Quality
    Reliability
    Availability
    Mechanism

The capability encoder produces a 134-dimensional feature vector.

Conceptually:

    phi_C(C) =
    [T, I, O, P, E, K, R, Q, Rel, A, M]

## 5. Similarity

Cosine similarity is used:

    similarity(A,B) =
        (A . B) / (||A|| ||B||)

Similarity measures vector alignment.

However, similarity alone is not considered sufficient for capability composition.

## 6. Compatibility

Functional compatibility is evaluated separately.

The compatibility score is:

    Compat(C1,C2)
      = w1 * PE
      + w2 * IO
      + w3 * R

where:

    PE = precondition/effect compatibility
    IO = input/output compatibility
    R  = resource compatibility

## 7. Composition

Two capabilities can be composed when the effects and outputs of the first capability satisfy the preconditions and inputs of the second.

For example:

    CreateOrder
        ->
    MakePayment
        ->
    SendConfirmation

## 8. Operational Properties

The representation stores:

    execution time
    resource cost
    monetary cost
    risk
    energy
    reliability
    availability

These properties allow alternative implementations to be compared.

## 9. Important Design Principle

Semantic similarity and functional composability are treated as different concepts.

Two capabilities may be similar in vector space without being valid consecutive operations.

Therefore the project uses both:

    similarity()

and:

    Compatibility::evaluate()

This distinction is central to the proposed representation.