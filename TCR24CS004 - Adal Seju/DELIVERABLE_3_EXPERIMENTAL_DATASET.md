# Deliverable 3: Experimental Dataset

**Domain**: Flight Booking System

---

## 1. Initial State & Goals
- **Initial State**: `User.authenticated=true`, `Flight.selected=true`, `Seats.available=true`, `Booking.created=false`.
- **Goal**: Produce `Ticket.issued=true`.

## 2. Capability Definitions

### C1: CreateBooking
- **Inputs**: `flightId`, `userId`
- **Outputs**: `bookingId`
- **Preconditions**: `Flight.selected=true`, `Seats.available=true`
- **Effects**: `Booking.created=true`
- **QoS**: Cost=10.0, Rel=0.99, Avail=0.999

### C2: ProcessPayment
- **Inputs**: `bookingId`, `paymentDetails`
- **Outputs**: `paymentReceipt`
- **Preconditions**: `Booking.created=true`
- **Effects**: `Payment.processed=true`
- **QoS**: Cost=20.0, Rel=0.98, Avail=0.995

### C3: IssueTicket
- **Inputs**: `bookingId`, `paymentReceipt`
- **Outputs**: `ticketId`
- **Preconditions**: `Payment.processed=true`
- **Effects**: `Ticket.issued=true`
- **QoS**: Cost=5.0, Rel=0.999, Avail=0.999

## 3. Composition Experiments
The implementation specifically tests standard linear compositions:
1. `CreateBooking -> ProcessPayment`: Confirms effect (`Booking.created`) satisfies subsequent preconditions, returning a unified "CreateBooking+ProcessPayment" capability.
2. `(CreateBooking+ProcessPayment) -> IssueTicket`: Confirms complete pipeline continuity, aggregating inputs (`flightId`, `userId`, `paymentDetails`) and correctly returning the final desired output (`ticketId`).
