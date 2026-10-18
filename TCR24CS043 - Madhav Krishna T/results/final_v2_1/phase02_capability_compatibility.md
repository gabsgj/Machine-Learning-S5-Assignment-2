# Experiment 1 — SCE-128 v2

- Formal accuracy: **1.0000**
- Raw cosine AUC: **0.6250**
- Blockwise cosine AUC: **0.6250**
- Structural relation AUC: **0.5250**
- v2 compatibility proxy AUC: **0.9000**

| From | To | Expected | Raw cosine | Blockwise cosine | Structural relation | |
|---|---|:---:|---:|---:|---:|---|
| C1 | C2 | True | 0.4909 | 0.6513 | -0.1440 | |
| C2 | C3 | True | 0.8689 | 0.9119 | -0.1329 | |
| C3 | C4 | True | 0.5521 | 0.7304 | -0.1114 | |
| C4 | C5 | True | 0.7693 | 0.8490 | -0.0537 | |
| C5 | C6 | True | 0.7921 | 0.8363 | -0.0369 | |
| C6 | C7 | True | 0.5133 | 0.6598 | -0.0578 | |
| C4 | C9 | True | 0.7253 | 0.8151 | -0.0572 | |
| C9 | C10 | True | 0.5744 | 0.6977 | -0.0942 | |
| C1 | C4 | False | 0.5386 | 0.6872 | -0.1210 | |
| C1 | C7 | False | 0.5012 | 0.6710 | -0.0421 | |
| C4 | C8 | False | 0.8332 | 0.8577 | -0.0788 | |
| C1 | C14 | False | 0.6639 | 0.7480 | -0.1202 | |
| C1 | C15 | False | 0.4934 | 0.6410 | -0.0706 | |
