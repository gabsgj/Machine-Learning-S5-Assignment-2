# USAGE GUIDE: Vector Embedding for Capability Composition

**Project**: University Course Registration Vector Embedding  
**Language**: C++17  

---

## 1. Prerequisites

To build and run this project, you need:
* A C++17 compliant compiler:
  * **Windows**: MinGW-w64 GCC (g++ 8.0+), MSVC (Visual Studio 2017+), or Clang
  * **Linux**: GCC (`g++` 8.0+) or Clang (`clang++` 7.0+)
  * **macOS**: Apple Clang or Homebrew GCC
* Terminal / Command Prompt / PowerShell.
* Standard C++ runtime library (no external packages or network access needed).

---

## 2. Project Setup

Verify the workspace structure:
```
UNIVERSITY_COURSE_REGISTRATION_EMBEDDING/
│
├── main.cpp                              # Source code
├── README.md                             # Project overview
├── USAGE.md                              # This usage guide
├── data/
│   └── course_registration_dataset.json  # Serialized dataset
│
├── DELIVERABLE_1_FORMAL_EMBEDDING_DESIGN.md
├── DELIVERABLE_2_IMPLEMENTATION.md
├── DELIVERABLE_3_EXPERIMENTAL_DATASET.md
└── DELIVERABLE_4_TECHNICAL_REPORT.md
```

---

## 3. Compilation

### Windows (MinGW-w64 GCC)
```powershell
g++ -std=c++17 main.cpp -o embedding.exe
```

### Windows (Microsoft Visual C++ / MSVC)
```cmd
cl /std:c++17 /EHsc main.cpp /Fe:embedding.exe
```

### Linux / macOS (GCC or Clang)
```bash
g++ -std=c++17 main.cpp -o embedding
# OR
clang++ -std=c++17 main.cpp -o embedding
```

---

## 4. Running the Program

### Windows
```powershell
.\embedding.exe
```

### Linux / macOS
```bash
./embedding
```

---

## 5. Understanding the Output

The executable displays console output organized into distinct sections:

1. **Header & Dimension Overview**: Confirms the 11D state, 11D goal, 35D functional, and 65D capability embedding dimensions.
2. **Representative Capability Embedding**: Displays an explicit vector breakdown for `C3 RegisterCourse`.
3. **Integrity Checks (16 Unit Assertions)**: Confirms that all core specification rules pass.
4. **Experiments 1 to 5**: Displays tabular and diagnostic logs for compatibility, composition, alternatives, irrelevance, and QoS attributes.
5. **Final Summary**: Provides an executive conclusion of the experimental run.

---

## 6. Running Experiments

All experiments run automatically upon executing the program:
* **Experiment 1**: Analyzes pairwise compatibility and negative precondition conflicts.
* **Experiment 2**: Executes the sequential pipeline $C_1 \to C_2 \to C_3 \to C_4 \to C_5 \to C_6$ and verifies goal satisfaction.
* **Experiment 3**: Analyzes alternative implementations ($C_9, C_{10}, C_{11}$) for functional and structural similarity.
* **Experiment 4**: Evaluates $C_8$ to demonstrate the orthogonality of goal relevance vs. applicability.
* **Experiment 5**: Compares operational QoS parameters.

---

## 7. Interpreting Similarity

* **Functional Similarity ($\phi_F \in \mathbb{R}^{35}$)**: Evaluates whether two capabilities have identical preconditions, effects, inputs, and outputs. A score of $1.0000$ indicates perfect functional interchangeability.
* **Full Cosine Similarity ($\phi_C \in \mathbb{R}^{65}$)**: Measures overall similarity including invocation mechanism, host type, and resources. A score $< 1.0000$ indicates architectural differences despite functional equivalence.
* **Block-Level Similarity**: Averages the cosine similarities across all 9 individual feature blocks to prevent larger blocks from dominating the score.

---

## 8. Interpreting Compatibility

* **Effect-Precondition Compatibility**: Measures the percentage of a downstream capability's preconditions directly produced by the upstream capability.
  * Note: Direct compatibility can be $0.0$ even for valid sequential compositions if intermediate preconditions were already established earlier in the state history.
* **Input-Output Compatibility ($IOComp$)**: Measures whether required data inputs are provided by preceding outputs (e.g., $C_3 \to C_4$ produces and consumes `enrollment_id`, yielding $1.0000$).

---

## 9. Interpreting Composition

* **State-Aware Composition**: The system checks:
  1. $Applicable(C_1, S)$
  2. $S' = Apply(S, E_1)$
  3. $Applicable(C_2, S')$
* If all 3 steps hold, $C_1 \to C_2$ is **VALID** in state $S$.
* If $C_1$ produces an effect that contradicts $C_2$'s negative preconditions (e.g., $C_4 \to C_7$ where $C_4$ sets `payment_completed = TRUE` while $C_7$ requires `payment_completed = FALSE`), composition is **INVALID**.

---

## 10. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `g++ is not recognized` | Compiler is not in system `PATH` | Add MinGW `bin` directory to environment variables. |
| `undefined reference to std::...` | Old compiler version | Ensure `-std=c++17` flag is present during compilation. |
| Assertion failure | Source code modified | Check line number in assertion output and revert unexpected dataset edits. |
