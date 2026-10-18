# Deliverable 3 — Experimental Dataset

## Domain

**Online Course Enrollment System**

The same domain is used across four formally specified problems to test
consistency rather than changing to unrelated toy examples.

## Core atomic capabilities

1. SelectCourse
2. MakePayment
3. EnrollStudent
4. SendNotification
5. CancelCourse
6. ManualEnrollStudent
7. ViewCourseDetails
8. ScholarshipVerification
9. ApplyDiscount

Each capability has formal inputs, outputs, preconditions, effects, constraints,
resources, cost, reliability, availability and mechanism.

## Main composition

```text
SelectCourse
      ↓
MakePayment
      ↓
EnrollStudent
      ↓
SendNotification
```

The composite is:

\[
CompleteCourseEnrollment =
SendNotification \circ EnrollStudent \circ MakePayment \circ SelectCourse.
\]

## Four problems

### Problem 1 — Regular enrollment

Tests the basic successful composition and the required compatible/incompatible
capability pattern.

### Problem 2 — Scholarship enrollment

Adds two capabilities before payment. This tests whether the representation
continues to work when the composition becomes longer.

### Problem 3 — Manual administrative enrollment

Replaces the database implementation with a GUI implementation. This tests
alternative implementations.

### Problem 4 — Alternative analysis

Focuses on the common enrollment/notification sub-composition.

The complete machine-readable dataset is in `data/experimental_dataset.json`.
