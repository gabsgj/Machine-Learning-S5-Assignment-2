# Experimental Report

## 1. Introduction

This project evaluates a capability composition approach for an online
shopping application using vector representations.

The experiments investigate:

- Capability compatibility
- Capability composition
- Alternative implementations
- Irrelevant capabilities
- Operational attributes
- Goal achievement

The experiments are implemented in Python and can be executed using:

```bash
python3 -m src.experiments
````

---

## 2. Experiment 1: Capability Compatibility

The first experiment tests whether capabilities can be connected based on
their preconditions and effects.

### Compatible Capability

The following sequence is tested:

```text
CreateOrder -> MakePayment
```

Result:

```text
CreateOrder -> MakePayment: True
```

`CreateOrder` produces the conditions required by `MakePayment`, namely:

```text
Order.exists = true
Order.status_created = true
```

The second compatible pair is:

```text
MakePayment -> SendNotification
```

Result:

```text
MakePayment -> SendNotification: True
```

`MakePayment` produces:

```text
Payment.status_success = true
```

which is required by `SendNotification`.

### Incompatible Capability

The following pair is tested:

```text
CreateOrder -> CancelCart
```

Result:

```text
CreateOrder -> CancelCart: False
```

The effects of `CreateOrder` do not satisfy the precondition required by
`CancelCart`.

Therefore, the experiment demonstrates that capability composition is
restricted by precondition/effect compatibility.

---

## 3. Experiment 2: Capability Composition

The compatible capabilities are composed into a single workflow:

```text
CreateOrder -> MakePayment -> SendNotification
```

The resulting composite capability has the following operational attributes:

```text
Cost: 6.0000
Reliability: 0.9123
Availability: 1.0000
```

The composite capability produces the following effects:

```text
Order.exists = true
Order.status_created = true
Payment.status_success = true
Notification.sent = true
```

The composition therefore represents a complete purchase workflow.

---

## 4. Composite Goal Verification

The composite capability is checked against the required application goal.

The goal requires:

```text
Order.exists = true
Payment.status_success = true
Notification.sent = true
```

The verification result is:

```text
Order.exists: required=True, produced=True
Payment.status_success: required=True, produced=True
Notification.sent: required=True, produced=True
Goal achieved: True
```

All required goal conditions are produced by the composite capability.

---

## 5. Experiment 3: Alternative Implementations

The project contains two capabilities that perform a similar functional role:

```text
SendNotification
SendEmailConfirmation
```

Both capabilities require:

```text
Payment.status_success = true
```

and produce:

```text
Notification.sent = true
```

Their vector representations are compared using cosine similarity.

The measured result is:

```text
SendNotification <-> SendEmailConfirmation: 0.9855
```

The high similarity reflects the similarity of the encoded capability
information.

This experiment demonstrates how vector representations can be used to
compare alternative implementations of a similar function.

---

## 6. Experiment 4: Irrelevant Capability

The project also tests whether an unrelated capability contributes to the
purchase goal.

The capability tested is:

```text
UpdateUserProfile
```

Its effect is:

```text
User.profile_updated
```

The purchase goal contains:

```text
Notification.sent
Order.exists
Payment.status_success
```

The experiment produces:

```text
Goal conditions: ['Notification.sent', 'Order.exists', 'Payment.status_success']
UpdateUserProfile effects: ['User.profile_updated']
Effects relevant to goal: []
UpdateUserProfile contributes to goal: False
```

Therefore, `UpdateUserProfile` does not contribute to the specified purchase
goal.

---

## 7. Experiment 5: Operational Attributes

The operational attributes of the capabilities used in the successful
composition are measured.

### Individual Capabilities

#### CreateOrder

```text
Cost: 2.0000
Reliability: 0.9900
Availability: 1.0000
```

#### MakePayment

```text
Cost: 3.0000
Reliability: 0.9700
Availability: 1.0000
```

#### SendNotification

```text
Cost: 1.0000
Reliability: 0.9500
Availability: 1.0000
```

### Composite Capability

```text
Cost: 6.0000
Reliability: 0.9123
Availability: 1.0000
```

The composite cost is the combined cost of the three capabilities:

```text
2.0 + 3.0 + 1.0 = 6.0
```

The composite reliability is calculated from the reliability values of the
participating capabilities.

The composite availability is:

```text
1.0000
```

---

## 8. Complete Experimental Results

The formal experiment execution produces the following results:

```text
============================================================
FORMAL EXPERIMENTS
============================================================

Experiment 1: Capability compatibility
CreateOrder -> MakePayment: True
CreateOrder -> CancelCart: False

Experiment 2: Capability composition
Composite: CreateOrder -> MakePayment -> SendNotification
Cost: 6.0000
Reliability: 0.9123
Availability: 1.0000

Composite goal verification
Order.exists: required=True, produced=True
Payment.status_success: required=True, produced=True
Notification.sent: required=True, produced=True
Goal achieved: True

Experiment 3: Alternative implementations
SendNotification <-> SendEmailConfirmation: 0.9855

Experiment 4: Irrelevant capability
UpdateUserProfile contributes to goal: False

Experiment 5: Operational attributes

Individual capabilities:
CreateOrder: cost=2.0000, reliability=0.9900, availability=1.0000
MakePayment: cost=3.0000, reliability=0.9700, availability=1.0000
SendNotification: cost=1.0000, reliability=0.9500, availability=1.0000

Composite capability:
Cost: 6.0000
Reliability: 0.9123
Availability: 1.0000
```

---

## 9. Automated Testing

The project includes automated tests using `pytest`.

The test suite is executed using:

```bash
python3 -m pytest
```

The final test execution produced:

```text
collected 7 items

tests/test_capability_composition.py ....... [100%]

7 passed
```

Therefore, all seven implemented tests passed successfully.

---

## 10. Summary

The experiments demonstrate the following:

1. Compatible capabilities can be identified using preconditions and effects.
2. Incompatible capabilities are rejected from the composition sequence.
3. Compatible capabilities can be composed into a composite capability.
4. Alternative implementations can be compared using cosine similarity.
5. Irrelevant capabilities can be identified based on their effects and the
   required goal conditions.
6. Cost, reliability, and availability can be calculated for a composite
   capability.
7. The resulting composite capability can be checked against the application
   goal.
8. The automated test suite successfully passed all seven tests.

The final successful workflow is:

```text
CreateOrder
     |
     v
MakePayment
     |
     v
SendNotification
```

The workflow achieves:

```text
Order.exists = true
Payment.status_success = true
Notification.sent = true
```

with:

```text
Cost: 6.0000
Reliability: 0.9123
Availability: 1.0000
```

The final goal verification is:

```text
Goal achieved: True
```

