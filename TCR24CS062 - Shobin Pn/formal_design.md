# Formal Embedding Design

## State
A state is represented as variable-value pairs and encoded as a binary vector.

## Goal
A goal contains desired state conditions and uses the same state feature space.

## Capability
A capability is represented using type, inputs, outputs, preconditions, effects, resources, cost, reliability, and availability.

## Embedding
The capability vector contains features for type, inputs, outputs, preconditions, effects, resources, cost, reliability, and availability.

## Similarity
Cosine similarity is used:

`sim(x,y) = (x · y) / (||x|| ||y||)`

## Compatibility
Compatibility is measured by the fraction of the second capability's preconditions satisfied by the first capability's effects.

## Composition
A sequence of compatible capabilities is represented as a composite capability. Cost is summed and reliability is multiplied across the sequence.
