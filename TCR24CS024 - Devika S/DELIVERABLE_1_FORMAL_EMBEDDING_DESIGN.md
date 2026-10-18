# Deliverable 1 — Formal Embedding Design

## 1. Formal application

`A = (S, C, S_I, G, R, K)`

- `S`: state space
- `C`: available capabilities
- `S_I`: initial state
- `G`: goal specification
- `R`: resources
- `K`: global constraints/policies

A state is `S = {(x1,v1),...,(xn,vn)}`. A goal is a set of desired conditions.

## 2. Capability model

`C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)`

The implementation explicitly stores all eleven components required by the assignment:
- type `T`
- inputs `I`
- outputs `O`
- preconditions `P`
- effects `E`
- constraints `K`
- resources `R`
- quality attributes `Q`
- reliability `Rel`
- availability `A`
- mechanism `M`

## 3. Embeddings

Separate representations are used for states/goals and capabilities.

`phi_S : S -> R^d_s`

`phi_G : G -> R^d_s`

`phi_C : C -> R^d_c`

Boolean state values use bipolar encoding: true -> +1 and false -> -1. Numeric values are smoothly bounded with `tanh(v/10)`. Categorical state values are represented through registered value dimensions in the implementation design rather than being treated as natural-language text.

Capability embedding:

`phi_C(C) = [v_pre || v_eff || v_type || v_input || v_output || v_constraint || v_resource || v_QoS]`

`v_pre` and `v_eff` encode variable/value conditions. `v_type` is one-hot over capability types. Input/output vectors use registered `(name,type)` port tokens. Constraints and resources use one-hot token blocks. `v_QoS` contains normalized execution time, monetary cost, resource cost, risk, reliability and availability.

This is a problem-specific representation designed for capability composition; it is not a direct application of Word2Vec or another pretrained embedding.

## 4. Similarity

Cosine similarity:

`Sim(x,y) = (x dot y)/(||x|| ||y||)`

It measures graded resemblance. It is not treated as proof of executable composition.

## 5. Compatibility

For `C_i -> C_j`, each precondition `p` of `C_j` is evaluated against the effects of `C_i`:

- `+1`: an effect establishes `p`
- `-1`: an effect conflicts with `p`
- `0`: `C_i` leaves `p` untouched

`Comp(C_i,C_j) = (1/|P_j|) sum m(p,E_i)`

Thus the required example gives:
- `CreateOrder -> MakePayment = +1` because `Order.exists=true` is produced and required.
- `CreateOrder -> CancelCart = -1` because `Order.exists=true` conflicts with `Order.exists=false`.

Input/output compatibility is separately measured by typed port matching.

## 6. Composition

For `C12 = C2 o C1`:

`P12 = P1 union (P2 \ E1)`

`E12 = E1 ⊕ E2`, with later effects overwriting earlier effects for the same variable.

Operational composition:

`Time12 = Time1 + Time2`

`Money12 = Money1 + Money2`

`Resource12 = max(Resource1, Resource2)`

`Risk12 = 1 - (1-Risk1)(1-Risk2)`

`Reliability12 = Reliability1 * Reliability2`

`Availability12 = Availability1 * Availability2`

Longer compositions are formed recursively.

## 7. Goal relevance

The effect subvector of a capability is compared with the goal vector. This provides a direct relevance signal while formal composition still uses preconditions/effects.
