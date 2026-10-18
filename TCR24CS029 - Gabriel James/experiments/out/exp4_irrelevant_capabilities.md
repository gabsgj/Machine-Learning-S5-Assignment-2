# Experiment 4: irrelevant capabilities

Distractor pool: 77 capabilities (53 corpus plus 24 unrelated decoys, three of them sharing a token with a requirement on purpose).

| requirement | rank of intended | P@1 | P@3 | P@5 | R@5 | MRR | AUC | best decoy | best decoy score | intended margin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| register_pat | 1 | 1.0000 | 0.3333 | 0.2000 | 1.0000 | 1.0000 | 1.0000 | DEC-RegisterEmployee (rank 10) | 0.4558 | 0.0000 |
| register_patient | 1 | 1.0000 | 0.6667 | 0.4000 | 1.0000 | 1.0000 | 1.0000 | DEC-RegisterEmployee (rank 13) | 0.4431 | 0.0363 |
| place_order | 1 | 1.0000 | 0.3333 | 0.2000 | 1.0000 | 1.0000 | 1.0000 | DEC-MatchVendorInvoice (rank 7) | 0.4032 | 0.0000 |
| summarize_document | 1 | 1.0000 | 0.3333 | 0.2000 | 1.0000 | 1.0000 | 1.0000 | DEC-FileExpense (rank 10) | 0.3298 | 0.0000 |
| export_audit_report | 1 | 1.0000 | 0.3333 | 0.2000 | 1.0000 | 1.0000 | 1.0000 | DEC-RunPayroll (rank 3) | 0.4962 | 0.0000 |

Weakest intended answer 0.8346; strongest decoy 0.4962 (DEC-RunPayroll).
