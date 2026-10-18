capabilities = [

    {
        "name": "CreateOrder",
        "type": "API",
        "inputs": ["cart_id"],
        "outputs": ["order_id"],
        "preconditions": {
            "Cart.exists": True,
            "Cart.item_count_positive": True
        },
        "effects": {
            "Order.exists": True,
            "Order.status": "CREATED"
        },
        "resources": [
            "DATABASE",
            "AUTHENTICATION"
        ],
        "cost": 0.01,
        "reliability": 0.99,
        "availability": 1
    },

    {
        "name": "MakePayment",
        "type": "API",
        "inputs": ["order_id", "amount"],
        "outputs": ["payment_id"],
        "preconditions": {
            "Order.exists": True
        },
        "effects": {
            "Payment.status": "SUCCESS"
        },
        "resources": [
            "PAYMENT_GATEWAY",
            "NETWORK"
        ],
        "cost": 0.05,
        "reliability": 0.98,
        "availability": 1
    },

    {
        "name": "SendNotification",
        "type": "EVENT",
        "inputs": ["order_id"],
        "outputs": ["notification_id"],
        "preconditions": {
            "Payment.status": "SUCCESS"
        },
        "effects": {
            "Notification.sent": True
        },
        "resources": [
            "NETWORK"
        ],
        "cost": 0.01,
        "reliability": 0.97,
        "availability": 1
    },

    {
        "name": "CancelCart",
        "type": "FUNCTION",
        "inputs": ["cart_id"],
        "outputs": [],
        "preconditions": {
            "Order.exists": False
        },
        "effects": {
            "Cart.cancelled": True
        },
        "resources": [
            "DATABASE"
        ],
        "cost": 0.01,
        "reliability": 0.99,
        "availability": 1
    },

    {
        "name": "UpdateUserProfile",
        "type": "DATABASE",
        "inputs": ["user_id"],
        "outputs": ["profile"],
        "preconditions": {
            "User.exists": True
        },
        "effects": {
            "User.profile_updated": True
        },
        "resources": [
            "DATABASE"
        ],
        "cost": 0.02,
        "reliability": 0.99,
        "availability": 1
    }
]