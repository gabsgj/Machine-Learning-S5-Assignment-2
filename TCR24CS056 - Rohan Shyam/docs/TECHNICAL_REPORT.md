# Technical Report: Formal Embeddings for Capability Composition

## 1. Problem definition

An application scenario contains snapshots of named variables, desired goal predicates, and capabilities that can change those variables. The technical problem is to represent these entities in vectors while retaining the formal details needed to compare capabilities, distinguish compatible from incompatible handoffs, and construct a composite capability. The system evaluates the representation and its composition rules on a commerce checkout scenario and small Level 1–5 examples. It does not find a plan or execute external application operations.

## 2. Design requirements

The design must encode states, goals, and atomic or composite capabilities; preserve identity, typed interfaces, preconditions, effects, constraints, resources, mechanism, cost, reliability, and availability; support similarity and evidence-producing compatibility as separate operations; and form an ordered composite when all handoffs pass. The assignment asks evaluation of distinct capability representation, state relationship, precondition/effect compatibility, typed input/output dependencies, composition, goal relevance, operational properties, consistency across problems, and computational/storage efficiency. The intended vector should be inspectable and reproducible for formally named input.

## 3. Related embedding approaches

Word2Vec learns dense word vectors from word contexts, making similar usage patterns geometrically close. That is useful for natural-language semantics, but this project receives structured identifiers, typed fields, predicates, costs, and explicit directionality. A pretrained word model could blur a distinction such as a producer effect and consumer precondition or treat variable-name synonyms as equivalent without a formal rule. It also would not, by itself, decide whether a typed output satisfies a downstream input. The assignment explicitly says that merely applying an existing embedding model is insufficient.

TF–IDF and other sparse bag-of-feature representations provide inspectable weighted coordinates and cosine comparison, but ordinary text tokens do not preserve field roles and logical operators unless those are deliberately encoded. Symbolic schemas and knowledge-graph representations preserve typed relations such as `produces`, `requires`, and `changes`; graph embeddings can then provide learned proximity, but learned scores still need a separate rule for directional compatibility. The implementation takes the transparent symbolic-feature route: formal roles are part of feature names, cosine supports resemblance, and a separate symbolic checker validates handoffs. This is a design choice suited to a small formal dataset, not a claim that it outperforms learned methods generally.

## 4. Proposed representation

The models in `backend/app/models/formal.py` represent a state as an ID plus a map of values; a goal as an ID plus predicate list; and a capability as an ID/name/type, mechanism, typed inputs/outputs, preconditions, effects, constraints, resources, five operational cost values, reliability, availability, and optional ordered component IDs. `backend/app/embedding/encoder.py` maps the implemented formal sections into named sparse coordinates. State features look like `state:Cart.exists=true`, goal features like `goal:Order.exists=true`, and capability sections use prefixes such as `condition:`, `effect:`, `io:`, and `operational:`. Capability name and ordered component IDs remain in the model but are not separate vector coordinates; the ID is encoded as identity.

The vectors have no fixed numeric length, shared learned vocabulary, or hash buckets. Only emitted named coordinates are stored; absent features act as zero. This makes each dimension auditable but ties overlap to literal names and representations.

## 5. Mathematical formulation

Let a state (s=(id,V)) map variable (x) to value (v). Its feature map emits `state:x=atom(v)` with value 1. For a goal (g=(id,P)), each predicate (p=(x,op,v)) emits `goal:x op atom(v)`; duplicate coordinates accumulate counts.

Let a capability (c) have formal sections (I,O,P,E,K,R,M,Q,rel,av). The encoder emits one or more named dimensions per field and scales capability coordinates by the implemented section multiplier. The exact coordinate names and weights are specified in [DESIGN.md](DESIGN.md). There is no hashing; the active dimension count is data-dependent.

For sparse maps (x,y), the system uses cosine

\[
sim(x,y)=\frac{\sum_{f\in F_x\cap F_y}x_fy_f}{\sqrt{\sum_{f\in F_x}x_f^2}\sqrt{\sum_{f\in F_y}y_f^2}},
\]

returning zero if either norm is zero. Capability similarity is the weighted mean of cosine scores for each section present in either capability; a missing counterpart contributes a zero score. Operational feature values are scaled by 0.15 but are not bounded or bucketed. Within the operational section, a very large cost value can still dominate reliability and availability coordinates.

## 6. Capability composition model

For an ordered sequence (c_1,\ldots,c_n), every adjacent pair must pass `check_compatibility`. Required consumer inputs need same-name, same-type producer outputs; consumer preconditions need same-variable producer equality effects that satisfy their operators. Optional inputs are ignored, and zero availability blocks a link. The output records evidence and reasons.

On success, `compose` creates a `COMPOSITE` capability. It carries the first operation's inputs and external preconditions, final operation's outputs, final effect per variable, unique constraints, unioned resources, the ordered component IDs, component-wise summed costs, and products of reliability and availability. Preconditions established by earlier equality effects become internal to the chain. The full operation and its boundaries are in [DESIGN.md](DESIGN.md).

## 7. Implementation

The implementation is in these current files:

| Required behavior | File | Actual behavior |
|---|---|---|
| `encode(state)` | `backend/app/embedding/encoder.py` (`EmbeddingEncoder.encode_state`) | Emits one named `state:<variable>=<value>` coordinate per state value. |
| `encode(goal)` | `backend/app/embedding/encoder.py` (`EmbeddingEncoder.encode_goal`) | Emits counted `goal:<predicate>` coordinates. |
| `encode(capability)` | `backend/app/embedding/encoder.py` (`EmbeddingEncoder.encode_capability`) | Emits weighted identity, type, I/O, condition, effect, constraint, resource, mechanism, and operational coordinates. |
| `compose(capabilities)` | `backend/app/composition/composer.py` (`compose`) | Validates ordered adjacent links, then aggregates a `COMPOSITE` representation or raises with diagnostics. |
| `similarity(x,y)` | `backend/app/embedding/encoder.py` (`sparse_cosine`, `capability_similarity`) | Computes sparse-map cosine or a weighted mean of capability section cosines. |

`backend/app/main.py` exposes these behaviors through FastAPI, while `backend/app/experiments/runner.py` selects experiment candidates from scenario declarations. `frontend/src/services/api.ts` calls those routes, and page components render returned values. The specifically requested `python3 -m pytest tests/ -v` could not start because `python3.exe` was inaccessible in this Windows environment. Running the same suite from `backend/` with `python -m pytest tests/ -v` reported **20 passed, 1 warning** (Starlette's deprecation notice concerning the installed httpx test client). A fresh `npm.cmd run build` from `frontend/` completed successfully; Vite emitted its advisory that the minified JavaScript chunk exceeds 500 kB (actual built chunk: 620.78 kB, 174.78 kB gzip).

## 8. Experimental methodology

The data is formal JSON: the default commerce scenario, five progressively varied example scenarios, and the added explicit composite example. The runner examines ordered producer/consumer pairs, discovers compatible chains, groups matching precondition/effect signatures with differing types, compares capability section vectors, measures exact goal-effect overlap, and reports operational values. It also encodes a state and goal and checks state applicability. It emits skip reasons when a scenario lacks a required candidate. The live API was run on commerce, Level 2, Level 3, and Level 5; the explicit composite dataset was validated and composed separately. See [EXPERIMENTS.md](EXPERIMENTS.md) for captured compact JSON results.

The five assignment experiments are compatibility, three-capability composition, alternative implementations, goal relevance, and operational attributes. The evaluation questions are considered directly in Section 10. The measurements are deterministic scenario outputs, not repeated statistical trials or an external benchmark.

### Dataset coverage audit

The collection-level coverage requested by Deliverable 3 is:

| Required element | File coverage |
|---|---|
| Initial states | `data/scenarios/commerce.json`; `data/scenarios/examples/level-1-single-capability.json`, `level-2-compatible-pair.json`, `level-3-full-chain.json`, `level-4-branching.json`, `level-5-everything.json`; `data/scenarios/composition-example.json` |
| Goal specifications | `data/scenarios/commerce.json`; each of the five `data/scenarios/examples/level-*.json` files named above; `data/scenarios/composition-example.json` |
| Atomic capabilities | `data/scenarios/commerce.json`; each of the five `data/scenarios/examples/level-*.json` files named above; the two component entries in `data/scenarios/composition-example.json` |
| Explicit capability composition | `data/scenarios/composition-example.json` declares `prepare-confirm-order` with `type: COMPOSITE` and ordered `components`; the commerce runner also generates a measured composite at runtime |
| Relevant constraints | `data/scenarios/commerce.json` declares `Cart.locked=false`; `data/scenarios/composition-example.json` declares the stable `Order.exists=true` confirmation constraint |
| Operational attributes | `data/scenarios/commerce.json`, all five Level examples, and `data/scenarios/composition-example.json` declare costs, reliability, and availability |

## 9. Results

The observed `GET /api/experiments` commerce response identified 7 capabilities, 2 states, 1 goal, and 60 observed capability dimensions. `create-order-api -> make-payment` was compatible; `create-order-api -> send-receipt` was incompatible due to missing `Payment.status=SUCCESS` and `payment_id: UUID`. The chain `[create-order-api, make-payment, send-receipt]` composed with reliability `0.9554985`, availability `0.9398592`, and time cost `960.0 ms`.

The API/database and API/GUI alias scores were `0.62915791` and `0.60934613`; matching `create-order-db` and `create-order-gui` pair score was `0.73736739`. Commerce goal analysis marked the order, payment, and receipt effects relevant and `cancel-cart` and `refresh-catalog` irrelevant. The captured Level 2 run found `create-order -> make-payment` compatible and skipped three-capability composition, alternatives, and operational aggregation because it had only two capabilities/no alternative group. Level 3 and Level 5 did not yield a valid three-capability handoff chain under the formal fields, despite their labels and ingredients.

The explicit two-stage composite example was accepted and composed via the API: the returned aggregate reliability was `0.9702`, availability `0.9506`, and time cost `40.0 ms`. All these figures were observed from the current API or runner in this phase; none are placeholder outputs.

## 10. Analysis

- **Distinct capability representation:** identity and type coordinates separate implementations; shared preconditions/effects can still create functional overlap. The results show nonzero but sub-one scores for alternatives.
- **State relationship:** state coordinates retain each variable and current value. Applicability and state/goal checks use formal predicate evaluation rather than relying on embedding cosine alone.
- **Precondition/effect compatibility:** the commerce compatible and incompatible pair outputs show evidence-based distinction. A score alone is not used to accept a link.
- **Typed input/output compatibility:** commerce's successful pair explicitly matches `order_id: UUID`; missing `payment_id: UUID` is visible as a failed requirement in the negative case.
- **Composition:** successful chains produce a new capability with propagated formal sections and aggregated operational values. Small examples correctly skip unsupported chain experiments.
- **Goal relevance:** exact matching effects and coverage distinguish goal-contributing operations from unrelated ones in commerce and Level 5.
- **Operational properties:** time, monetary/resource/risk/energy costs, reliability, and availability are present as coordinates/fields; costs add and the latter two multiply for a composite. The values are scenario declarations, not measured production telemetry.
- **Consistency:** deterministic, name-based encoding yields repeatable maps, but there is no corpus-level learned calibration. Different scenarios naturally have different active coordinates, and semantically synonymous names do not align.
- **Efficiency:** encoding and sparse cosine iterate over emitted keys, so cost is linear in the number of nonzero dimensions. Capability pair analysis partitions by section. The chain search explores candidate continuations recursively and can grow combinatorially as the capability count grows. No large-scale runtime or memory benchmark was run, so scalability is not empirically established.

## 11. Limitations

The current implementation has these limitations:

- literal names do not generalize across synonyms or semantically equivalent variables;
- compatibility supports same-name typed fields and producer equality effects with the implemented scalar predicate operators, not arbitrary theorem proving; field domains are not checked in the compatibility function;
- the linear composition model does not handle branching, loops, rollback, concurrency, conditional effects, or resource contention;
- reliability and availability multiplication assumes independent component outcomes;
- active scenario replacement is in memory and resets when the backend restarts;
- the feature weights are hand-designed and are not empirically learned or calibrated on a large dataset;
- numerical operational costs are scaled but not normalized or bucketed before within-section cosine, so large cost magnitudes can dominate reliability/availability features in that section;
- the frontend production bundle currently triggers Vite's >500 kB chunk advisory;
- a formally plausible real workflow can be rejected if its dataset omits an effect or output required by the handoff model, as demonstrated by skips in Level 3 and Level 5.

## 12. Conclusion

The project implements an explainable hybrid: named sparse formal features support inspectable similarity, while a separate symbolic checker and ordered composer preserve the operational distinction between resemblance and composability. The captured scenario experiments demonstrate encoding, directional compatibility, alternatives, goal overlap, and aggregate operational attributes. The results establish behavior on this small formal dataset; they do not establish general semantic understanding, production-scale performance, or execution correctness for arbitrary workflows.
