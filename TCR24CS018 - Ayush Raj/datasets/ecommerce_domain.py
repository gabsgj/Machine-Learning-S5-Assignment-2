"""
E-Commerce Order-to-Fulfillment Domain Dataset.
Matches and expands the formal application example from Assignment 2 specification.
"""

from capembed.core import (
    Capability,
    CapabilityType,
    InputSpec,
    OutputSpec,
    OperationalProfile,
    ExecutionMechanism,
    State,
    Goal,
    DomainSchema,
)


def get_ecommerce_domain():
    state_variables = [
        "User.authenticated",
        "User.role",
        "Cart.exists",
        "Cart.item_count",
        "Cart.locked",
        "Order.exists",
        "Order.status",
        "Payment.status",
        "Inventory.available",
        "Inventory.reserved",
        "Shipping.scheduled",
        "Notification.sent",
        "User.profile_updated",
        "Review.submitted",
    ]

    resources = [
        "Database",
        "PaymentGateway",
        "Network",
        "MessageQueue",
        "AuthenticationToken",
        "WarehouseRobotics",
        "ExternalEmailService",
    ]

    schema = DomainSchema(
        name="EcommerceDomain",
        state_variables=state_variables,
        data_types=["UUID", "STRING", "INTEGER", "DECIMAL", "BOOLEAN"],
        data_names=[
            "cart_id", "order_id", "payment_receipt", "user_id",
            "amount", "reservation_id", "tracking_num", "notification_id",
            "review_id", "profile_data"
        ],
        resource_names=resources,
    )

    initial_state = State(variables={
        "User.authenticated": True,
        "User.role": "CUSTOMER",
        "Cart.exists": True,
        "Cart.item_count": 3,
        "Cart.locked": False,
        "Order.exists": False,
        "Order.status": "NOT_STARTED",
        "Payment.status": "NOT_STARTED",
        "Inventory.available": True,
        "Inventory.reserved": False,
        "Shipping.scheduled": False,
        "Notification.sent": False,
        "User.profile_updated": False,
        "Review.submitted": False,
    })

    goal = Goal(
        name="OrderFulfillmentGoal",
        conditions={
            "Order.exists": True,
            "Payment.status": "SUCCESS",
            "Inventory.reserved": True,
            "Notification.sent": True,
        }
    )

    # Core capabilities
    c1_create_order = Capability(
        name="CreateOrder",
        cap_type=CapabilityType.API,
        inputs=[
            InputSpec(name="cart_id", data_type="UUID", domain="valid UUIDs", required=True),
        ],
        outputs=[
            OutputSpec(name="order_id", data_type="UUID", domain="valid UUIDs"),
            OutputSpec(name="amount", data_type="DECIMAL", domain="positive real"),
        ],
        preconditions={
            "User.authenticated": True,
            "Cart.exists": True,
        },
        effects={
            "Order.exists": True,
            "Order.status": "CREATED",
            "Cart.locked": True,
        },
        constraints=["quantity > 0"],
        resources={"Database", "Network"},
        operational_profile=OperationalProfile(
            execution_time_ms=85.0,
            monetary_cost=0.01,
            resource_cost=1.5,
            risk=0.02,
            reliability=0.995,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.API,
            properties={"method": "POST", "endpoint": "/orders"},
        ),
    )

    c2_make_payment = Capability(
        name="MakePayment",
        cap_type=CapabilityType.SERVICE,
        inputs=[
            InputSpec(name="order_id", data_type="UUID", domain="valid UUIDs", required=True),
            InputSpec(name="amount", data_type="DECIMAL", domain="positive real", required=True),
        ],
        outputs=[
            OutputSpec(name="payment_receipt", data_type="STRING", domain="valid receipt tokens"),
        ],
        preconditions={
            "Order.exists": True,
        },
        effects={
            "Payment.status": "SUCCESS",
        },
        constraints=["amount <= transaction_limit"],
        resources={"PaymentGateway", "Network"},
        operational_profile=OperationalProfile(
            execution_time_ms=250.0,
            monetary_cost=0.30,
            resource_cost=2.0,
            risk=0.04,
            reliability=0.99,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.SERVICE,
            properties={"method": "POST", "endpoint": "/payments/charge"},
        ),
    )

    c3_cancel_cart = Capability(
        name="CancelCart",
        cap_type=CapabilityType.API,
        inputs=[
            InputSpec(name="cart_id", data_type="UUID", domain="valid UUIDs", required=True),
        ],
        outputs=[],
        preconditions={
            "Order.exists": False,
            "Cart.exists": True,
        },
        effects={
            "Cart.exists": False,
            "Cart.locked": False,
        },
        constraints=[],
        resources={"Database"},
        operational_profile=OperationalProfile(
            execution_time_ms=40.0,
            monetary_cost=0.0,
            resource_cost=1.0,
            risk=0.01,
            reliability=0.999,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.API,
            properties={"method": "DELETE", "endpoint": "/cart"},
        ),
    )

    c4_reserve_inventory = Capability(
        name="ReserveInventory",
        cap_type=CapabilityType.SERVICE,
        inputs=[
            InputSpec(name="order_id", data_type="UUID", domain="valid UUIDs", required=True),
        ],
        outputs=[
            OutputSpec(name="reservation_id", data_type="UUID", domain="valid UUIDs"),
        ],
        preconditions={
            "Order.exists": True,
            "Inventory.available": True,
        },
        effects={
            "Inventory.reserved": True,
        },
        constraints=["quantity <= inventory_available"],
        resources={"Database"},
        operational_profile=OperationalProfile(
            execution_time_ms=60.0,
            monetary_cost=0.005,
            resource_cost=1.0,
            risk=0.01,
            reliability=0.998,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.SERVICE,
            properties={"method": "POST", "endpoint": "/inventory/reserve"},
        ),
    )

    c5_send_notification = Capability(
        name="SendNotification",
        cap_type=CapabilityType.EVENT,
        inputs=[
            InputSpec(name="order_id", data_type="UUID", domain="valid UUIDs", required=True),
        ],
        outputs=[
            OutputSpec(name="notification_id", data_type="UUID", domain="valid UUIDs"),
        ],
        preconditions={
            "Payment.status": "SUCCESS",
        },
        effects={
            "Notification.sent": True,
        },
        constraints=[],
        resources={"ExternalEmailService", "Network"},
        operational_profile=OperationalProfile(
            execution_time_ms=120.0,
            monetary_cost=0.002,
            resource_cost=0.5,
            risk=0.01,
            reliability=0.985,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.EVENT,
            properties={"trigger": "OrderPaid", "handler": "SendEmailNotification"},
        ),
    )

    # Alternative implementations of CreateOrder for Experiment 3
    c1_api = Capability(
        name="CreateOrder_API",
        cap_type=CapabilityType.API,
        inputs=[InputSpec(name="cart_id", data_type="UUID", domain="valid UUIDs", required=True)],
        outputs=[
            OutputSpec(name="order_id", data_type="UUID", domain="valid UUIDs"),
            OutputSpec(name="amount", data_type="DECIMAL", domain="positive real"),
        ],
        preconditions={"User.authenticated": True, "Cart.exists": True},
        effects={"Order.exists": True, "Order.status": "CREATED", "Cart.locked": True},
        resources={"Database", "Network"},
        operational_profile=OperationalProfile(
            execution_time_ms=85.0, monetary_cost=0.01, resource_cost=1.5, risk=0.02, reliability=0.995, availability=1.0
        ),
        mechanism=ExecutionMechanism(CapabilityType.API, {"method": "POST", "endpoint": "/orders"}),
    )

    c1_db = Capability(
        name="CreateOrder_DB",
        cap_type=CapabilityType.DATABASE,
        inputs=[InputSpec(name="cart_id", data_type="UUID", domain="valid UUIDs", required=True)],
        outputs=[
            OutputSpec(name="order_id", data_type="UUID", domain="valid UUIDs"),
            OutputSpec(name="amount", data_type="DECIMAL", domain="positive real"),
        ],
        preconditions={"User.authenticated": True, "Cart.exists": True},
        effects={"Order.exists": True, "Order.status": "CREATED", "Cart.locked": True},
        resources={"Database"},
        operational_profile=OperationalProfile(
            execution_time_ms=15.0, monetary_cost=0.001, resource_cost=2.0, risk=0.01, reliability=0.999, availability=1.0
        ),
        mechanism=ExecutionMechanism(CapabilityType.DATABASE, {"operation": "INSERT", "table": "orders"}),
    )

    c1_gui = Capability(
        name="CreateOrder_GUI",
        cap_type=CapabilityType.GUI,
        inputs=[InputSpec(name="cart_id", data_type="UUID", domain="valid UUIDs", required=True)],
        outputs=[
            OutputSpec(name="order_id", data_type="UUID", domain="valid UUIDs"),
            OutputSpec(name="amount", data_type="DECIMAL", domain="positive real"),
        ],
        preconditions={"User.authenticated": True, "Cart.exists": True},
        effects={"Order.exists": True, "Order.status": "CREATED", "Cart.locked": True},
        resources={"Network"},
        operational_profile=OperationalProfile(
            execution_time_ms=650.0, monetary_cost=0.00, resource_cost=0.5, risk=0.08, reliability=0.96, availability=0.95
        ),
        mechanism=ExecutionMechanism(CapabilityType.GUI, {"action": "CLICK", "component": "submit_button"}),
    )

    # Irrelevant capabilities for Experiment 4
    irr1_profile = Capability(
        name="UpdateUserProfile",
        cap_type=CapabilityType.API,
        inputs=[InputSpec(name="profile_data", data_type="STRING", domain="text", required=True)],
        outputs=[],
        preconditions={"User.authenticated": True},
        effects={"User.profile_updated": True},
        resources={"Database"},
        operational_profile=OperationalProfile(execution_time_ms=50.0, monetary_cost=0.0, reliability=0.99),
        mechanism=ExecutionMechanism(CapabilityType.API, {"method": "PUT", "endpoint": "/users/profile"}),
    )

    irr2_review = Capability(
        name="SubmitProductReview",
        cap_type=CapabilityType.API,
        inputs=[InputSpec(name="review_id", data_type="UUID", domain="valid UUIDs", required=True)],
        outputs=[],
        preconditions={"User.authenticated": True},
        effects={"Review.submitted": True},
        resources={"Database"},
        operational_profile=OperationalProfile(execution_time_ms=70.0, monetary_cost=0.0, reliability=0.98),
        mechanism=ExecutionMechanism(CapabilityType.API, {"method": "POST", "endpoint": "/reviews"}),
    )

    all_capabilities = [
        c1_create_order,
        c2_make_payment,
        c3_cancel_cart,
        c4_reserve_inventory,
        c5_send_notification,
        c1_api,
        c1_db,
        c1_gui,
        irr1_profile,
        irr2_review,
    ]

    return {
        "schema": schema,
        "initial_state": initial_state,
        "goal": goal,
        "capabilities": all_capabilities,
        "c1": c1_create_order,
        "c2": c2_make_payment,
        "c3": c3_cancel_cart,
        "c4": c4_reserve_inventory,
        "c5": c5_send_notification,
        "alternatives": [c1_api, c1_db, c1_gui],
        "irrelevant": [irr1_profile, irr2_review],
    }
