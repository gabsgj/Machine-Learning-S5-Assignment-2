# Deliverable 1: Formal Embedding Design

## 1. Formal application and capability model

An application is represented as \(\mathcal{A}=(\mathcal{S},\mathcal{C},S_I,G,\mathcal{R},K)\). A state is a partial map from variable names to typed values. A goal is a partial map of required variable values. A capability is the tuple

\[
C_i=(T_i,I_i,O_i,P_i,E_i,K_i,R_i,Q_i,Rel_i,A_i,M_i),
\]

where type and mechanism identify the implementation, inputs and outputs are typed ports, preconditions and effects are finite sets of equality predicates, \(K_i\) contains local constraints, \(R_i\) contains resources, \(Q_i=(t_i,m_i,risk_i)\) records latency, money, resource use, and risk, \(Rel_i\in[0,1]\) is reliability, and \(A_i\in\{0,1\}\) is availability. In the included JSON schema, the four QoS names are `timeCostMs`, `moneyCost`, `resourceCost`, and `risk`.

Capabilities are state transitions. Applying \(C_i\) to \(S\) is defined only when every predicate in \(P_i\) is satisfied; the resulting state is \(S'=S\oplus E_i\), where effects overwrite state values for variables they set.

## 2. Feature vocabulary and embeddings

Let \(V=(v_1,\ldots,v_d)\) be the sorted union of state variables appearing in the initial state, goal, capability preconditions, or effects. For Boolean-valued facts, define the bipolar state encoding:

\[
\phi_S(S)_k=\begin{cases}+1&S(v_k)=true\\-1&S(v_k)=false\\0&v_k\text{ is missing or non-Boolean.}\end{cases}
\]

The goal encoding is a masked vector:

\[
\phi_G(G)_k=\begin{cases}+1&G(v_k)=true\\-1&G(v_k)=false\\0&v_k\notin G.\end{cases}
\]

For this implementation, capability vectors concatenate interpretable subspaces:

\[
\phi_C(C)=[p(C);e(C);\tau(C);q(C);Rel(C);A(C)]\in\mathbb{R}^{2d+|T|+6}.
\]

Here \(p_k=+1\) for a required true predicate, \(-1\) for a required false predicate, and 0 if unconstrained. The effect block uses the same coding for values set. \(\tau\) is one-hot over capability types in the dataset. The four QoS coordinates are nonnegative normalized values: \(\log(1+t)/10\), \(\log(1+1000m)/10\), \(\log(1+r)/10\), and risk clipped to \([0,1]\). Reliability and availability occupy separate coordinates. Mechanism strings are retained in the formal record but omitted from the numeric vector; this avoids treating endpoint names as functional facts.

Missing/non-Boolean state values encode as zero in this starter implementation. The method is exact for Boolean predicates used by the included experiments; richer typed values should use one-hot or normalized numeric encodings in a broader implementation.

## 3. Similarity and compatibility

Cosine similarity compares equal-length vectors:

\[
sim(x,y)=\frac{x^Ty}{\|x\|_2\|y\|_2},
\]

with score 0 if either vector has zero norm. This score describes resemblance over all included dimensions. It is not a composition test.

For sequential compatibility from \(C_i\) to \(C_j\), compare effects with downstream preconditions. Define satisfied predicates \(M=\{k\in P_j:E_i(k)=P_j(k)\}\), contradictions \(X=\{k\in P_j:k\in E_i\land E_i(k)\ne P_j(k)\}\), and unresolved predicates \(U=P_j\setminus(M\cup X)\). Required output ports of \(C_i\) must have a same-named output in \(O_i\) with the same type as a required input in \(I_j\). The implementation reports `compatible` when \(X=\emptyset\) and required ports match; it reports `fully_enabled` only when additionally \(U=\emptyset\). An unresolved precondition may be supplied by the current state, so compatibility alone is not proof of executability.

## 4. Composition

Given an ordered sequence \((C_1,\ldots,C_n)\), its composite denotes \(C_n\circ\cdots\circ C_1\). Preconditions already established by earlier effects are discharged. A conflicting requirement rejects composition. Later effects overwrite earlier effects on the same variable. Ports are combined by name, and ports produced within the sequence are removed from the composite's external inputs. QoS is summed componentwise, reliability is multiplied, and availability is the conjunction of component availability.

For independent failures, the reliability aggregation is \(Rel(C)=\prod_i Rel(C_i)\). This is a modeling assumption, not a claim that real service failures are independent. Risk is currently summed as a simple cumulative proxy rather than combined probabilistically.

## 5. Goal relevance

Direct goal coverage is

\[
GR(C,G)=\frac{|\{g\in G:E_C\text{ sets }g\text{ to its required value}\}|}{|G|},
\]

and is 0 for an empty goal. This intentionally measures direct contribution only; it does not infer transitive contribution through later capabilities.

## 6. Scope and assumptions

The representation uses deterministic equality predicates and finite typed ports. State encoding currently specializes to Boolean facts; values such as `Payment.status="SUCCESS"` remain in the formal JSON and exact predicate logic, but map to zero in the state/goal vector. Capability identity is kept in the formal record rather than assigned a unique ID coordinate. This is intentional: identifiers do not imply functional distance. Planner and path-search algorithms are outside the assignment's scope.

