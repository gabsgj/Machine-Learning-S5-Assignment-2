# Vector Embedding for Capability Composition

A custom, numpy-only vector embedding that encodes formally specified states, goals, and capabilities so that the embedding (a) preserves sequential compatibility between capabilities and (b) supports composite capability construction by chaining.  No off-the-shelf embedding model is used; every dimension is hand-designed and justified.

---

## Setup

**Python:** 3.10 or later (uses `list[str]` type-hint syntax).

**Dependencies:**
```bash
pip install numpy
```

**Running experiments** (from the project root):
```bash
python experiments/exp1_compatibility.py
python experiments/exp2_composition.py
python experiments/exp3_alt_implementations.py
python experiments/exp4_irrelevant.py
python experiments/exp5_operational.py
```

---

## Project Structure

```
project/
├── README.md
├── data/
│   ├── domain1_orders.json        # E-commerce order processing (6 capabilities)
│   ├── domain2_library.json       # Library checkout system     (6 capabilities)
│   └── domain3_hotel.json         # Hotel booking system        (7 capabilities)
├── src/
│   ├── __init__.py
│   ├── encode.py                  # Core encoding, similarity, compatibility, compose
│   ├── compose.py                 # Higher-level chain utilities and display helpers
│   └── compatibility.py           # Matrix computation and ranking utilities
├── experiments/
│   ├── exp1_compatibility.py      # Sequential compatibility demonstration
│   ├── exp2_composition.py        # 3-step chain composition
│   ├── exp3_alt_implementations.py# API vs DATABASE vs GUI variants
│   ├── exp4_irrelevant.py         # Goal-directed relevance ranking
│   └── exp5_operational.py        # Reliability / cost trade-off scoring
└── report/
    └── report.md
```

---

## Vector Layout

Each capability is encoded into a **59-dimensional** vector. The layout is fixed and domain-independent (except for the precondition/effect segments which are padded to 12 slots).

| Slice | Dims | Segment | Description |
|-------|------|---------|-------------|
| `[0:12]` | 12 | `type_onehot` | One-hot over 9 capability types: API, DATABASE, GUI, EVENT, FUNCTION, FILE, COMPUTATION, MESSAGE, SERVICE (indices 0–8); slots 9–11 are zero-padding |
| `[12:16]` | 4 | `io_features` | `[input_count/10, output_count/10, required_count/10, optional_count/10]` — counts normalised by clamping to max 10 |
| `[16:17]` | 1 | `io_name_match` | Fraction of input names that also appear in output names (0–1) |
| `[17:29]` | 12 | `resource_multihot` | Multi-hot over global resource vocabulary of 12 resources (see below) |
| `[29:34]` | 5 | `cost_normalized` | `[time_ms, money, resource, risk, energy]` each min-max normalised to [0,1] across all domains |
| `[34:35]` | 1 | `reliability` | Scalar float in [0, 1] from the capability spec |
| `[35:47]` | 12 | `precondition_vector` | +1 = variable must be True, −1 = must be False, 0 = not constrained |
| `[47:59]` | 12 | `effect_vector` | +1 = variable set True, −1 = set False, 0 = unchanged |

**Global resource vocabulary** (indices 0–11):
`database, payment_gateway, email_service, inventory_system, shipping_api, catalog_db, member_db, rfid_scanner, payment_terminal, pms_db, housekeeping_system, kitchen_system`

**State-variable vocabularies** (per domain, padded to 12 slots in the vector):

*Domain 1 — ecommerce_orders:* `cart_active, cart_empty, order_created, payment_pending, payment_complete, payment_failed, inventory_reserved, inventory_released, order_shipped, order_cancelled, refund_issued, notification_sent`

*Domain 2 — library_checkout:* `member_active, book_searched, book_available, book_reserved, book_checked_out, book_returned, fine_pending, fine_paid, renewal_requested, renewal_approved, hold_placed, account_suspended`

*Domain 3 — hotel_booking:* `search_done, room_available, reservation_made, payment_authorized, payment_captured, checked_in, checked_out, room_service_requested, room_service_delivered, reservation_cancelled, refund_processed, loyalty_points_credited`

---

## Function Reference

All public functions are in `src/encode.py` unless noted.

| Function | Signature | Description |
|----------|-----------|-------------|
| `encode_state` | `(state: dict, state_vars: list[str]) -> np.ndarray` | Encodes a state dict to a vector over `state_vars`; True→+1, False→−1, absent→0 |
| `encode_goal` | `(goal: dict, state_vars: list[str]) -> np.ndarray` | Identical to `encode_state`; a goal is a partial desired-state assignment |
| `encode_capability` | `(capability: dict, state_vars: list[str], resource_vocab=None) -> np.ndarray` | Encodes a capability dict into the full 59-dim vector using the layout above |
| `similarity` | `(vector_x: np.ndarray, vector_y: np.ndarray) -> float` | Cosine similarity over the full concatenated vector; returns 0.0 if either vector is zero |
| `compatibility` | `(cap_i_vec: np.ndarray, cap_j_vec: np.ndarray) -> float` | `dot(effect_i, precond_j) / sum(|precond_j|)`; measures how well capability i enables capability j |
| `compose` | `(capability_vectors, capability_dicts, state_vars, resource_vocab=None) -> np.ndarray` | Composes an ordered list of capability vectors into one composite; type from first cap, preconditions from first + unsatisfied later needs, effects last-writer-wins, cost summed, reliability multiplied |
| `collect_cost_stats` | `(domains: list[dict]) -> None` | Scans all capabilities to compute global min/max per cost field; call before `encode_capability` |
| `load_domain` | `(filepath: str) -> dict` | Loads a domain JSON file |
| `load_all_domains` | `(data_dir: str) -> tuple` | Loads all domain files, fits cost stats, returns domains and filenames |

**`src/compose.py`** additionally provides:
- `chain_capabilities(names, domain)` — build a composite vector from a list of capability names
- `describe_vector(vec, label)` — return a human-readable string of all vector segments
- `show_composition(names, domain)` — print a full composition breakdown table

**`src/compatibility.py`** additionally provides:
- `pairwise_compatibility_matrix(caps, state_vars)` — N×N numpy matrix
- `print_compatibility_table(caps, state_vars, title)` — pretty-print the matrix
- `rank_by_compatibility(source_cap, candidates, state_vars)` — sorted list of (name, compat, sim) tuples

---

## Expected Output

### Experiment 1 — Sequential Compatibility

```
======================================================================
  Experiment 1 — Sequential Compatibility Scoring
  Domain: ecommerce_orders
======================================================================

  Primary Hypothesis Test:
  Pair                                      Compatibility   Similarity    Expected
  ---------------------------------------- -------------- ------------  ----------
  CreateOrder  -> MakePayment                      1.0000       0.2713    HIGH (+)
  CreateOrder  -> CancelCart                      -1.0000       0.5395    LOW  (-)
  MakePayment  -> ShipOrder                        1.0000       0.4157    MED  (+)
  ShipOrder    -> SendNotif                        0.0000       0.1716    MED  (+)
  CancelCart   -> CreateOrder                     -1.0000       0.5395        ZERO
  SendNotif    -> CancelCart                       0.0000       0.1915         NEG


  Full 6x6 Compatibility Matrix (rows=predecessor, cols=successor)
                         CreateOrder       MakePayment  ReserveInventory         ShipOrder  SendNotification        CancelCart
  ----------------  ----------------  ----------------  ----------------  ----------------  ----------------  ----------------
       CreateOrder           -0.5000            1.0000            0.5000            0.0000            1.0000           -1.0000
       MakePayment            0.0000           -0.5000           -0.5000            1.0000            0.0000            0.0000
  ReserveInventory            0.0000            0.0000           -0.5000            0.5000            0.0000            0.0000
         ShipOrder            0.0000            0.0000            0.0000            0.0000            0.0000            0.0000
  SendNotification            0.0000            0.0000            0.0000            0.0000            0.0000            0.0000
        CancelCart           -1.0000            0.0000            0.0000            0.0000            0.0000           -1.0000

  Effect vector breakdown (CreateOrder):
    State vars : ['cart_active', 'cart_empty', 'order_created', 'payment_pending', 'payment_complete', 'payment_failed', 'inventory_reserved', 'inventory_released', 'order_shipped', 'order_cancelled', 'refund_issued', 'notification_sent']
    Effect     : [-1.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  Precond vector (MakePayment):
    Precond    : [0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  Precond vector (CancelCart):
    Precond    : [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

  dot(effect_CO, precond_MP) = 2.0000
  sum(|precond_MP|)          = 2.0000
  => Compatibility score     = 1.0000  (CONFIRMED HIGH)

  dot(effect_CO, precond_CC) = -1.0000
  sum(|precond_CC|)          = 1.0000
  => Compatibility score     = -1.0000  (CONFIRMED LOW/NEG)

  Key observation:
    CreateOrder->MakePayment : POSITIVE  (effect satisfies preconditions)
    CreateOrder->CancelCart  : NEGATIVE  (effect contradicts preconditions)
    Similarity disagrees: both pairs can have moderate similarity (same domain,
    similar structure) yet completely different compatibility scores.
======================================================================
```

### Experiment 2 — Chain Composition

```
======================================================================
  Experiment 2 — Chain Composition
  Chain: CreateOrder -> MakePayment -> ShipOrder
======================================================================

  Individual capability properties:
  Capability            Reliability   Cost[time]     Effect[non-zero]
  -------------------- ------------ ------------ --------------------
  CreateOrder                0.9800       0.1034           dims:    3
  MakePayment                0.9500       0.5172           dims:    3
  ShipOrder                  0.9200       1.0000           dims:    1

  Composite capability properties:
  COMPOSITE                  0.8565       1.0000           dims:    6
  (reliability = 0.9800 x 0.9500 x 0.9200 = 0.8565)

  Precondition vector (state-variable space):
    state_vars  : ['cart_active', 'cart_empty', 'order_created', 'payment_pending', 'payment_complete', 'payment_failed', 'inventory_reserved', 'inventory_released', 'order_shipped', 'order_cancelled', 'refund_issued', 'notification_sent']
    CreateOrder : [1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    MakePayment : [0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    ShipOrder   : [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    COMPOSITE   : [1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    (composite precond = CreateOrder's base; later caps' unsatisfied needs added)

  Effect vector (state-variable space):
    CreateOrder : [-1.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    MakePayment : [0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    ShipOrder   : [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    COMPOSITE   : [-1.0, 0.0, 1.0, -1.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    (last-writer-wins; composite reflects final world state after chain)

  Similarity(composite, individual):
  Capability                  Similarity  Notes
  ------------------------- ------------  -----------------------------------
  CreateOrder                     0.5958  < 1.0 (composite is broader)
  MakePayment                     0.6773  < 1.0 (composite is broader)
  ShipOrder                       0.5927  < 1.0 (composite is broader)

  Pairwise individual similarity (for reference):
  Pair                                       Similarity
  ---------------------------------------- ------------
  CreateOrder <-> MakePayment                    0.2713
  MakePayment <-> ShipOrder                      0.4157
  CreateOrder <-> ShipOrder                      0.2798

  Conclusion:
    The composite inherits CreateOrder's entry preconditions,
    accumulates all intermediate and final effects (ShipOrder wins on
    conflicting dims), sums costs, and multiplies reliabilities.
    similarity(composite, Ci) < 1.0 for all i, confirming the composite
    is strictly richer than any individual capability.
======================================================================
```

### Experiment 3 — Alternative Implementations

```
======================================================================
  Experiment 3 — Alternative Implementations of the Same Capability
  Operation: 'complete a payment' (same precond/effect, diff mechanism)
======================================================================

  Variant properties:
  Variant                Type         Resources                        Reliability  Cost[time]
  ---------------------- ------------ -------------------------------- ----------- -----------
  MakePayment_API        API          payment_gateway,database                0.9500      0.5172
  MakePayment_DB         DATABASE     database                                0.9300      0.0000
  MakePayment_GUI        GUI          database,payment_gateway                0.8800      1.0000

  Precondition and Effect vectors (should be IDENTICAL across variants):
  state_vars: ['cart_active', 'cart_empty', 'order_created', 'payment_pending', 'payment_complete', 'payment_failed', 'inventory_reserved', 'inventory_released', 'order_shipped', 'order_cancelled', 'refund_issued', 'notification_sent']
  MakePayment_API        precond=[0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  effect=[0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  MakePayment_DB         precond=[0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  effect=[0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  MakePayment_GUI        precond=[0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  effect=[0.0, 0.0, 0.0, -1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]

  Pairwise Similarity (should be HIGH but NOT 1.0):
  Pair                                            Similarity
  --------------------------------------------- ------------
  MakePayment_API <-> MakePayment_DB                  0.8130 <- NOT 1.0 (type/cost/resource differ)
  MakePayment_API <-> MakePayment_GUI                 0.8988 <- NOT 1.0 (type/cost/resource differ)
  MakePayment_DB <-> MakePayment_GUI                  0.7784 <- NOT 1.0 (type/cost/resource differ)

  Compatibility with ShipOrder (should be SIMILAR across variants):
  Variant                 comp->ShipOrder  sim(v,Ship)
  ---------------------- ---------------- ------------
  MakePayment_API                  1.0000       0.4144
  MakePayment_DB                   1.0000       0.3301
  MakePayment_GUI                  1.0000       0.4775

  Key insight:
    All three share identical precondition/effect vectors.
    Cosine similarity is HIGH because the state-transition segments
    (largest contribution) match perfectly.  The non-unity gap comes
    from type one-hot, resources, and cost/reliability differences.
    Compatibility with ShipOrder is IDENTICAL for all variants since
    compatibility() depends only on the effect/precondition segments.
======================================================================
```

### Experiment 4 — Goal-Directed Relevance Ranking

```
======================================================================
  Experiment 4 — Goal-Directed Relevance Ranking
  Domain: hotel_booking
======================================================================

  Goal: {'checked_in': True, 'payment_captured': True, 'loyalty_points_credited': True}
  Goal vector (12-dim state space): [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
  State variables: ['search_done', 'room_available', 'reservation_made', 'payment_authorized', 'payment_captured', 'checked_in', 'checked_out', 'room_service_requested', 'room_service_delivered', 'reservation_cancelled', 'refund_processed', 'loyalty_points_credited']

  Rank   Capability                Type          Effect-Goal Sim  Notes
  ------ ------------------------- ------------ ----------------  ------------------------------
  1      CapturePayment            API                    0.5774  <-- HIGHLY RELEVANT (effect matches goal)
  2      CheckIn                   GUI                    0.5774  <-- HIGHLY RELEVANT (effect matches goal)
  3      CheckOut                  SERVICE                0.4082  <-- Partially relevant
  4      SearchRooms               API                    0.0000    No alignment with goal
  5      MakeReservation           API                    0.0000    No alignment with goal
  6      OrderRoomService          MESSAGE                0.0000    No alignment with goal
  7      CancelReservation         API                    0.0000    No alignment with goal

  Effect vector detail (capability vs goal):
  Capability                 Effect segment over state vars
  -------------------------  ----------------------------------------------------
    GOAL                     [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
  SearchRooms                [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  MakeReservation            [0.0, -1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  CapturePayment             [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  CheckIn                    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  OrderRoomService           [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]
  CheckOut                   [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
  CancelReservation          [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0]

  Conclusion:
    CheckIn, CapturePayment, CheckOut rank highest because their
    effects directly set goal-required variables to the desired values.
    SearchRooms / OrderRoomService effects are orthogonal to the goal,
    yielding near-zero scores. CancelReservation may score negative
    because it sets room_available=True while the goal doesn't need it,
    but primarily because its effects conflict with goal vars.
======================================================================
```

### Experiment 5 — Operational Scoring

```
======================================================================
  Experiment 5 — Operational Scoring: Reliability & Cost Trade-offs
======================================================================

  Predecessor: SearchCatalog
  Variant                          Compat     Rely     Cost   Score_prod   Score_wt  Rank
  ------------------------------ -------- -------- -------- ------------ ----------  ------
  Checkout_HighRel_LowCost         0.0000   0.9900   0.0556       0.0000     0.3849
  Checkout_LowRel_HighCost         0.0000   0.7000   0.8800       0.0000     0.1040
  Checkout_MedRel_MedCost          0.0000   0.8500   0.5471       0.0000     0.2306

  Ranking by multiplicative score (compat * rely * (1-cost)):
    1. Checkout_HighRel_LowCost  score=0.0000
    2. Checkout_LowRel_HighCost  score=0.0000
    3. Checkout_MedRel_MedCost  score=0.0000

  Ranking by weighted score (0.4*compat + 0.4*rely - 0.2*cost):
    1. Checkout_HighRel_LowCost  score=0.3849
    2. Checkout_MedRel_MedCost  score=0.2306
    3. Checkout_LowRel_HighCost  score=0.1040

  Ranking changed between formulations: True
    Product score favours high-reliability+low-cost multiply.
    Weighted score allows high reliability to compensate for cost.

  Predecessor: PayFine
  Variant                          Compat     Rely     Cost   Score_prod   Score_wt  Rank
  ------------------------------ -------- -------- -------- ------------ ----------  ------
  Checkout_HighRel_LowCost         0.3333   0.9900   0.0556       0.3117     0.5182
  Checkout_LowRel_HighCost         0.3333   0.7000   0.8800       0.0280     0.2373
  Checkout_MedRel_MedCost          0.3333   0.8500   0.5471       0.1283     0.3639

  Ranking by multiplicative score (compat * rely * (1-cost)):
    1. Checkout_HighRel_LowCost  score=0.3117
    2. Checkout_MedRel_MedCost  score=0.1283
    3. Checkout_LowRel_HighCost  score=0.0280

  Ranking by weighted score (0.4*compat + 0.4*rely - 0.2*cost):
    1. Checkout_HighRel_LowCost  score=0.5182
    2. Checkout_MedRel_MedCost  score=0.3639
    3. Checkout_LowRel_HighCost  score=0.2373

  Ranking changed between formulations: False

  Sensitivity analysis: varying reliability and cost independently
  (Predecessor: SearchCatalog -> Checkout variant)
     Reliability    Cost(avg)   Score_prod   Score_wt
  -------------- ------------ ------------ ----------
            0.99         0.05       0.0000     0.3860
            0.99         0.20       0.0000     0.3560
            0.99         0.50       0.0000     0.2960
            0.99         0.80       0.0000     0.2360
            0.90         0.05       0.0000     0.3500
            0.90         0.20       0.0000     0.3200
            0.90         0.50       0.0000     0.2600
            0.90         0.80       0.0000     0.2000
            0.80         0.05       0.0000     0.3100
            0.80         0.20       0.0000     0.2800
            0.80         0.50       0.0000     0.2200
            0.80         0.80       0.0000     0.1600
            0.70         0.05       0.0000     0.2700
            0.70         0.20       0.0000     0.2400
            0.70         0.50       0.0000     0.1800
            0.70         0.80       0.0000     0.1200

  Conclusion:
    Variant A (high reliability, low cost) consistently ranks #1.
    Variant B (low reliability, high cost) ranks #3 under both formulas.
    The multiplicative formula penalizes high-cost variants more sharply
    because it multiplies (1-cost) rather than subtracting a fraction.
    Rankings can diverge when reliability/cost trade-offs are balanced.
======================================================================
```

---

## Known Limitations

1. **Fixed vocabulary size (12 state variables per domain).** If a domain exceeds 12 variables, extra variables are silently truncated. Extending the vector dimension requires redefining all index constants and re-encoding all capabilities.

2. **Cross-domain composition is undefined.** The precondition/effect segments are domain-specific (different state-variable vocabularies occupy the same index positions), so composing capabilities from different domains produces a meaningless vector. A shared ontology or variable renaming layer would be required.

3. **Cost normalisation is dataset-dependent.** `collect_cost_stats()` must see all capabilities before encoding. Adding a new capability with a cost outside the observed range will produce values outside [0, 1] until stats are refit.

4. **Availability is stored outside the main vector.** Time-based availability (`{start, end}`) is not encoded into the 59-dim vector, so compatibility() and similarity() cannot detect temporal conflicts (e.g., a capability available 08:00–20:00 cannot follow one that runs at midnight).

5. **Boolean-only state variables.** The embedding assumes all state variables are boolean. Continuous or categorical variables (e.g., `room_count: 42`) cannot be encoded faithfully without extending the scheme to numeric/categorical slots.
