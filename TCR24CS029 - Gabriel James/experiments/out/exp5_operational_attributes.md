# Experiment 5: operational attributes and context gates

## Numeric quality attributes

| attribute | pair | composed | pass boundary | fail boundary | pass verdict | fail verdict |
| --- | --- | --- | --- | --- | --- | --- |
| cost-time | PAT-CreateOrder -> PAT-MakePayment | 320.000000 | 320.000000 | 319.680000 | compatible | incompatible |
| cost-money | PAT-CreateOrder -> PAT-MakePayment | 0.500000 | 0.500000 | 0.499500 | compatible | incompatible |
| cost-energy | PAT-CreateOrder -> PAT-MakePayment | 0.006000 | 0.006000 | 0.005994 | compatible | incompatible |
| cost-resource | DEC-ScheduleMaintenance -> DEC-EscalateTicket | 0.100000 | 0.100000 | 0.099900 | uncertain | incompatible |
| risk | DEC-ScheduleMaintenance -> DEC-EscalateTicket | 0.039600 | 0.039600 | 0.039560 | uncertain | incompatible |
| reliability | DEC-ScheduleMaintenance -> DEC-EscalateTicket | 0.940800 | 0.940800 | 0.941741 | uncertain | incompatible |

## Availability windows

| weekday | minute | availability | verdict | note |
| --- | --- | --- | --- | --- |
| (omitted) | 0 | skip | uncertain | no time point supplied; window evaluation skipped |
| mon | 480 | pass | uncertain | opens at 08:00 |
| mon | 200 | fail | incompatible | before the window |
| mon | 1019 | pass | uncertain | one minute before close |
| mon | 1020 | fail | incompatible | the closing minute is outside (half open interval) |
| sat | 480 | fail | incompatible | weekend |

## Resources and roles

| check | enforced | inventory | outcome | verdict |
| --- | --- | --- | --- | --- |
| resources | yes | decoy_db | pass | uncertain |
| resources | yes | (empty) | fail | incompatible |
| resources | no | (empty) | skip | uncertain |
| resources | no | decoy_db | skip | uncertain |
| roles | yes | service | pass | uncertain |
| roles | yes | service, admin | pass | uncertain |
| roles | yes | customer | fail | incompatible |
| roles | no | (empty) | skip | uncertain |

## Mapper weight sweep

| conditions weight | name weight | fields weight | Pat_reg total | form total | margin | ambiguous | kind tie break | selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.00 | 0.50 | 0.50 | 0.7637 | 0.6934 | 0.0703 | no | no | AR-PatReg |
| 0.05 | 0.47 | 0.47 | 0.7755 | 0.7087 | 0.0668 | no | no | AR-PatReg |
| 0.10 | 0.45 | 0.45 | 0.7873 | 0.7240 | 0.0633 | no | no | AR-PatReg |
| 0.15 | 0.42 | 0.42 | 0.7991 | 0.7394 | 0.0598 | no | no | AR-PatReg |
| 0.20 | 0.40 | 0.40 | 0.8109 | 0.7547 | 0.0562 | no | no | AR-PatReg |
| 0.25 | 0.38 | 0.38 | 0.8228 | 0.7700 | 0.0527 | no | no | AR-PatReg |
| 0.30 | 0.35 | 0.35 | 0.8346 | 0.7854 | 0.0492 | no | yes | AR-PatReg |
| 0.35 | 0.33 | 0.33 | 0.8464 | 0.8007 | 0.0457 | no | yes | AR-PatReg |
| 0.40 | 0.30 | 0.30 | 0.8582 | 0.8160 | 0.0422 | no | yes | AR-PatReg |
| 0.45 | 0.28 | 0.28 | 0.8700 | 0.8314 | 0.0387 | no | yes | AR-PatReg |
| 0.50 | 0.25 | 0.25 | 0.8818 | 0.8467 | 0.0352 | no | yes | AR-PatReg |
| 0.55 | 0.22 | 0.22 | 0.8937 | 0.8620 | 0.0316 | no | yes | AR-PatReg |
| 0.60 | 0.20 | 0.20 | 0.9055 | 0.8774 | 0.0281 | no | yes | AR-PatReg |
| 0.65 | 0.17 | 0.17 | 0.9173 | 0.8927 | 0.0246 | no | yes | AR-PatReg |
| 0.70 | 0.15 | 0.15 | 0.9291 | 0.9080 | 0.0211 | no | yes | AR-PatReg |
| 0.75 | 0.12 | 0.12 | 0.9409 | 0.9233 | 0.0176 | no | yes | AR-PatReg |
| 0.80 | 0.10 | 0.10 | 0.9527 | 0.9387 | 0.0141 | no | yes | AR-PatReg |
| 0.85 | 0.08 | 0.08 | 0.9646 | 0.9540 | 0.0105 | no | yes | AR-PatReg |
| 0.90 | 0.05 | 0.05 | 0.9764 | 0.9693 | 0.0070 | no | yes | AR-PatReg |
| 0.95 | 0.03 | 0.03 | 0.9882 | 0.9847 | 0.0035 | no | yes | AR-PatReg |
| 1.00 | 0.00 | 0.00 | 1.0000 | 1.0000 | 0.0000 | no | yes | AR-PatReg |

Every composed quantity has a passing and a rejecting counterpart through the real engine: a cap exactly at the composed value passes, a cap just below it fails exactly that check and turns the pair incompatible, and the reliability floor behaves symmetrically. The windowed availability form is exercised at its boundaries, including the half open closing minute. An inventory that covers the requirements passes, a missing entry fails the pair, and the enforce flags gate the checks so an absent inventory never rejects on its own. The weight sweep keeps the intended capability on top for every combination; below the ambiguity margin the delivery kind resolves the near tie, and at the default weights the margin is 0.0492, the same value the CLI reports.
