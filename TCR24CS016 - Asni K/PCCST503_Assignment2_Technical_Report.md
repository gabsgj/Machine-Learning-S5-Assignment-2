# PCCST503 Assignment 2
# Design of a Vector Embedding for Capability Composition

## 1. Problem Definition

The assignment investigates whether formally specified application states,
goals, and executable capabilities can be represented in a vector space
such that useful functional relationships are preserved.

The focus is not on redesigning the planner from Assignment 1. Instead,
the focus is on representing the operations that make up a plan.

A capability is treated as a reusable operation with formal inputs, outputs,
preconditions, effects, constraints, resources, operational properties,
and an execution mechanism.

The central application example is an online purchase workflow:

```text
CreateOrder -> MakePayment -> SendNotification
```

The corresponding composite capability is:

```text
CompletePurchase
```

---

## 2. Design Requirements

The implementation addresses the following required properties:

1. Capability identity
2. State awareness
3. Precondition-effect compatibility
4. Input-output compatibility
5. Similarity and composability
6. Composition
7. Goal relevance
8. Operational properties

The representation must distinguish similarity from composability. Two
capabilities can be functionally similar while still being unable to execute
one after another.

---

## 3. Related Embedding Approaches

### 3.1 Word2Vec-style distributed representations

Word2Vec represents words using dense vectors and preserves useful semantic
relationships. This provides the motivation for thinking about relationships
in a vector space.

However, the present problem is different. A capability is not simply a
word. Its important properties include preconditions, effects, resources,
constraints, and operational values.

Therefore, directly applying Word2Vec to capability names would lose important
functional information.

### 3.2 One-hot and feature-based representations

A structured feature representation is transparent and easy to inspect.
Each formal property can contribute features to the final vector.

The disadvantage is that it is less compact and does not automatically learn
latent relationships from a large corpus.

### 3.3 Proposed hybrid structured representation

This project combines symbolic feature encoding with explicit numeric
operational attributes.

The design is therefore interpretable while still producing vectors that
can be compared using cosine similarity.

---

## 4. Proposed Representation

A capability is represented as:

```text
C = (T, I, O, P, E, K, R, Q, Rel, A, M)
```

where:

- `T` = type
- `I` = inputs
- `O` = outputs
- `P` = preconditions
- `E` = effects
- `K` = constraints
- `R` = resources
- `Q` = operational quality/cost attributes
- `Rel` = reliability
- `A` = availability
- `M` = execution mechanism

The symbolic part of the vector is:

```text
v_symbolic(C) =
[
    function identity,
    inputs,
    outputs,
    preconditions,
    effects,
    constraints,
    resources,
    type,
    mechanism
]
```

The operational part is:

```text
v_operational(C) =
[
    time_cost / 10,
    resource_cost / 10,
    money_cost / 10,
    risk,
    reliability,
    availability
]
```

The final vector is:

```text
v(C) = [v_symbolic(C), v_operational(C)]
```

The symbolic representation is problem-specific and intentionally
interpretable.

---

## 5. State Representation

A state is represented as:

```text
S = {(x1,v1), (x2,v2), ..., (xn,vn)}
```

Example:

```text
User.authenticated = true
User.role = CUSTOMER
Cart.exists = true
Cart.item_count = 3
Order.exists = false
Payment.status = NOT_STARTED
Inventory.available = true
Notification.sent = false
```

Each variable and value contributes a feature to the state vector.

---

## 6. Goal Representation

A goal is a set of desired conditions.

The example goal is:

```text
Order.exists = true
Payment.status = SUCCESS
Notification.sent = true
```

The goal vector uses the same symbolic vocabulary so that state, capability,
and goal features can be compared.

---

## 7. Mathematical Formulation

For vectors `x` and `y`, cosine similarity is:

```text
sim(x,y) = (x · y) / (||x|| ||y||)
```

If either vector has zero magnitude, similarity is defined as zero.

However, similarity alone is not sufficient for composition.

### 7.1 Precondition-effect compatibility

For capabilities `Ci` and `Cj`, define:

```text
PE(Ci,Cj) =
number of Cj preconditions satisfied by Ci effects
---------------------------------------------------
number of Cj preconditions
```

### 7.2 Input-output compatibility

Similarly:

```text
IO(Ci,Cj) =
number of Cj inputs supplied by Ci outputs
-------------------------------------------
number of Cj inputs
```

### 7.3 Resource relationship

A small resource-overlap term is included:

```text
R(Ci,Cj) =
resource overlap / required resources of Cj
```

### 7.4 Overall compatibility

The implemented compatibility score is:

```text
Compat(Ci,Cj)
    = 0.60 PE(Ci,Cj)
    + 0.30 IO(Ci,Cj)
    + 0.10 R(Ci,Cj)
```

The result is additionally adjusted by availability and reliability.

The precondition/effect component receives the largest weight because
state-transition compatibility is the key requirement for sequential
composition.

---

## 8. Capability Composition Model

Consider:

```text
C1 = CreateOrder
C2 = MakePayment
C3 = SendNotification
```

Their relationships are:

```text
CreateOrder
    |
    | Order.exists = true
    v
MakePayment
    |
    | Payment.status = SUCCESS
    v
SendNotification
```

Therefore:

```text
CompletePurchase
    = SendNotification ◦ MakePayment ◦ CreateOrder
```

The implementation checks each adjacent pair before constructing the
composite capability.

For a sequence:

```text
C1 -> C2 -> ... -> Cn
```

the composite operational properties include:

```text
time cost      = sum of component time costs
resource cost  = sum of component resource costs
money cost     = sum of component money costs
reliability    = product of component reliabilities
availability   = product of component availabilities
```

Risk is accumulated with an upper bound of 1.

---

## 9. Goal Relevance

For a capability `C` and goal `G`, direct goal relevance is:

```text
GoalRel(C,G) =
goal conditions directly produced by C
--------------------------------------
total goal conditions
```

For the composite purchase capability, all three goal conditions are
produced:

```text
Order.exists = true
Payment.status = SUCCESS
Notification.sent = true
```

Thus the composite has full direct goal relevance.

---

## 10. Implementation

The main implementation is:

```text
src/capability_embedding.py
```

It contains:

```python
encode_state(state)
encode_goal(goal)
encode_capability(capability)
encode(entity)
similarity(x, y)
compatibility(c1, c2)
compose(capabilities)
goal_relevance(capability, goal)
```

The implementation uses Python dataclasses to represent the formal entities.

No external pretrained embedding model is required.

---

## 11. Experimental Methodology

Five experiments are implemented.

### Experiment 1 — Capability Compatibility

The assignment requires a case where:

```text
C1 -> C2
```

is compatible but:

```text
C1 -> C3
```

is incompatible.

The project uses:

```text
C1 = CreateOrder
C2 = MakePayment
C3 = CancelCart
```

CreateOrder produces:

```text
Order.exists = true
```

MakePayment requires:

```text
Order.exists = true
```

CancelCart requires:

```text
Order.exists = false
```

Therefore CreateOrder -> MakePayment is the valid composition.

---

### Experiment 2 — Capability Composition

The sequence:

```text
CreateOrder -> MakePayment -> SendNotification
```

is composed into:

```text
CompletePurchase
```

The composite vector can then be compared with each atomic capability vector.

---

### Experiment 3 — Alternative Implementations

Three implementations of the same broad function are included:

```text
CreateOrderAPI
CreateOrderDatabase
CreateOrderGUI
```

Their effects are functionally similar:

```text
Order.exists = true
Order.status = CREATED
```

but their mechanisms differ:

```text
POST /orders
INSERT orders
CLICK submit_button
```

The embedding therefore retains both functional similarity and implementation
specificity.

---

### Experiment 4 — Irrelevant Capabilities

The purchase goal is compared with:

```text
UpdateProfile
```

This capability updates a profile and does not directly contribute to:

```text
Order.exists = true
Payment.status = SUCCESS
Notification.sent = true
```

Therefore its direct goal relevance is zero.

---

### Experiment 5 — Operational Attributes

The implementation investigates:

- reliability
- availability
- risk
- time cost
- resource cost
- monetary cost

These properties are represented explicitly rather than hidden inside the
functional symbolic representation.

---

## 12. Results

Running:

```bash
python src/run_experiments.py
```

produces:

```text
results/experiment_results.csv
results/experiment_summary.md
```

The exact numeric results are generated by the implementation rather than
hard-coded into the report.

The expected qualitative behaviour is:

1. CreateOrder -> MakePayment receives a substantially higher compatibility
   score than CreateOrder -> CancelCart.
2. The three-step sequence can be composed successfully.
3. Alternative implementations have non-zero functional similarity while
   remaining distinguishable through type and mechanism features.
4. UpdateProfile has zero direct relevance to the purchase goal.
5. Operational attributes remain available for comparing implementations
   and evaluating composite capabilities.

---

## 13. Analysis

### Capability representation

Different capabilities are distinguishable because their functional tokens,
inputs, outputs, preconditions, effects, resources and mechanisms contribute
different vector components.

### State relationship

States and goals use the same formal variable/value vocabulary. This makes it
possible to inspect relationships between conditions and capability effects.

### Precondition-effect compatibility

This is explicitly evaluated rather than inferred from similarity alone.
This is important because two capabilities may be semantically similar but
still fail to compose.

### Input-output compatibility

Produced outputs are matched against required inputs. This gives a second
functional signal for composition.

### Composition

Composite capabilities are represented by aggregating their formal properties
and encoding the resulting capability using the same function as atomic
capabilities.

### Goal relevance

A capability is directly relevant when its effects satisfy goal conditions.

### Operational properties

Cost, reliability, availability, risk and resource requirements are retained
as explicit numeric or symbolic features.

### Consistency

The same encoding and compatibility functions are used across all test
cases, making the representation deterministic.

### Efficiency

For a fixed vocabulary of dimension `d`, vector encoding is approximately
linear in the number of fields/tokens in a capability. Cosine similarity is
`O(d)`. The current demonstration uses a small fixed vocabulary, so storage
and computation requirements are low.

---

## 14. Limitations

### 14.1 Manual vocabulary

The feature vocabulary is manually defined for the demonstration application.
A larger application would require a more systematic schema or learned
feature dictionary.

### 14.2 Sparse representation

The current representation is primarily feature-based and can be sparse.
A learned dense embedding could potentially capture more latent relationships.

### 14.3 Constraint reasoning

Constraints are not evaluated by a complete symbolic constraint solver.
They are represented as features.

### 14.4 Dynamic availability

The current availability value is scalar. A dynamic system could extend this
to:

```text
A(t)
```

as described in the assignment.

### 14.5 Small experimental dataset

The dataset is designed to demonstrate the required relationships rather
than to train a production-scale model.

---

## 15. Conclusion

This project demonstrates a problem-specific vector representation for formal
application states, goals and capabilities.

The central design decision is to separate:

```text
similarity
```

from:

```text
compatibility
```

because functional resemblance does not guarantee composability.

The structured representation preserves capability identity, inputs,
outputs, preconditions, effects, resources, mechanisms and operational
properties. A separate compatibility function then evaluates whether one
capability can validly precede another.

The final composition:

```text
CreateOrder
      ↓
MakePayment
      ↓
SendNotification
      ↓
CompletePurchase
```

shows how atomic capabilities can be combined into a representation of
complex application functionality.

---

## 16. Future Work

Possible extensions include:

1. learning the feature weights from a larger dataset;
2. replacing the manual vocabulary with a learned ontology;
3. using dense neural embeddings while retaining symbolic compatibility;
4. implementing a full constraint solver;
5. modelling time-dependent availability;
6. learning composition vectors from many execution traces;
7. integrating the embedding with a planner in a future system.

The current work intentionally does not redesign the planner from Assignment 1.
