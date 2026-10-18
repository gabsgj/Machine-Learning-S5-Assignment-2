# PCCST503 Assignment 2 — Design of a Vector Embedding for Capability Composition

This implementation is based directly on the supplied Assignment 2 specification.

## Domain
E-commerce order processing, using the formal example pattern required by the assignment:
- `CreateOrder` (C1)
- `MakePayment` (C2)
- `CancelCart` (C3)

## Embedding
A structured, problem-specific vector is used rather than simply applying an existing pretrained embedding:

`phi_C(C) = [v_pre || v_eff || v_type || v_input || v_output || v_constraints || v_resources || v_QoS]`

State and goal entities use the state-variable representation `phi_S` and `phi_G`. Cosine similarity is used for graded comparison; directional precondition/effect compatibility is used for composability.

## Required operations
- `encode(state)`
- `encode(goal)`
- `encode(capability)`
- `compose(capabilities)` (implemented as recursive pairwise composition)
- `similarity(x,y)`

## Five required experiments
1. Capability compatibility: CreateOrder -> MakePayment vs CreateOrder -> CancelCart.
2. Capability composition: CreateOrder -> MakePayment -> SendNotification.
3. Alternative implementations: API, DATABASE and GUI order creation.
4. Irrelevant capabilities: AddToCart, UpdateProfile and other non-goal-direct operations.
5. Operational attributes: cost, reliability, availability and risk sensitivity.

## Build
`make clean && make`

## Run
`./assignment2_embedding ecommerce_capability_dataset.json`

The JSON file contains the formal initial state, goal, constraints, resources and capabilities. The implementation intentionally does not include BFS, DFS, A*, D* Lite, LPA* or replanning because the assignment explicitly excludes planner redesign.
