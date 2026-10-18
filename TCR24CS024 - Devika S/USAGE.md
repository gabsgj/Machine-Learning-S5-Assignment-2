# Usage

## Build
```bash
make clean && make
```

## Run the complete evaluation
```bash
./assignment2_embedding ecommerce_capability_dataset.json
```

The program prints:
- state and capability dimensions
- Experiment 1 compatibility scores
- Experiment 2 composition properties and component similarities
- Experiment 3 alternative implementation similarities
- Experiment 4 goal relevance
- Experiment 5 operational attributes

## Main source files
- `include/types.hpp` — formal state, goal, capability, input/output, QoS types
- `include/engine.hpp` — JSON loading
- `include/embedding.hpp` — embedding, similarity, compatibility and composition
- `include/experiments.hpp` — required experiments
- `src/main.cpp` — executable entry point
