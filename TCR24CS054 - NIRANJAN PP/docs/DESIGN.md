# System Design

## 1. Overview

This project implements a capability composition system for an online
shopping application.

The system represents application states, goals, and capabilities using
fixed-length numerical vectors. Cosine similarity is used to compare
capabilities, while preconditions and effects are used to determine whether
capabilities are compatible and can be composed.

The implementation is written in Python.

---

## 2. Application Model

The example application is an online shopping application.

The initial state includes:

- User is authenticated
- Cart exists
- Cart contains items
- Inventory is available
- No order has been created
- Payment has not succeeded
- Notification has not been sent

The required goal is:

```text
Order.exists = true
Payment.status_success = true
Notification.sent = true
````

---

## 3. Capability Model

Each capability is represented using:

* Preconditions
* Effects
* Inputs
* Outputs
* Constraints
* Resources
* Cost
* Reliability
* Availability

The main capabilities in the application are:

```text
CreateOrder
MakePayment
SendNotification
CancelCart
SendEmailConfirmation
UpdateUserProfile
```

The main purchase workflow uses:

```text
CreateOrder -> MakePayment -> SendNotification
```

---

## 4. Vector Representation

Each capability is converted into a fixed-length numerical vector.

The vector contains information derived from the capability's:

* Preconditions
* Effects
* Inputs
* Outputs
* Constraints
* Resources
* Cost
* Reliability
* Availability

All capability vectors have the same dimensionality, allowing them to be
compared mathematically.

The vector encoding is implemented in:

```text
src/embedding.py
```

---

## 5. Cosine Similarity

Cosine similarity is used to measure similarity between capability vectors.

The project uses this to compare capabilities with similar or different
functional roles.

For example:

```text
SendNotification <-> SendEmailConfirmation
```

produces a cosine similarity of:

```text
0.9855
```

This indicates that their vector representations are highly similar.

---

## 6. Capability Compatibility

Compatibility is determined by comparing the effects of one capability with
the preconditions of the next capability.

For example:

```text
CreateOrder -> MakePayment
```

is compatible because `CreateOrder` produces:

```text
Order.exists = true
Order.status_created = true
```

which are required by `MakePayment`.

Similarly:

```text
MakePayment -> SendNotification
```

is compatible because `MakePayment` produces:

```text
Payment.status_success = true
```

which is required by `SendNotification`.

The project also demonstrates an incompatible pair:

```text
CreateOrder -> CancelCart
```

which is reported as:

```text
False
```

---

## 7. Capability Composition

Compatible capabilities can be combined into a composite capability.

The main composition is:

```text
CreateOrder -> MakePayment -> SendNotification
```

The composite capability produces:

```text
Order.exists = true
Order.status_created = true
Payment.status_success = true
Notification.sent = true
```

Its operational attributes are:

```text
Cost: 6.0000
Reliability: 0.9123
Availability: 1.0000
```

The composition functionality is implemented in:

```text
src/composition.py
```

---

## 8. Goal Verification

After composition, the resulting composite capability is checked against the
required goal.

The verification produces:

```text
Order.exists: required=True, produced=True
Payment.status_success: required=True, produced=True
Notification.sent: required=True, produced=True

Goal achieved: True
```

Therefore, the composed capability satisfies all required goal conditions.

---

## 9. Project Structure

```text
assignment2_ml/
│
├── data/
│   └── applications.json
│
├── docs/
│   ├── DESIGN.md
│   ├── EXPERIMENTAL_RESULTS.md
│   └── REPORT.md
│
├── src/
│   ├── main.py
│   ├── models.py
│   ├── embedding.py
│   ├── compatibility.py
│   ├── composition.py
│   └── experiments.py
│
├── tests/
│   └── test_capability_composition.py
│
├── requirements.txt
└── README.md
```
