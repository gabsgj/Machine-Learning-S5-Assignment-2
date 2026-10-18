# Experiment 1: capability compatibility

The assignment pattern (C_1 CreateOrder, C_2 MakePayment, C_3 CancelCart):

| pair | verdict | vector score | coverage | signed cosine | functional sim | implementation sim | name sim | full cosine |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C_1 -> C_2 (composable) | compatible | 1.0000 | 1.0000 | 1.0000 | 0.8399 | 0.9835 | 0.6550 | 0.7186 |
| C_1 -> C_3 (incompatible) | incompatible | 0.0000 | 1.0000 | -1.0000 | 0.6708 | 0.9762 | 0.5588 | 0.7146 |
| C_2 -> C_3 | uncertain |  |  |  |  |  |  |  |

The seventeen labeled dataset pairs:

| problem | case | label | verdict | vector score | functional sim | name sim | raw cosine |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hospital_alias | clinic-order-sample | compatible | compatible | 1.0000 | 0.7807 | 0.3523 | 0.7558 |
| hospital_alias | clinic-sample-result | uncertain | uncertain | 1.0000 | 0.8406 | 0.6910 | 0.8229 |
| hospital_alias | clinic-result-before-sample | uncertain | uncertain | 0.4419 | 0.8406 | 0.6910 | 0.8229 |
| hospital_alias | clinic-order-result-skipping-sample | uncertain | uncertain | 0.3891 | 0.7776 | 0.2696 | 0.7933 |
| hospital_alias | alias-register-verify | compatible | compatible | 1.0000 | 0.8617 | 0.4613 | 0.7979 |
| hospital_alias | alias-verify-register | uncertain | uncertain | 0.5000 | 0.8617 | 0.4613 | 0.7979 |
| ecommerce_purchase | ecom-place-pay | uncertain | uncertain | 0.9881 | 0.8034 | 0.7474 | 0.7240 |
| ecommerce_purchase | ecom-add-place | uncertain | uncertain | 1.0000 | 0.6752 | 0.4789 | 0.7284 |
| ecommerce_purchase | ecom-ship-before-pay | uncertain | uncertain | 0.3950 | 0.7034 | 0.5648 | 0.5642 |
| ecommerce_purchase | ecom-totals-then-pay | uncertain | uncertain | 0.0000 | 0.5746 | 0.2285 | 0.6016 |
| ecommerce_purchase | ecom-ship-then-confirm | incompatible | incompatible | 0.1839 | 0.8377 | 0.7180 | 0.7804 |
| ecommerce_purchase | ecom-cancel-then-confirm | incompatible | incompatible | 0.0000 | 0.6129 | 0.6006 | 0.6163 |
| ecommerce_purchase | ecom-cancel-then-ship | incompatible | incompatible | 0.0000 | 0.7998 | 0.6117 | 0.7595 |
| document_processing | docs-parse-summarize | compatible | compatible | 1.0000 | 0.9128 | 0.3499 | 0.8104 |
| document_processing | docs-parse-index | uncertain | uncertain | 1.0000 | 0.8143 | 0.4555 | 0.6877 |
| document_processing | docs-index-notify | uncertain | uncertain | 0.3230 | 0.8241 | 0.2398 | 0.7283 |
| document_processing | docs-notify-summarize | uncertain | uncertain | 0.1820 | 0.8217 | 0.1911 | 0.7229 |

Three-class agreement over the seventeen labels: symbolic accuracy 1.0000 (the outcome is reported, never guessed). A scalar viewpoint has no way to express "cannot prove", so its AUC understates the symbolic system; the vector compatibility score still ranks composable pairs highest (AUC 0.9405), functional similarity is weaker (0.7738) and name similarity is below chance (0.3214).

Decidable discrimination (composable against provably incompatible): vector compatibility score AUC 1.0000, functional similarity AUC 0.7778, name similarity AUC 0.0000, raw full-vector cosine AUC 0.7778.

Vocabulary name pair labels (18 pairs): the sparse text cosine scores equivalent pairs at mean 0.7698 (minimum 0.6369) and distinct pairs at mean 0.1890 (maximum 0.6699), AUC 0.9846. The two mechanism pairs (the same operation through a different delivery persona, names deliberately disjoint) stay at or below 0.0000: name similarity is the wrong instrument for them, and their operation equality is pinned by the equivalence groups.

Noise floor from the 24 unrelated capabilities: full-vector cosine mean 0.7090 max 0.7984 (the full vector shares positive structure everywhere, which is why comparisons use the partitioned views), name similarity mean 0.0525 max 0.3686.
