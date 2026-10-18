"""
Experimental dataset for Assignment 2.

Builds the e-commerce domain from the assignment PDF (CreateOrder,
MakePayment, CancelCart, SendNotification) plus the extra capabilities
needed to run all five required experiments:

  1. Capability compatibility   -> C1=CreateOrder, C2=MakePayment, C3=CancelCart
  2. Capability composition      -> CreateOrder -> MakePayment -> SendNotification
  3. Alternative implementations -> CreateOrder_API / _DB / _GUI
  4. Irrelevant capabilities     -> GetWeatherForecast, LogAnalyticsEvent
  5. Operational attributes      -> MakePayment_Degraded (lower reliability/higher risk)
"""

from capability_model import Capability, IOSpec, State, Goal


def build_capabilities():
    caps = {}

    caps["CreateOrder"] = Capability(
        id="CreateOrder",
        type="API",
        inputs=(IOSpec("cart_id", "UUID", "valid UUIDs", True),),
        outputs=(IOSpec("order_id", "UUID", "valid UUIDs"),),
        preconditions=(
            "Cart.exists=True",
            "Cart.item_count>0",
            "User.authenticated=True",
        ),
        effects={"Order.exists": True, "Order.status": "CREATED", "Cart.locked": True},
        constraints=("quantity>0",),
        resources=("Database", "Authentication token"),
        cost={"time": 100.0, "money": 0.0, "resource": 2.0, "risk": 0.05, "energy": 1.0},
        reliability=0.99,
        availability=1.0,
        mechanism={"method": "POST", "endpoint": "/orders"},
    )

    caps["MakePayment"] = Capability(
        id="MakePayment",
        type="API",
        inputs=(
            IOSpec("order_id", "UUID", "valid UUIDs", True),
            IOSpec("payment_amount", "decimal", ">0", True),
        ),
        outputs=(IOSpec("payment_id", "UUID", "valid UUIDs"),),
        preconditions=("Order.exists=True",),
        effects={"Payment.status": "SUCCESS", "Order.status": "PAID"},
        constraints=("payment_amount<=transaction_limit",),
        resources=("Payment gateway", "Network"),
        cost={"time": 250.0, "money": 0.01, "resource": 1.0, "risk": 0.10, "energy": 1.5},
        reliability=0.97,
        availability=1.0,
        mechanism={"method": "POST", "endpoint": "/payments"},
    )

    caps["CancelCart"] = Capability(
        id="CancelCart",
        type="API",
        inputs=(IOSpec("cart_id", "UUID", "valid UUIDs", True),),
        outputs=(),
        preconditions=("Order.exists=False",),
        effects={"Cart.exists": False},
        constraints=(),
        resources=("Database",),
        cost={"time": 50.0, "money": 0.0, "resource": 0.5, "risk": 0.02, "energy": 0.5},
        reliability=0.995,
        availability=1.0,
        mechanism={"method": "DELETE", "endpoint": "/cart"},
    )

    caps["SendNotification"] = Capability(
        id="SendNotification",
        type="EVENT",
        inputs=(IOSpec("order_id", "UUID", "valid UUIDs", True),),
        outputs=(IOSpec("notification_id", "UUID", "valid UUIDs"),),
        preconditions=("Payment.status=SUCCESS",),
        effects={"Notification.sent": True},
        constraints=(),
        resources=("Network",),
        cost={"time": 30.0, "money": 0.0, "resource": 0.2, "risk": 0.01, "energy": 0.2},
        reliability=0.995,
        availability=1.0,
        mechanism={"trigger": "OrderCreated", "handler": "SendNotification"},
    )

    # --- Experiment 3: alternative implementations of CreateOrder ----------
    caps["CreateOrder_API"] = caps["CreateOrder"]  # the original is already API-based

    caps["CreateOrder_DB"] = Capability(
        id="CreateOrder_DB",
        type="DATABASE",
        inputs=(IOSpec("cart_id", "UUID", "valid UUIDs", True),),
        outputs=(IOSpec("order_id", "UUID", "valid UUIDs"),),
        preconditions=(
            "Cart.exists=True",
            "Cart.item_count>0",
            "User.authenticated=True",
        ),
        effects={"Order.exists": True, "Order.status": "CREATED", "Cart.locked": True},
        constraints=("quantity>0",),
        resources=("Database",),
        cost={"time": 40.0, "money": 0.0, "resource": 1.0, "risk": 0.03, "energy": 0.6},
        reliability=0.995,
        availability=1.0,
        mechanism={"operation": "INSERT", "table": "orders"},
    )

    caps["CreateOrder_GUI"] = Capability(
        id="CreateOrder_GUI",
        type="GUI",
        inputs=(IOSpec("cart_id", "UUID", "valid UUIDs", True),),
        outputs=(IOSpec("order_id", "UUID", "valid UUIDs"),),
        preconditions=(
            "Cart.exists=True",
            "Cart.item_count>0",
            "User.authenticated=True",
        ),
        effects={"Order.exists": True, "Order.status": "CREATED", "Cart.locked": True},
        constraints=("quantity>0",),
        resources=("Database", "Authentication token"),
        cost={"time": 1200.0, "money": 0.0, "resource": 0.5, "risk": 0.08, "energy": 0.3},
        reliability=0.98,
        availability=1.0,
        mechanism={"action": "CLICK", "component": "checkout_button"},
    )

    # --- Experiment 4: irrelevant capabilities ------------------------------
    caps["GetWeatherForecast"] = Capability(
        id="GetWeatherForecast",
        type="API",
        inputs=(IOSpec("city", "string", "valid city names", True),),
        outputs=(IOSpec("forecast", "json", "weather payload"),),
        preconditions=(),
        effects={"Weather.lastFetched": True},
        constraints=(),
        resources=("Network",),
        cost={"time": 80.0, "money": 0.0, "resource": 0.3, "risk": 0.02, "energy": 0.2},
        reliability=0.99,
        availability=1.0,
        mechanism={"method": "GET", "endpoint": "/weather"},
    )

    caps["LogAnalyticsEvent"] = Capability(
        id="LogAnalyticsEvent",
        type="EVENT",
        inputs=(IOSpec("event_name", "string", "any", True),),
        outputs=(),
        preconditions=(),
        effects={"Analytics.logged": True},
        constraints=(),
        resources=("Network",),
        cost={"time": 10.0, "money": 0.0, "resource": 0.1, "risk": 0.01, "energy": 0.05},
        reliability=0.999,
        availability=1.0,
        mechanism={"trigger": "AnyEvent", "handler": "LogAnalyticsEvent"},
    )

    # --- Experiment 5: operational attributes -------------------------------
    caps["MakePayment_Degraded"] = Capability(
        id="MakePayment_Degraded",
        type="API",
        inputs=caps["MakePayment"].inputs,
        outputs=caps["MakePayment"].outputs,
        preconditions=caps["MakePayment"].preconditions,
        effects=dict(caps["MakePayment"].effects),
        constraints=caps["MakePayment"].constraints,
        resources=caps["MakePayment"].resources,
        cost={"time": 250.0, "money": 0.01, "resource": 1.0, "risk": 0.45, "energy": 1.5},
        reliability=0.55,
        availability=1.0,
        # Deliberately identical mechanism to MakePayment: this variant
        # differs only in cost/reliability/risk (operational attributes),
        # not in implementation, so nothing here should leak into the
        # functional block.
        mechanism={"method": "POST", "endpoint": "/payments"},
    )

    return caps


def build_states():
    initial = State({
        "User.authenticated": True,
        "User.role": "CUSTOMER",
        "Cart.exists": True,
        "Cart.item_count": 3,
        "Order.exists": False,
        "Payment.status": "NOT_STARTED",
        "Inventory.available": True,
        "Notification.sent": False,
    })
    return {"initial": initial}


def build_goals():
    purchase_complete = Goal.from_equalities({
        "Order.exists": True,
        "Payment.status": "SUCCESS",
        "Notification.sent": True,
    })
    return {"purchase_complete": purchase_complete}
