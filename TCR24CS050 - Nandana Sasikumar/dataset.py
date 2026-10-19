"""
dataset.py
==========
Experimental Dataset for Assignment 2 (Deliverable 3).

Formally specifies:
1. Application Domain (State Variables & Types)
2. Initial State S_I
3. Goal Specification G
4. Atomic Capabilities (C_1 to C_7):
   - C_1: CreateOrder (API)
   - C_2: MakePayment (API)
   - C_3: CancelCart (API) [Incompatible with C_1's effect]
   - C_4: MakePaymentDB (DATABASE) [Alternative implementation of C_2]
   - C_5: MakePaymentGUI (GUI) [Alternative implementation of C_2]
   - C_6: SendNotification (SERVICE) [Composes with C_2 to finish purchase]
   - C_7: BrowseProducts (API) [Irrelevant to purchase goal]
"""

from capability_embedding import Domain, State, Goal, Capability, QoS

# 1. State Variables for E-Commerce Shopping & Order Domain
ECOMMERCE_VARIABLES = [
    "User.authenticated",
    "User.role_customer",
    "Cart.exists",
    "Cart.item_count_positive",
    "Inventory.available",
    "Order.exists",
    "Payment.status_success",
    "Notification.sent",
]

# Instantiate Domain
ecommerce_domain = Domain(variables=ECOMMERCE_VARIABLES)

# 2. Initial State S_I (from Section 3.1 of PDF)
initial_state = State(
    name="InitialState",
    values={
        "User.authenticated": True,
        "User.role_customer": True,
        "Cart.exists": True,
        "Cart.item_count_positive": True,
        "Inventory.available": True,
        "Order.exists": False,
        "Payment.status_success": False,
        "Notification.sent": False,
    }
)

# 3. Goal Specification G (from Section 3.2 of PDF)
goal_complete_purchase = Goal(
    name="CompletePurchaseGoal",
    target_conditions={
        "Order.exists": True,
        "Payment.status_success": True,
        "Notification.sent": True,
    }
)

# 4. Atomic Capabilities

# C_1: CreateOrder
c1_create_order = Capability(
    name="CreateOrder",
    cap_type="API",
    preconditions={
        "Cart.exists": True,
        "Cart.item_count_positive": True,
        "Inventory.available": True,
    },
    effects={
        "Order.exists": True,
    },
    inputs={"cart_id": "UUID"},
    outputs={"order_id": "UUID"},
    qos=QoS(execution_time_ms=120.0, monetary_cost=0.010, reliability=0.99, availability=1.0),
    mechanism={"method": "POST", "endpoint": "/orders"}
)

# C_2: MakePayment (API)
c2_make_payment_api = Capability(
    name="MakePayment_API",
    cap_type="API",
    preconditions={
        "Order.exists": True,
    },
    effects={
        "Payment.status_success": True,
    },
    inputs={"order_id": "UUID", "payment_token": "Token"},
    outputs={"receipt_id": "UUID"},
    qos=QoS(execution_time_ms=250.0, monetary_cost=0.050, reliability=0.98, availability=1.0),
    mechanism={"method": "POST", "endpoint": "/payments"}
)

# C_3: CancelCart (Incompatible with CreateOrder -> requires Order.exists = False)
c3_cancel_cart = Capability(
    name="CancelCart",
    cap_type="API",
    preconditions={
        "Order.exists": False,
        "Cart.exists": True,
    },
    effects={
        "Cart.exists": False,
    },
    inputs={"cart_id": "UUID"},
    outputs={"cancellation_status": "bool"},
    qos=QoS(execution_time_ms=80.0, monetary_cost=0.005, reliability=0.99, availability=1.0),
    mechanism={"method": "DELETE", "endpoint": "/cart"}
)

# C_4: MakePaymentDB (Database Alternative to C_2)
c4_make_payment_db = Capability(
    name="MakePayment_DB",
    cap_type="DATABASE",
    preconditions={
        "Order.exists": True,
    },
    effects={
        "Payment.status_success": True,
    },
    inputs={"order_id": "UUID"},
    outputs={"row_id": "int"},
    qos=QoS(execution_time_ms=35.0, monetary_cost=0.002, reliability=0.999, availability=1.0),
    mechanism={"operation": "INSERT", "table": "payments"}
)

# C_5: MakePaymentGUI (GUI Alternative to C_2)
c5_make_payment_gui = Capability(
    name="MakePayment_GUI",
    cap_type="GUI",
    preconditions={
        "Order.exists": True,
    },
    effects={
        "Payment.status_success": True,
    },
    inputs={"button_click": "Event"},
    outputs={"confirmation_dialog": "str"},
    qos=QoS(execution_time_ms=600.0, monetary_cost=0.000, reliability=0.95, availability=1.0),
    mechanism={"action": "CLICK", "component": "pay_now_button"}
)

# C_6: SendNotification (Chains after payment)
c6_send_notification = Capability(
    name="SendNotification",
    cap_type="SERVICE",
    preconditions={
        "Payment.status_success": True,
    },
    effects={
        "Notification.sent": True,
    },
    inputs={"order_id": "UUID", "recipient_email": "str"},
    outputs={"message_id": "str"},
    qos=QoS(execution_time_ms=140.0, monetary_cost=0.003, reliability=0.97, availability=1.0),
    mechanism={"handler": "EmailDispatcher"}
)

# C_7: BrowseProducts (Irrelevant to purchase goal)
c7_browse_products = Capability(
    name="BrowseProducts",
    cap_type="API",
    preconditions={
        "User.authenticated": True,
    },
    effects={
        "Cart.exists": True,  # Already true in initial state
    },
    inputs={"query": "str"},
    outputs={"catalog_items": "list"},
    qos=QoS(execution_time_ms=90.0, monetary_cost=0.001, reliability=0.995, availability=1.0),
    mechanism={"method": "GET", "endpoint": "/catalog/search"}
)

ALL_CAPABILITIES = [
    c1_create_order,
    c2_make_payment_api,
    c3_cancel_cart,
    c4_make_payment_db,
    c5_make_payment_gui,
    c6_send_notification,
    c7_browse_products,
]
