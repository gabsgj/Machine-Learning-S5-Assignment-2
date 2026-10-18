# ML Assignment 2: Vector Embedding for Capability Composition

This repository contains a simple Python implementation of vector embeddings for capability composition, designed for Assignment 2 of the PCCST503 course.

## Overview
The goal of this assignment is to represent formal entities (states, goals, capabilities) as numerical vectors in a continuous space, preserving their functional relationships. This implementation uses a simple Bag-of-Words (BoW) style feature vectorization to map precondition and effect strings into a multidimensional vector space. 

## Requirements
- Python 3.x
- NumPy (`pip install numpy`)

## Usage
Run the main script to see the experiments executing:
```bash
python3 assignment2.py
```

## Structure
- `assignment2.py`: Contains the definition for `State`, `Goal`, and `Capability`, along with the `encode`, `compose`, and `similarity` functions. It also runs the 5 required experiments.
- `SYSTEM_DESIGN.md`: Explains the mathematical formulations, architecture, and design decisions behind this implementation.
