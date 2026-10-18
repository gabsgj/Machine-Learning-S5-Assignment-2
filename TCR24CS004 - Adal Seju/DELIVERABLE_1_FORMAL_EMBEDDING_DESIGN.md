# Deliverable 1: Formal Embedding Design for Capability Composition

**Domain**: Flight Booking System  
**Target Application**: Capability Vector Embedding and Composition

---

## 1. Introduction
This document defines a generalized, deterministic vector embedding designed to capture functional semantics and non-functional QoS characteristics of software capabilities in a **Flight Booking System**. It leverages the generalized framework provided in the `CapabilityEmbedding` reference library.

## 2. Problem Definition
To automatically chain software services (like selecting flights, booking, and payment), we must embed capabilities into a numerical vector space that mathematically guarantees logical entailment (effects satisfying preconditions) rather than just semantic proximity.

## 3. Formal Application Model
The domain is formally defined as $A = (S, C, S_I, G, R, K)$:
* $S$: State space (e.g., `User.authenticated`, `Seats.available`, `Ticket.issued`).
* $C$: Capabilities (e.g., `CreateBooking`, `ProcessPayment`, `IssueTicket`).
* $S_I$: The initial state before a transaction begins.
* $G$: The goal specification (e.g., `Ticket.issued = true`).

## 4. Capability Representation
We encode each capability as a multi-dimensional array encapsulating:
1. **Type & Mechanism**: Categorical structure (API, SERVICE, etc.) and specific implementation.
2. **Inputs & Outputs**: Dynamic dictionaries matching data flow requirements (e.g., `flightId`, `paymentDetails`).
3. **Preconditions & Effects**: Ternary logic encoding ($\{-1, 0, 1\}$) mapped dynamically to state variables, resolving necessary prerequisites and resulting mutations.
4. **Resources & Constraints**: Required underlying architecture and execution boundaries.
5. **Quality of Service (QoS)**: Real-valued features (Cost, Reliability, Availability) representing operational envelopes.

## 5. Generalized Embedding Logic
Unlike rigid schemas, this embedding framework assigns indices dynamically to discovered state keys and variables, producing standard mathematical vectors upon which structural compatibility and similarity (Cosine Similarity) algorithms operate flawlessly.
