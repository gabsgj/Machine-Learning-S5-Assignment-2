# Vector Embedding Compatibility Design

![C++17](https://img.shields.io/badge/C++-17-blue.svg)
![LaTeX](https://img.shields.io/badge/LaTeX-Documentation-success.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

**Author:** Harikrishnan M  
**University Number:** TCR24CS032

## 📖 Project Overview
This repository contains the formal design specification, technical report, and implementation details for the **Capability Composition Model and Vector Space Framework**. The primary objective is to map complex operational workflows into a unified, computable vector space, enabling formal compositional reasoning and fast compatibility evaluation using dense vector operations.

## ✨ Core Features
* **Unified Vector Representation:** Encodes state preconditions, operational effects, cost, reliability, and availability in a single dense vector.
* **Rapid Compatibility Evaluation:** Utilizes fast inner-product calculations ($\langle \vec{e}_1, \vec{p}_2 \rangle$) to evaluate capability chaining.
* **Exact Composition Operators:** Preserves rigorous mathematical constraints during recursive capability compounding.
* **High-Performance Implementation:** Core evaluation metrics and recursive operational logic implemented in C++17.

## 🧮 Mathematical Formulation
Capabilities are embedded into a unified $2d+3$ dimensional vector space. This structure allocates:
* $d$ dimensions for preconditions ($\vec{p}$)
* $d$ dimensions for effects ($\vec{e}$)
* $3$ dimensions for operational attributes: cost ($c$), reliability ($r$), and availability ($a$)

For a given capability $C$, the vector is structured as:
$$\mathbf{v}_C = [\vec{p}^{\,T}, \vec{e}^{\,T}, c, r, a]^T \in \mathbb{R}^{2d+3}$$

When compounding two capabilities $C_1$ and $C_2$ ($C_{12} = C_2 \circ C_1$), the composition preserves these mathematical bounds:
* **Preconditions:** $\vec{p}_{12} = \max(\vec{p}_1, \vec{p}_2 - \vec{e}_1)$
* **Effects:** $\vec{e}_{12} = \max(\vec{e}_1, \vec{e}_2)$
* **Attributes:** $c_{12} = c_1 + c_2$, $r_{12} = r_1 \cdot r_2$, $a_{12} = \min(a_1, a_2)$

## 📂 Repository Structure
* `docs/`: Contains the LaTeX source files and build scripts for all technical documentation.
  * `formal_design.tex`: Formal mathematical definitions of the vector space and composition operators.
  * `technical_report.tex`: Experimental methodology, implementation results, architecture analysis, and limitations.
  * `build_docs.sh`: Automated shell script to clean and compile the LaTeX documents into PDFs.
* `src/` *(Planned/Ongoing)*: C++ source code for the vector space embeddings and compatibility metrics.
* `tests/` *(Planned/Ongoing)*: Unit tests for validating compositional math and inner-product filtering.

## 📊 Experimental Results
The framework underwent rigorous experimental validation, demonstrating:
1. **Compatibility Metric Evaluation:** Perfect matching (1.0 inner product) for exact operational alignment.
2. **Recursive Composition Math:** State vectors exactly matched theoretical limits during chained compounding.
3. **Implementation Semantic Affinity:** High cosine similarity (0.89) maintained across differing implementation variants (API vs. DB).
4. **Irrelevant Filtering:** Clean zero-scoring (0.00) for operationally incompatible capability chains.

## ⚙️ Prerequisites
To build the documentation and run the experimental framework natively, you will need:
* A standard **LaTeX distribution** (e.g., `texlive-full` on Linux/WSL).
* **C++17 Compiler** (e.g., `g++` or `clang++`).
* GNU `make` or `cmake` (for building the C++ binaries).

## 🚀 Build Instructions
### Building the Documentation
Navigate to the documentation folder, clean any previous build artifacts, and execute the bash build script:

```bash
cd docs
rm -f *.aux *.log *.pdf
./build_docs.sh
