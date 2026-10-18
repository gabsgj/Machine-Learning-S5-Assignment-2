# Sandbox Input Examples

A curated list of example JSON payloads you can paste directly into the **Custom Sandbox** tab.
Each example demonstrates a different pattern in the vector embedding space.

---

## Valid State Variable Keys (copy-paste ready)

```
Order.exists            Order.status_CREATED     Order.status_PAID
Payment.status_SUCCESS  Payment.status_FAILED     Notification.sent
Cart.exists             Cart.item_count           Inventory.available
User.authenticated      User.role_CUSTOMER        User.role_ADMIN
```

> Values can be `1` (true/required), `0` (don't-care/default), or `-1` (explicitly false/negated).

---

## Examples

### 1. Notify Admin After Order Is Created
A simple notification capability — requires admin role and an existing order.

```json
{
  "name": "NotifyAdmin",
  "preconditions": {
    "User.role_ADMIN": 1,
    "Order.exists": 1
  },
  "effects": {
    "Notification.sent": 1
  },
  "cost": 0.05,
  "reliability": 0.99,
  "availability": 1.0
}
```

---

### 2. Guest Checkout (No Auth Required)
A capability that creates an order without requiring the user to be authenticated.
Notice `User.authenticated` is absent (defaults to 0 = don't care).

```json
{
  "name": "GuestCheckout",
  "preconditions": {
    "Cart.exists": 1,
    "Cart.item_count": 1,
    "Inventory.available": 1
  },
  "effects": {
    "Order.exists": 1,
    "Order.status_CREATED": 1,
    "Cart.exists": -1
  },
  "cost": 0.08,
  "reliability": 0.97,
  "availability": 1.0
}
```

---

### 3. Process Refund (Reverses Payment)
Demonstrates negative effects — this capability actively un-sets the payment success flag.

```json
{
  "name": "ProcessRefund",
  "preconditions": {
    "Order.status_PAID": 1,
    "Payment.status_SUCCESS": 1,
    "User.authenticated": 1
  },
  "effects": {
    "Payment.status_SUCCESS": -1,
    "Payment.status_FAILED": 1,
    "Order.status_PAID": -1
  },
  "cost": 0.25,
  "reliability": 0.92,
  "availability": 0.95
}
```

---

### 4. Inventory Reservation
A precursor step before checkout — checks and locks inventory.

```json
{
  "name": "ReserveInventory",
  "preconditions": {
    "Cart.item_count": 1,
    "Inventory.available": 1
  },
  "effects": {
    "Inventory.available": -1
  },
  "cost": 0.02,
  "reliability": 0.999,
  "availability": 1.0
}
```

---

### 5. Admin Order Cancellation
An admin-only action. Requires an active order and admin privileges; cancels it and restores inventory.

```json
{
  "name": "AdminCancelOrder",
  "preconditions": {
    "Order.exists": 1,
    "User.role_ADMIN": 1
  },
  "effects": {
    "Order.exists": -1,
    "Order.status_CREATED": -1,
    "Inventory.available": 1
  },
  "cost": 0.03,
  "reliability": 1.0,
  "availability": 1.0
}
```

---

### 6. Payment Failure Recovery
Triggered specifically when a payment has failed. Sets up a retry path.

```json
{
  "name": "RecoverFailedPayment",
  "preconditions": {
    "Payment.status_FAILED": 1,
    "Order.exists": 1,
    "User.authenticated": 1
  },
  "effects": {
    "Payment.status_FAILED": -1,
    "Payment.status_SUCCESS": 1,
    "Order.status_PAID": 1
  },
  "cost": 0.15,
  "reliability": 0.88,
  "availability": 0.97
}
```

---

### 7. High-Availability API Payment (Low Cost)
A payment variant optimized for reliability — models a premium external payment API.

```json
{
  "name": "PremiumPaymentAPI",
  "preconditions": {
    "Order.exists": 1,
    "User.authenticated": 1
  },
  "effects": {
    "Payment.status_SUCCESS": 1,
    "Order.status_PAID": 1
  },
  "cost": 0.50,
  "reliability": 0.9995,
  "availability": 0.999
}
```

---

### 8. Irrelevant Capability (Marketing Email)
This has **zero overlap** with any order/payment goal vector.
Its embedding will show 0 dot-product against the goal — it will be pruned by any planner.

```json
{
  "name": "SendMarketingEmail",
  "preconditions": {
    "User.authenticated": 1
  },
  "effects": {
    "Notification.sent": 1
  },
  "cost": 0.01,
  "reliability": 0.98,
  "availability": 1.0
}
```

---

### 9. Full Purchase Flow (Manual Composite)
Hand-crafted composite representing the full checkout pipeline in one step.
Compare this to the auto-composed C₁₂ in the **Composition** tab.

```json
{
  "name": "FullPurchase_Manual",
  "preconditions": {
    "Cart.item_count": 1,
    "Inventory.available": 1,
    "User.authenticated": 1
  },
  "effects": {
    "Order.exists": 1,
    "Order.status_PAID": 1,
    "Payment.status_SUCCESS": 1,
    "Cart.exists": -1,
    "Inventory.available": -1
  },
  "cost": 0.18,
  "reliability": 0.94,
  "availability": 0.98
}
```

---

### 10. Zero-Effect Capability (Edge Case)
A capability with no effects — demonstrates what an all-zero effect sub-vector looks like.
Useful for understanding the embedding of pure "sensor" or "check" capabilities.

```json
{
  "name": "CheckOrderStatus",
  "preconditions": {
    "Order.exists": 1,
    "User.authenticated": 1
  },
  "effects": {},
  "cost": 0.001,
  "reliability": 1.0,
  "availability": 1.0
}
```

---

## Tips for Exploring the Embedding Space

| Pattern | What to observe |
|---|---|
| Set an effect to `-1` | Bar turns **amber** — represents an active negation in vector space |
| Leave effects empty `{}` | The effects sub-vector is all zeros — orthogonal to every goal |
| Make preconditions = effects | Capability is *idempotent* — applying it twice has no extra impact |
| Set `reliability: 0.5` | Drastic drop — see how the ops sub-vector differs from a reliable capability |
| Two capabilities sharing the same effects | Compare them in the **Alternative Impl.** tab — they'll show high cosine similarity |
