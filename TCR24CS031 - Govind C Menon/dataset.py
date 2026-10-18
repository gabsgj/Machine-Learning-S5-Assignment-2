"""
dataset.py
==========
Formal Dataset Generator and Repository for E-Commerce Capability Domain.
Creates the Application A = (S, C, SI, G, R, K) and exports JSON / CSV data files.
"""

import json
import os
import pandas as pd
from typing import Dict, List, Tuple
from models import (
    Application, State, Goal, Capability, CapabilityType,
    InputSpec, OutputSpec, Precondition, Effect, Constraint,
    Resource, QualityAttributes, ExecutionMechanism
)


def build_ecommerce_application() -> Tuple[Application, Dict[str, Capability]]:
    """
    Constructs the canonical formal e-commerce application model:
    A = (S, C, SI, G, R, K)
    """
    # 1. State Space Schema
    state_space_schema = {
        "User.authenticated": {"type": "bool", "default": True},
        "User.role": {"type": "enum", "values": ["GUEST", "CUSTOMER", "ADMIN"], "default": "CUSTOMER"},
        "Cart.exists": {"type": "bool", "default": True},
        "Cart.item_count": {"type": "int", "default": 3},
        "Cart.locked": {"type": "bool", "default": False},
        "Order.exists": {"type": "bool", "default": False},
        "Order.status": {"type": "enum", "values": ["NONE", "CREATED", "PAID", "FULFILLED", "CANCELLED"], "default": "NONE"},
        "Payment.status": {"type": "enum", "values": ["NOT_STARTED", "PENDING", "SUCCESS", "FAILED"], "default": "NOT_STARTED"},
        "Inventory.available": {"type": "bool", "default": True},
        "Invoice.generated": {"type": "bool", "default": False},
        "Notification.sent": {"type": "bool", "default": False},
        "Profile.updated": {"type": "bool", "default": False},
        "Report.generated": {"type": "bool", "default": False},
        "Music.playing": {"type": "bool", "default": False}
    }

    # 2. Initial State SI
    initial_state = State(
        name="SI_InitialOrderState",
        variables={
            "User.authenticated": True,
            "User.role": "CUSTOMER",
            "Cart.exists": True,
            "Cart.item_count": 3,
            "Cart.locked": False,
            "Order.exists": False,
            "Order.status": "NONE",
            "Payment.status": "NOT_STARTED",
            "Inventory.available": True,
            "Invoice.generated": False,
            "Notification.sent": False,
            "Profile.updated": False,
            "Report.generated": False,
            "Music.playing": False
        }
    )

    # 3. Goal Specification G
    goal = Goal(
        name="PurchaseAndNotifyGoal",
        conditions=[
            Precondition(variable="Order.exists", operator="==", value=True),
            Precondition(variable="Payment.status", operator="==", value="SUCCESS"),
            Precondition(variable="Notification.sent", operator="==", value=True)
        ]
    )

    # 4. Global Resources R
    available_resources = [
        Resource(name="Database", resource_type="system", quantity=10.0),
        Resource(name="PaymentGateway", resource_type="service", quantity=5.0),
        Resource(name="Network", resource_type="network", quantity=100.0),
        Resource(name="EmailService", resource_type="service", quantity=20.0),
        Resource(name="FileSystem", resource_type="hardware", quantity=50.0),
        Resource(name="GPU", resource_type="hardware", quantity=2.0),
        Resource(name="AuthToken", resource_type="security", quantity=1.0)
    ]

    # 5. Global Constraints K
    global_constraints = [
        Constraint(name="authenticated_user", expression="User.authenticated == True", constraint_type="security"),
        Constraint(name="valid_inventory", expression="Inventory.available == True", constraint_type="state"),
        Constraint(name="cart_non_empty", expression="Cart.item_count > 0", constraint_type="input")
    ]

    # 6. Capabilities C
    capabilities: Dict[str, Capability] = {}

    # C1: CreateOrder (Standard Function)
    c_create_order = Capability(
        name="CreateOrder",
        capability_type=CapabilityType.FUNCTION,
        inputs=[
            InputSpec(name="cart_id", data_type="UUID", domain="valid UUIDs", required=True)
        ],
        outputs=[
            OutputSpec(name="order_id", data_type="UUID", domain="valid UUIDs")
        ],
        preconditions=[
            Precondition(variable="Cart.exists", operator="==", value=True),
            Precondition(variable="Cart.item_count", operator=">", value=0),
            Precondition(variable="Cart.locked", operator="==", value=False)
        ],
        effects=[
            Effect(variable="Order.exists", value=True, operation="SET"),
            Effect(variable="Order.status", value="CREATED", operation="SET"),
            Effect(variable="Cart.locked", value=True, operation="SET")
        ],
        constraints=[
            Constraint(name="cart_has_items", expression="Cart.item_count > 0", constraint_type="input")
        ],
        resources=[
            Resource(name="Database", resource_type="system", quantity=1.0)
        ],
        quality=QualityAttributes(
            monetary_cost=0.01,
            execution_time_ms=80.0,
            resource_cost=2.0,
            risk=0.05,
            energy_cost=0.01
        ),
        reliability=0.99,
        availability=1.0,
        mechanism=ExecutionMechanism(
            mechanism_type="FUNCTION_CALL",
            endpoint_or_target="create_order_function",
            protocol_or_action="EXECUTE"
        ),
        description="Creates an order from an active unlocked cart with items."
    )
    capabilities[c_create_order.name] = c_create_order

    # C2: MakePayment (Standard API)
    c_make_payment = Capability(
        name="MakePayment",
        capability_type=CapabilityType.API,
        inputs=[
            InputSpec(name="order_id", data_type="UUID", domain="valid UUIDs", required=True),
            InputSpec(name="payment_details", data_type="dict", domain="payment payload", required=True)
        ],
        outputs=[
            OutputSpec(name="payment_receipt", data_type="string", domain="receipt token")
        ],
        preconditions=[
            Precondition(variable="Order.exists", operator="==", value=True),
            Precondition(variable="Order.status", operator="==", value="CREATED"),
            Precondition(variable="Payment.status", operator="==", value="NOT_STARTED")
        ],
        effects=[
            Effect(variable="Payment.status", value="SUCCESS", operation="SET"),
            Effect(variable="Order.status", value="PAID", operation="SET")
        ],
        constraints=[
            Constraint(name="transaction_limit", expression="payment_amount <= transaction_limit", constraint_type="domain")
        ],
        resources=[
            Resource(name="PaymentGateway", resource_type="service", quantity=1.0),
            Resource(name="Network", resource_type="network", quantity=1.0)
        ],
        quality=QualityAttributes(
            monetary_cost=0.10,
            execution_time_ms=250.0,
            resource_cost=4.0,
            risk=0.10,
            energy_cost=0.02
        ),
        reliability=0.97,
        availability=0.99,
        mechanism=ExecutionMechanism(
            mechanism_type="REST_API",
            endpoint_or_target="/api/v1/payments",
            protocol_or_action="POST"
        ),
        description="Processes payment for a created order via payment gateway."
    )
    capabilities[c_make_payment.name] = c_make_payment

    # C3: SendNotification (Message Queue)
    c_send_notification = Capability(
        name="SendNotification",
        capability_type=CapabilityType.MESSAGE,
        inputs=[
            InputSpec(name="order_id", data_type="UUID", domain="valid UUIDs", required=True),
            InputSpec(name="notification_payload", data_type="string", domain="text", required=False)
        ],
        outputs=[
            OutputSpec(name="notification_receipt", data_type="string", domain="delivery id")
        ],
        preconditions=[
            Precondition(variable="Payment.status", operator="==", value="SUCCESS"),
            Precondition(variable="Notification.sent", operator="==", value=False)
        ],
        effects=[
            Effect(variable="Notification.sent", value=True, operation="SET")
        ],
        constraints=[
            Constraint(name="valid_recipient", expression="user.role in {CUSTOMER, ADMIN}", constraint_type="security")
        ],
        resources=[
            Resource(name="EmailService", resource_type="service", quantity=1.0),
            Resource(name="Network", resource_type="network", quantity=1.0)
        ],
        quality=QualityAttributes(
            monetary_cost=0.005,
            execution_time_ms=40.0,
            resource_cost=1.0,
            risk=0.01,
            energy_cost=0.005
        ),
        reliability=0.995,
        availability=1.0,
        mechanism=ExecutionMechanism(
            mechanism_type="MESSAGE_QUEUE",
            endpoint_or_target="notifications.topic",
            protocol_or_action="PUBLISH"
        ),
        description="Dispatches email / SMS confirmation once payment is successful."
    )
    capabilities[c_send_notification.name] = c_send_notification

    # C4: CancelCart (Incompatible with created order)
    c_cancel_cart = Capability(
        name="CancelCart",
        capability_type=CapabilityType.FUNCTION,
        inputs=[
            InputSpec(name="cart_id", data_type="UUID", domain="valid UUIDs", required=True)
        ],
        outputs=[
            OutputSpec(name="cart_status", data_type="string", domain="CANCELLED")
        ],
        preconditions=[
            Precondition(variable="Order.exists", operator="==", value=False),
            Precondition(variable="Cart.exists", operator="==", value=True),
            Precondition(variable="Cart.locked", operator="==", value=False)
        ],
        effects=[
            Effect(variable="Cart.exists", value=False, operation="SET"),
            Effect(variable="Cart.item_count", value=0, operation="SET")
        ],
        constraints=[],
        resources=[
            Resource(name="Database", resource_type="system", quantity=1.0)
        ],
        quality=QualityAttributes(
            monetary_cost=0.00,
            execution_time_ms=20.0,
            resource_cost=1.0,
            risk=0.01,
            energy_cost=0.002
        ),
        reliability=0.999,
        availability=1.0,
        mechanism=ExecutionMechanism(
            mechanism_type="FUNCTION_CALL",
            endpoint_or_target="cancel_cart_function",
            protocol_or_action="EXECUTE"
        ),
        description="Cancels the active shopping cart (only permitted if no order exists)."
    )
    capabilities[c_cancel_cart.name] = c_cancel_cart

    # C5: CheckInventory
    c_check_inventory = Capability(
        name="CheckInventory",
        capability_type=CapabilityType.SERVICE,
        inputs=[
            InputSpec(name="cart_id", data_type="UUID", domain="valid UUIDs", required=True)
        ],
        outputs=[
            OutputSpec(name="inventory_status", data_type="string", domain="AVAILABLE")
        ],
        preconditions=[
            Precondition(variable="Cart.exists", operator="==", value=True)
        ],
        effects=[
            Effect(variable="Inventory.available", value=True, operation="SET")
        ],
        constraints=[],
        resources=[
            Resource(name="Database", resource_type="system", quantity=1.0),
            Resource(name="Network", resource_type="network", quantity=1.0)
        ],
        quality=QualityAttributes(
            monetary_cost=0.002,
            execution_time_ms=30.0,
            resource_cost=1.5,
            risk=0.02,
            energy_cost=0.005
        ),
        reliability=0.99,
        availability=1.0,
        mechanism=ExecutionMechanism(
            mechanism_type="MICROSERVICE",
            endpoint_or_target="/inventory/check",
            protocol_or_action="GET"
        ),
        description="Verifies stock availability for cart items."
    )
    capabilities[c_check_inventory.name] = c_check_inventory

    # C6: GenerateInvoice
    c_generate_invoice = Capability(
        name="GenerateInvoice",
        capability_type=CapabilityType.FILE,
        inputs=[
            InputSpec(name="order_id", data_type="UUID", domain="valid UUIDs", required=True),
            InputSpec(name="payment_receipt", data_type="string", domain="receipt token", required=True)
        ],
        outputs=[
            OutputSpec(name="invoice_pdf", data_type="binary", domain="PDF stream")
        ],
        preconditions=[
            Precondition(variable="Order.exists", operator="==", value=True),
            Precondition(variable="Payment.status", operator="==", value="SUCCESS")
        ],
        effects=[
            Effect(variable="Invoice.generated", value=True, operation="SET")
        ],
        constraints=[],
        resources=[
            Resource(name="FileSystem", resource_type="hardware", quantity=1.0),
            Resource(name="Database", resource_type="system", quantity=1.0)
        ],
        quality=QualityAttributes(
            monetary_cost=0.02,
            execution_time_ms=120.0,
            resource_cost=3.0,
            risk=0.03,
            energy_cost=0.015
        ),
        reliability=0.98,
        availability=0.99,
        mechanism=ExecutionMechanism(
            mechanism_type="FILE_IO",
            endpoint_or_target="/storage/invoices",
            protocol_or_action="WRITE"
        ),
        description="Renders and stores a tax invoice for a paid order."
    )
    capabilities[c_generate_invoice.name] = c_generate_invoice

    # C7: UpdateProfile (Irrelevant to purchase goal)
    c_update_profile = Capability(
        name="UpdateProfile",
        capability_type=CapabilityType.GUI,
        inputs=[
            InputSpec(name="user_id", data_type="UUID", domain="valid UUIDs", required=True),
            InputSpec(name="user_profile", data_type="dict", domain="profile payload", required=True)
        ],
        outputs=[
            OutputSpec(name="profile_data", data_type="dict", domain="updated profile")
        ],
        preconditions=[
            Precondition(variable="User.authenticated", operator="==", value=True)
        ],
        effects=[
            Effect(variable="Profile.updated", value=True, operation="SET")
        ],
        constraints=[],
        resources=[
            Resource(name="Database", resource_type="system", quantity=1.0)
        ],
        quality=QualityAttributes(
            monetary_cost=0.00,
            execution_time_ms=50.0,
            resource_cost=1.0,
            risk=0.01,
            energy_cost=0.005
        ),
        reliability=0.99,
        availability=1.0,
        mechanism=ExecutionMechanism(
            mechanism_type="UI_COMPONENT",
            endpoint_or_target="profile_form",
            protocol_or_action="SUBMIT"
        ),
        description="Updates user preferences, address, and profile data."
    )
    capabilities[c_update_profile.name] = c_update_profile

    # C8: GenerateReport (Irrelevant to purchase goal)
    c_generate_report = Capability(
        name="GenerateReport",
        capability_type=CapabilityType.COMPUTATION,
        inputs=[
            InputSpec(name="report_type", data_type="string", domain="financial/sales", required=True)
        ],
        outputs=[
            OutputSpec(name="report_file", data_type="binary", domain="XLSX/PDF")
        ],
        preconditions=[
            Precondition(variable="User.authenticated", operator="==", value=True),
            Precondition(variable="User.role", operator="==", value="ADMIN")
        ],
        effects=[
            Effect(variable="Report.generated", value=True, operation="SET")
        ],
        constraints=[],
        resources=[
            Resource(name="GPU", resource_type="hardware", quantity=1.0),
            Resource(name="Database", resource_type="system", quantity=2.0)
        ],
        quality=QualityAttributes(
            monetary_cost=0.50,
            execution_time_ms=1500.0,
            resource_cost=8.0,
            risk=0.15,
            energy_cost=0.20
        ),
        reliability=0.94,
        availability=0.95,
        mechanism=ExecutionMechanism(
            mechanism_type="BATCH_JOB",
            endpoint_or_target="analytics_worker",
            protocol_or_action="COMPUTE"
        ),
        description="Runs heavy analytical aggregation queries for executive reports."
    )
    capabilities[c_generate_report.name] = c_generate_report

    # C9: PlayMusic (Completely irrelevant capability)
    c_play_music = Capability(
        name="PlayMusic",
        capability_type=CapabilityType.SERVICE,
        inputs=[
            InputSpec(name="track_id", data_type="string", domain="media id", required=False)
        ],
        outputs=[
            OutputSpec(name="audio_stream", data_type="stream", domain="audio buffer")
        ],
        preconditions=[
            Precondition(variable="User.authenticated", operator="==", value=True)
        ],
        effects=[
            Effect(variable="Music.playing", value=True, operation="SET")
        ],
        constraints=[],
        resources=[
            Resource(name="Network", resource_type="network", quantity=1.0)
        ],
        quality=QualityAttributes(
            monetary_cost=0.00,
            execution_time_ms=15.0,
            resource_cost=0.5,
            risk=0.00,
            energy_cost=0.001
        ),
        reliability=0.999,
        availability=1.0,
        mechanism=ExecutionMechanism(
            mechanism_type="AUDIO_STREAM",
            endpoint_or_target="media_player",
            protocol_or_action="PLAY"
        ),
        description="Plays background ambient audio stream in web client."
    )
    capabilities[c_play_music.name] = c_play_music

    # --- Alternative Implementation Capabilities for Experiment 3 ---
    # CreateOrderAPI (API Implementation)
    c_create_order_api = Capability(
        name="CreateOrderAPI",
        capability_type=CapabilityType.API,
        inputs=[
            InputSpec(name="cart_id", data_type="UUID", domain="valid UUIDs", required=True)
        ],
        outputs=[
            OutputSpec(name="order_id", data_type="UUID", domain="valid UUIDs")
        ],
        preconditions=[
            Precondition(variable="Cart.exists", operator="==", value=True),
            Precondition(variable="Cart.item_count", operator=">", value=0),
            Precondition(variable="Cart.locked", operator="==", value=False)
        ],
        effects=[
            Effect(variable="Order.exists", value=True, operation="SET"),
            Effect(variable="Order.status", value="CREATED", operation="SET"),
            Effect(variable="Cart.locked", value=True, operation="SET")
        ],
        constraints=[
            Constraint(name="rate_limit", expression="requests_per_sec <= 100", constraint_type="network")
        ],
        resources=[
            Resource(name="Network", resource_type="network", quantity=1.0),
            Resource(name="Database", resource_type="system", quantity=1.0),
            Resource(name="AuthToken", resource_type="security", quantity=1.0)
        ],
        quality=QualityAttributes(
            monetary_cost=0.03,
            execution_time_ms=120.0,
            resource_cost=2.5,
            risk=0.08,
            energy_cost=0.015
        ),
        reliability=0.98,
        availability=0.99,
        mechanism=ExecutionMechanism(
            mechanism_type="REST_API",
            endpoint_or_target="/api/orders/create",
            protocol_or_action="POST"
        ),
        description="Creates order via external REST API service."
    )
    capabilities[c_create_order_api.name] = c_create_order_api

    # CreateOrderDatabase (Direct Database Implementation)
    c_create_order_db = Capability(
        name="CreateOrderDatabase",
        capability_type=CapabilityType.DATABASE,
        inputs=[
            InputSpec(name="cart_id", data_type="UUID", domain="valid UUIDs", required=True)
        ],
        outputs=[
            OutputSpec(name="order_id", data_type="UUID", domain="valid UUIDs")
        ],
        preconditions=[
            Precondition(variable="Cart.exists", operator="==", value=True),
            Precondition(variable="Cart.item_count", operator=">", value=0),
            Precondition(variable="Cart.locked", operator="==", value=False)
        ],
        effects=[
            Effect(variable="Order.exists", value=True, operation="SET"),
            Effect(variable="Order.status", value="CREATED", operation="SET"),
            Effect(variable="Cart.locked", value=True, operation="SET")
        ],
        constraints=[
            Constraint(name="db_connection_pool", expression="active_conns < max_conns", constraint_type="resource")
        ],
        resources=[
            Resource(name="Database", resource_type="system", quantity=1.0)
        ],
        quality=QualityAttributes(
            monetary_cost=0.005,
            execution_time_ms=35.0,
            resource_cost=1.5,
            risk=0.02,
            energy_cost=0.005
        ),
        reliability=0.995,
        availability=1.0,
        mechanism=ExecutionMechanism(
            mechanism_type="DATABASE_INSERT",
            endpoint_or_target="orders_table",
            protocol_or_action="INSERT"
        ),
        description="Creates order via direct atomic database stored transaction."
    )
    capabilities[c_create_order_db.name] = c_create_order_db

    # CreateOrderGUI (GUI / Browser Event Implementation)
    c_create_order_gui = Capability(
        name="CreateOrderGUI",
        capability_type=CapabilityType.GUI,
        inputs=[
            InputSpec(name="cart_id", data_type="UUID", domain="valid UUIDs", required=True)
        ],
        outputs=[
            OutputSpec(name="order_id", data_type="UUID", domain="valid UUIDs")
        ],
        preconditions=[
            Precondition(variable="Cart.exists", operator="==", value=True),
            Precondition(variable="Cart.item_count", operator=">", value=0),
            Precondition(variable="Cart.locked", operator="==", value=False)
        ],
        effects=[
            Effect(variable="Order.exists", value=True, operation="SET"),
            Effect(variable="Order.status", value="CREATED", operation="SET"),
            Effect(variable="Cart.locked", value=True, operation="SET")
        ],
        constraints=[],
        resources=[
            Resource(name="FileSystem", resource_type="hardware", quantity=0.5),
            Resource(name="Network", resource_type="network", quantity=1.0)
        ],
        quality=QualityAttributes(
            monetary_cost=0.00,
            execution_time_ms=250.0,
            resource_cost=3.0,
            risk=0.10,
            energy_cost=0.02
        ),
        reliability=0.96,
        availability=0.98,
        mechanism=ExecutionMechanism(
            mechanism_type="GUI_INTERACTION",
            endpoint_or_target="checkout_submit_btn",
            protocol_or_action="CLICK"
        ),
        description="Creates order via browser UI form submission click."
    )
    capabilities[c_create_order_gui.name] = c_create_order_gui

    # Operational variations for Experiment 5
    c_payment_high_cost_low_rel = Capability(
        name="MakePayment_HighCost_LowRel",
        capability_type=CapabilityType.API,
        inputs=c_make_payment.inputs,
        outputs=c_make_payment.outputs,
        preconditions=c_make_payment.preconditions,
        effects=c_make_payment.effects,
        constraints=c_make_payment.constraints,
        resources=c_make_payment.resources,
        quality=QualityAttributes(
            monetary_cost=0.50,
            execution_time_ms=500.0,
            resource_cost=6.0,
            risk=0.30,
            energy_cost=0.05
        ),
        reliability=0.80,
        availability=1.0,
        mechanism=c_make_payment.mechanism,
        description="Payment capability variant with high monetary cost ($0.50) and reduced reliability (0.80)."
    )
    capabilities[c_payment_high_cost_low_rel.name] = c_payment_high_cost_low_rel

    c_payment_economy = Capability(
        name="MakePayment_Economy",
        capability_type=CapabilityType.API,
        inputs=c_make_payment.inputs,
        outputs=c_make_payment.outputs,
        preconditions=c_make_payment.preconditions,
        effects=c_make_payment.effects,
        constraints=c_make_payment.constraints,
        resources=c_make_payment.resources,
        quality=QualityAttributes(
            monetary_cost=0.01,
            execution_time_ms=300.0,
            resource_cost=2.0,
            risk=0.15,
            energy_cost=0.01
        ),
        reliability=0.92,
        availability=0.95,
        mechanism=c_make_payment.mechanism,
        description="Budget payment gateway with lowest cost but modest reliability."
    )
    capabilities[c_payment_economy.name] = c_payment_economy

    c_payment_enterprise = Capability(
        name="MakePayment_Enterprise",
        capability_type=CapabilityType.API,
        inputs=c_make_payment.inputs,
        outputs=c_make_payment.outputs,
        preconditions=c_make_payment.preconditions,
        effects=c_make_payment.effects,
        constraints=c_make_payment.constraints,
        resources=c_make_payment.resources,
        quality=QualityAttributes(
            monetary_cost=0.15,
            execution_time_ms=100.0,
            resource_cost=5.0,
            risk=0.02,
            energy_cost=0.03
        ),
        reliability=0.999,
        availability=1.0,
        mechanism=c_make_payment.mechanism,
        description="Enterprise multi-region payment gateway with ultra-high reliability and low latency."
    )
    capabilities[c_payment_enterprise.name] = c_payment_enterprise

    app = Application(
        name="ECommerceOrderProcessingApp",
        state_space_schema=state_space_schema,
        capabilities=capabilities,
        initial_state=initial_state,
        goal=goal,
        available_resources=available_resources,
        global_constraints=global_constraints
    )

    return app, capabilities


def export_dataset(app: Application, data_dir: str = "data") -> Tuple[str, str]:
    """
    Exports the formal application and capability dataset into JSON and CSV formats.
    """
    os.makedirs(data_dir, exist_ok=True)
    json_path = os.path.join(data_dir, "capabilities.json")
    csv_path = os.path.join(data_dir, "capabilities.csv")

    # 1. Export JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(app.to_dict(), f, indent=2)

    # 2. Export CSV summary
    rows = []
    for cap in app.capabilities.values():
        rows.append({
            "name": cap.name,
            "type": cap.capability_type.value,
            "inputs_count": len(cap.inputs),
            "inputs_list": ", ".join(i.name for i in cap.inputs),
            "outputs_count": len(cap.outputs),
            "outputs_list": ", ".join(o.name for o in cap.outputs),
            "preconditions_count": len(cap.preconditions),
            "effects_count": len(cap.effects),
            "resources_list": ", ".join(r.name for r in cap.resources),
            "monetary_cost": cap.quality.monetary_cost,
            "execution_time_ms": cap.quality.execution_time_ms,
            "resource_cost": cap.quality.resource_cost,
            "risk": cap.quality.risk,
            "reliability": cap.reliability,
            "availability": cap.availability,
            "mechanism_type": cap.mechanism.mechanism_type,
            "mechanism_endpoint": cap.mechanism.endpoint_or_target
        })

    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)

    return json_path, csv_path


if __name__ == "__main__":
    app, caps = build_ecommerce_application()
    j_p, c_p = export_dataset(app)
    print(f"Dataset generated with {len(caps)} capabilities.")
    print(f"JSON saved to: {j_p}")
    print(f"CSV saved to: {c_p}")
