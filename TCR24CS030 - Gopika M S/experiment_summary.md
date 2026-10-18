# Experiment Summary

## Encoding

All state and goal vectors use the same symbolic vocabulary. Capability
vectors additionally include six operational attributes.

## Experiment 1 — Capability Compatibility

- CreateOrder → MakePayment: 0.9079
- CreateOrder → CancelCart: 0.0970

The first pair is expected to be substantially more compatible because
CreateOrder produces `Order.exists = true`, which satisfies MakePayment's
precondition. CancelCart requires `Order.exists = false`.

## Experiment 2 — Composition

Composite capability:

`CompletePurchase = SendNotification ◦ MakePayment ◦ CreateOrder`

The implementation constructs a composite capability only when adjacent
precondition/effect requirements are satisfied.

Composite reliability:
`0.9653`

Composite availability:
`0.9605`

Composite goal relevance:
`1.0000`

## Experiment 3 — Alternative Implementations

CreateOrder is compared with database and GUI implementations.

- API vs Database similarity: 0.9304
- API vs GUI similarity: 0.9268

They share functional information but retain mechanism/type information,
so they are related without being represented as identical.

## Experiment 4 — Irrelevant Capabilities

Goal relevance:

- CreateOrder: 0.3333
- MakePayment: 0.3333
- SendNotification: 0.3333
- UpdateProfile: 0.0000

UpdateProfile does not directly produce any of the specified purchase-goal
conditions.

## Experiment 5 — Operational Attributes

The representation records reliability, availability, risk, time cost,
resource cost and monetary cost. These are treated separately from the
symbolic functional features so that operational properties can be
analysed without changing the functional identity of a capability.

## Conclusion

The experiments show that a structured, problem-specific vector can
represent functional identity while a separate compatibility function
captures the stronger condition needed for composition.
