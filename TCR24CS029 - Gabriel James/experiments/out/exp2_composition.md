# Experiment 2: capability composition

The composite interface: inputs [customer_id], outputs [order_id, payment_reference], net delta [Order.exists SET true].

## Vector relations of C_1 o C_2

| relation | cosine |
| --- | --- |
| composite vs C_1 | 0.8632 |
| composite vs C_2 | 0.8264 |
| composite vs C_3 (not a member) | 0.7069 |
| algebraic vs re-encoded composite | 0.9660 |
| (C_1 o C_2) o C_3 vs C_1 o (C_2 o C_3) | 1.0000 |

## Composition laws

| quantity | C_1 | C_2 | C_3 | C_1 o C_2 | whole sequence |
| --- | --- | --- | --- | --- | --- |
| time_ms | 120 | 200 | 90 | 320.0 | 410.0 |
| money | 0 | 0.5 | 0 | 0.5000 | 0.5000 |
| risk | 0.01 | 0.03 | 0.01 | 0.0397 | 0.0493 |
| reliability | 0.99 | 0.98 | 0.99 | 0.9702 | 0.9605 |

## Sequence validity

| step | verdict | note |
| --- | --- | --- |
| C_1 -> C_2 | compatible | order established, payment binds |
| C_2 -> C_3 | uncertain | payment writes no state; honest uncertainty |
| composite C_1 o C_2 self check | uncertain | run as one capability |
| composite C_1 o C_2 o C_3 self check | incompatible | cancel requires the absence the create established |

The composite relates positively to both members without collapsing onto either; the algebraic superposition and the re-encoded specification agree; both bracketings of the sequence agree on the effect fold, the precondition union, the quality law and the re-encoded vector (cosine 1.0000). The invalid ordering is detected by the composite self check: the sequence requires the order not to exist while its net effect establishes it.
