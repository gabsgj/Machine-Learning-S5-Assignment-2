# Deliverable 4: Technical Report

## 1. Problem definition

The goal is to represent formal application states, goals, and executable capabilities in a vector space that supports analysis of functional similarity, compatibility, composition, goal contribution, and operational attributes. Capabilities are modeled as transitions with typed inputs/outputs, preconditions/effects, mechanism, QoS, reliability, and availability. The system does not implement a planner.

## 2. Design requirements

The design must distinguish capabilities, relate them to states and goals, distinguish similarity from directional composability, account for typed ports, represent composite operations, and make operational attributes inspectable. It should remain interpretable and reproducible without external model training.

## 3. Related embedding approaches

One-hot and bipolar predicate encodings are transparent and preserve exact symbolic facts, but do not learn semantic similarity. Dense learned embeddings (for example, Word2Vec-style distributional vectors) can capture statistical regularities, but a high embedding similarity does not establish that one service satisfies another's preconditions or input schema. Graph embeddings can represent nodes and dependencies, but direction and typed constraints require explicit relation modeling. This implementation combines a hand-designed partitioned feature vector with exact symbolic compatibility checks: vectors support comparisons while formal predicates determine whether composition is permitted.

## 4. Proposed representation

The state and goal vectors share a sorted state-variable vocabulary. Boolean states use bipolar values; goal vectors use zero for unspecified facts. A capability vector concatenates signed precondition features, signed effect features, one-hot capability type, four normalized QoS coordinates, reliability, and availability. Mechanism text remains symbolic metadata. The provided e-commerce example yields 13 state/goal dimensions and a 38-dimensional capability vector.

## 5. Mathematical formulation

For vocabulary \(V\), \(\phi_S(S)_k\) is +1/-1/0 for true/false/missing Boolean facts. \(\phi_G(G)_k\) is +1/-1/0 for required true/false/unspecified facts. \(\phi_C(C)=[p;e;\tau;q;Rel;A]\). Cosine similarity is used only for descriptive vector comparison. The implementation handles non-Boolean values in exact predicates and effects but leaves their state/goal vector coordinate at zero; a categorical-value expansion is needed for vector-level representation of those values.

## 6. Capability composition model

An ordered sequence composes as \(C_n\circ\cdots\circ C_1\). Preconditions established by preceding effects are removed from the composite's external requirements; contradictions reject composition. Effects are merged in order with later assignments taking precedence. Time, money, and resource costs are summed; reliability is multiplied under an independence assumption; availability is conjunctive. The composite embedding is produced by the same function as an atomic capability.

## 7. Implementation

`capability_embedding.py` is a standard-library-only Python implementation. `ecommerce_purchase_flow.json` supplies the formal application. The public operations are `encode_state`, `encode_goal`, `encode_capability`, `compose`, and `similarity`; dedicated methods check predicate/typed-port compatibility and goal relevance. Command-line flags expose the vectors, composite, and experiment suite.

## 8. Experimental methodology

Five reproducible checks cover: a controlled enabling/contradictory successor pair; a three-capability composite; alternate API/database implementations with equivalent effects; goal-relevant and irrelevant effects; and operational trade-offs. The experiments are deterministic and operate on the packaged JSON plus a small controlled compatibility example. Run `py -3 capability_embedding.py --experiments` from the project folder.

## 9. Results

| Experiment | Observed result |
|---|---|
| Compatibility | CreateOrder -> MakePayment is fully enabled. CreateOrder -> CancelCart is contradicted on `Order.exists` and rejected. |
| Composition | The three-step composite has reliability 0.9861, time 250 ms, money cost 0.065, resource cost 3, and cumulative risk 0.04. Its capability vector has 38 coordinates. |
| Alternative implementation | The two payment capabilities set the same effects. Their full-vector cosine is 0.8318; the mechanism types remain visibly distinct (API and DATABASE). |
| Goal relevance | Direct goal coverage is 0.20 for GenerateInvoice and 0.00 for BrowseCatalog and UpdateWishlist. |
| Operational attributes | API payment is 120 ms / $0.05 / .992 reliability; database payment is 35 ms / $0.002 / .965 reliability. Both are marked available in this dataset. |

The API/database comparison illustrates why vector similarity is not a compatibility test: their effects match, but implementations and quality attributes differ. Conversely, a high cosine alone would not establish that a sequence is executable.

## 10. Analysis

The partitioned representation is auditable: each dimension corresponds to a declared predicate, type, or quality attribute. The controlled compatibility case confirms that a positive effect can satisfy a downstream precondition while an opposing value is rejected. Ordered composition captures accumulated effects and operational cost. Alternative payment methods share function-level effects but preserve implementation and operational differences. The goal-coverage measure is intentionally conservative: it counts only direct effects and therefore assigns zero to useful intermediate capabilities whose outputs enable later goal-producing operations.

## 11. Limitations

The state and goal vectors currently encode Boolean values only; categorical and numeric values are zero-valued in those vector spaces, although symbolic predicates still handle the provided categorical payment status. Port matching uses same-name, same-type required ports and does not support explicit renaming or transformation adapters. The compatibility result distinguishes contradicted from unresolved conditions, but `compatible` means “not contradicted and ports match,” not “executable from the initial state”; callers should use `fully_enabled` or check unresolved predicates against a state. The simple composite port merger is name-based and can misrepresent more complex internal dataflow. Risk is summed rather than probabilistically combined. Reliability multiplication assumes independent failures. Availability is embedded and aggregated but no time-varying availability model is present. Global hazards and arbitrary constraints are retained in the source dataset but not enforced by a planner. No learned embeddings, large-scale benchmark, latency profiling, or statistical significance analysis is included.

## 12. Conclusion

A small interpretable feature map combined with exact symbolic checks can represent useful functional relationships for a formal capability set. The experiment demonstrates directional compatibility, ordered composition, functional comparison across mechanisms, direct goal coverage, and operational trade-offs. The evidence is a deterministic synthetic demonstration rather than a general benchmark. Extending typed state features, dataflow-aware ports, constraints, and state-conditioned evaluation is the next step toward a more general capability embedding system.
