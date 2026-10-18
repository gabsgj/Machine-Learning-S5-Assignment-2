/*
    EXPERIMENT 4: IRRELEVANT CAPABILITIES

    Goal:

        confirmation_sent = YES

    Relevant capabilities:

        CreateOrder
        MakePayment
        SendConfirmation

    Irrelevant capabilities:

        UpdateUserProfile
        GenerateReport

    Goal relevance is calculated by comparing capability
    effects with goal conditions.

    Relevance score:

        matching goal conditions
        ------------------------
        total goal conditions

    Therefore, a capability whose effects do not contribute
    to the goal receives a low or zero relevance score.
*/