eg2ml.zip
Zip Archive
eg3ml.zip
Zip Archive
ml 2.pdf
PDF
machine learning assignment. 2 examples have been attached. just explain what the project is about, use python, how many files of code are we talking about. Machine Learning 
Assignment 1 
Design of a Safe Semantic Planner in a Finite 
Cartesian State Space 
Department of Computer Science and Engineering 
Objective 
The objective of this assignment is to design and implement a generic planning algorithm 
that computes a safe path in a finite Cartesian state space. Although inspired by AI plan 
ning, this assignment emphasizes graph search, heuristic design, optimization, software 
engineering, and experimental evaluation. 
Problem Definition 
Let 
S ={s1,s2,...,sn} 
be a finite set of states embedded in a Cartesian space 
Rd. 
Each state has a vector representation 
si = (x1,x2,...,xd). 
The planner receives 
• Initial state sI 
• Goal state sG 
• Set of bad states 
• Directed transitions 
B ={b1,b2,...,bk} 
T ={(si,sj)} 
Each transition additionally contains 
• Cost 
1 
• Reliability 
• Safety score 
• Availability flag 
The planner must compute a sequence of transitions from the initial state to the goal 
while avoiding bad states. 
Optimization Objectives 
A valid planner should satisfy: 
1. Reach the goal state. 
2. Never visit a bad state. 
3. Minimize total transition cost. 
4. Maximize the minimum Euclidean distance from every visited state to the nearest 
bad state. 
5. Produce the solution within reasonable execution time. 
An example objective function is 
Score(P) = αG−βC +γD+δR 
where 
• G=goal completion 
• C =cumulative transition cost 
• D=minimum safety distance 
• R=cumulative reliability 
Dynamic Environment 
The planner should be designed so that the following may change periodically: 
• Goal state 
• Bad states 
• Transition availability 
• New transitions 
• Removed transitions 
Students should explain how their implementation can efficiently replan after such 
updates. 
2 
Suggested Software Interfaces 
State 
class State 
{ 
public : 
uint64 t id ; 
std :: vector<double> embedding; 
}; 
Transition 
class Transition 
{ 
public : 
uint64 t id ; 
uint64 t from; 
uint64 t to; 
double cost ; 
double safety ; 
double reliability ; 
bool available ; 
}; 
Planning Problem 
class PlanningProblem 
{ 
public : 
uint64 t initialState ; 
uint64 t goalState ; 
std :: vector<uint64 t> badStates ; 
std :: vector<State> states ; 
std :: vector<Transition> transitions ; 
}; 
Planning Result 
class PlanningResult 
{ 
public : 
bool success ; 
std :: vector<uint64 t> statePath ; 
std :: vector<uint64 t> transitionPath ; 
double totalCost ; 
3 
double safetyScore ; 
}; 
Planner Interface 
class Planner 
{ 
public : 
virtual PlanningResult plan( 
const PlanningProblem& problem)=0; 
}; 
Algorithm Design Guidelines 
Students may choose one of the following: 
• LPA* 
• D* Lite 
The report must clearly describe 
1. State representation 
2. Data structures 
3. Heuristic function 
4. Safety computation 
5. Time complexity 
6. Space complexity 
Illustrative Test Cases 
Test Case 1: Basic Reachability 
Graph: 
S →A→B→G 
Expected result: planner returns the unique valid path. 
4 
Test Case 2: Bad State Avoidance 
Paths: 
where X is a bad state, 
and 
S →A→X→G 
S →C→D→G. 
Expected result: second path must be selected. 
Test Case 3: Safety Margin 
Two valid paths exist. 
Path 1 has lower cost but passes close to bad states. 
Path 2 has higher cost but remains significantly farther away. 
Students should explain how the planner balances cost and safety. 
Test Case 4: Dynamic Transition 
Initially, 
S →A→G 
Later, transition (A,G) becomes unavailable. 
Expected result: planner computes an alternative path. 
Test Case 5: Goal Update 
The goal changes during execution. 
The planner should produce a revised path without rebuilding all data structures 
whenever possible. 
Test Case 6: Transition Addition 
A new shortcut transition is inserted. 
Expected result: planner discovers the improved solution. 
Students should evaluate: 
• Goal success rate 
• Number of bad states visited (expected zero) 
• Total path cost 
• Minimum distance to bad states 
• Number of explored states 
• Planning time 
5 
• Memory usage 
• Replanning time 
Deliverables 
1. C++ source code. 
2. Design report. 
3. Experimental results. 
4. User manual. 
5. Demonstration. 
Bonus (Optional) 
Implement one or more of the following: 
• Multi-goal planning. 
• Time-dependent transition availability. 
• Incremental replanning. 
• Parallel search. 
• Learning-based heuristic. 
• Test it on Knowledge graph. i only want to know necessary stuff on what we r working on. then we'll directly get into code. give all codes at once(unless specified). define clearly the structure-eg: in folder xyz, create file abc.. 

The output is now consistent with the intended experiments. Do not change the code again yet.

The only thing I want to fix before submission is Experiment 4's interpretation: BrowseCatalog gets compatibility 1.0 because it has no preconditions, but its dependency score is correctly 0.0. That's not a code failure; it shows why the assignment's distinction between compatibility and similarity/dependency matters.

Next step: prepare the technical report and README from the actual implementation/results.

We need to produce:

README.md
Technical report
Final check that the folder contains all required files
Then, if needed, package the project as a ZIP.

I can 
generate the README + report content next, based strictly on the Assignment 2 requirements and your actual experiment results.

sure go on

The two documents are ready:

Download README.md
Download technical_report.md

Next: we should do the final project check — make sure your actual project folder has the correct files and that everything runs from a clean directory. Then we can package the submission ZIP. 

README.md
Document
technical_report.md
Document

i did right click->new folder=README.md but its not opening. also there is a pycache inside src . is that ok?where to attach the technical_report.md

Yes—three separate things:

1. README.md is a file, not a folder

You accidentally did:

Right click → New folder → README.md

Delete that folder.

Then inside your main ml_assignment_2 folder:

Right click → New → Text Document

Rename the resulting file to:

README.md

Make sure it is not:

README.md.txt

If Windows hides extensions, enable:

File Explorer → View → Show → File name extensions

Then open README.md with Notepad/VS Code and paste the README I gave you.

2. __pycache__ inside src

That's normal. Python creates it automatically when you run the program.

You do not need it for submission.

Your final folder should ideally look like:

ml_assignment_2/
│
├── src/
│   ├── models.py
│   ├── embedding.py
│   ├── composition.py
│   ├── experiments.py
│   ├── main.py
│   └── __pycache__/       ← DELETE this before ZIP
│
├── data/
│   └── problems.json
│
├── README.md
└── technical_report.md

So just delete __pycache__ before making the final ZIP. It will be recreated if you run the program again, so delete it after your final run.

3. Where does technical_report.md go?

Put it in the main project folder, at the same level as README.md:

ml_assignment_2/
├── src/
├── data/
├── README.md
└── technical_report.md

So not inside src and not inside data.

You can download it here:

Download technical_report.md

And the README here:

Download README.md

If your college specifically asks for a PDF/DOCX report rather than .md, don't submit the Markdown report yet—we should convert it to the required format first.

technical_report.md
Document
README.md
Document
Chat paused until usage resets tomorrow at 12:34 AM
You’ve reached the limit for chats that include files or images. Start a new text-only chat or upgrade to continue now.
New chat
Claim free offer

Library
/
technical_report.md
Machine Learning Assignment 2
Design of a Vector Embedding for Capability Composition
Abstract

This project designs and implements a problem-specific vector
representation for formally specified states, goals and executable
capabilities. The primary objective is to preserve relationships needed
to identify compatible capabilities and construct complex capabilities
from simpler ones.

The implementation represents functional properties including
preconditions, effects, inputs, outputs and capability type. It
additionally represents operational attributes including execution time,
monetary cost, resource cost, risk and reliability.

The evaluation uses an e-commerce capability dataset and five
experiments covering compatibility, sequential composition, alternative
implementations, irrelevant capabilities and operational attributes.

1. Introduction

A capability-oriented application can be represented using states, goals
and executable capabilities. A capability has conditions under which it
can execute, inputs, outputs, effects, implementation information and
operational properties.

For capability composition, the representation must preserve more than
superficial similarity.

The central research question is:

Can formal states, goals and executable capabilities be represented in
a vector space while preserving relationships required for capability
compatibility, composition and construction of complex application
functionality?

The project focuses on representation rather than path-search
algorithms.

2. Formal Representation

The application is represented conceptually as:

A = (S, C, SI, G, R, K)

where S is the state space, C the set of capabilities, SI the
initial state, G the goal specification, R the resources and K the
global constraints and policies.

The implementation focuses on states, goals and capabilities.

3. State Representation

A state is represented as state-variable/value pairs. The experimental
dataset contains variables such as:

User.authenticated
User.role
Cart.exists
Cart.item_count
Order.exists
Payment.status
Notification.sent

For each variable/value feature:

1.0 means the specified value matches.
-1.0 means the variable is specified with another value.
0.0 means the variable is unspecified.

State vector dimension: 16.

4. Goal Representation

A goal is a collection of desired conditions. The experimental goal
includes:

Order.exists = True
Payment.status = SUCCESS
Notification.sent = True

Goals use the same condition encoding as states.

Goal vector dimension: 16.

5. Capability Representation

A capability is represented conceptually by type, inputs, outputs,
preconditions, effects, constraints, resources, operational quality,
reliability, availability and execution mechanism.

The implementation encodes:

[preconditions]
[effects]
[inputs]
[outputs]
[capability type]
[time cost]
[money cost]
[resource cost]
[risk]
[reliability]

Capability vector dimension: 48.

6. Operational Attributes

Five operational attributes are included:

Time cost
Money cost
Resource cost
Risk
Reliability

Time uses a logarithmic transformation:

log(1 + time)

to reduce the effect of large raw values.

7. Similarity

Cosine similarity is used:

sim(a,b) = (a · b) / (||a|| ||b||)

Similarity is not treated as the definition of composability.

The implementation distinguishes:

VECTOR SIMILARITY
        ≠
FUNCTIONAL COMPATIBILITY
        ≠
DEPENDENCY
8. Functional Compatibility

Compatibility is evaluated using precondition/effect and input/output
relationships.

The score is:

Compatibility =
    0.7 × precondition/effect score
  + 0.3 × input/output score

A separate dependency score indicates whether the second capability
actually depends on requirements supplied by the first.

9. Capability Composition

For:

C1 : S0 → S1
C2 : S1 → S2

the capabilities can be composed when the relevant requirements of C2
are satisfied by C1.

The experiment constructs:

CreateOrder
    →
MakePayment_API
    →
SendNotification

Composite properties:

Time cost:     225.00 ms
Money cost:    0.0650
Reliability:  0.990017

Effects include:

Order.exists = True
Order.status = PAID
Payment.status = SUCCESS
Notification.sent = True
10. Experimental Setup
States:          3
Goals:           1
Capabilities:    8

State dimension:       16
Goal dimension:        16
Capability dimension: 48

Capabilities:

CreateOrder
MakePayment_API
MakePayment_DB
MakePayment_GUI
SendNotification
CancelCart
BrowseCatalog
UpdateWishlist
11. Experiment 1 --- Capability Compatibility

Pair Vector Precondition/Effect Input/Output Dependency Compatibility
Similarity

CreateOrder → 0.0748 1.0000 1.0000 1.0000 1.0000
MakePayment_API

CreateOrder → MakePayment_API has low cosine similarity but perfect
functional compatibility. CreateOrder → CancelCart has higher cosine
similarity but lower functional compatibility.

This demonstrates that vector similarity and composability are not
identical relationships.

12. Experiment 2 --- Capability Composition

The chain is:

CreateOrder
    →
MakePayment_API
    →
SendNotification

Pairwise compatibility:

CreateOrder → MakePayment_API = 1.0000
MakePayment_API → SendNotification = 1.0000

The composite capability has:

Time cost:     225.00 ms
Money cost:    0.0650
Reliability:   0.990017

This demonstrates construction of a larger capability from smaller
capabilities.

13. Experiment 3 --- Alternative Implementations

The three payment implementations are:

MakePayment_API
MakePayment_DB
MakePayment_GUI

Pairwise similarities:

Pair Similarity

API ↔ Database 0.9372
API ↔ GUI 0.9383
Database ↔ GUI 0.9368

Their common functional structure keeps them closely related while their
capability types distinguish the implementation mechanisms.

14. Experiment 4 --- Irrelevant Capabilities

Reference:

MakePayment_API

Results:

Capability Similarity Compatibility Dependency

BrowseCatalog 0.3027 1.0000 0.0000
UpdateWishlist 0.2647 0.3000 0.0000
CancelCart 0.0135 0.3000 0.0000

BrowseCatalog receives compatibility 1.0000 because it has no
requirements that are violated. Its dependency score is 0.0000,
showing that it does not depend on payment.

This illustrates why compatibility and dependency are separately
reported.

15. Experiment 5 --- Operational Attributes

Implementation Time (ms) Money Resource Risk Reliability

API 120 0.050 1 0.010 0.992
Database 35 0.002 2 0.050 0.965
GUI 200 0.080 1 0.030 0.975

A controlled experiment changes only operational attributes of the API
capability:

Comparison Similarity

Original → Cheap/Fast 0.998981
Original → Expensive/Slow 0.935757
Cheap/Fast → Expensive/Slow 0.929360

Operational vectors:

Original:
[0.479579, 0.05, 0.1, 0.01, 0.992]

Cheap/Fast:
[0.304452, 0.001, 0.1, 0.001, 0.999]

Expensive/Slow:
[0.690875, 1.0, 1.0, 0.5, 0.5]

The functional fields remain unchanged while the operational dimensions
change.

16. Evaluation Against Required Properties
Capability identity

Different capabilities have distinct structured representations.

State awareness

Preconditions and effects are encoded using state-variable/value
features.

Precondition-effect compatibility

The implementation evaluates whether effects of one capability satisfy
preconditions of another.

Input-output compatibility

Inputs and outputs are represented and compared separately.

Similarity versus composability

Cosine similarity is explicitly separated from functional compatibility.

Composition

Sequential capabilities can be combined into composite capabilities.

Goal relevance

Goals are represented in the same condition-based space as states, and
capability effects provide the information needed to relate capabilities
to desired state conditions.

Operational properties

Time, money, resource cost, risk and reliability are included.

Consistency

Fixed feature ordering ensures that equivalent vector positions have
consistent meanings.

Efficiency

The representation uses fixed-size numeric vectors and direct
comparisons.

17. Limitations

The dataset is small and domain-specific, so the experiments do not
establish generalization to other application domains.

The feature space is manually designed and the compatibility weights are
manually selected:

70% precondition/effect
30% input/output

Functional compatibility is explicitly calculated from formal
relationships rather than inferred solely from cosine similarity.

The current evaluation also contains limited quantitative testing of
direct capability-to-goal relevance.

18. Conclusion

The implementation provides a structured, problem-specific vector
representation for formal states, goals and executable capabilities.

The representation combines state conditions, preconditions, effects,
inputs/outputs, capability type and operational attributes.

The experiments demonstrate that:

Vector similarity and functional compatibility capture different
relationships.
Alternative implementations of the same function remain closely
related.
Sequential capabilities can be combined into composite capabilities.
Operational attributes influence the resulting representation.

The resulting system therefore provides a concrete vector representation
supporting capability identity, state awareness, compatibility analysis,
sequential composition and operational-property representation.