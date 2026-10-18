
````markdown
# Deliverable 3: Experimental Dataset

## 1. Dataset Overview

The experimental dataset represents a simple e-commerce application.

The application contains capabilities related to:

- creating an order
- making a payment
- confirming an order
- cancelling a cart
- sending an email

The dataset is used to evaluate capability compatibility, composition,
similarity, goal relevance, and operational attributes.

---

## 2. Initial State

The initial state is:

```text
cart_exists
````

Its vector representation is:

```text
[1, 0, 0, 0]
```

This represents a state in which a shopping cart exists.

---

## 3. Goal

The main goal is:

```text
payment_success
```

Its vector representation is:

```text
[0, 0, 1, 0]
```

The objective is to determine whether available capabilities can
contribute toward this goal.

---

## 4. Atomic Capabilities

### 4.1 CreateOrder

```text
Name:
CreateOrder

Input:
cart_id

Output:
order_id

Precondition:
cart_exists

Effect:
order_exists

Cost:
0.01

Reliability:
0.99
```

---

### 4.2 MakePayment

```text
Name:
MakePayment

Input:
order_id

Output:
payment_id

Precondition:
order_exists

Effect:
payment_success

Cost:
0.05

Reliability:
0.98
```

---

### 4.3 ConfirmOrder

```text
Name:
ConfirmOrder

Input:
payment_id

Output:
confirmation_id

Precondition:
payment_success

Effect:
order_confirmed

Cost:
0.02

Reliability:
0.99
```

---

### 4.4 CancelCart

```text
Name:
CancelCart

Input:
cart_id

Output:
none

Precondition:
cart_exists

Effect:
order_cancelled

Cost:
0.02

Reliability:
0.97
```

---

### 4.5 SendEmail

```text
Name:
SendEmail

Inputs:
email_address
message

Output:
email_id

Precondition:
email_address_available

Effect:
email_sent

Cost:
0.03

Reliability:
0.95
```

---

# 5. Experiment 1: Capability Compatibility

The first experiment evaluates whether the representation can distinguish
compatible and incompatible capabilities.

### Test 1

```text
CreateOrder → MakePayment
```

CreateOrder produces:

```text
order_exists
```

MakePayment requires:

```text
order_exists
```

The output and input also match:

```text
order_id → order_id
```

Therefore:

```text
Compatible = Yes
```

---

### Test 2

```text
CreateOrder → CancelCart
```

CreateOrder produces:

```text
order_exists
```

CancelCart requires:

```text
cart_exists
```

Therefore the effect-precondition condition is not satisfied.

Although both capabilities operate on a shopping cart/order domain,
they are not composition-compatible under the implemented rule.

Therefore:

```text
Compatible = No
```

---

# 6. Experiment 2: Capability Composition

The second experiment evaluates whether atomic capabilities can be
combined into a composite capability.

The sequence is:

```text
CreateOrder
      ↓
MakePayment
      ↓
ConfirmOrder
```

The first composition is:

```text
CreateOrder → MakePayment
```

which produces:

```text
CreateOrder_MakePayment
```

The second composition is:

```text
CreateOrder_MakePayment → ConfirmOrder
```

which produces:

```text
CreateOrder_MakePayment_ConfirmOrder
```

The resulting composite capability has:

```text
Cost:
0.08

Reliability:
0.960498
```

This experiment tests recursive capability composition.

---

# 7. Experiment 3: Similarity vs Composability

Cosine similarity is used to compare capability vectors.

The measured results are:

| Capability Pair           | Similarity | Compatible |
| ------------------------- | ---------: | ---------- |
| CreateOrder – MakePayment |   0.597541 | Yes        |
| CreateOrder – CancelCart  |   0.668224 | No         |
| CreateOrder – SendEmail   |   0.443541 | No         |

The result demonstrates that a higher similarity value does not
necessarily mean that two capabilities can be composed.

For example:

```text
CreateOrder – CancelCart
Similarity = 0.668224
Compatibility = No
```

while:

```text
CreateOrder – MakePayment
Similarity = 0.597541
Compatibility = Yes
```

Therefore:

```text
Similarity and composability are different relationships.
```

---

# 8. Experiment 4: Goal Relevance

The goal is:

```text
payment_success
```

The capabilities are evaluated according to whether their effects
contribute directly to this goal.

### MakePayment

Effect:

```text
payment_success
```

Therefore:

```text
MakePayment → Relevant
```

### CreateOrder

Effect:

```text
order_exists
```

Therefore:

```text
CreateOrder → Not directly relevant
```

However, CreateOrder is still useful because it enables MakePayment.

This demonstrates the difference between:

* direct goal relevance
* usefulness for composition

---

# 9. Experiment 5: Operational Attributes

The dataset includes two operational attributes:

* cost
* reliability

### Cost

For a composite capability:

```text
Cost(composite)
=
Cost(C1) + Cost(C2)
```

For example:

```text
CreateOrder + MakePayment

0.01 + 0.05 = 0.06
```

### Reliability

For sequential capabilities:

```text
Reliability(composite)
=
Reliability(C1) × Reliability(C2)
```

For example:

```text
0.99 × 0.98 = 0.9702
```

For three capabilities:

```text
0.99 × 0.98 × 0.99 = 0.960498
```

These values allow the effect of operational properties on capability
composition to be investigated.

---

# 10. Experimental Summary

| Experiment             | Purpose                                                                    |
| ---------------------- | -------------------------------------------------------------------------- |
| Compatibility          | Test whether compatible and incompatible capabilities can be distinguished |
| Composition            | Construct composite capabilities                                           |
| Similarity             | Measure functional resemblance                                             |
| Goal relevance         | Identify capabilities contributing to the goal                             |
| Operational attributes | Evaluate cost and reliability                                              |

The dataset provides atomic capabilities, an initial state, a goal,
capability relationships, compositions, and operational attributes.

These experiments will be used in the technical report to evaluate the
proposed embedding.



```
