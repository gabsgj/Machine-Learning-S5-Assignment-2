# Capability Composition Using Vector Embeddings

## Overview

This project implements a capability composition system for an online
shopping application using vector embeddings.

The main idea is to represent application states, goals, and capabilities
using fixed-length numerical vectors. These vectors can then be used to
calculate similarity between capabilities.

The project also checks whether capabilities can be connected based on their
preconditions and effects. Compatible capabilities can be composed into a
larger workflow that can be checked against a target goal.

The implementation is written in Python.

---

## Project Objectives

The project demonstrates:

- Representation of application states and goals
- Fixed-length vector representation of capabilities
- Cosine similarity between capability vectors
- Compatibility checking between capabilities
- Comparison of alternative implementations
- Identification of irrelevant capabilities
- Composition of multiple compatible capabilities
- Calculation of cost, reliability, and availability
- Verification that a composed capability achieves the required goal
- Automated testing using pytest

---

## Application Example

The example application represents a simple online shopping workflow.

The main capabilities are:

- `CreateOrder`
- `MakePayment`
- `SendNotification`
- `CancelCart`
- `SendEmailConfirmation`
- `UpdateUserProfile`

The successful purchase workflow is:

```text
CreateOrder
     |
     v
MakePayment
     |
     v
SendNotification
