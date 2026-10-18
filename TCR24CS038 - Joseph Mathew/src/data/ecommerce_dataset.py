"""Formally Specified E-Commerce Order Fulfillment Domain.

Corresponds to Deliverable 3 and Sections 3, 4, 5, 7 of PCCST503 Assignment 2.
Includes:
- Initial state S_I
- Goal specification G
- Atomic capabilities (C1..C12)
- Alternative implementations (API vs Database vs GUI)
- Irrelevant capabilities (Weather, Log compression)
- Operational attributes and constraints
"""

from __future__ import annotations
import json
from typing import Dict, Any, List, Tuple

from src.models.state import State, Goal, Condition, Effect
from src.models.capability import (
    Capability, CapabilityType, ExecutionMechanism, DataParameter
)
from src.models.operational import (
    CostProfile, ResourceRequirement, Constraint
)
from src.embedding.schema import EmbeddingSchema


def build_ecommerce_domain() -> Dict[str, Any]:
    # 1. State Variables
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
        "Notification.sent",
        "Shipment.dispatched",
        "System.log_compressed",
        "External.weather_cached"
    ]

    data_types = [
        "cart_id",
        "order_id",
        "payment_token",
        "receipt_id",
        "tracking_number",
        "notification_payload",
        "weather_data",
        "log_archive"
    ]

    resource_types = [
        "Database",
        "PaymentGateway",
        "EmailService",
        "InventoryWarehouse",
        "Network",
        "DiskIO"
    ]

    capability_types = [
        "API",
        "DATABASE",
        "GUI",
        "EVENT",
        "FUNCTION",
        "FILE",
        "COMPUTATION",
        "MESSAGE",
        "SERVICE"
    ]

    schema = EmbeddingSchema(
        state_variables=state_variables,
        data_types=data_types,
        resource_types=resource_types,
        capability_types=capability_types,
        latent_dim=16
    )

    # 2. Initial State S_I (PDF Page 3)
    initial_state = State(
        name="S_Initial",
        variables={
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
            "Notification.sent": False,
            "Shipment.dispatched": False,
            "System.log_compressed": False,
            "External.weather_cached": False
        }
    )

    # 3. Goal Specification G (PDF Page 4)
    goal = Goal(
        name="OrderFulfillmentGoal",
        conditions=[
            Condition(variable="Order.exists", operator="==", value=True),
            Condition(variable="Payment.status", operator="==", value="SUCCESS"),
            Condition(variable="Notification.sent", operator="==", value=True)
        ]
    )

    # 4. Atomic Capabilities
    # C1: CreateOrder (PDF Section 7 Exp 1)
    c1_create_order = Capability(
        name="CreateOrder",
        capability_type=CapabilityType.API,
        inputs=[
            DataParameter(name="cart_id", data_type="cart_id", domain="UUID", required=True)
        ],
        outputs=[
            DataParameter(name="order_id", data_type="order_id", domain="UUID")
        ],
        preconditions=[
            Condition(variable="Cart.exists", operator="==", value=True),
            Condition(variable="Inventory.available", operator="==", value=True)
        ],
        effects=[
            Effect(variable="Order.exists", action="set", value=True),
            Effect(variable="Order.status", action="set", value="CREATED"),
            Effect(variable="Cart.locked", action="set", value=True)
        ],
        constraints=[
            Constraint(name="cart_not_empty", expression="Cart.item_count > 0")
        ],
        resources=[
            ResourceRequirement(name="Database", amount=1.0),
            ResourceRequirement(name="Network", amount=1.0)
        ],
        cost=CostProfile(execution_time_ms=120.0, monetary_cost=0.01, resource_units=2.0, risk=0.01, energy_joules=15.0),
        reliability=0.99,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(
            type=CapabilityType.API,
            details={"method": "POST", "endpoint": "/orders"}
        )
    )

    # C2: MakePayment (PDF Section 7 Exp 1)
    c2_make_payment = Capability(
        name="MakePayment",
        capability_type=CapabilityType.SERVICE,
        inputs=[
            DataParameter(name="order_id", data_type="order_id", domain="UUID", required=True)
        ],
        outputs=[
            DataParameter(name="payment_token", data_type="payment_token", domain="Token")
        ],
        preconditions=[
            Condition(variable="Order.exists", operator="==", value=True),
            Condition(variable="Order.status", operator="==", value="CREATED")
        ],
        effects=[
            Effect(variable="Payment.status", action="set", value="SUCCESS"),
            Effect(variable="Order.status", action="set", value="PAID")
        ],
        constraints=[
            Constraint(name="valid_limit", expression="payment_amount <= transaction_limit")
        ],
        resources=[
            ResourceRequirement(name="PaymentGateway", amount=1.0),
            ResourceRequirement(name="Network", amount=1.0)
        ],
        cost=CostProfile(execution_time_ms=350.0, monetary_cost=0.15, resource_units=3.0, risk=0.02, energy_joules=35.0),
        reliability=0.98,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(
            type=CapabilityType.SERVICE,
            details={"gateway": "StripeGateway", "mode": "synchronous"}
        )
    )

    # C3: CancelCart (Incompatible with CreateOrder in Section 7 Exp 1)
    c3_cancel_cart = Capability(
        name="CancelCart",
        capability_type=CapabilityType.API,
        inputs=[
            DataParameter(name="cart_id", data_type="cart_id", domain="UUID", required=True)
        ],
        outputs=[],
        preconditions=[
            Condition(variable="Order.exists", operator="==", value=False),
            Condition(variable="Cart.locked", operator="==", value=False)
        ],
        effects=[
            Effect(variable="Cart.exists", action="set", value=False),
            Effect(variable="Cart.item_count", action="set", value=0)
        ],
        resources=[
            ResourceRequirement(name="Database", amount=1.0)
        ],
        cost=CostProfile(execution_time_ms=50.0, monetary_cost=0.0, resource_units=1.0, risk=0.005, energy_joules=5.0),
        reliability=0.999,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(
            type=CapabilityType.API,
            details={"method": "DELETE", "endpoint": "/cart"}
        )
    )

    # C4: SendNotification (Completes sequence C1 -> C2 -> C4)
    c4_send_notification = Capability(
        name="SendNotification",
        capability_type=CapabilityType.EVENT,
        inputs=[
            DataParameter(name="payment_token", data_type="payment_token", domain="Token", required=True)
        ],
        outputs=[
            DataParameter(name="receipt_id", data_type="receipt_id", domain="UUID")
        ],
        preconditions=[
            Condition(variable="Payment.status", operator="==", value="SUCCESS")
        ],
        effects=[
            Effect(variable="Notification.sent", action="set", value=True)
        ],
        resources=[
            ResourceRequirement(name="EmailService", amount=1.0),
            ResourceRequirement(name="Network", amount=1.0)
        ],
        cost=CostProfile(execution_time_ms=90.0, monetary_cost=0.005, resource_units=1.0, risk=0.01, energy_joules=10.0),
        reliability=0.995,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(
            type=CapabilityType.EVENT,
            details={"trigger": "PaymentSuccess", "handler": "SendEmailReceipt"}
        )
    )

    # C5: ReserveInventory (Optional pipeline step)
    c5_reserve_inventory = Capability(
        name="ReserveInventory",
        capability_type=CapabilityType.FUNCTION,
        inputs=[
            DataParameter(name="cart_id", data_type="cart_id", domain="UUID", required=True)
        ],
        outputs=[],
        preconditions=[
            Condition(variable="Inventory.available", operator="==", value=True)
        ],
        effects=[
            Effect(variable="Inventory.reserved", action="set", value=True)
        ],
        resources=[
            ResourceRequirement(name="InventoryWarehouse", amount=1.0)
        ],
        cost=CostProfile(execution_time_ms=80.0, monetary_cost=0.002, resource_units=1.5, risk=0.005, energy_joules=8.0),
        reliability=0.99,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(
            type=CapabilityType.FUNCTION,
            details={"fn": "warehouse.reserve_stock"}
        )
    )

    # 5. Alternative Implementations of CreateOrder (Section 7 Exp 3)
    # C1_API: already c1_create_order
    # C1_DB: Direct database insert
    c1_db = Capability(
        name="CreateOrder_Database",
        capability_type=CapabilityType.DATABASE,
        inputs=[
            DataParameter(name="cart_id", data_type="cart_id", domain="UUID", required=True)
        ],
        outputs=[
            DataParameter(name="order_id", data_type="order_id", domain="UUID")
        ],
        preconditions=[
            Condition(variable="Cart.exists", operator="==", value=True),
            Condition(variable="Inventory.available", operator="==", value=True)
        ],
        effects=[
            Effect(variable="Order.exists", action="set", value=True),
            Effect(variable="Order.status", action="set", value="CREATED"),
            Effect(variable="Cart.locked", action="set", value=True)
        ],
        resources=[
            ResourceRequirement(name="Database", amount=2.0)
        ],
        cost=CostProfile(execution_time_ms=45.0, monetary_cost=0.001, resource_units=1.0, risk=0.005, energy_joules=5.0),
        reliability=0.998,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(
            type=CapabilityType.DATABASE,
            details={"operation": "INSERT", "table": "orders"}
        )
    )

    # C1_GUI: User frontend click
    c1_gui = Capability(
        name="CreateOrder_GUI",
        capability_type=CapabilityType.GUI,
        inputs=[
            DataParameter(name="cart_id", data_type="cart_id", domain="UUID", required=True)
        ],
        outputs=[
            DataParameter(name="order_id", data_type="order_id", domain="UUID")
        ],
        preconditions=[
            Condition(variable="Cart.exists", operator="==", value=True),
            Condition(variable="Inventory.available", operator="==", value=True)
        ],
        effects=[
            Effect(variable="Order.exists", action="set", value=True),
            Effect(variable="Order.status", action="set", value="CREATED"),
            Effect(variable="Cart.locked", action="set", value=True)
        ],
        resources=[
            ResourceRequirement(name="Network", amount=1.0)
        ],
        cost=CostProfile(execution_time_ms=650.0, monetary_cost=0.0, resource_units=1.0, risk=0.05, energy_joules=45.0),
        reliability=0.95,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(
            type=CapabilityType.GUI,
            details={"action": "CLICK", "component": "submit_button"}
        )
    )

    # 6. Alternative Implementations of MakePayment (Operational Trade-offs, Section 7 Exp 5)
    # High Reliability, High Cost
    c2_premium_gateway = Capability(
        name="MakePayment_PremiumGateway",
        capability_type=CapabilityType.SERVICE,
        inputs=[
            DataParameter(name="order_id", data_type="order_id", domain="UUID", required=True)
        ],
        outputs=[
            DataParameter(name="payment_token", data_type="payment_token", domain="Token")
        ],
        preconditions=[
            Condition(variable="Order.exists", operator="==", value=True),
            Condition(variable="Order.status", operator="==", value="CREATED")
        ],
        effects=[
            Effect(variable="Payment.status", action="set", value="SUCCESS"),
            Effect(variable="Order.status", action="set", value="PAID")
        ],
        resources=[
            ResourceRequirement(name="PaymentGateway", amount=2.0)
        ],
        cost=CostProfile(execution_time_ms=180.0, monetary_cost=0.45, resource_units=4.0, risk=0.001, energy_joules=20.0),
        reliability=0.9995,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(
            type=CapabilityType.SERVICE,
            details={"provider": "EnterpriseSLA", "redundancy": True}
        )
    )

    # Budget Gateway (Low Cost, Lower Reliability)
    c2_budget_gateway = Capability(
        name="MakePayment_BudgetGateway",
        capability_type=CapabilityType.SERVICE,
        inputs=[
            DataParameter(name="order_id", data_type="order_id", domain="UUID", required=True)
        ],
        outputs=[
            DataParameter(name="payment_token", data_type="payment_token", domain="Token")
        ],
        preconditions=[
            Condition(variable="Order.exists", operator="==", value=True),
            Condition(variable="Order.status", operator="==", value="CREATED")
        ],
        effects=[
            Effect(variable="Payment.status", action="set", value="SUCCESS"),
            Effect(variable="Order.status", action="set", value="PAID")
        ],
        resources=[
            ResourceRequirement(name="PaymentGateway", amount=1.0)
        ],
        cost=CostProfile(execution_time_ms=800.0, monetary_cost=0.02, resource_units=1.0, risk=0.08, energy_joules=50.0),
        reliability=0.92,
        availability=0.90,
        execution_mechanism=ExecutionMechanism(
            type=CapabilityType.SERVICE,
            details={"provider": "BudgetPeerGateway", "redundancy": False}
        )
    )

    # 7. Irrelevant Capabilities (Section 7 Exp 4)
    c_irrelevant_weather = Capability(
        name="QueryWeather",
        capability_type=CapabilityType.API,
        inputs=[],
        outputs=[
            DataParameter(name="weather_data", data_type="weather_data", domain="JSON")
        ],
        preconditions=[],
        effects=[
            Effect(variable="External.weather_cached", action="set", value=True)
        ],
        resources=[ResourceRequirement(name="Network", amount=1.0)],
        cost=CostProfile(execution_time_ms=200.0, monetary_cost=0.001, resource_units=1.0, risk=0.01, energy_joules=10.0),
        reliability=0.98,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(
            type=CapabilityType.API,
            details={"endpoint": "https://api.weather.com/v1"}
        )
    )

    c_irrelevant_logs = Capability(
        name="CompressLogFiles",
        capability_type=CapabilityType.FILE,
        inputs=[],
        outputs=[
            DataParameter(name="log_archive", data_type="log_archive", domain="TAR_GZ")
        ],
        preconditions=[],
        effects=[
            Effect(variable="System.log_compressed", action="set", value=True)
        ],
        resources=[ResourceRequirement(name="DiskIO", amount=2.0)],
        cost=CostProfile(execution_time_ms=1500.0, monetary_cost=0.0, resource_units=3.0, risk=0.001, energy_joules=120.0),
        reliability=0.999,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(
            type=CapabilityType.FILE,
            details={"tool": "gzip", "path": "/var/log/sys.log"}
        )
    )

    capabilities = [
        c1_create_order,
        c2_make_payment,
        c3_cancel_cart,
        c4_send_notification,
        c5_reserve_inventory,
        c1_db,
        c1_gui,
        c2_premium_gateway,
        c2_budget_gateway,
        c_irrelevant_weather,
        c_irrelevant_logs
    ]

    return {
        "domain_name": "EcommerceOrderFulfillment",
        "schema": schema,
        "initial_state": initial_state,
        "goal": goal,
        "capabilities": capabilities,
        "named_capabilities": {c.name: c for c in capabilities}
    }


def save_ecommerce_dataset(output_path: str = "datasets/ecommerce_domain.json"):
    data = build_ecommerce_domain()
    # Serialize to JSON format
    serializable = {
        "domain_name": data["domain_name"],
        "schema": {
            "state_variables": data["schema"].state_variables,
            "data_types": data["schema"].data_types,
            "resource_types": data["schema"].resource_types,
            "capability_types": data["schema"].capability_types,
            "total_dim": data["schema"].total_dim,
        },
        "initial_state": data["initial_state"].model_dump(),
        "goal": data["goal"].model_dump(),
        "capabilities": [c.model_dump() for c in data["capabilities"]]
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)
    return output_path
