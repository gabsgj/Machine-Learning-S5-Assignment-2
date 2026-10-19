from models.capability import Capability

capabilities = [

    # =====================================================
    # 1. Create Order
    # =====================================================

    Capability(
        name="CreateOrder",
        capability_type="API",
        inputs=["cart_id"],
        outputs=["order_id"],
        preconditions={
            "Cart.exists": True,
            "Cart.item_count": 1
        },
        effects={
            "Order.exists": True
        },
        resources=["Database"],
        constraints=["Cart not empty"],
        cost={"time": 100, "money": 1},
        reliability=0.99,
        availability=1,
        mechanism="POST /orders"
    ),

    # =====================================================
    # 2. Make Payment
    # =====================================================

    Capability(
        name="MakePayment",
        capability_type="API",
        inputs=["order_id"],
        outputs=["payment_id"],
        preconditions={
            "Order.exists": True
        },
        effects={
            "Payment.status": "SUCCESS"
        },
        resources=["Payment Gateway"],
        constraints=["Valid payment"],
        cost={"time": 150, "money": 2},
        reliability=0.98,
        availability=1,
        mechanism="POST /payment"
    ),

    # =====================================================
    # 3. Send Notification
    # =====================================================

    Capability(
        name="SendNotification",
        capability_type="SERVICE",
        inputs=["payment_id"],
        outputs=["notification_id"],
        preconditions={
            "Payment.status": "SUCCESS"
        },
        effects={
            "Notification.sent": True
        },
        resources=["Email Server"],
        constraints=[],
        cost={"time": 50, "money": 0},
        reliability=0.97,
        availability=1,
        mechanism="Email Service"
    ),

    # =====================================================
    # 4. Cancel Cart
    # =====================================================

    Capability(
        name="CancelCart",
        capability_type="GUI",
        inputs=["cart_id"],
        outputs=[],
        preconditions={
            "Order.exists": False
        },
        effects={
            "Cart.exists": False
        },
        resources=["Database"],
        constraints=[],
        cost={"time": 20, "money": 0},
        reliability=0.99,
        availability=1,
        mechanism="Button Click"
    ),

    # =====================================================
    # 5. Create Order (API)
    # =====================================================

    Capability(
        name="CreateOrder_API",
        capability_type="API",
        inputs=["cart_id"],
        outputs=["order_id"],
        preconditions={
            "Cart.exists": True,
            "Cart.item_count": 1
        },
        effects={
            "Order.exists": True
        },
        resources=["Database"],
        constraints=[],
        cost={"time": 100, "money": 1},
        reliability=0.99,
        availability=1,
        mechanism="POST /orders"
    ),

    # =====================================================
    # 6. Create Order (GUI)
    # =====================================================

    Capability(
        name="CreateOrder_GUI",
        capability_type="GUI",
        inputs=["cart_id"],
        outputs=["order_id"],
        preconditions={
            "Cart.exists": True,
            "Cart.item_count": 1
        },
        effects={
            "Order.exists": True
        },
        resources=["Database"],
        constraints=[],
        cost={"time": 120, "money": 1},
        reliability=0.98,
        availability=1,
        mechanism="Button Click"
    ),

    # =====================================================
    # 7. Create Order (DATABASE)
    # =====================================================

    Capability(
        name="CreateOrder_DATABASE",
        capability_type="DATABASE",
        inputs=["cart_id"],
        outputs=["order_id"],
        preconditions={
            "Cart.exists": True,
            "Cart.item_count": 1
        },
        effects={
            "Order.exists": True
        },
        resources=["Database"],
        constraints=[],
        cost={"time": 80, "money": 1},
        reliability=0.995,
        availability=1,
        mechanism="Stored Procedure"
    ),

Capability(
    name="PlayMusic",
    capability_type="SERVICE",
    inputs=["song_name"],
    outputs=["music_stream"],
    preconditions={},
    effects={},
    resources=["Speaker"],
    constraints=[],
    cost={"time": 30, "money": 0},
    reliability=0.99,
    availability=1,
    mechanism="Music Service"
),

Capability(
    name="ChangeTheme",
    capability_type="GUI",
    inputs=["theme_name"],
    outputs=["theme_updated"],
    preconditions={},
    effects={},
    resources=[],
    constraints=[],
    cost={"time": 10, "money": 0},
    reliability=1.0,
    availability=1,
    mechanism="GUI Theme"
),

Capability(
    name="BackupLogs",
    capability_type="SERVICE",
    inputs=["log_file"],
    outputs=["backup_file"],
    preconditions={},
    effects={},
    resources=["Database"],
    constraints=[],
    cost={"time": 60, "money": 1},
    reliability=0.97,
    availability=1,
    mechanism="Backup Service"
),

Capability(
    name="FastPayment",
    capability_type="API",
    inputs=["order_id"],
    outputs=["payment_id"],
    preconditions={
        "Order.exists": True
    },
    effects={
        "Payment.status": "SUCCESS"
    },
    resources=["Payment Gateway"],
    constraints=[],
    cost={"time": 80, "money": 3},
    reliability=0.99,
    availability=1,
    mechanism="Fast Gateway"
),

Capability(
    name="SlowPayment",
    capability_type="API",
    inputs=["order_id"],
    outputs=["payment_id"],
    preconditions={
        "Order.exists": True
    },
    effects={
        "Payment.status": "SUCCESS"
    },
    resources=["Payment Gateway"],
    constraints=[],
    cost={"time": 250, "money": 1},
    reliability=0.85,
    availability=1,
    mechanism="Slow Gateway"
)

]