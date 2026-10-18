# Phase 01 — Formal Dataset Validation

- Capabilities: **18** (15 logical + 3 implementation variants)
- Required relation accuracy: **1.0000**
- Duplicate capability IDs: **none**

## Composition chains
- `purchase_success_chain`: **PASS**
  - composite: `C1__C2__C3__C4__C5__C6__C7`
  - reliability: `0.929160`
  - execution time: `820.0 ms`
- `cancel_and_release_chain`: **PASS**
  - composite: `C4__C9__C10`
  - reliability: `0.965398`
  - execution time: `320.0 ms`

## Alternative implementations
- `CREATE_ORDER_IMPLEMENTATIONS`: functional contract same=`True`, mechanisms distinct=`True`

## Alternative implementation vector similarity
- `C4_API<->C4_DB`: `0.6579`
- `C4_API<->C4_GUI`: `0.6151`
- `C4_DB<->C4_GUI`: `0.7210`

## Initial-state applicability
- `C1`: `1.0000`
- `C2`: `0.5000`
- `C3`: `0.5000`
- `C4`: `0.6667`
- `C4_API`: `0.6667`
- `C4_DB`: `0.6667`
- `C4_GUI`: `0.6667`
- `C5`: `0.0000`
- `C6`: `0.0000`
- `C7`: `0.0000`
- `C8`: `0.0000`
- `C9`: `0.0000`
- `C10`: `0.0000`
- `C11`: `0.5000`
- `C12`: `0.0000`
- `C13`: `0.0000`
- `C14`: `1.0000`
- `C15`: `0.0000`
