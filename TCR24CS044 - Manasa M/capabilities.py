class Capability:

    def __init__(
        self,
        name,
        capability_type,
        inputs,
        outputs,
        preconditions,
        effects,
        constraints=None,
        resources=None,
        cost=0.0,
        reliability=1.0,
        availability=1
    ):
        self.name = name
        self.capability_type = capability_type
        self.inputs = inputs
        self.outputs = outputs
        self.preconditions = preconditions
        self.effects = effects
        self.constraints = constraints or {}
        self.resources = resources or []
        self.cost = cost
        self.reliability = reliability
        self.availability = availability

    def __repr__(self):
        return self.name


def create_capabilities():

    create_order = Capability(
        name="CreateOrder",
        capability_type="API",
        inputs={
            "cart_id": "UUID"
        },
        outputs={
            "order_id": "UUID"
        },
        preconditions={
            "Cart.exists": True,
            "Cart.item_count_positive": True,
            "Inventory.available": True
        },
        effects={
            "Order.exists": True,
            "Order.status": "CREATED"
        },
        constraints={
            "quantity_positive": True
        },
        resources=[
            "Database",
            "Network"
        ],
        cost=0.01,
        reliability=0.99,
        availability=1
    )

    make_payment = Capability(
        name="MakePayment",
        capability_type="API",
        inputs={
            "order_id": "UUID",
            "payment_details": "PaymentInfo"
        },
        outputs={
            "payment_id": "UUID"
        },
        preconditions={
            "Order.exists": True,
            "Order.status": "CREATED"
        },
        effects={
            "Payment.status": "SUCCESS"
        },
        constraints={
            "payment_amount_valid": True
        },
        resources=[
            "PaymentGateway",
            "Network"
        ],
        cost=0.05,
        reliability=0.97,
        availability=1
    )

    send_notification = Capability(
        name="SendNotification",
        capability_type="SERVICE",
        inputs={
            "order_id": "UUID"
        },
        outputs={
            "notification_id": "UUID"
        },
        preconditions={
            "Payment.status": "SUCCESS"
        },
        effects={
            "Notification.sent": True
        },
        constraints={},
        resources=[
            "NotificationService",
            "Network"
        ],
        cost=0.02,
        reliability=0.98,
        availability=1
    )

    cancel_cart = Capability(
        name="CancelCart",
        capability_type="FUNCTION",
        inputs={
            "cart_id": "UUID"
        },
        outputs={
            "cancel_status": "BOOLEAN"
        },
        preconditions={
            "Order.exists": False
        },
        effects={
            "Cart.cancelled": True
        },
        constraints={},
        resources=[
            "Database"
        ],
        cost=0.005,
        reliability=0.99,
        availability=1
    )

    update_profile = Capability(
        name="UpdateProfile",
        capability_type="DATABASE",
        inputs={
            "user_id": "UUID"
        },
        outputs={
            "profile_status": "BOOLEAN"
        },
        preconditions={
            "User.authenticated": True
        },
        effects={
            "User.profile_updated": True
        },
        constraints={},
        resources=[
            "Database"
        ],
        cost=0.01,
        reliability=0.99,
        availability=1
    )

    search_product = Capability(
        name="SearchProduct",
        capability_type="API",
        inputs={
            "keyword": "STRING"
        },
        outputs={
            "product_list": "LIST"
        },
        preconditions={},
        effects={
            "Product.search_completed": True
        },
        constraints={},
        resources=[
            "Database",
            "Network"
        ],
        cost=0.01,
        reliability=0.98,
        availability=1
    )

    return [
        create_order,
        make_payment,
        send_notification,
        cancel_cart,
        update_profile,
        search_product
    ]