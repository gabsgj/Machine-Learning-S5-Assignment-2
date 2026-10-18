"""
Deliverable 3: Experimental Benchmark Dataset for Capability Composition.
Formally specified application problems containing initial states, goal specifications,
atomic capabilities, capability compositions, constraints, and operational attributes.

Assignment 2: Design of a Vector Embedding for Capability Composition.
Student: Melita Mariam Mathew
Registration Number: TCCR24CS046
"""

from typing import List, Dict, Any, Tuple
import json
import os

from src.models import (
    Capability,
    CompositeCapability,
    State,
    Goal,
    CapabilityType,
    ExecutionMechanism,
    OperationalAttributes,
    StateCondition,
    InputSpec,
    OutputSpec,
)
from src.embedding import CapabilityEmbeddingSpace


def get_benchmark_state_variables() -> List[str]:
    """All state variables used in the benchmark domain."""
    return [
        "User.authenticated",
        "User.role",
        "Cart.exists",
        "Cart.item_count",
        "Cart.locked",
        "Inventory.available",
        "Order.exists",
        "Order.status",
        "Payment.status",
        "Invoice.generated",
        "Shipment.dispatched",
        "Notification.sent",
        "AuditLog.written",
        "UI.theme_mode",
        "Report.generated",
    ]


def get_benchmark_io_vocab() -> List[str]:
    """All input/output parameter names and data types."""
    return [
        "cart_id",
        "user_id",
        "order_id",
        "payment_token",
        "receipt_id",
        "tracking_number",
        "report_id",
        "theme_name",
        "UUID",
        "INT",
        "STRING",
        "TOKEN",
        "BOOLEAN",
        "DOCUMENT",
    ]


def build_benchmark_dataset() -> Dict[str, Any]:
    """
    Construct the formal application dataset:
    A = (S, C, S_I, G, R, K)
    """

    # -------------------------------------------------------------------------
    # 1. Initial State (S_I) from Assignment PDF Section 3.1
    # -------------------------------------------------------------------------
    initial_state = State(
        variables={
            "User.authenticated": True,
            "User.role": "CUSTOMER",
            "Cart.exists": True,
            "Cart.item_count": 3,
            "Cart.locked": False,
            "Inventory.available": True,
            "Order.exists": False,
            "Order.status": "NOT_STARTED",
            "Payment.status": "NOT_STARTED",
            "Invoice.generated": False,
            "Shipment.dispatched": False,
            "Notification.sent": False,
            "AuditLog.written": False,
            "UI.theme_mode": "LIGHT",
            "Report.generated": False,
        }
    )

    # -------------------------------------------------------------------------
    # 2. Goal Specification (G) from Assignment PDF Section 3.2
    # -------------------------------------------------------------------------
    primary_goal = Goal(
        conditions=[
            StateCondition("Order.exists", True, "=="),
            StateCondition("Payment.status", "SUCCESS", "=="),
            StateCondition("Notification.sent", True, "=="),
        ]
    )

    extended_goal = Goal(
        conditions=[
            StateCondition("Order.exists", True, "=="),
            StateCondition("Payment.status", "SUCCESS", "=="),
            StateCondition("Invoice.generated", True, "=="),
            StateCondition("Shipment.dispatched", True, "=="),
            StateCondition("Notification.sent", True, "=="),
        ]
    )

    # -------------------------------------------------------------------------
    # 3. Available Resources (R) & Constraints (K)
    # -------------------------------------------------------------------------
    available_resources = [
        "Database",
        "PaymentGateway",
        "AuthenticationToken",
        "Network",
        "FileSystem",
        "NotificationService",
        "InventoryDB",
    ]

    global_constraints = [
        "quantity > 0",
        "quantity <= inventory_available",
        "payment_amount <= transaction_limit",
        "user.role in {CUSTOMER, ADMIN}",
    ]

    # -------------------------------------------------------------------------
    # 4. Atomic Capabilities (C)
    # -------------------------------------------------------------------------
    capabilities: Dict[str, Capability] = {}

    # C1: CreateOrder (API)
    capabilities["C1_CreateOrder_API"] = Capability(
        id="C1_CreateOrder_API",
        name="CreateOrder (REST API)",
        type=CapabilityType.API,
        inputs=[
            InputSpec("cart_id", "UUID", "Cart identifier", True),
            InputSpec("user_id", "UUID", "User identifier", True),
        ],
        outputs=[
            OutputSpec("order_id", "UUID", "Generated order identifier"),
        ],
        preconditions=[
            StateCondition("Cart.exists", True, "=="),
            StateCondition("Cart.item_count", 0, ">"),
            StateCondition("Inventory.available", True, "=="),
        ],
        effects=[
            StateCondition("Order.exists", True, "=="),
            StateCondition("Order.status", "CREATED", "=="),
            StateCondition("Cart.locked", True, "=="),
        ],
        constraints=["cart_item_count > 0", "inventory_available == true"],
        resources=["Database", "Network", "InventoryDB"],
        operational=OperationalAttributes(
            time_ms=120.0,
            cost_money=0.015,
            resource_cost=2.0,
            risk=0.04,
            energy=1.2,
            reliability=0.992,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.API,
            details={"method": "POST", "endpoint": "/orders"},
        ),
    )

    # C1_DB: CreateOrder (Database Direct)
    capabilities["C1_CreateOrder_DB"] = Capability(
        id="C1_CreateOrder_DB",
        name="CreateOrder (Direct DB INSERT)",
        type=CapabilityType.DATABASE,
        inputs=[
            InputSpec("cart_id", "UUID", "Cart identifier", True),
            InputSpec("user_id", "UUID", "User identifier", True),
        ],
        outputs=[
            OutputSpec("order_id", "UUID", "Generated order identifier"),
        ],
        preconditions=[
            StateCondition("Cart.exists", True, "=="),
            StateCondition("Cart.item_count", 0, ">"),
            StateCondition("Inventory.available", True, "=="),
        ],
        effects=[
            StateCondition("Order.exists", True, "=="),
            StateCondition("Order.status", "CREATED", "=="),
            StateCondition("Cart.locked", True, "=="),
        ],
        constraints=["cart_item_count > 0"],
        resources=["Database"],
        operational=OperationalAttributes(
            time_ms=45.0,
            cost_money=0.005,
            resource_cost=3.5,
            risk=0.02,
            energy=0.8,
            reliability=0.998,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.DATABASE,
            details={"operation": "INSERT", "table": "orders"},
        ),
    )

    # C1_GUI: CreateOrder (GUI Submit)
    capabilities["C1_CreateOrder_GUI"] = Capability(
        id="C1_CreateOrder_GUI",
        name="CreateOrder (GUI Automation Click)",
        type=CapabilityType.GUI,
        inputs=[
            InputSpec("cart_id", "UUID", "Cart identifier", True),
        ],
        outputs=[
            OutputSpec("order_id", "UUID", "Generated order identifier"),
        ],
        preconditions=[
            StateCondition("Cart.exists", True, "=="),
            StateCondition("Cart.item_count", 0, ">"),
            StateCondition("Inventory.available", True, "=="),
        ],
        effects=[
            StateCondition("Order.exists", True, "=="),
            StateCondition("Order.status", "CREATED", "=="),
            StateCondition("Cart.locked", True, "=="),
        ],
        constraints=["browser_session_active == true"],
        resources=["Network", "Database"],
        operational=OperationalAttributes(
            time_ms=850.0,
            cost_money=0.08,
            resource_cost=5.0,
            risk=0.15,
            energy=3.5,
            reliability=0.94,
            availability=0.95,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.GUI,
            details={"action": "CLICK", "component": "submit_button"},
        ),
    )

    # C2: MakePayment (API Payment Gateway)
    capabilities["C2_MakePayment"] = Capability(
        id="C2_MakePayment",
        name="MakePayment (Stripe Gateway)",
        type=CapabilityType.SERVICE,
        inputs=[
            InputSpec("order_id", "UUID", "Order identifier", True),
            InputSpec("payment_token", "TOKEN", "Credit card / token", True),
        ],
        outputs=[
            OutputSpec("receipt_id", "UUID", "Payment receipt confirmation"),
        ],
        preconditions=[
            StateCondition("Order.exists", True, "=="),
            StateCondition("Order.status", "CREATED", "=="),
        ],
        effects=[
            StateCondition("Payment.status", "SUCCESS", "=="),
        ],
        constraints=["payment_amount <= transaction_limit"],
        resources=["PaymentGateway", "Network", "Database"],
        operational=OperationalAttributes(
            time_ms=250.0,
            cost_money=0.035,
            resource_cost=2.0,
            risk=0.03,
            energy=1.5,
            reliability=0.995,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.SERVICE,
            details={"gateway": "Stripe", "action": "charge_token"},
        ),
    )

    # C2_Alt: MakePayment_Wallet (Internal Wallet Service)
    capabilities["C2_MakePayment_Wallet"] = Capability(
        id="C2_MakePayment_Wallet",
        name="MakePayment (Internal Wallet)",
        type=CapabilityType.FUNCTION,
        inputs=[
            InputSpec("order_id", "UUID", "Order identifier", True),
        ],
        outputs=[
            OutputSpec("receipt_id", "UUID", "Wallet debit confirmation"),
        ],
        preconditions=[
            StateCondition("Order.exists", True, "=="),
            StateCondition("Order.status", "CREATED", "=="),
        ],
        effects=[
            StateCondition("Payment.status", "SUCCESS", "=="),
        ],
        constraints=["wallet_balance >= order_amount"],
        resources=["Database"],
        operational=OperationalAttributes(
            time_ms=35.0,
            cost_money=0.002,
            resource_cost=1.2,
            risk=0.01,
            energy=0.5,
            reliability=0.999,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.FUNCTION,
            details={"module": "wallet_service", "method": "debit_balance"},
        ),
    )

    # C3: CancelCart (Incompatible with C1)
    capabilities["C3_CancelCart"] = Capability(
        id="C3_CancelCart",
        name="CancelCart (Abort Cart Before Order)",
        type=CapabilityType.API,
        inputs=[
            InputSpec("cart_id", "UUID", "Cart identifier", True),
        ],
        outputs=[],
        preconditions=[
            StateCondition("Order.exists", False, "=="),  # Requires order NOT to exist!
            StateCondition("Cart.exists", True, "=="),
        ],
        effects=[
            StateCondition("Cart.exists", False, "=="),
            StateCondition("Cart.item_count", 0, "=="),
        ],
        constraints=["cart_not_locked == true"],
        resources=["Database"],
        operational=OperationalAttributes(
            time_ms=80.0,
            cost_money=0.005,
            resource_cost=1.0,
            risk=0.02,
            energy=0.6,
            reliability=0.99,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.API,
            details={"method": "DELETE", "endpoint": "/carts"},
        ),
    )

    # C4: SendNotification (Event Handler)
    capabilities["C4_SendNotification"] = Capability(
        id="C4_SendNotification",
        name="SendNotification (Order Confirmation Email)",
        type=CapabilityType.EVENT,
        inputs=[
            InputSpec("order_id", "UUID", "Order identifier", True),
            InputSpec("receipt_id", "UUID", "Receipt identifier", False),
        ],
        outputs=[],
        preconditions=[
            StateCondition("Payment.status", "SUCCESS", "=="),
        ],
        effects=[
            StateCondition("Notification.sent", True, "=="),
        ],
        constraints=[],
        resources=["NotificationService", "Network"],
        operational=OperationalAttributes(
            time_ms=180.0,
            cost_money=0.008,
            resource_cost=1.5,
            risk=0.05,
            energy=0.9,
            reliability=0.985,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.EVENT,
            details={"trigger": "PaymentSucceeded", "handler": "SendNotification"},
        ),
    )

    # C5: GenerateInvoice (Computation)
    capabilities["C5_GenerateInvoice"] = Capability(
        id="C5_GenerateInvoice",
        name="GenerateInvoice (PDF Accounting Document)",
        type=CapabilityType.COMPUTATION,
        inputs=[
            InputSpec("order_id", "UUID", "Order identifier", True),
            InputSpec("receipt_id", "UUID", "Receipt identifier", True),
        ],
        outputs=[
            OutputSpec("receipt_id", "DOCUMENT", "Formatted invoice PDF"),
        ],
        preconditions=[
            StateCondition("Payment.status", "SUCCESS", "=="),
        ],
        effects=[
            StateCondition("Invoice.generated", True, "=="),
        ],
        constraints=[],
        resources=["FileSystem"],
        operational=OperationalAttributes(
            time_ms=320.0,
            cost_money=0.012,
            resource_cost=4.0,
            risk=0.03,
            energy=2.1,
            reliability=0.99,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.COMPUTATION,
            details={"library": "ReportLab", "output": "/invoices"},
        ),
    )

    # C6: DispatchShipment (Logistics Service)
    capabilities["C6_DispatchShipment"] = Capability(
        id="C6_DispatchShipment",
        name="DispatchShipment (Warehouse Dispatch)",
        type=CapabilityType.SERVICE,
        inputs=[
            InputSpec("order_id", "UUID", "Order identifier", True),
        ],
        outputs=[
            OutputSpec("tracking_number", "STRING", "Courier tracking number"),
        ],
        preconditions=[
            StateCondition("Payment.status", "SUCCESS", "=="),
            StateCondition("Invoice.generated", True, "=="),
        ],
        effects=[
            StateCondition("Shipment.dispatched", True, "=="),
        ],
        constraints=["warehouse_operating_hours == true"],
        resources=["Network", "Database"],
        operational=OperationalAttributes(
            time_ms=450.0,
            cost_money=0.05,
            resource_cost=2.5,
            risk=0.06,
            energy=2.8,
            reliability=0.975,
            availability=0.98,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.SERVICE,
            details={"carrier": "FedEx", "service": "PriorityExpress"},
        ),
    )

    # -------------------------------------------------------------------------
    # Irrelevant Capabilities (Exp 4)
    # -------------------------------------------------------------------------
    # C_IRR_1: GenerateSalesReport
    capabilities["C_IRR_1_SalesReport"] = Capability(
        id="C_IRR_1_SalesReport",
        name="GenerateSalesReport (Admin BI Analytics)",
        type=CapabilityType.COMPUTATION,
        inputs=[
            InputSpec("user_id", "UUID", "Admin user ID", True),
        ],
        outputs=[
            OutputSpec("report_id", "DOCUMENT", "Aggregated sales metrics"),
        ],
        preconditions=[
            StateCondition("User.authenticated", True, "=="),
        ],
        effects=[
            StateCondition("Report.generated", True, "=="),
        ],
        constraints=["user.role == ADMIN"],
        resources=["Database", "FileSystem"],
        operational=OperationalAttributes(
            time_ms=1500.0,
            cost_money=0.12,
            resource_cost=8.0,
            risk=0.02,
            energy=6.5,
            reliability=0.99,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.COMPUTATION,
            details={"query": "SELECT SUM(total) FROM orders", "format": "PDF"},
        ),
    )

    # C_IRR_2: ToggleUITheme
    capabilities["C_IRR_2_ToggleTheme"] = Capability(
        id="C_IRR_2_ToggleTheme",
        name="ToggleUITheme (Dark/Light Preference)",
        type=CapabilityType.GUI,
        inputs=[
            InputSpec("theme_name", "STRING", "Target theme name", True),
        ],
        outputs=[],
        preconditions=[],
        effects=[
            StateCondition("UI.theme_mode", "DARK", "=="),
        ],
        constraints=[],
        resources=[],
        operational=OperationalAttributes(
            time_ms=15.0,
            cost_money=0.0001,
            resource_cost=0.2,
            risk=0.001,
            energy=0.05,
            reliability=0.9999,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.GUI,
            details={"action": "SWITCH_CSS_THEME"},
        ),
    )

    # C_IRR_3: WriteAuditLog
    capabilities["C_IRR_3_WriteAuditLog"] = Capability(
        id="C_IRR_3_WriteAuditLog",
        name="WriteAuditLog (System Log Flush)",
        type=CapabilityType.FILE,
        inputs=[],
        outputs=[],
        preconditions=[],
        effects=[
            StateCondition("AuditLog.written", True, "=="),
        ],
        constraints=[],
        resources=["FileSystem"],
        operational=OperationalAttributes(
            time_ms=30.0,
            cost_money=0.001,
            resource_cost=1.0,
            risk=0.01,
            energy=0.3,
            reliability=0.995,
            availability=1.0,
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.FILE,
            details={"file": "/var/log/audit.log", "mode": "append"},
        ),
    )

    return {
        "state_variables": get_benchmark_state_variables(),
        "io_vocab": get_benchmark_io_vocab(),
        "initial_state": initial_state,
        "primary_goal": primary_goal,
        "extended_goal": extended_goal,
        "available_resources": available_resources,
        "global_constraints": global_constraints,
        "capabilities": capabilities,
    }


def save_dataset_to_json(filepath: str) -> None:
    """Serialize the benchmark dataset to clean JSON format."""
    dataset = build_benchmark_dataset()

    serializable = {
        "metadata": {
            "assignment": "Assignment 2: Design of a Vector Embedding for Capability Composition",
            "author": "Melita Mariam Mathew",
            "registration_number": "TCCR24CS046",
            "domain": "E-Commerce Formal Application Model (S, C, S_I, G, R, K)",
        },
        "state_variables": dataset["state_variables"],
        "io_vocab": dataset["io_vocab"],
        "initial_state": dataset["initial_state"].to_dict(),
        "primary_goal": dataset["primary_goal"].to_dict(),
        "extended_goal": dataset["extended_goal"].to_dict(),
        "available_resources": dataset["available_resources"],
        "global_constraints": dataset["global_constraints"],
        "capabilities": {cid: cap.to_dict() for cid, cap in dataset["capabilities"].items()},
    }

    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)


if __name__ == "__main__":
    out_file = os.path.join(os.path.dirname(__file__), "benchmark_data.json")
    save_dataset_to_json(out_file)
    print(f"Benchmark dataset saved successfully to: {out_file}")
