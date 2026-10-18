# Assignment 2: Design of a Vector Embedding for Capability Composition

## 1. Problem Definition

The assignment studies how formally specified application states, goals, and executable
capabilities can be represented in a vector space so that functional relationships such
as compatibility and composition can be investigated.

The implementation uses a small e-commerce application. Capabilities include order
creation, payment, notification, cart cancellation, profile update, and product search.

The focus is the representation of operations rather than redesigning the planner from
Assignment 1.

## 2. Design Requirements

The embedding is evaluated for:
- capability identity;
- state awareness;
- precondition-effect compatibility;
- input-output compatibility;
- similarity versus composability;
- capability composition;
- goal relevance;
- operational properties;
- consistency;
- computational/storage efficiency.

## 3. Related Embedding Approaches

### One-hot / multi-hot representation

Categorical and set-valued properties can be represented with binary feature vectors.
This is interpretable and simple, but it does not automatically encode deeper
relationships.

### Word2Vec-style distributed representations

Word2Vec represents words as dense vectors and can capture semantic relationships.
For this assignment, a generic word embedding is not sufficient by itself because
capability composition depends on formal inputs, outputs, preconditions, effects,
constraints and resources.

### Structured feature embedding

The proposed method uses a structured feature vector specifically designed for the
formal capability model. It preserves separate feature blocks for different functional
roles.

## 4. Proposed Representation

For a capability C:

C = (T, I, O, P, E, K, R, Q, Rel, A)

The embedding is:

φ(C) = [V_T, V_I, V_O, V_P, V_E, V_K, V_R, V_Q]

where:

- V_T = capability type vector
- V_I = input vector
- V_O = output vector
- V_P = precondition vector
- V_E = effect vector
- V_K = constraint vector
- V_R = resource vector
- V_Q = operational vector

The operational vector is:

V_Q = [normalized_cost, reliability, availability, risk]

State and goal encodings use a common condition vocabulary.

## 5. Mathematical Formulation

### Capability vector

φ(C) = concat(V_T, V_I, V_O, V_P, V_E, V_K, V_R, V_Q)

### Similarity

Cosine similarity is:

sim(x,y) = (x · y) / (||x|| ||y||)

### Compatibility

For capabilities C_i and C_j:

C_i -> C_j

is compatible when the relevant effects of C_i satisfy the preconditions of C_j
and required data dependencies are available.

A key relationship is:

E_i ⇒ P_j

and, where applicable:

O_i ⇒ I_j

Similarity is used as a descriptive measure, while compatibility is evaluated
structurally.

## 6. Capability Composition Model

For:

C1 : S0 -> S1
C2 : S1 -> S2

if C1 produces the conditions required by C2, then:

C2 ∘ C1 : S0 -> S2

For the experiment:

CreateOrder -> MakePayment -> SendNotification

the composite capability is named:

CompletePurchase

Its aggregated operational properties are:

- cost = sum of component costs;
- reliability = product of component reliabilities;
- availability = minimum component availability;
- risk = capped sum;
- resources = union of component resources.

The final effects are the final values produced by the sequence.

## 7. Implementation

The implementation is divided into:

- `models.py`: formal data structures;
- `encoder.py`: structured vector construction;
- `composition.py`: compatibility and composition;
- `experiments.py`: all experiments and result generation;
- `main.py`: program entry point.

The dataset is stored in `data/application.json`.

## 8. Experimental Methodology

### Experiment 1: Capability compatibility

Test:

- CreateOrder -> MakePayment
- CreateOrder -> CancelCart

Expected relationship:

- CreateOrder -> MakePayment: compatible
- CreateOrder -> CancelCart: incompatible

### Experiment 2: Capability composition

Compose:

CreateOrder -> MakePayment -> SendNotification

and compare the encoded composite capability with its atomic components and
the mean of the atomic vectors.

### Experiment 3: Alternative implementations

Compare:

- CreateOrder
- CreateOrder_Database
- CreateOrder_GUI

They have similar functional preconditions/effects but different implementation
types and resources.

### Experiment 4: Irrelevant capabilities

Compare goal-related capabilities with:

- UpdateProfile
- SearchProduct

### Experiment 5: Operational attributes

Compare:

- MakePayment
- MakePayment_Backup

using cost, reliability, availability and risk.

## 9. Results

Run:

```bash
python -m src.main
```

Then insert the generated tables and plots from `results/` into the final report.

Important generated files:

- `capability_vectors.csv`
- `similarity_matrix.csv`
- `compatibility_results.csv`
- `composition_results.csv`
- `alternative_implementation_results.csv`
- `irrelevant_results.csv`
- `operational_results.csv`
- `experiment_summary.csv`
- `similarity_heatmap.png`
- `experiment_scores.png`

## 10. Analysis

Discuss whether:
1. different capabilities receive distinguishable vectors;
2. state/goal conditions can be represented;
3. compatible and incompatible pairs are distinguished structurally;
4. input-output dependencies are represented;
5. composition can be represented;
6. goal-related capabilities differ from irrelevant capabilities;
7. operational attributes influence vectors;
8. the representation remains consistent across experiments.

Do not claim that cosine similarity alone proves composability. The implementation
uses structural compatibility for that purpose.

## 11. Limitations

- The vocabulary is built from the experimental dataset, so unseen predicates require
  vocabulary extension.
- Exact symbolic condition matching is used; semantic equivalence such as
  "authenticated" and "user_logged_in" is not automatically learned.
- The vector is interpretable but not a learned dense embedding.
- The operational features are normalized using the current dataset.
- The experiment uses a small synthetic application rather than a large real-world
  capability corpus.

## 12. Conclusion

The project demonstrates a problem-specific structured vector representation for
formally specified application capabilities. The representation combines functional
properties and operational attributes and separates vector similarity from the
structural compatibility relation required for composition.

The experiments investigate capability compatibility, composition, alternative
implementations, irrelevant capabilities, and operational properties.
