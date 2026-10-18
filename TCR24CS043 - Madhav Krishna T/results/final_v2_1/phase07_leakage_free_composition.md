# SCE-128 v2.1 Experiment 6 — Leakage-Free Learned Composition

Training pairs: 8
Training mean cosine: 0.8531
Held-out direct-pair mean: 0.8546
Mean final chain consistency: 0.8316
Minimum final chain consistency: 0.7929

## Held-out direct pairs
- C1->C11: 0.8517
- C4->C12: 0.8545
- C4->C13: 0.8758
- C5->C8: 0.8363

## Recursive chains
- purchase_success_chain (L=7): final=0.7929; prefixes=[1.0, 0.8256, 0.8394, 0.831, 0.8248, 0.8212, 0.7929]
- cancel_and_release_chain (L=3): final=0.7977; prefixes=[1.0, 0.8806, 0.7977]
- inventory_to_order (L=3): final=0.8358; prefixes=[1.0, 0.819, 0.8358]
- order_to_verify (L=3): final=0.8354; prefixes=[1.0, 0.8527, 0.8354]
- payment_to_notify (L=3): final=0.8219; prefixes=[1.0, 0.8648, 0.8219]
- create_to_update (L=2): final=0.8545; prefixes=[1.0, 0.8545]
- create_to_get (L=2): final=0.8758; prefixes=[1.0, 0.8758]
- create_to_refund (L=3): final=0.8189; prefixes=[1.0, 0.8527, 0.8189]
- add_to_remove (L=2): final=0.8517; prefixes=[1.0, 0.8517]

## Methodological note
The formal composite is encoded separately and is never supplied to the prediction step. This avoids the v2 leakage that made composition consistency trivially equal to 1.0.