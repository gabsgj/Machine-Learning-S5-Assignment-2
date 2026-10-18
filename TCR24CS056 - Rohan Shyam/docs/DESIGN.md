# Formal Embedding Design

The implementation is in `backend/app/models/formal.py`, `backend/app/embedding/encoder.py`, `backend/app/composition/compatibility.py`, and `backend/app/composition/composer.py`.

## Formal entities

A state is (s=(id,V)), where (V) is a finite map from variable names to JSON values. A goal is (g=(id,P)), where (P) is a non-empty list of predicates. A predicate is (p=(name,op,value)), with `op` in ({=,\ne,>,\ge,<,\le,in\}).

A capability is

\[
c=(id,name,type,M,I,O,P,E,K,R,Q,rel,av,components),
\]

where `type` is one of `API`, `DATABASE`, `GUI`, `EVENT`, `FUNCTION`, `FILE`, `COMPUTATION`, `MESSAGE`, `SERVICE`, or `COMPOSITE`; (M) is a string-to-string mechanism map; (I,O) are lists of typed fields `(name,type,domain?,required?)`; (P,E,K) are preconditions, effects, and constraints; (R) is a resource-name list; (Q=(time\_ms,money,resource,risk,energy)) contains nonnegative costs; reliability and availability are each in ([0,1]); and `components` retains ordered component IDs where applicable. State values and predicate values can be JSON values. The encoder uses a stable textual atom for each scalar; compound values use Python's `repr` representation.

## Sparse feature function

Each embedding is a finite map (\phi(x):F_x\to\mathbb{R}), with (F_x) the features emitted for that entity. Feature names are explicit strings, not integer indices. There is no fixed vector length, fitted vocabulary, or hashing: the coordinates are the feature keys present in each encoded entity, and absent coordinates are zero when maps are compared.

For a state (s):

\[
\phi_S(s)=\{\texttt{state:}x\texttt{=}a(v):v=V[x]\},
\]

where (a(v)) lowercases booleans (`true`/`false`) and stringifies scalar values.

For a goal (g),

\[
\phi_G(g)[\texttt{goal:}q(p)]=\#\{p\in P:q(p)=q\},
\]

where (q(p)) is `name + operator + atom(value)`. For an `in` predicate with a list value, its values are atomized, sorted, and joined in braces.

Capability features are first counted by section and then multiplied by the section's encoder weight (w_j). For each feature (f) in section (j), (\phi_C(c)[f]=w_j\,n_f(c)), with these exact sections and weights. Capability `name` and `components` are stored in the formal model but do not produce embedding coordinates; identity uses `id` only.

| Section | Weight | Dimensions emitted |
|---|---:|---|
| `identity` | 0.20 | `identity:<id>` |
| `type` | 0.35 | `type:<type>` |
| `io` | 1.00 | `io:input:<name>:<type>`, optional `:domain=<domain>`, `io:input-required:<bool>` at 0.2 before section scaling; outputs use `io:output:<name>:<type>` and optional domain |
| `condition` | 1.25 | `condition:<predicate>` for preconditions |
| `effect` | 1.25 | `effect:<predicate>` |
| `constraint` | 0.80 | `constraint:<predicate>` |
| `resource` | 0.55 | `resource:<resource-name>` |
| `mechanism` | 0.20 | `mechanism:<key>=<value>` |
| `operational` | 0.15 | `operational:cost:<field>`, `operational:reliability`, and `operational:availability` |

The input-required marker is added with raw count 0.2 then multiplied by the IO weight (1.0); input field domain markers use raw count 0.35. Output requiredness is not encoded. Operational values are multiplied by 0.15, not bucketed. Repeated feature keys accumulate counts. `weighted()` omits zero values and rounds emitted coordinates to eight decimal places. The displayed `EmbeddingEncoder.weights` mapping also contains `state` and `goal` at 1.0; state/goal coordinate values are one per entry and are not passed through `weighted()`.

## Similarity

For arbitrary feature maps (x,y), `sparse_cosine` is

\[
sim(x,y)=\begin{cases}
\frac{\sum_{f\in F_x\cap F_y}x_fy_f}{\sqrt{\sum_{f\in F_x}x_f^2}\sqrt{\sum_{f\in F_y}y_f^2}}, & \|x\|\|y\|>0,\\
0,&\text{otherwise.}
\end{cases}
\]

The result is clipped to ([-1,1]) and rounded to eight decimal places. Capability similarity partitions each encoded vector by its first colon-delimited section. If (J) is the union of sections present in either vector, the API returns

\[
sim_C(c_1,c_2)=\frac{\sum_{j\in J}w_j\,sim(\phi_j(c_1),\phi_j(c_2))}{\sum_{j\in J}w_j},
\]

using the section weights in the table for this second weighted average as well as the coordinate scaling. A missing side for a present section yields a zero cosine for that section; sections absent from both sides do not enter (J). The method reports per-section scores and says explicitly that resemblance does not imply composability.

Goal relevance is a related, explicitly separate calculation: goal predicates are projected to `effect:<predicate>` dimensions at the effect weight and compared by cosine to a capability's effect-only projection. The API also reports exact matching effect count and coverage `matches / number of goal conditions`.

## Compatibility

For a producer (c_p) and next consumer (c_n), compatibility is directional. Every required consumer input `(name,type)` needs a producer output with the same name and type. Every consumer precondition must be implied by a producer equality effect on the same variable. The implementation tests that implication using the predicate operator and value; e.g. an equality effect of `count=3` satisfies a consumer condition `count>0`. Optional inputs are ignored. Availability equal to zero on either capability makes the pair incompatible. The result includes one evidence record per requirement and failure reasons. Consumer constraints are not part of this handoff test; state applicability separately checks a capability's preconditions and constraints against a state.

The check does not prove arbitrary logical implications, compare field domains, or check resource capacity. It must not be confused with vector similarity.

## Composition

For an ordered list (C=(c_1,\ldots,c_n)), (n\ge2), composition first requires compatibility for every pair ((c_i,c_{i+1})). Any failed link raises a composition error carrying diagnostics. A successful composite has:

- `type=COMPOSITE`, ordered component IDs, and mechanism `{"composition":"ordered"}`;
- the first capability's inputs and external preconditions, except later preconditions established by any earlier equality effect are internalized;
- the last capability's outputs;
- the final listed effect for each variable, all unique constraints, and the union of resources;
- component-wise sum of the five costs;
- reliability (\prod_i rel(c_i)) and availability (\prod_i av(c_i)).

The result is encoded by the same capability encoder. Products model independent component success/availability. This operation models a linear chain; it does not propagate a full application state or synthesize new typed fields.

## Runtime locations

The public encoding endpoints and similarity/composition endpoints are listed in [ARCHITECTURE.md](ARCHITECTURE.md). The detailed observed experiments are in [EXPERIMENTS.md](EXPERIMENTS.md).
