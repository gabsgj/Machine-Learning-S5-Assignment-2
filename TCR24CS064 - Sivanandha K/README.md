# PCCST503 – Machine Learning

## Assignment 2: Design of a Vector Embedding for Capability Composition

### Student Details

Name: **SIVANANDHA K**

Register Number: **TCR24CS064**

Course: Machine Learning

---

## 📌 Project Description

This project implements a **problem-specific vector representation for formal states, goals, and executable capabilities**.

The system represents capabilities using a **44-dimensional feature vector** and evaluates:

* Capability representation
* Capability compatibility
* Vector similarity
* Alternative implementations
* Capability composition
* Goal relevance
* Operational properties

---

## 📥 Inputs

The system uses:

1. States
2. Goals
3. Capabilities
4. Inputs and outputs
5. Preconditions and effects
6. Resources
7. Execution mechanisms
8. Cost
9. Risk
10. Reliability
11. Availability

---

## 📤 Outputs

The program produces:

* Capability vector representations
* Vector similarity values
* Capability compatibility results
* Composite capability
* Composite cost, risk, reliability, and availability
* State and goal vectors
* Experimental results

---

## 🛠️ Technologies Used

* Python 3
* NumPy
* JSON
* Cosine Similarity
* Vector-based Feature Representation

---

## ⚙️ How to Run the Project

### Step 1: Install NumPy

```bash
pip3 install numpy
```

### Step 2: Open the Project Folder

```bash
cd ~/PCCST503_Assignment_2
```

### Step 3: Run the Experiments

```bash
python3 experiments.py
```

### Step 4: Save Results

```bash
python3 experiments.py > results.txt
```

---

## 🧠 Main Functions

The implementation provides:

```text
encode_state()
encode_goal()
encode_capability()
similarity()
compatibility()
compose()
```

The capability representation includes:

* Capability type
* Inputs
* Outputs
* Preconditions
* Effects
* Resources
* Execution mechanism
* Cost
* Risk
* Reliability
* Availability

---

## 🔗 Capability Composition

The main composition tested is:

```text
CreateOrder
      ↓
MakePayment
      ↓
SendNotification
```

Compatibility results:

```text
CreateOrder → MakePayment = 1.0
MakePayment → SendNotification = 1.0
```

---

## 📊 Experimental Results

### Capability Representation

```text
CreateOrder -> vector dimension = 44 , non-zero features = 14
MakePayment -> vector dimension = 44 , non-zero features = 14
CancelCart -> vector dimension = 44 , non-zero features = 9
```

### Capability Compatibility

```text
CreateOrder -> MakePayment : 1.0
CreateOrder -> CancelCart : 0.0
```

### Vector Similarity

```text
CreateOrder vs CreateOrderDatabase = 0.783
CreateOrder vs CancelCart = 0.436
```

### Alternative Implementations

```text
API vs Database = 0.783
API vs GUI = 0.832
Database vs GUI = 0.782
```

### Goal Relevance

```text
CreateOrder vs CompletePurchase goal = 0.167
CheckInventory vs CompletePurchase goal = 0.0
```

### Composite Capability

```text
Composite capability vector dimension = 44
Composite cost = 0.65
Composite risk = 0.17
Composite reliability = 0.941
Composite availability = 1.0
```

### State and Goal Encoding

```text
Initial state vector dimension = 44
Goal vector dimension = 44
CreateOrder vs initial state = 0.0
```

---

## 📁 Project Structure

```text
PCCST503_Assignment_2/
│
├── README.md
├── requirements.txt
├── .gitignore
├── capability_embedding.py
├── capability_dataset.json
├── experiments.py
├── results.txt
└── report.md
```

---

## 🔓 Repository Status

This repository contains the complete implementation, experimental dataset, results, and technical report required for the assignment.

The repository is public as required by the assignment instructions.

