# Deliverable 3 — Experimental Dataset

## Application problem
E-commerce order processing.

The dataset uses the formal initial-state and goal pattern supplied by the assignment. It contains typed inputs/outputs, preconditions, effects, constraints, resources, cost, reliability, availability and execution mechanisms.

## Initial state
- `User.authenticated = true`
- `User.role = CUSTOMER`
- `Cart.exists = true`
- `Cart.item_count = 3`
- `Order.exists = false`
- `Payment.status = NOT_STARTED`
- `Inventory.available = true`
- `Notification.sent = false`

## Goal
- `Order.exists = true`
- `Payment.status = SUCCESS`
- `Notification.sent = true`

## Capability set
| ID | Type | Purpose |
|---|---|---|
| CreateOrder | API | C1; creates an order |
| MakePayment | SERVICE | C2; completes payment |
| CancelCart | API | C3; requires no order |
| SendNotification | EVENT | notifies after payment |
| CreateOrder_DB | DATABASE | alternative order implementation |
| CreateOrder_GUI | GUI | alternative order implementation |
| AddToCart | API | intermediate capability |
| UpdateProfile | API | irrelevant capability |

## Required compositions
`CompletePurchase = SendNotification o MakePayment o CreateOrder`

## Operational experiment
`operational_variants.json` varies cost, reliability, availability and risk for CreateOrder while keeping the functional precondition/effect definition unchanged.
