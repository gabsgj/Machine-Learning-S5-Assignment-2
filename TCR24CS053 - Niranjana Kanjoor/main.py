import math
import re
import json


# ============================================================
# 1. INITIAL STATE
# ============================================================

INITIAL_STATE = {
    "User.authenticated": True,
    "Cart.exists": True,
    "Cart.item_count": 3,
    "Order.exists": False,
    "Order.status": "NONE",
    "Payment.status": "NOT_STARTED",
    "Inventory.available": True,
    "Invoice.exists": False,
    "Notification.sent": False
}


# ============================================================
# 2. GOAL STATE
# ============================================================

GOAL = {
    "Order.exists": True,
    "Payment.status": "SUCCESS",
    "Invoice.exists": True,
    "Notification.sent": True
}


# ============================================================
# 3. CAPABILITY DEFINITIONS
# ============================================================

CAPABILITIES = {

    "AddToCart": {
        "type": "FUNCTION",
        "inputs": [
            "product_id",
            "quantity"
        ],
        "outputs": [
            "cart_id"
        ],
        "preconditions": [
            "User.authenticated=true",
            "Product.exists=true",
            "Product.available=true"
        ],
        "effects": [
            "Cart.exists=true",
            "Cart.item_count=increases"
        ],
        "constraints": [
            "quantity>0"
        ],
        "resources": [
            "Database",
            "Network"
        ],
        "cost": 0.00,
        "reliability": 0.99,
        "availability": 1.0,
        "mechanism": "FUNCTION"
    },


    "CheckInventory": {
        "type": "DATABASE",
        "inputs": [
            "product_id"
        ],
        "outputs": [
            "availability_status"
        ],
        "preconditions": [
            "Product.exists=true"
        ],
        "effects": [
            "Inventory.checked=true"
        ],
        "constraints": [],
        "resources": [
            "Database"
        ],
        "cost": 0.00,
        "reliability": 0.995,
        "availability": 1.0,
        "mechanism": "DATABASE"
    },


    "CreateOrder": {
        "type": "API",
        "inputs": [
            "cart_id"
        ],
        "outputs": [
            "order_id"
        ],
        "preconditions": [
            "Cart.exists=true",
            "Cart.item_count>0",
            "Inventory.available=true"
        ],
        "effects": [
            "Order.exists=true",
            "Order.status=CREATED",
            "Cart.locked=true"
        ],
        "constraints": [
            "Cart.item_count>0"
        ],
        "resources": [
            "Database",
            "Authentication",
            "Network"
        ],
        "cost": 0.01,
        "reliability": 0.98,
        "availability": 1.0,
        "mechanism": "API"
    },


    "MakePayment": {
        "type": "SERVICE",
        "inputs": [
            "order_id",
            "payment_amount"
        ],
        "outputs": [
            "transaction_id"
        ],
        "preconditions": [
            "Order.exists=true",
            "Order.status=CREATED"
        ],
        "effects": [
            "Payment.status=SUCCESS"
        ],
        "constraints": [
            "payment_amount>0"
        ],
        "resources": [
            "Payment Gateway",
            "Network",
            "Authentication Token"
        ],
        "cost": 0.50,
        "reliability": 0.97,
        "availability": 1.0,
        "mechanism": "PAYMENT_SERVICE"
    },


    "GenerateInvoice": {
        "type": "FUNCTION",
        "inputs": [
            "order_id",
            "transaction_id"
        ],
        "outputs": [
            "invoice_id"
        ],
        "preconditions": [
            "Payment.status=SUCCESS"
        ],
        "effects": [
            "Invoice.exists=true"
        ],
        "constraints": [],
        "resources": [
            "Database",
            "File System"
        ],
        "cost": 0.01,
        "reliability": 0.99,
        "availability": 1.0,
        "mechanism": "FUNCTION"
    },


    "SendNotification": {
        "type": "MESSAGE",
        "inputs": [
            "user_id",
            "message"
        ],
        "outputs": [
            "notification_id"
        ],
        "preconditions": [
            "Payment.status=SUCCESS"
        ],
        "effects": [
            "Notification.sent=true"
        ],
        "constraints": [],
        "resources": [
            "Network",
            "External Notification Service"
        ],
        "cost": 0.02,
        "reliability": 0.95,
        "availability": 1.0,
        "mechanism": "MESSAGE"
    },


    "CancelCart": {
        "type": "FUNCTION",
        "inputs": [
            "cart_id"
        ],
        "outputs": [
            "status"
        ],
        "preconditions": [
            "Cart.exists=true",
            "Order.exists=false"
        ],
        "effects": [
            "Cart.cancelled=true",
            "Cart.exists=false"
        ],
        "constraints": [],
        "resources": [
            "Database"
        ],
        "cost": 0.00,
        "reliability": 0.99,
        "availability": 1.0,
        "mechanism": "FUNCTION"
    },


    "UpdateProfile": {
        "type": "GUI",
        "inputs": [
            "user_id",
            "profile_data"
        ],
        "outputs": [
            "status"
        ],
        "preconditions": [
            "User.authenticated=true"
        ],
        "effects": [
            "User.profile_updated=true"
        ],
        "constraints": [],
        "resources": [
            "Database",
            "Network"
        ],
        "cost": 0.00,
        "reliability": 0.99,
        "availability": 1.0,
        "mechanism": "GUI"
    }
}


# ============================================================
# 4. CONVERT CAPABILITY INTO TEXT
# ============================================================

def capability_to_text(name, capability):

    parts = []

    parts.append(name)
    parts.append(capability["type"])
    parts.append(capability["mechanism"])

    parts.extend(capability["inputs"])
    parts.extend(capability["outputs"])
    parts.extend(capability["preconditions"])
    parts.extend(capability["effects"])
    parts.extend(capability["constraints"])
    parts.extend(capability["resources"])

    return " ".join(parts)


# ============================================================
# 5. TOKENIZATION
# ============================================================

def tokenize(text):

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9_.=><]+",
        " ",
        text
    )

    return text.split()


# ============================================================
# 6. CREATE VOCABULARY
# ============================================================

all_documents = []


for name, capability in CAPABILITIES.items():

    all_documents.append(
        capability_to_text(name, capability)
    )


all_documents.append(
    " ".join(
        str(key) + "=" + str(value)
        for key, value in INITIAL_STATE.items()
    )
)


all_documents.append(
    " ".join(
        str(key) + "=" + str(value)
        for key, value in GOAL.items()
    )
)


vocabulary = sorted(
    set(
        token
        for document in all_documents
        for token in tokenize(document)
    )
)


word_to_index = {
    word: index
    for index, word in enumerate(vocabulary)
}


# ============================================================
# 7. TEXT VECTOR
# ============================================================

def text_vector(text):

    vector = [0.0] * len(vocabulary)

    tokens = tokenize(text)

    for token in tokens:

        if token in word_to_index:

            index = word_to_index[token]

            vector[index] += 1.0


    magnitude = math.sqrt(
        sum(
            value * value
            for value in vector
        )
    )


    if magnitude != 0:

        vector = [
            value / magnitude
            for value in vector
        ]


    return vector


# ============================================================
# 8. ENCODE STATE
# ============================================================

def encode_state(state):

    text = " ".join(
        str(key) + "=" + str(value)
        for key, value in state.items()
    )

    return text_vector(text)


# ============================================================
# 9. ENCODE GOAL
# ============================================================

def encode_goal(goal):

    text = " ".join(
        str(key) + "=" + str(value)
        for key, value in goal.items()
    )

    return text_vector(text)


# ============================================================
# 10. ENCODE CAPABILITY
# ============================================================

def encode_capability(name):

    capability = CAPABILITIES[name]

    vector = text_vector(
        capability_to_text(
            name,
            capability
        )
    )

    # Add operational attributes
    vector.extend([
        capability["cost"],
        capability["reliability"],
        capability["availability"]
    ])

    return vector


# ============================================================
# 11. COSINE SIMILARITY
# ============================================================

def similarity(vector_a, vector_b):

    length = min(
        len(vector_a),
        len(vector_b)
    )

    a = vector_a[:length]
    b = vector_b[:length]


    dot_product = sum(
        x * y
        for x, y in zip(a, b)
    )


    magnitude_a = math.sqrt(
        sum(
            x * x
            for x in a
        )
    )


    magnitude_b = math.sqrt(
        sum(
            y * y
            for y in b
        )
    )


    if magnitude_a == 0 or magnitude_b == 0:

        return 0.0


    return (
        dot_product
        /
        (magnitude_a * magnitude_b)
    )


# ============================================================
# 12. CHECK EFFECT AND PRECONDITION
# ============================================================

def effect_satisfies_precondition(
    effect,
    precondition
):

    effect = (
        effect
        .lower()
        .replace(" ", "")
    )

    precondition = (
        precondition
        .lower()
        .replace(" ", "")
    )


    if effect == precondition:

        return True


    return False


# ============================================================
# 13. CAPABILITY COMPATIBILITY
# ============================================================

def compatibility(
    capability_a,
    capability_b
):

    effects = CAPABILITIES[
        capability_a
    ]["effects"]


    preconditions = CAPABILITIES[
        capability_b
    ]["preconditions"]


    # Every state precondition of the second
    # capability must be satisfied by an effect
    # of the first capability.

    for precondition in preconditions:

        satisfied = False


        for effect in effects:

            if effect_satisfies_precondition(
                effect,
                precondition
            ):

                satisfied = True

                break


        if not satisfied:

            return False


    return True


# ============================================================
# 14. COMPOSE CAPABILITIES
# ============================================================

def compose(capability_names):

    vectors = [
        encode_capability(name)
        for name in capability_names
    ]


    if not vectors:

        return []


    dimension = len(vectors[0])


    composite = []


    for i in range(dimension):

        value = sum(
            vector[i]
            for vector in vectors
        ) / len(vectors)


        composite.append(value)


    return composite


# ============================================================
# 15. VECTOR SUMMARY
# ============================================================

def print_vector_summary(
    name,
    vector
):

    preview = vector[:10]


    formatted = [
        round(value, 3)
        for value in preview
    ]


    print(
        f"{name}: {formatted} ..."
    )


# ============================================================
# EXPERIMENT 1
# CAPABILITY COMPATIBILITY
# ============================================================

def experiment_1():

    print("\n" + "=" * 70)

    print(
        "EXPERIMENT 1: CAPABILITY COMPATIBILITY"
    )

    print("=" * 70)


    pairs = [

        (
            "CreateOrder",
            "MakePayment"
        ),

        (
            "CreateOrder",
            "CancelCart"
        ),

        (
            "MakePayment",
            "GenerateInvoice"
        ),

        (
            "MakePayment",
            "SendNotification"
        )

    ]


    for first, second in pairs:

        result = compatibility(
            first,
            second
        )


        vector_similarity = similarity(
            encode_capability(first),
            encode_capability(second)
        )


        print(
            f"{first:20} -> "
            f"{second:20} | "
            f"Compatible = {result} | "
            f"Similarity = "
            f"{vector_similarity:.3f}"
        )


# ============================================================
# EXPERIMENT 2
# CAPABILITY COMPOSITION
# ============================================================

def experiment_2():

    print("\n" + "=" * 70)

    print(
        "EXPERIMENT 2: CAPABILITY COMPOSITION"
    )

    print("=" * 70)


    chain = [

        "CreateOrder",
        "MakePayment",
        "GenerateInvoice"

    ]


    print("\nComposition chain:")


    for i in range(
        len(chain) - 1
    ):

        first = chain[i]

        second = chain[i + 1]


        print(
            f"{first} -> "
            f"{second} : "
            f"{compatibility(first, second)}"
        )


    composite_vector = compose(
        chain
    )


    print("\nComposite capability:")

    print(
        "CompletePurchase = "
        "CreateOrder -> "
        "MakePayment -> "
        "GenerateInvoice"
    )


    print_vector_summary(
        "Composite vector",
        composite_vector
    )


    print(
        "\nRelation with "
        "individual capabilities:"
    )


    for capability in chain:

        sim = similarity(
            composite_vector,
            encode_capability(capability)
        )


        print(
            f"Composite vs "
            f"{capability}: "
            f"{sim:.3f}"
        )


# ============================================================
# EXPERIMENT 3
# ALTERNATIVE IMPLEMENTATIONS
# ============================================================

def experiment_3():

    print("\n" + "=" * 70)

    print(
        "EXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS"
    )

    print("=" * 70)


    api = {

        "type": "API",

        "mechanism": "REST API",

        "inputs": [
            "cart_id"
        ],

        "outputs": [
            "order_id"
        ],

        "preconditions": [
            "Cart.exists=true"
        ],

        "effects": [
            "Order.exists=true"
        ],

        "constraints": [],

        "resources": [
            "Network"
        ],

        "cost": 0.01,

        "reliability": 0.98,

        "availability": 1.0
    }


    database = {

        "type": "DATABASE",

        "mechanism": "INSERT",

        "inputs": [
            "cart_id"
        ],

        "outputs": [
            "order_id"
        ],

        "preconditions": [
            "Cart.exists=true"
        ],

        "effects": [
            "Order.exists=true"
        ],

        "constraints": [],

        "resources": [
            "Database"
        ],

        "cost": 0.005,

        "reliability": 0.99,

        "availability": 1.0
    }


    gui = {

        "type": "GUI",

        "mechanism": "CLICK",

        "inputs": [
            "cart_id"
        ],

        "outputs": [
            "order_id"
        ],

        "preconditions": [
            "Cart.exists=true"
        ],

        "effects": [
            "Order.exists=true"
        ],

        "constraints": [],

        "resources": [
            "Network"
        ],

        "cost": 0.02,

        "reliability": 0.96,

        "availability": 1.0
    }


    implementations = {

        "CreateOrder_API": api,

        "CreateOrder_DATABASE": database,

        "CreateOrder_GUI": gui

    }


    vectors = {}


    for name, capability in implementations.items():

        text = capability_to_text(
            name,
            capability
        )


        vectors[name] = text_vector(
            text
        )


        print_vector_summary(
            name,
            vectors[name]
        )


    print("\nPairwise similarities:")


    names = list(
        vectors.keys()
    )


    for i in range(
        len(names)
    ):

        for j in range(
            i + 1,
            len(names)
        ):

            sim = similarity(
                vectors[names[i]],
                vectors[names[j]]
            )


            print(
                f"{names[i]} vs "
                f"{names[j]}: "
                f"{sim:.3f}"
            )


# ============================================================
# EXPERIMENT 4
# IRRELEVANT CAPABILITIES
# ============================================================

def experiment_4():

    print("\n" + "=" * 70)

    print(
        "EXPERIMENT 4: IRRELEVANT CAPABILITY"
    )

    print("=" * 70)


    goal_vector = encode_goal(
        GOAL
    )


    relevant = [

        "CreateOrder",

        "MakePayment",

        "GenerateInvoice",

        "SendNotification"

    ]


    irrelevant = [

        "UpdateProfile",

        "CancelCart"

    ]


    print(
        "\nSimilarity with goal:\n"
    )


    for name in relevant:

        sim = similarity(
            encode_capability(name),
            goal_vector
        )


        print(
            f"{name:20} | "
            f"Relevant | "
            f"Similarity = "
            f"{sim:.3f}"
        )


    for name in irrelevant:

        sim = similarity(
            encode_capability(name),
            goal_vector
        )


        print(
            f"{name:20} | "
            f"Irrelevant | "
            f"Similarity = "
            f"{sim:.3f}"
        )


# ============================================================
# EXPERIMENT 5
# OPERATIONAL ATTRIBUTES
# ============================================================

def experiment_5():

    print("\n" + "=" * 70)

    print(
        "EXPERIMENT 5: OPERATIONAL ATTRIBUTES"
    )

    print("=" * 70)


    print(
        "\nCapability"
        "            Cost"
        "       Reliability"
        "    Availability"
    )


    print("-" * 70)


    for name, capability in CAPABILITIES.items():

        print(
            f"{name:20} "
            f"{capability['cost']:8.3f} "
            f"{capability['reliability']:12.3f} "
            f"{capability['availability']:12.3f}"
        )


# ============================================================
# BASIC ENCODING TEST
# ============================================================

def basic_encoding_test():

    print("\n" + "=" * 70)

    print(
        "BASIC ENCODING TEST"
    )

    print("=" * 70)


    state_vector = encode_state(
        INITIAL_STATE
    )


    goal_vector = encode_goal(
        GOAL
    )


    print_vector_summary(
        "Initial state vector",
        state_vector
    )


    print_vector_summary(
        "Goal vector",
        goal_vector
    )


    for name in CAPABILITIES:

        vector = encode_capability(
            name
        )


        print_vector_summary(
            name,
            vector
        )


# ============================================================
# SAVE DATASET
# ============================================================

def save_dataset():

    dataset = {

        "initial_state": INITIAL_STATE,

        "goal": GOAL,

        "capabilities": CAPABILITIES,

        "experiments": {

            "compatibility": [

                [
                    "CreateOrder",
                    "MakePayment"
                ],

                [
                    "CreateOrder",
                    "CancelCart"
                ],

                [
                    "MakePayment",
                    "GenerateInvoice"
                ],

                [
                    "MakePayment",
                    "SendNotification"
                ]

            ],

            "composition": [

                "CreateOrder",

                "MakePayment",

                "GenerateInvoice"

            ],

            "alternative_implementations": [

                "API",

                "DATABASE",

                "GUI"

            ],

            "irrelevant_capabilities": [

                "UpdateProfile",

                "CancelCart"

            ],

            "operational_attributes": [

                "cost",

                "reliability",

                "availability"

            ]

        }

    }


    with open(
        "dataset.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            dataset,
            file,
            indent=4
        )


    print(
        "\nDataset saved as dataset.json"
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("\n")

    print("=" * 70)

    print(
        "VECTOR EMBEDDING FOR "
        "CAPABILITY COMPOSITION"
    )

    print(
        "Assignment 2"
    )

    print("=" * 70)


    print(
        f"\nNumber of capabilities: "
        f"{len(CAPABILITIES)}"
    )


    print(
        "Embedding dimension: "
        f"{len(encode_capability('CreateOrder'))}"
    )


    basic_encoding_test()

    experiment_1()

    experiment_2()

    experiment_3()

    experiment_4()

    experiment_5()

    save_dataset()


    print("\n" + "=" * 70)

    print(
        "ALL EXPERIMENTS COMPLETED"
    )

    print("=" * 70)


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    main()