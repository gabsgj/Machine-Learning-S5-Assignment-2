# Deliverable 2: Implementation Document

**Project**: Capability Embedding (Flight Booking System Domain)  
**Language**: C++17 (ISO/IEC 14882:2017)  
**Entry Point**: `src/main.cpp`

---

## 1. Implementation Overview
This implementation adapts the `CapabilityEmbedding` library for a Flight Booking domain. The library provides generalized structural classes (`State`, `Goal`, `Capability`) along with robust embedding logic (`Embedding.h/cpp`).

## 2. Core Architecture
- **`Types.h/cpp`**: Defines formal primitives (e.g., Ternary logic representation for precondition matching) and a builder pattern for declarative initialization.
- **`Embedding.h/cpp`**: Performs vectorization (`encodeCapability`, `encodeState`) and computes mathematical operations like `cosineSimilarity` and strict pipeline composition.
- **`main.cpp`**: Instantiates a concrete scenario simulating a `CreateBooking -> ProcessPayment -> IssueTicket` workflow, testing compatibility logic and verifying composite capability generation.

## 3. Build Instructions
The project uses CMake for robust compilation. From the project root directory:
```bash
mkdir build
cd build
cmake ..
cmake --build .
```
Executing the compiled binary (`flight_booking_embedding.exe`) will output detailed compatibility reports and the unified vector embedding signatures of the composite capabilities.
