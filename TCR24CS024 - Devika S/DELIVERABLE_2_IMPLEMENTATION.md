# Deliverable 2 — Implementation

## Language
C++17.

## Components
- `types.hpp`: formal state, goal, capability, input/output, constraints, resources and QoS structures.
- `engine.hpp`: JSON dataset parser.
- `embedding.hpp`: state/goal/capability encoders, cosine similarity, compatibility, input-output compatibility and composition.
- `experiments.hpp`: all five required experiments.
- `main.cpp`: executable.

## Required interface mapping
- `encode(state)` -> `EmbeddingEngine::encode(const State&)`
- `encode(goal)` -> `EmbeddingEngine::encode(const Goal&)`
- `encode(capability)` -> `EmbeddingEngine::encode(const Capability&)`
- `compose(capabilities)` -> recursive `EmbeddingEngine::compose(...)`
- `similarity(x,y)` -> `EmbeddingEngine::similarity(...)`

## Scope
No planner search or replanning algorithm is implemented. The supplied assignment explicitly places BFS, DFS, A*, D* Lite, LPA*, path search and replanning outside the scope of Assignment 2.
