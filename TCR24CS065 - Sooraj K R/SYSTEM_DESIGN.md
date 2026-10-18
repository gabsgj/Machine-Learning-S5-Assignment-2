# System Design: Vector Embedding for Capability Composition

## 1. Problem Definition
The assignment asks for a vector representation of formal entities: states, goals, and executable capabilities. The purpose of this representation is to preserve functional relationships such as compatibility, composition, and similarity, rather than just semantic language meanings.

## 2. Proposed Representation
We use a Bag-of-Words (BoW) style multi-hot encoding mechanism to represent states, capabilities, and goals. Each unique property (such as `OrderExists=True` as a precondition, or `PaymentStatus=SUCCESS` as an effect) is assigned a unique index in a high-dimensional continuous vector space (simplified to a fixed array of size 50 in our code).

### Mathematical Formulation
Let the universe of features be $F = \{f_1, f_2, ..., f_n\}$.
The embedding function $\phi: E \rightarrow \mathbb{R}^d$ maps an entity $e$ (State, Goal, or Capability) to a vector where each index corresponds to the presence or frequency of a feature $f_i$ in the entity $e$.

For a state $S$, the features are `STATE_key_value`.
For a goal $G$, the features are `GOAL_key_value`.
For a capability $C_i$, the features are the union of `PRE_key_value`, `EFF_key_value`, and `MECH_type`.

### Similarity Measure
We use the standard Cosine Similarity to measure the functional resemblance between two encoded entities:
$$ \text{similarity}(v_1, v_2) = \frac{v_1 \cdot v_2}{||v_1|| \times ||v_2||} $$

## 3. Capability Composition Model
Given two capabilities $C_1$ and $C_2$, the composition $C_{12} = C_2 \circ C_1$ is modeled as a new `Capability` object:
- **Preconditions**: Inherited primarily from $C_1$ (assuming $C_1$ satisfies the bridging requirements for $C_2$).
- **Effects**: Represent the final state after $C_2$ executes, thus inherited from $C_2$.
- **Cost**: The sum of costs $Cost(C_1) + Cost(C_2)$.
- **Reliability**: The product of probabilities $Reliability(C_1) \times Reliability(C_2)$.

## 4. Operational Properties
Operational attributes like Cost, Reliability, and Availability are maintained distinctly from the semantic vector embedding. While they could theoretically be appended as numerical features in the vector array (e.g., $v_{d+1} = \text{cost}$), it is practically more robust to evaluate them independently because they follow different algebraic rules (e.g., reliability multiplies, cost adds, while preconditions are semantic sets).

## 5. Experiments Conducted
The implemented code verifies:
1. **Capability Compatibility:** Distinguishing between capabilities that can run sequentially vs. those that conflict.
2. **Capability Composition:** Creating a unified vector for a multi-step operation.
3. **Alternative Implementations:** Testing if two capabilities with the same effects (e.g., API vs. Database) have high similarity despite different underlying mechanisms.
4. **Irrelevant Capabilities:** Ensuring unrelated operations yield low or zero cosine similarity.
5. **Operational attributes:** Demonstrating correct mathematical tracking of cost and reliability during composition.
