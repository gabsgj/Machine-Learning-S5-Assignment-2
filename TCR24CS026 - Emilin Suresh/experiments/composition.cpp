/*
    EXPERIMENT 2: CAPABILITY COMPOSITION

    Objective:
    Demonstrate that multiple individually executable capabilities
    can form a larger composite capability.

    Composition chain:

        CreateOrder
             |
             v
        MakePayment
             |
             v
        SendConfirmation

    Expected result:

        CreateOrder
            ->
        MakePayment
            ->
        SendConfirmation

    is a valid composition.

    Composite operational properties are calculated from
    the individual capabilities.

    Execution time:
        sum of execution times

    Resource cost:
        sum of resource costs

    Monetary cost:
        sum of monetary costs

    Reliability:
        product of individual reliabilities

    Availability:
        all capabilities must be available.
*/