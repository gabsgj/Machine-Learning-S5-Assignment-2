# FGEE: formal embedding design

## 4. Proposed representation

Let variables be x_1,...,x_n with finite domains D_1,...,D_n. Set D=sum_k |D_k|. A state is represented by concatenating one-hot vectors for each variable, using D coordinates rather than one coordinate for each complete state. A goal is represented by a mask G_k of permitted values for every variable; unconstrained variables permit their whole domain.

Each capability has an allowed-value set B_k for every variable, a write flag W_k and, when written, a constant A_k. Preconditions, capability constraints and global policies are intersected into B_k. If a constant assignment violates a global policy on that variable, the capability is made structurally impossible by an empty guard set. An empty guard anywhere means no valid source state.

The main functional vector is [guard masks, write flags, assigned-value masks]. The contract block holds allowed-value masks for inputs and outputs, plus required-input flags. Port slots are pairs of name and type label; their finite value vocabularies are built from the problem specification. A new subset of a known port domain can be encoded, enabling intersected external requirements.

The remaining blocks are mechanism counts, resource indicators and seven raw operational values. Atomic mechanisms are canonical JSON combinations of type and mechanism, represented by one-hot counts. Composites retain summed counts. The schema fixes every coordinate meaning and must accompany numerical arrays. from_vector reconstructs the capability blocks from numbers without needing the original capability specification.

## 5. Mathematical formulation

State encoding: phi_S(s)=concat_k onehot_{D_k}(s[x_k]) in {0,1}^D. Goal encoding: phi_G(G)=concat_k 1_{v in G_k}, also in {0,1}^D. A state satisfies a goal iff every selected state value has mask value 1; equivalently their dot product equals n. State validity requires exactly one declared value per variable.

Guard compilation: B_k={v in D_k : every predicate on x_k in P_i union K_i union K is true at v}. Applicability is s[x_k] in B_k for every k. On applicability, f_i(s)[x_k]=A_k if W_k=1, otherwise s[x_k]. For unary global policies, assigned values are checked against the policy mask; unassigned variables preserve policy validity.

Capability encoding: phi_C(C)=[b,w,a,i,o,r,h,z,q]. Here b and a each have D entries, w has n, i and o each have V port-value entries, r has B required-input entries, h has H mechanism counts, z has J resource entries and q has 7 operational entries. Therefore d_C=2D+n+2V+B+H+J+7. The implementation block order is exactly this order.

Operational q order is time_ms, money, energy, risk, resource_cost, reliability, availability. Units are retained for accounting, not mixed into semantic similarity. A raw full-vector distance establishes numerical distinction but is dominated by units such as milliseconds and must not be interpreted as functional closeness.

Functional similarity: let U be the union of written variables. E(i,j) is the fraction of variables in U written by both to the same value, or 1 when U is empty. For each variable, J_k=|B_i,k intersect B_j,k|/|B_i,k union B_j,k|, taking 1 for an empty union. Define sigma(i,j)=0.7 E(i,j)+0.3 mean_k J_k. This bounded symmetric score emphasizes effect resemblance; weights are declared choices, not fitted parameters. Unconstrained-variable agreement can inflate guard resemblance.

Directional coverage: for each k, t_k=1 if an upstream write A_i,k belongs to B_j,k and 0 otherwise; if there is no write, t_k=|B_i,k intersect B_j,k|/|B_i,k|. Set kappa(i,j)=product_k t_k for a nonempty upstream guard box, otherwise 0. This is the exact fraction of modeled upstream-applicable states accepted by the downstream guard, under uniform counting over the Cartesian product. It is not a probability of runtime success.

Typed output o matches required input p when names and type labels agree and domain(o) is a subset of domain(p). Let I_ij be true when every required downstream input is supplied by a matching upstream output. Guaranteed compatibility requires a nonempty upstream guard box, every assigned singleton or preserved upstream guard set contained in the downstream guard, and I_ij. Existential compatibility requires kappa>0 and I_ij. Availability and current resources are separate execution questions.

Direct goal relevance is the fraction of nontrivial goal-variable restrictions established by a write to an allowed goal value. It identifies direct contribution, not every indirect dependency. goal_satisfied applies a supplied capability or composite to an initial state and checks all goal predicates. Fixed-sequence leave-one-out evaluation identifies upstream steps needed for that given sequence; it performs no planning.

## 6. Capability composition model

compose([C_1,...,C_m]) means execute C_1 first and C_m last. For two capabilities C then D, substitute earlier assignments into the later guard. For a variable written by C, require A_C,k in B_D,k; a failed requirement makes the composition impossible. For an unwritten variable, intersect B_C,k with B_D,k. Empty intersections also make the composition impossible. The composite retains the resulting initial-state guard box.

Composite effects use latest assignment: A_comp,k=A_D,k if D writes k, else A_C,k if C writes k, else no write. Write masks take logical OR and assigned-value masks select the later nonzero assignment block. Thus composition is a nonlinear, role-aware operation on encoded masks, not vector addition or averaging. Numerical vectors can be decoded, composed and repacked without source specifications.

Correctness argument: if C writes x_k, its value before D is the known constant A_C,k, so the later guard reduces to a constant truth test. Otherwise the value remains the initial x_k and both guards must hold, exactly represented by intersection. Unary guards are independent across variables. Last-write effects equal sequential assignments. These facts prove equality of composite and sequential partial functions; induction extends it to any finite sequence. Semantic composition is associative but generally noncommutative.

Example: Compile requires stage=RAW and writes BUILT; Test requires BUILT and writes TESTED; Deploy requires TESTED, credentials=true and environment=PROD, then writes DEPLOYED. The composite requires stage=RAW, credentials=true and environment=PROD, plus size>0. It writes DEPLOYED. Simply unioning effects would retain conflicting categorical assignments; adding vectors would lose the initial guard and overwrite semantics.

Contracts are processed in order. Prior outputs bind later inputs when the typed domain inclusion test succeeds. Without such an output, an input remains external. Repeated external requirements use domain intersection, require matching types and combine required flags by OR. Same-name incompatible internal outputs cause rejection. Outputs are retained until another output with the same name overwrites them. Port domains describe guarantees; the simulator does not generate actual output values.

For serial operations, time, money, energy and resource_cost sum. Reliability is the product of per-step reliability under an independence assumption. Aggregate risk is 1-product(1-risk_i), also requiring independence. Availability is AND, resources are union and mechanism counts sum. Composition constructs a structural capability even when operational gates currently prevent execution. Associativity of the full vector is tested on the supplied valid contracts; arbitrary unresolved external/internal port aliasing can require a richer contract calculus.
