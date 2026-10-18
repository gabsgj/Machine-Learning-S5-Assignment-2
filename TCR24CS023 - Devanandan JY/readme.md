# Autonomous Capability Embedding Engine
**Name:** Devanandan J Y | **Institution:** Government Engineering College (GEC) Thrissur  
**Course:** PCCST503 – Machine Learning | Assignment 2

##  Project Overview
This repository provides a mathematical vector embedding architecture designed for autonomous software capability composition. Unlike standard NLP embeddings (like Word2Vec) that map semantic similarities, this engine embeds deterministic functional operations into a continuous Cartesian space. 

By separating variables into distinct functional, schema, and operational subspaces, the engine allows an automated planner to mathematically verify dependency chains, detect logical contradictions, and compute the exact algebraic cost of a composed software pipeline without relying on natural language inference.

## The Masked Subspace Architecture
Standard flat vectors suffer from "null-value ambiguity"—they cannot easily distinguish between a state variable that must be `False` versus a state variable that is entirely irrelevant. 

To solve this, this engine uses a **Masked Subspace Architecture**. A capability `C` is mapped to an array formatted as:
`[ p_val | p_mask | e_val | e_mask | q_ops ]`

*   `p_val` & `e_val`: Target values for preconditions and effects (1.0 for True, -1.0 for False).
*   `p_mask` & `e_mask`: Binary masks (1.0 or 0.0) indicating whether a variable is actively required/mutated by the capability, or simply ignored.
*   `q_ops`: A 3-dimensional operational cost vector containing Latency, Monetary Cost, and Log-Reliability.

##  Mathematical Foundations

### 1. Multiplicative Reliability via Log-Space Additivity
Execution reliability probabilities multiply (e.g., `0.99 * 0.95 = 0.9405`). To keep the vector space strictly additive, we apply a negative log-likelihood transformation to the reliability coordinate:
`q_ops[2] = -ln(max(Reliability, 1e-6))`

By logarithmic identity, `-ln(A * B) = -ln(A) + -ln(B)`. Therefore, standard vector addition during capability composition exactly computes the composite failure probability.

### 2. Directed Compatibility
When checking if Capability A can transition into Capability B (`A -> B`), the engine computes an overlap mask:
`m_overlap = e_mask_A * p_mask_B`

A strict logical contradiction exists (and compatibility is blocked) if Capability A outputs a state that directly conflicts with the requirements of Capability B across the overlapping mask.

### 3. Algebraic Composition Model
When executing Capability A followed by Capability B (`B ◦ A`), the composite vector is calculated via element-wise matrix operations:
*   **Inherited Preconditions:** The composite retains A's preconditions, plus any preconditions of B that A's effects did not satisfy.
*   **Overwritten Effects:** B's effects overwrite A's effects wherever they overlap.
*   **Accumulated Operations:** Latency, cost, and log-reliability are summed perfectly.

##  Benchmark Results: Web Deployment Pipeline
The engine was evaluated using a highly parameterized Cloud DevOps and Web Deployment benchmark (Next.js, Supabase, Vercel, Render) across 5 core experiments.

*   **Experiment 1: Strict Compatibility:** The engine successfully validated the dependency chain `InitSupabase -> DeployNextjs` (Compatibility = 1.0) and accurately rejected contradictory sequences.
*   **Experiment 2: Algebraic Composition:** Composing `InitSupabase` and `DeployNextjs` yielded a unified vector that preserved the initial `GitRepoExists=True` precondition and correctly summed the latencies (450ms + 1200ms = 1650ms).
*   **Experiment 3: Decoupled Similarity:** `DeployVercel` and `DeployRender` yielded a Functional Cosine Similarity of 1.0. The engine correctly grouped them as functionally identical deployment substitutes despite differing operational costs and execution mechanisms.
*   **Experiment 4: Irrelevant Distractors:** Goal relevance was evaluated by comparing the goal vector (`AppLive=True`) against a distractor capability (`InstallSteamGame`). The dot product returned a 0.0 relevance score, instantly filtering the distractor.
*   **Experiment 5: Operational Homomorphism:** Vector additivity on the log-reliability sector yielded an exact match to the scalar probability multiplication, validating the engine's mathematical integrity.

##  Quick Start Guide

### Prerequisites
*   Python 3.10+
*   NumPy

```bash
# 1. Install required dependencies
pip install numpy

# 2. Clone the repository and navigate to the root directory
cd capability-embedding-engine

# 3. Execute the benchmark suite
python main.py
