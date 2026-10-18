"""
E-Commerce / Order-to-Cash Application Domain (Sections 3.1, 3.2, 4.3, 5, 7).
Formally specifies initial state, goal, atomic capabilities, alternative implementations,
irrelevant capabilities, and operational quality benchmarks.
"""

from typing import Dict, Any, List
from capability_embedding.core.types import CapabilityType, ExecutionMechanism, InputSpec, OutputSpec
from capability_embedding.core.operational import OperationalQuality, ResourceRequirement, CapabilityConstraint
from capability_embedding.core.state import State, Goal
from capability_embedding.core.capability import Capability


def get_ecommerce_initial_state() -> State:
    """Formal initial state SI from Section 3.1."""
    return State({
        "User.authenticated": True,
        "User.role": "CUSTOMER",
        "Cart.exists": True,
        "Cart.item_count": 3,
        "Order.exists": False,
        "Payment.status": "NOT_STARTED",
        "Inventory.available": True,
        "Notification.sent": False,
        "Order.status": "NONE"
    })


def get_ecommerce_goal() -> Goal:
    """Formal goal specification G from Section 3.2."""
    return Goal({
        "Order.exists": True,
        "Payment.status": "SUCCESS",
        "Notification.sent": True
    })


def get_ecommerce_capabilities() -> Dict[str, Capability]:
    """
    Formal atomic capabilities for the E-Commerce domain.
    Includes C1, C2, C3 from Section 7 Experiment 1, alternative implementations
    from Experiment 3, and irrelevant capabilities from Experiment 4.
    """
    caps = {}

    # C1: CreateOrder (API)
    caps["CreateOrder_API"] = Capability(
        name="CreateOrder_API",
        capability_type=CapabilityType.API,
        inputs=[
            InputSpec(name="cart_id", var_type="UUID", domain="valid UUIDs", required=True),
            InputSpec(name="user_token", var_type="STRING", required=True)
        ],
        outputs=[
            OutputSpec(name="order_id", var_type="UUID", domain="valid UUIDs")
        ],
        preconditions={
            "Cart.exists": True,
            "User.authenticated": True
        },
        effects={
            "Order.exists": True,
            "Order.status": "CREATED"
        },
        constraints=[
            CapabilityConstraint(expression="Cart.item_count > 0", variables=["Cart.item_count"])
        ],
        resources=[
            ResourceRequirement(name="Database", resource_type="STORAGE"),
            ResourceRequirement(name="Network", resource_type="NETWORK")
        ],
        quality=OperationalQuality(
            execution_time_ms=120.0,
            monetary_cost=0.015,
            resource_cost=2.0,
            risk=0.02,
            energy_cost=0.8,
            reliability=0.995,
            availability=0.999
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.API,
            details={"method": "POST", "endpoint": "/orders"}
        )
    )

    # Alternative 1: CreateOrder (Database direct stored procedure)
    caps["CreateOrder_DB"] = Capability(
        name="CreateOrder_DB",
        capability_type=CapabilityType.DATABASE,
        inputs=[
            InputSpec(name="cart_id", var_type="UUID", required=True)
        ],
        outputs=[
            OutputSpec(name="order_id", var_type="UUID")
        ],
        preconditions={
            "Cart.exists": True,
            "User.authenticated": True
        },
        effects={
            "Order.exists": True,
            "Order.status": "CREATED"
        },
        constraints=[
            CapabilityConstraint(expression="Cart.item_count > 0", variables=["Cart.item_count"])
        ],
        resources=[
            ResourceRequirement(name="Database", resource_type="STORAGE")
        ],
        quality=OperationalQuality(
            execution_time_ms=25.0,
            monetary_cost=0.003,
            resource_cost=1.5,
            risk=0.01,
            energy_cost=0.3,
            reliability=0.999,
            availability=0.9995
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.DATABASE,
            details={"operation": "INSERT", "table": "orders"}
        )
    )

    # Alternative 2: CreateOrder (GUI button click)
    caps["CreateOrder_GUI"] = Capability(
        name="CreateOrder_GUI",
        capability_type=CapabilityType.GUI,
        inputs=[
            InputSpec(name="cart_id", var_type="UUID", required=True)
        ],
        outputs=[
            OutputSpec(name="order_id", var_type="UUID")
        ],
        preconditions={
            "Cart.exists": True,
            "User.authenticated": True
        },
        effects={
            "Order.exists": True,
            "Order.status": "CREATED"
        },
        constraints=[
            CapabilityConstraint(expression="Cart.item_count > 0", variables=["Cart.item_count"])
        ],
        resources=[
            ResourceRequirement(name="Browser", resource_type="CLIENT")
        ],
        quality=OperationalQuality(
            execution_time_ms=650.0,
            monetary_cost=0.05,
            resource_cost=4.0,
            risk=0.08,
            energy_cost=2.5,
            reliability=0.96,
            availability=0.98
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.GUI,
            details={"action": "CLICK", "component": "submit_order_button"}
        )
    )

    # C2: MakePayment
    caps["MakePayment"] = Capability(
        name="MakePayment",
        capability_type=CapabilityType.SERVICE,
        inputs=[
            InputSpec(name="order_id", var_type="UUID", required=True),
            InputSpec(name="amount", var_type="FLOAT", required=True)
        ],
        outputs=[
            OutputSpec(name="payment_receipt", var_type="STRING")
        ],
        preconditions={
            "Order.exists": True
        },
        effects={
            "Payment.status": "SUCCESS"
        },
        constraints=[
            CapabilityConstraint(expression="payment_amount <= transaction_limit", variables=["amount"])
        ],
        resources=[
            ResourceRequirement(name="PaymentGateway", resource_type="EXTERNAL"),
            ResourceRequirement(name="Network", resource_type="NETWORK")
        ],
        quality=OperationalQuality(
            execution_time_ms=350.0,
            monetary_cost=0.05,
            resource_cost=3.0,
            risk=0.03,
            energy_cost=1.2,
            reliability=0.985,
            availability=0.995
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.SERVICE,
            details={"gateway": "Stripe", "action": "charge"}
        )
    )

    # C3: CancelCart (Incompatible with C1!)
    caps["CancelCart"] = Capability(
        name="CancelCart",
        capability_type=CapabilityType.FUNCTION,
        inputs=[
            InputSpec(name="cart_id", var_type="UUID", required=True)
        ],
        outputs=[],
        preconditions={
            "Order.exists": False  # Specifically requires that no order exists yet!
        },
        effects={
            "Cart.exists": False
        },
        resources=[
            ResourceRequirement(name="Database", resource_type="STORAGE")
        ],
        quality=OperationalQuality(
            execution_time_ms=30.0,
            monetary_cost=0.001,
            resource_cost=0.5,
            risk=0.005,
            energy_cost=0.1,
            reliability=0.999,
            availability=1.0
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.FUNCTION,
            details={"fn": "cart_service.discard"}
        )
    )

    # C4: SendNotification
    caps["SendNotification"] = Capability(
        name="SendNotification",
        capability_type=CapabilityType.MESSAGE,
        inputs=[
            InputSpec(name="order_id", var_type="UUID", required=True),
            InputSpec(name="payment_receipt", var_type="STRING", required=True)
        ],
        outputs=[
            OutputSpec(name="notification_id", var_type="UUID")
        ],
        preconditions={
            "Payment.status": "SUCCESS"
        },
        effects={
            "Notification.sent": True
        },
        resources=[
            ResourceRequirement(name="EmailService", resource_type="EXTERNAL")
        ],
        quality=OperationalQuality(
            execution_time_ms=80.0,
            monetary_cost=0.005,
            resource_cost=1.0,
            risk=0.01,
            energy_cost=0.4,
            reliability=0.992,
            availability=0.999
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.MESSAGE,
            details={"channel": "Email", "template": "order_receipt"}
        )
    )

    # C5: CheckInventory
    caps["CheckInventory"] = Capability(
        name="CheckInventory",
        capability_type=CapabilityType.DATABASE,
        inputs=[
            InputSpec(name="cart_id", var_type="UUID", required=True)
        ],
        outputs=[
            OutputSpec(name="stock_available", var_type="BOOLEAN")
        ],
        preconditions={
            "Cart.exists": True
        },
        effects={
            "Inventory.available": True
        },
        resources=[
            ResourceRequirement(name="Database", resource_type="STORAGE")
        ],
        quality=OperationalQuality(
            execution_time_ms=45.0,
            monetary_cost=0.002,
            resource_cost=0.8,
            risk=0.005,
            energy_cost=0.2,
            reliability=0.999,
            availability=1.0
        ),
        mechanism=ExecutionMechanism(
            mechanism_type=CapabilityType.DATABASE,
            details={"table": "inventory", "action": "SELECT"}
        )
    )

    # Irrelevant Capabilities (Experiment 4)
    caps["UpdateUserAvatar"] = Capability(
        name="UpdateUserAvatar",
        capability_type=CapabilityType.FILE,
        inputs=[InputSpec(name="image_bytes", var_type="BYTES", required=True)],
        outputs=[OutputSpec(name="avatar_url", var_type="STRING")],
        preconditions={"User.authenticated": True},
        effects={"User.avatar_updated": True},
        resources=[ResourceRequirement(name="S3Storage", resource_type="STORAGE")],
        quality=OperationalQuality(execution_time_ms=180.0, monetary_cost=0.004, reliability=0.98),
        mechanism=ExecutionMechanism(CapabilityType.FILE, {"storage": "S3", "bucket": "avatars"})
    )

    caps["GenerateTaxAuditReport"] = Capability(
        name="GenerateTaxAuditReport",
        capability_type=CapabilityType.COMPUTATION,
        inputs=[InputSpec(name="fiscal_year", var_type="INTEGER", required=True)],
        outputs=[OutputSpec(name="audit_pdf", var_type="FILE")],
        preconditions={"User.role": "ADMIN"},
        effects={"TaxReport.generated": True},
        resources=[ResourceRequirement(name="CPUCluster", resource_type="COMPUTE")],
        quality=OperationalQuality(execution_time_ms=2500.0, monetary_cost=0.20, reliability=0.95),
        mechanism=ExecutionMechanism(CapabilityType.COMPUTATION, {"engine": "Spark"})
    )

    caps["BrowseCatalogRecommendations"] = Capability(
        name="BrowseCatalogRecommendations",
        capability_type=CapabilityType.SERVICE,
        inputs=[InputSpec(name="category", var_type="STRING", required=False)],
        outputs=[OutputSpec(name="recommendations", var_type="LIST")],
        preconditions={},
        effects={"Catalog.viewed": True},
        resources=[ResourceRequirement(name="RecEngine", resource_type="SERVICE")],
        quality=OperationalQuality(execution_time_ms=90.0, monetary_cost=0.008, reliability=0.99),
        mechanism=ExecutionMechanism(CapabilityType.SERVICE, {"service": "RecSys"})
    )

    # Detrimental capability (contradicts goal)
    caps["ResetOrderState"] = Capability(
        name="ResetOrderState",
        capability_type=CapabilityType.FUNCTION,
        inputs=[],
        outputs=[],
        preconditions={"Order.exists": True},
        effects={"Order.exists": False, "Payment.status": "NOT_STARTED", "Notification.sent": False},
        resources=[ResourceRequirement(name="Database", resource_type="STORAGE")],
        quality=OperationalQuality(execution_time_ms=40.0, monetary_cost=0.001, reliability=0.99),
        mechanism=ExecutionMechanism(CapabilityType.FUNCTION, {"fn": "orders.reset"})
    )

    return caps
