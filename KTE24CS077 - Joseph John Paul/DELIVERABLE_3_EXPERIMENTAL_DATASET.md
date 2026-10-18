# Deliverable 3: Experimental Dataset Specification

**Domain**: University Course Registration System  
**Dataset Format**: JSON and In-Memory C++ Structures  
**File Location**: `data/course_registration_dataset.json`  

---

## 1. Dataset Overview

This document provides the complete, unambiguous specification of the dataset used in the Course Registration capability composition experiment. It covers all 11 state predicates, 5 inputs, 8 outputs, 8 resources, 5 constraints, 6 capability types, 8 mechanism channels, and 11 formal capabilities ($C_1 \dots C_{11}$).

---

## 2. Application Domain

* **Domain**: University Course Registration System
* **Context**: Academic course enrollment lifecycle encompassing student authentication, prerequisite verification, course seat availability, enrollment holding, financial payment settlement, notification delivery, and registration confirmation.

---

## 3. State Vocabulary (11 Predicates)

| Index | Predicate Symbol | Semantic Meaning |
| :---: | :--- | :--- |
| `0` | `student_authenticated` | Student identity verified via authentication service |
| `1` | `student_exists` | Student record is present in university database |
| `2` | `student_eligible` | Student meets GPA, prerequisite, and financial standing |
| `3` | `course_exists` | Course catalog entry exists for current term |
| `4` | `course_available` | Course has unreserved seat capacity |
| `5` | `registration_open` | Registration semester window is active |
| `6` | `enrollment_exists` | Student holds an active course enrollment reservation |
| `7` | `payment_completed` | Required tuition fees are processed |
| `8` | `notification_sent` | Registration notification / receipt dispatched |
| `9` | `registration_confirmed` | Final academic registration confirmed in system |
| `10` | `registration_report_generated` | Administrative audit report generated on disk |

---

## 4. Initial State ($S_0$)

$$
\phi_S(S_0) = [+1, +1, -1, +1, +1, +1, -1, -1, -1, -1, -1]
$$

| Predicate | Initial Value | Encoding |
| :--- | :---: | :---: |
| `student_authenticated` | `TRUE` | `+1.0` |
| `student_exists` | `TRUE` | `+1.0` |
| `student_eligible` | `FALSE` | `-1.0` |
| `course_exists` | `TRUE` | `+1.0` |
| `course_available` | `TRUE` | `+1.0` |
| `registration_open` | `TRUE` | `+1.0` |
| `enrollment_exists` | `FALSE` | `-1.0` |
| `payment_completed` | `FALSE` | `-1.0` |
| `notification_sent` | `FALSE` | `-1.0` |
| `registration_confirmed` | `FALSE` | `-1.0` |
| `registration_report_generated` | `FALSE` | `-1.0` |

---

## 5. Goal Definition ($G_{\text{primary}}$)

$$
\phi_G(G) = [0, 0, 0, 0, 0, 0, +1, +1, +1, +1, 0]
$$

* Targets:
  1. `enrollment_exists = TRUE` (`+1`)
  2. `payment_completed = TRUE` (`+1`)
  3. `notification_sent = TRUE` (`+1`)
  4. `registration_confirmed = TRUE` (`+1`)

---

## 6. Input Vocabulary (5 Dimensions)

| Index | Input Identifier | Description |
| :---: | :--- | :--- |
| `0` | `student_id` | Unique student identification number |
| `1` | `course_id` | Unique course offering identifier |
| `2` | `enrollment_id` | Active reservation/enrollment tracking token |
| `3` | `payment_details` | Payment instrument, card token, or account details |
| `4` | `registration_details` | Final schedule, course metadata, and recipient details |

---

## 7. Output Vocabulary (8 Dimensions)

| Index | Output Identifier | Description |
| :---: | :--- | :--- |
| `0` | `eligibility_status` | Boolean eligibility clearance token |
| `1` | `availability_status` | Seat availability report |
| `2` | `enrollment_id` | Generated enrollment tracking ID |
| `3` | `payment_receipt` | Financial payment confirmation receipt |
| `4` | `notification_id` | Outgoing message delivery identifier |
| `5` | `confirmation_id` | Final official registration confirmation code |
| `6` | `drop_confirmation` | Enrollment cancellation receipt |
| `7` | `registration_report` | Formatted audit report document |

---

## 8. Resource Vocabulary (8 Dimensions)

`0: StudentDatabase`, `1: CourseDatabase`, `2: RegistrationDatabase`, `3: AuthenticationService`, `4: PaymentGateway`, `5: Network`, `6: NotificationService`, `7: FileSystem`.

---

## 9. Constraint Vocabulary (5 Dimensions)

`0: authentication_required`, `1: registration_period_required`, `2: positive_payment`, `3: valid_student`, `4: valid_course`.

---

## 10. Capability Type Vocabulary (6 Dimensions)

`0: API`, `1: DATABASE`, `2: FUNCTION`, `3: SERVICE`, `4: COMPUTATION`, `5: GUI`.

---

## 11. Mechanism Vocabulary (8 Dimensions)

`0: MECH_LOCAL_FUNCTION` (In-memory programmatic execution)  
`1: MECH_SQL_DATABASE_QUERY` (Direct database query engine)  
`2: MECH_REST_POST_REGISTRATION` (`POST /registration`)  
`3: MECH_REST_POST_PAYMENT` (`POST /payment`)  
`4: MECH_REST_GET_AVAILABILITY` (`GET /courses/{id}/availability`)  
`5: MECH_NOTIFICATION_SERVICE` (Message broker protocol)  
`6: MECH_REST_DELETE_REGISTRATION` (`DELETE /registration`)  
`7: MECH_REPORT_GENERATOR` (File system report engine)  

---

## 12. Primary Capability Dataset ($C_1 \dots C_8$)

| ID | Name | Type | Inputs | Outputs | Preconditions | Effects | Cost | Rel. | Avail. | Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **C1** | `CheckEligibility` | FUNCTION | `student_id` | `eligibility_status` | `student_exists=1, student_auth=1` | `student_eligible=1` | 5.0 | 0.990 | 1.0 | Local Function |
| **C2** | `CheckCourseAvailability` | DATABASE | `course_id` | `availability_status` | `course_exists=1, reg_open=1` | `course_available=1` | 3.0 | 0.995 | 1.0 | Database Query |
| **C3** | `RegisterCourse` | API | `student_id, course_id` | `enrollment_id` | `student_auth=1, student_eligible=1, course_avail=1, reg_open=1` | `enrollment_exists=1` | 10.0 | 0.990 | 1.0 | `POST /registration` |
| **C4** | `MakePayment` | API | `enrollment_id, payment_details` | `payment_receipt` | `enrollment_exists=1` | `payment_completed=1` | 15.0 | 0.980 | 1.0 | `POST /payment` |
| **C5** | `SendNotification` | SERVICE | `student_id, reg_details` | `notification_id` | `enrollment_exists=1, payment_completed=1` | `notification_sent=1` | 4.0 | 0.970 | 1.0 | NotificationService |
| **C6** | `ConfirmRegistration` | FUNCTION | `enrollment_id` | `confirmation_id` | `enrollment_exists=1, payment_completed=1` | `registration_confirmed=1` | 2.0 | 0.995 | 1.0 | Local Function |
| **C7** | `DropCourse` | API | `enrollment_id` | `drop_confirmation` | `enrollment_exists=1, payment_completed=-1` | `enrollment_exists=-1` | 8.0 | 0.990 | 1.0 | `DELETE /registration` |
| **C8** | `GenerateRegistrationReport` | COMPUTATION | `enrollment_id` | `registration_report` | `enrollment_exists=1` | `registration_report_generated=1` | 20.0 | 0.950 | 1.0 | ReportGenerator |

---

## 13. Alternative Implementations ($C_9, C_{10}, C_{11}$)

All three alternatives share the exact functional specification of $C_2$ ($P, E, I, O$), but vary in implementation architecture:

| ID | Name | Type | Mechanism | Resources | $\phi_F$ Sim vs $C_2$ | $\phi_C$ Sim vs $C_2$ |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **C9** | `CheckCourseAvailability_API` | API | `GET /courses/{id}/availability` | `CourseDatabase, Network` | 1.0000 | 0.8870 |
| **C10** | `CheckCourseAvailability_DATABASE` | DATABASE | `SELECT availability FROM courses` | `CourseDatabase` | 1.0000 | 1.0000 |
| **C11** | `CheckCourseAvailability_FUNCTION` | FUNCTION | `localAvailabilityFunction` | `CourseDatabase` | 1.0000 | 0.8335 |

---

## 14. Valid Composition Cases

* **Primary Registration Pipeline**:
  $$C_1 \to C_2 \to C_3 \to C_4 \to C_5 \to C_6$$
  Valid in initial state $S_0$, transforming $S_0 \to S_{\text{final}}$ such that $S_{\text{final}} \models G_{\text{primary}}$.
* **Data-Coupled Pair**:
  $$C_3 \to C_4$$
  $C_3$ produces `enrollment_id` and sets `enrollment_exists = TRUE`, satisfying $C_4$'s data input and operational precondition.

---

## 15. Invalid Composition Cases

* **Negative Precondition Conflict**:
  $$C_4 \to C_7$$
  $C_4$ produces `payment_completed = TRUE`. $C_7$ requires `payment_completed = FALSE`. Hence, $C_7$ is inexecutable in any state produced after $C_4$.

---

## 16. Irrelevant Capabilities

* **$C_8$ (`GenerateRegistrationReport`)**:
  * Effect: `registration_report_generated = TRUE`.
  * Target Goal: Does not include `registration_report_generated`.
  * Direct Goal Relevance: $0.0000$.
  * State Applicability: Executable after $C_3$, demonstrating that applicability does not equal goal relevance.

---

## 17. Operational Attributes

| Capability | Cost ($) | Normalized Cost ($Cost/20$) | Reliability | Availability |
| :--- | :---: | :---: | :---: | :---: |
| $C_1$ | 5.0 | 0.2500 | 0.990 | 1.000 |
| $C_2$ | 3.0 | 0.1500 | 0.995 | 1.000 |
| $C_3$ | 10.0 | 0.5000 | 0.990 | 1.000 |
| $C_4$ | 15.0 | 0.7500 | 0.980 | 1.000 |
| $C_5$ | 4.0 | 0.2000 | 0.970 | 1.000 |
| $C_6$ | 2.0 | 0.1000 | 0.995 | 1.000 |
| $C_7$ | 8.0 | 0.4000 | 0.990 | 1.000 |
| $C_8$ | 20.0 | 1.0000 | 0.950 | 1.000 |
| **Composite ($C_{\text{registration}}$)** | **39.0** | **N/A (Cumulative)** | **0.9224** | **1.000** |

---

## 18. Dataset Reproducibility

The dataset is serialized in `data/course_registration_dataset.json` and programmatically instantiated in `main.cpp` via `createCapabilities()`. It requires no external network calls or database fixtures.
