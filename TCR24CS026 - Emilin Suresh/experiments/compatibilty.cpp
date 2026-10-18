/*
    EXPERIMENT 1: COMPATIBILITY

    Objective:
    Determine whether the output/effects of one capability
    satisfy the preconditions and inputs of another capability.

    Required cases:

    1. CreateOrder -> MakePayment
       Expected: Compatible

    2. CreateOrder -> CancelCart
       Expected: Incompatible

    Compatibility is calculated using:

        Compatibility =
            w1 * PreconditionEffect
          + w2 * InputOutput
          + w3 * ResourceCompatibility

    A capability pair is considered executable/composable
    when the required compatibility conditions are satisfied.
*/