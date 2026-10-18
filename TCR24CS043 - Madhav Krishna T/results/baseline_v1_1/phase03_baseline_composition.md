# Experiment 2 — Capability Composition

## Purpose
Evaluate whether the formal capability composition model produces coherent composite representations and whether the deterministic vector composition baseline remains close to the independently encoded formal composite.

## Method
For each valid chain, symbolic composition is treated as ground truth. The v1 vector composition operator is applied recursively and compared against the independently encoded formal composite using cosine similarity.

## Overall results
- Mean non-trivial vector composition consistency: **0.6880**
- Minimum non-trivial vector composition consistency: **0.5283**
- Mean formal composite goal alignment: **0.9733**
- Mean final goal alignment: **0.9744**

## purchase_success_chain

Chain: `C1 → C2 → C3 → C4 → C5 → C6 → C7`
Final composite: **AddToCartThenCheckInventoryThenReserveInventoryThenCreateOrderThenMakePaymentThenVerifyPaymentThenSendNotification**
Final reliability: **0.929160**
Final execution time: **820.0 ms**
Final vector consistency: **0.5283**
Final goal alignment: **0.9826**

### Prefix analysis
| Length | Prefix | Vector consistency | Formal goal alignment | Reliability | Time (ms) |
|---:|---|---:|---:|---:|---:|
| 1 | `C1` | 1.0000 | 0.9617 | 0.995000 | 60.0 |
| 2 | `C1 → C2` | 0.7336 | 0.9693 | 0.985050 | 150.0 |
| 3 | `C1 → C2 → C3` | 0.8115 | 0.9752 | 0.970274 | 280.0 |
| 4 | `C1 → C2 → C3 → C4` | 0.7139 | 0.9757 | 0.960572 | 380.0 |
| 5 | `C1 → C2 → C3 → C4 → C5` | 0.6563 | 0.9808 | 0.941360 | 630.0 |
| 6 | `C1 → C2 → C3 → C4 → C5 → C6` | 0.6756 | 0.9790 | 0.933829 | 740.0 |
| 7 | `C1 → C2 → C3 → C4 → C5 → C6 → C7` | 0.5283 | 0.9826 | 0.929160 | 820.0 |

### Step compatibility
| From | To | Score | PE exact | IO exact | PE vector | IO vector |
|---|---|---:|---:|---:|---:|---:|
| C1 | C2 | 0.8768 | 1.00 | 1.00 | 0.5091 | 1.0000 |
| C1__C2 | C3 | 0.9875 | 1.00 | 1.00 | 1.0000 | 1.0000 |
| C1__C2__C3 | C4 | 0.9875 | 1.00 | 1.00 | 1.0000 | 1.0000 |
| C1__C2__C3__C4 | C5 | 0.8835 | 1.00 | 0.50 | 1.0000 | 0.7701 |
| C1__C2__C3__C4__C5 | C6 | 0.9700 | 1.00 | 1.00 | 1.0000 | 1.0000 |
| C1__C2__C3__C4__C5__C6 | C7 | 0.9583 | 1.00 | 1.00 | 1.0000 | 1.0000 |

## cancel_and_release_chain

Chain: `C4 → C9 → C10`
Final composite: **CreateOrderThenCancelOrderThenReleaseInventory**
Final reliability: **0.965398**
Final execution time: **320.0 ms**
Final vector consistency: **0.6918**
Final goal alignment: **0.9662**

### Prefix analysis
| Length | Prefix | Vector consistency | Formal goal alignment | Reliability | Time (ms) |
|---:|---|---:|---:|---:|---:|
| 1 | `C4` | 1.0000 | 0.9660 | 0.990000 | 100.0 |
| 2 | `C4 → C9` | 0.6930 | 0.9767 | 0.975150 | 220.0 |
| 3 | `C4 → C9 → C10` | 0.6918 | 0.9662 | 0.965398 | 320.0 |

### Step compatibility
| From | To | Score | PE exact | IO exact | PE vector | IO vector |
|---|---|---:|---:|---:|---:|---:|
| C4 | C9 | 1.0000 | 1.00 | 1.00 | 1.0000 | 1.0000 |
| C4__C9 | C10 | 0.8919 | 1.00 | 0.50 | 1.0000 | 0.8379 |

## Interpretation guidance
Vector composition consistency is a baseline measure, not a learned-model performance claim. A decline in consistency as chain length grows would motivate a learned Compose_theta operator in the later stage of the project.
