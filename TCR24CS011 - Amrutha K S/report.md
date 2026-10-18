# PCCST503 Assignment 2
# Design of a Vector Embedding for Capability Composition
## 1. Problem Definition
The assignment investigates how formally specified states, goals and
executable capabilities can be represented in a vector space so that
useful functional relationships are preserved. The motivation is
different from ordinary word embeddings. Word2Vec represents semantic
relationships between words, whereas this assignment focuses on
functional relationships between capabilities: what a capability
requires, what it produces, how it changes application state, and under
which constraints it operates.
A capability is represented using its type, inputs, outputs,
preconditions, effects, constraints, resources, cost, reliability,
availability and execution mechanism. The goal is to determine whether
such information can be encoded numerically and then used to investigate
similarity, compatibility and composition.
The primary research question is: How can formally specified states,
goals, and executable capabilities be represented in a vector space such
that the representation preserves the relationships required for
capability compatibility, composition, and construction of complex
application functionality?
## 2. Design Requirements
The proposed representation addresses the following requirements from
the assignment:
1. Capability identity: different capabilities must be distinguishable.
2. State awareness: the representation should capture relationships
between operations and application states.
3. Precondition-effect compatibility: an effect produced by one
capability should be usable to satisfy a precondition of another.
4. Input-output compatibility: outputs from one capability should be
comparable with required inputs of another.
5. Similarity and composability: functional resemblance must be
distinguished from actual composability.
6. Composition: atomic capabilities should be combined into a
representation of a composite capability.
7. Goal relevance: capabilities contributing to a specified goal should
be identifiable.
8. Operational properties: cost, reliability, availability, resources
and constraints should be represented.
## 3. Related Embedding Approaches
Word2Vec is a distributed representation approach in which words are
mapped to vectors and useful semantic relationships can be represented
in the vector space. However, directly applying a language embedding is
not sufficient for this problem because capability composition depends
on formal relationships such as preconditions and effects.
For example, CreateOrder and MakePayment do not need to be semantically
similar in natural language. They are functionally composable because
CreateOrder produces Order.exists = true and Order.status = CREATED,
which satisfy preconditions of MakePayment. Therefore, this project uses
a structured feature-based embedding rather than treating capability
names as ordinary words.
## 4. Proposed Representation
The application domain is an online purchase system. The experimental
dataset contains an initial state, a goal specification and six
capabilities.
The capabilities include CreateOrder, MakePayment, CancelCart,
SendNotification and two alternative implementations of order creation
using a database and a GUI.
A capability is represented as:
C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i)
where T is the capability type, I and O are inputs and outputs, P and E
are preconditions and effects, K contains constraints, R contains
resources, Q contains operational cost attributes, Rel is reliability, A
is availability and M is the execution mechanism.
The encoder converts categorical information into feature dimensions and
keeps numerical operational properties as numerical dimensions. The
resulting feature vector is standardized before use.
## 5. Mathematical Formulation
The capability embedding is defined as:
phi_C : C -> R^d
For a capability C_i, the vector contains features derived from:
- capability type
- input names, types and domains
- output names, types and domains
- preconditions
- effects
- constraints
- resources
- execution mechanism
- execution cost
- reliability
- availability
Cosine similarity is used to measure vector resemblance:
similarity(x,y) = (x . y) / (||x|| ||y||)
However, cosine similarity is not used as the sole composability
criterion. Two capabilities may have similar representations while still
being incompatible.
Functional compatibility is calculated separately as:
Compatibility(C_i,C_j) = 0.7 PE(C_i,C_j) + 0.3 IO(C_i,C_j)
where PE measures whether effects of C_i satisfy preconditions of C_j,
and IO measures whether outputs of C_i satisfy required inputs of C_j.
## 6. Capability Composition Model
For two capabilities:
C1 : S0 -> S1
C2 : S1 -> S2
if the effects and outputs of C1 satisfy the preconditions and inputs of
C2, then the composition is valid:
C2 o C1 : S0 -> S2
In the experimental application:
CreateOrder -> MakePayment
CreateOrder produces:
Order.exists = true
Order.status = CREATED
These conditions satisfy the relevant preconditions of MakePayment.
Therefore the composite capability is:
CompletePurchase = SendNotification o MakePayment o CreateOrder
The vector of a composite capability is produced by taking the mean of
the vectors of its atomic components. For two components:
v_complete = (v_create_order + v_make_payment) / 2
This is a simple composition operator chosen for the assignment and is
not claimed to be an optimal learned composition function.
## 7. Implementation
The implementation is organized as follows:
- models.py defines formal data structures.
- encoder.py converts structured capability descriptions into vectors.
- compatibility.py calculates cosine similarity and formal
compatibility.
- composition.py checks compositions and creates composite capabilities
and vectors.
- experiments.py executes the required experiments and writes result
files and graphs.
- capabilities.json contains the formal experimental dataset.
- main.py runs the complete system.
The system uses Python, NumPy, scikit-learn and Matplotlib.
## 8. Experimental Methodology
### 8.1 Capability Compatibility
The first experiment compares CreateOrder -> MakePayment and
CreateOrder -> CancelCart. According to the formal specifications, the
first pair should be compatible because CreateOrder establishes the
order state required by MakePayment. The second pair should be
incompatible because CancelCart requires Order.exists = false while
CreateOrder produces Order.exists = true.
### 8.2 Capability Composition
The second experiment constructs a three-capability composite from
CreateOrder, MakePayment and SendNotification. The composite vector is
compared with the vectors of all three atomic components.
### 8.3 Alternative Implementations
The third experiment compares three ways of creating an order: API-based
CreateOrder, database-based CreateOrderDatabase and GUI-based
CreateOrderGUI. They have related functional effects but different
implementation mechanisms and operational attributes.
### 8.4 Irrelevant Capabilities
The fourth experiment measures simple goal relevance by counting how
many effects of each capability correspond to conditions in the
specified purchase goal.
### 8.5 Operational Attributes
The fifth experiment records execution time, cost index, risk,
reliability and availability for each capability.
## 9. Results
Run `python main.py` before final submission. The program
automatically creates the following files in `results/`:
- compatibility_results.csv
- composition_results.csv
- similarity_results.csv
- goal_relevance.csv
- operational_results.csv
- compatibility_plot.png
- composition_plot.png
- similarity_plot.png
**### 9.1 Compatibility Results
The experiment produced the following results:
  Capability Pair       Cosine Similarity  Compatibility Score Composable
  CreateOrder ->                  0.3114               1.0000 True
  MakePayment                                                  
  CreateOrder ->                  0.1595               0.3000 False
  CancelCart                                                   
  MakePayment ->                  0.2051               0.7000 True
  SendNotification                                             
CreateOrder -> MakePayment is fully compatible because the effects of
CreateOrder satisfy the preconditions of MakePayment. CreateOrder ->
CancelCart is incompatible because CreateOrder establishes Order.exists
= true, while CancelCart requires Order.exists = false. MakePayment ->
SendNotification is compatible at the threshold of 0.7 because
MakePayment produces Payment.status = SUCCESS, which is the precondition
of SendNotification.
These results demonstrate that cosine similarity and formal
compatibility are distinct measures.
9.2 Composition Results
The system constructs the three-capability composite:
CompletePurchase = SendNotification o MakePayment o CreateOrder
The resulting similarities between the composite vector and the atomic
capability vectors are:
  Atomic Capability     Similarity to Composite
  CreateOrder                            0.7351
  MakePayment                            0.7514
  SendNotification                       0.5828
The embedding dimension is 65. The composite remains related to all
three atomic capabilities, with the highest similarity to MakePayment.
9.3 Alternative Implementation Results**
The API, database and GUI implementations share functional
characteristics such as producing an order, but their execution
mechanisms are represented separately. CreateOrder has cosine similarity
0.6967 with CreateOrderDatabase and 0.6537 with CreateOrderGUI.
CreateOrderDatabase and CreateOrderGUI have similarity 0.6857.
### 9.4 Goal Relevance Results
Goal relevance is calculated from the overlap between capability effects
and the desired goal conditions. The values are stored in
`goal_relevance.csv`. CreateOrder contributes Order.exists to the
goal, MakePayment contributes Payment.status, and SendNotification
contributes Notification.sent.
### 9.5 Operational Results
Execution time, cost index, risk, reliability and availability are
stored in `operational_results.csv`. For example, CreateOrder has
execution time 100 ms, reliability 0.99 and availability 1, while
MakePayment has execution time 250 ms, reliability 0.98 and availability
1.
## 10. Analysis
The experiments demonstrate why capability similarity and capability
compatibility should not be treated as identical concepts. Compatibility
depends on formal precondition-effect and input-output relationships.
CreateOrder -> MakePayment is a valid composition because the state
established by CreateOrder enables MakePayment. CreateOrder ->
CancelCart is invalid because the resulting order state conflicts with
the precondition of CancelCart. MakePayment -> SendNotification is also
valid because MakePayment establishes Payment.status = SUCCESS, which is
required by SendNotification.
The alternative implementation experiment demonstrates that the same
broad function can be implemented using different mechanisms. Therefore,
the representation includes both functional information and mechanism
information rather than treating API, database and GUI implementations
as completely identical.
The composition experiment shows that a three-capability sequence can be
mapped to a composite vector. The mean operator provides a simple
baseline for composition, but its limitations must be recognized.
Operational properties provide additional information that is not purely
semantic. For example, two capabilities may provide similar effects
while having different execution times or reliability values.
## 11. Limitations
The dataset is small and manually constructed. The feature design is
also manually specified rather than learned from a large corpus. The
compatibility weights are chosen heuristically, and the mean operation
used for vector composition is a simple baseline. More complex logical
expressions, temporal constraints and dynamic availability are not fully
modeled. Therefore, the system should be considered a problem-specific
prototype rather than a general-purpose learned embedding model.
## 12. Conclusion
This project presents a structured vector representation for formally
specified application capabilities. The representation incorporates
functional properties such as inputs, outputs, preconditions and effects
together with constraints, resources and operational attributes.
The experiments emphasize that vector similarity alone is insufficient
for capability composition. Explicit compatibility reasoning is required
to determine whether one capability can provide the conditions needed by
another. The proposed approach therefore combines vector representation
with formal compatibility checks and a composition operator. The
complete experimental sequence CreateOrder -> MakePayment ->
SendNotification produces the target conditions Order.exists = true,
Payment.status = SUCCESS and Notification.sent = true.
The work provides a baseline for more advanced approaches in which
compatibility and composition could be learned from larger datasets or
represented using graph-based or neural architectures.
## References
1. Assignment 2: Design of a Vector Embedding for Capability
Composition, PCCST503.
2. Mikolov et al., Word2Vec-related distributed word representation
work, introduced as background motivation in the assignment brief.