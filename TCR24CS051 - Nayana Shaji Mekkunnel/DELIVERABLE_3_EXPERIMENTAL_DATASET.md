# Deliverable 3: Experimental Dataset

## Dataset

`ecommerce_purchase_flow.json` formalizes an e-commerce order and fulfillment application. It is derived from the supplied Ecommerce Capability Composition example. It contains an initial state, a goal, global hazard predicates, and ten atomic capabilities.

### Initial state and goal

The initial state records an authenticated customer, a populated cart, no order, payment not started, inventory available, and no invoice, shipment, or notification. The goal requires `Order.exists=true`, `Payment.status=SUCCESS`, and `Invoice.generated`, `Shipment.dispatched`, and `Notification.sent` to be true. A global hazard marks `Payment.status=FAILED`.

### Capabilities

| Capability | Type | Key preconditions/effects | Operational attributes |
|---|---|---|---|
| CreateOrder | API | Authenticated cart -> order exists/status CREATED | 80 ms, $0.01, reliability .999 |
| ValidateInventory | SERVICE | Order exists -> status VALIDATED | 50 ms, $0.005, reliability .995 |
| MakePayment_API | API | Status VALIDATED -> payment SUCCESS/status PAID | 120 ms, $0.05, reliability .992 |
| MakePayment_DB | DATABASE | Same payment effect through internal ledger | 35 ms, $0.002, reliability .965 |
| GenerateInvoice | FUNCTION | Payment SUCCESS -> invoice generated | 40 ms, $0.001, reliability .999 |
| DispatchShipment | SERVICE | Payment SUCCESS -> shipment dispatched/status FULFILLED | 90 ms, $0.02, reliability .988 |
| SendNotification | EVENT | Invoice and shipment ready -> notification sent | 20 ms, $0.001, reliability .990 |
| CancelCart | API | Cart exists -> cart removed | 30 ms, $0.00, reliability .999 |
| BrowseCatalog | API | No required state predicate -> catalog viewed | 15 ms, $0.00, reliability .999 |
| UpdateWishlist | DATABASE | Authenticated user -> wishlist updated | 25 ms, $0.00, reliability .999 |

Each capability includes typed ports, a mechanism, QoS attributes, and reliability in the JSON. Mechanisms include REST endpoints, a gRPC service, a database operation, local PDF rendering, a logistics endpoint, and an event bus. The purchase dataset includes ten capabilities; the table enumerates all ten. (One operational row above combines the alternative payment implementations as two separate dataset entries.)

## Experimental cases

1. **Directional compatibility:** controlled formal example where CreateOrder sets `Order.exists=true`; MakePayment requires true; CancelCart requires false.
2. **Composition:** `CreateOrder -> ValidateInventory -> MakePayment_API`; inspect merged preconditions/effects, reliability, QoS, and encoded vector dimension.
3. **Alternative mechanisms:** compare API and database payment capabilities. Their functional effects are identical while type and operational dimensions differ.
4. **Irrelevant capabilities:** compare direct effects against the purchase goal for invoice generation, catalog browsing, and wishlist updating.
5. **Operational attributes:** compare the API and database payment variants on money cost, latency, reliability, and availability.

## Reproduction

From this folder, run:

```text
py -3 capability_embedding.py --experiments
```

The dataset is synthetic and illustrative. Operational values are example inputs, not measurements of production services. The compatibility pair in Experiment 1 is deliberately controlled to test one enabling and one contradictory relationship; the larger e-commerce dataset provides the realistic formal application context.

