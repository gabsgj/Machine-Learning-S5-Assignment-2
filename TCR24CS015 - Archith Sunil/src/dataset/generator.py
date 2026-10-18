from __future__ import annotations
import json
import os
from typing import Dict, List, Any

from src.models.state import StateVariable, StateVariableType, ApplicationState
from src.models.goal import ComparisonOp, GoalCondition, GoalSpecification
from src.models.capability import (
    Capability, CapabilityType, InputSpec, OutputSpec,
    Precondition, Effect, CapabilityConstraint, QualityAttributes, ExecutionMechanism
)
from src.models.problem import ApplicationProblem


def create_ecommerce_benchmark() -> ApplicationProblem:
    """
    Constructs the canonical e-commerce application problem
    formally specified in Assignment 2 (Pages 3-7 & 10).
    """
    state_vars = [
        StateVariable("User.authenticated", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("User.role", StateVariableType.ENUM, domain=["CUSTOMER", "ADMIN", "GUEST"], default_value="CUSTOMER"),
        StateVariable("Cart.exists", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("Cart.item_count", StateVariableType.INTEGER, default_value=0),
        StateVariable("Cart.locked", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("Order.exists", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("Order.status", StateVariableType.ENUM, domain=["NONE", "CREATED", "PENDING", "PAID", "CANCELLED", "SHIPPED"], default_value="NONE"),
        StateVariable("Payment.status", StateVariableType.ENUM, domain=["NOT_STARTED", "PROCESSING", "SUCCESS", "FAILED"], default_value="NOT_STARTED"),
        StateVariable("Inventory.available", StateVariableType.BOOLEAN, default_value=True),
        StateVariable("Notification.sent", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("Discount.applied", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("Telemetry.processed", StateVariableType.BOOLEAN, default_value=False),
    ]

    initial_state = ApplicationState(
        name="InitialState_S_I",
        values={
            "User.authenticated": True,
            "User.role": "CUSTOMER",
            "Cart.exists": True,
            "Cart.item_count": 3,
            "Cart.locked": False,
            "Order.exists": False,
            "Order.status": "NONE",
            "Payment.status": "NOT_STARTED",
            "Inventory.available": True,
            "Notification.sent": False,
            "Discount.applied": False,
            "Telemetry.processed": False,
        }
    )

    goal = GoalSpecification(
        name="Goal_PurchaseAndNotify",
        conditions=[
            GoalCondition("Order.exists", True, ComparisonOp.EQ),
            GoalCondition("Payment.status", "SUCCESS", ComparisonOp.EQ),
            GoalCondition("Notification.sent", True, ComparisonOp.EQ),
        ]
    )

    # Atomic Capabilities
    c1 = Capability(
        id="C1_CreateOrder",
        name="CreateOrder",
        type=CapabilityType.API,
        inputs=[
            InputSpec("cart_id", "UUID", "valid UUIDs", True),
            InputSpec("user_id", "UUID", "valid UUIDs", True)
        ],
        outputs=[
            OutputSpec("order_id", "UUID", "valid UUIDs"),
            OutputSpec("total_amount", "FLOAT", "positive decimals")
        ],
        preconditions=[
            Precondition("Cart.exists", True),
            Precondition("Inventory.available", True)
        ],
        effects=[
            Effect("Order.exists", True),
            Effect("Order.status", "CREATED"),
            Effect("Cart.locked", True)
        ],
        resources=["Database", "Network"],
        quality=QualityAttributes(time_ms=100.0, resource_cost=2.0, monetary_cost=0.01, risk=0.02, energy_cost=0.01),
        reliability=0.99,
        availability=1.0,
        mechanism=ExecutionMechanism("HTTP_REST", {"method": "POST", "endpoint": "/orders"}),
        description="Creates an order record from an active shopping cart."
    )

    c2 = Capability(
        id="C2_MakePayment",
        name="MakePayment",
        type=CapabilityType.SERVICE,
        inputs=[
            InputSpec("order_id", "UUID", "valid UUIDs", True),
            InputSpec("total_amount", "FLOAT", "positive decimals", True)
        ],
        outputs=[
            OutputSpec("receipt_id", "UUID", "valid UUIDs"),
            OutputSpec("payment_token", "STRING", "alphanumeric token")
        ],
        preconditions=[
            Precondition("Order.exists", True),
            Precondition("Order.status", "CREATED")
        ],
        effects=[
            Effect("Payment.status", "SUCCESS"),
            Effect("Order.status", "PAID")
        ],
        resources=["PaymentGateway", "Network", "AuthToken"],
        quality=QualityAttributes(time_ms=250.0, resource_cost=3.0, monetary_cost=0.05, risk=0.04, energy_cost=0.02),
        reliability=0.98,
        availability=0.999,
        mechanism=ExecutionMechanism("EXTERNAL_SERVICE", {"provider": "StripeGateway", "action": "charge"}),
        description="Executes payment transaction for created order."
    )

    c3 = Capability(
        id="C3_CancelCart",
        name="CancelCart",
        type=CapabilityType.API,
        inputs=[InputSpec("cart_id", "UUID", "valid UUIDs", True)],
        outputs=[OutputSpec("cancellation_ref", "STRING", "alphanumeric")],
        preconditions=[
            Precondition("Order.exists", False),
            Precondition("Cart.exists", True)
        ],
        effects=[
            Effect("Cart.exists", False),
            Effect("Cart.item_count", 0)
        ],
        resources=["Database", "Network"],
        quality=QualityAttributes(time_ms=60.0, resource_cost=1.0, monetary_cost=0.005, risk=0.01, energy_cost=0.005),
        reliability=0.995,
        availability=1.0,
        mechanism=ExecutionMechanism("HTTP_REST", {"method": "DELETE", "endpoint": "/cart"}),
        description="Cancels the active shopping cart before any order is placed."
    )

    c4 = Capability(
        id="C4_SendNotification",
        name="SendNotification",
        type=CapabilityType.EVENT,
        inputs=[
            InputSpec("receipt_id", "UUID", "valid UUIDs", True),
            InputSpec("order_id", "UUID", "valid UUIDs", True)
        ],
        outputs=[OutputSpec("message_id", "STRING", "dispatch ID")],
        preconditions=[
            Precondition("Payment.status", "SUCCESS")
        ],
        effects=[
            Effect("Notification.sent", True)
        ],
        resources=["EmailService", "Network"],
        quality=QualityAttributes(time_ms=80.0, resource_cost=1.0, monetary_cost=0.002, risk=0.01, energy_cost=0.005),
        reliability=0.99,
        availability=1.0,
        mechanism=ExecutionMechanism("EVENT_DISPATCH", {"trigger": "OrderPaid", "handler": "SendEmail"}),
        description="Sends order confirmation receipt notification to customer."
    )

    c5 = Capability(
        id="C5_ApplyDiscount",
        name="ApplyDiscount",
        type=CapabilityType.FUNCTION,
        inputs=[InputSpec("coupon_code", "STRING", "valid code", True)],
        outputs=[OutputSpec("discount_pct", "FLOAT", "0.0-1.0")],
        preconditions=[
            Precondition("Cart.exists", True),
            Precondition("Cart.locked", False)
        ],
        effects=[
            Effect("Discount.applied", True)
        ],
        resources=["Database"],
        quality=QualityAttributes(time_ms=25.0, resource_cost=0.5, monetary_cost=0.001, risk=0.005, energy_cost=0.001),
        reliability=0.999,
        availability=1.0,
        mechanism=ExecutionMechanism("LOCAL_FUNC", {"module": "pricing", "function": "apply_coupon"}),
        description="Applies promotional discount coupon to unlocked shopping cart."
    )

    # Distractor / Irrelevant Capability 1 (Admin task)
    c6_distractor = Capability(
        id="C6_ExportAuditLog",
        name="ExportAuditLog",
        type=CapabilityType.FILE,
        inputs=[InputSpec("start_date", "STRING", "YYYY-MM-DD", True)],
        outputs=[OutputSpec("audit_csv", "FILE", "CSV export")],
        preconditions=[
            Precondition("User.role", "ADMIN")
        ],
        effects=[
            Effect("Telemetry.processed", True)
        ],
        resources=["FileSystem", "Database"],
        quality=QualityAttributes(time_ms=450.0, resource_cost=5.0, monetary_cost=0.02, risk=0.01, energy_cost=0.04),
        reliability=0.97,
        availability=0.99,
        mechanism=ExecutionMechanism("FILE_IO", {"path": "/var/log/audit.csv", "format": "CSV"}),
        description="Exports administrative system audit logs (irrelevant to customer purchase)."
    )

    # Distractor / Irrelevant Capability 2 (Weather fetch)
    c7_distractor = Capability(
        id="C7_ProcessWeatherTelemetry",
        name="ProcessWeatherTelemetry",
        type=CapabilityType.COMPUTATION,
        inputs=[InputSpec("lat", "FLOAT", "coordinate", True), InputSpec("lon", "FLOAT", "coordinate", True)],
        outputs=[OutputSpec("forecast", "STRING", "weather string")],
        preconditions=[],
        effects=[
            Effect("Telemetry.processed", True)
        ],
        resources=["Network", "ExternalService"],
        quality=QualityAttributes(time_ms=300.0, resource_cost=1.5, monetary_cost=0.01, risk=0.02, energy_cost=0.02),
        reliability=0.95,
        availability=0.98,
        mechanism=ExecutionMechanism("EXTERNAL_API", {"endpoint": "https://weather.service/forecast"}),
        description="Processes meteorology telemetry feed (completely orthogonal to e-commerce)."
    )

    capabilities = [c1, c2, c3, c4, c5, c6_distractor, c7_distractor]
    resources = ["Database", "Network", "PaymentGateway", "AuthToken", "EmailService", "FileSystem", "ExternalService"]

    return ApplicationProblem(
        name="ECommerce_OrderFulfillment",
        description="Canonical e-commerce capability composition domain with purchasing pipeline and distractors.",
        state_variables=state_vars,
        initial_state=initial_state,
        goal=goal,
        available_resources=resources,
        global_constraints=[
            CapabilityConstraint("RoleCheck", "User.role in {CUSTOMER, ADMIN}", "SECURITY")
        ],
        capabilities=capabilities
    )


def create_alternative_implementations_benchmark() -> List[Capability]:
    """
    Constructs capabilities that perform identical state transformations
    via different execution mechanisms (API, Database, GUI) for Experiment 3.
    """
    # 1. CreateOrder via API
    c_api = Capability(
        id="CreateOrder_API",
        name="CreateOrder (REST API)",
        type=CapabilityType.API,
        inputs=[InputSpec("cart_id", "UUID", "valid UUIDs", True)],
        outputs=[OutputSpec("order_id", "UUID", "valid UUIDs")],
        preconditions=[Precondition("Cart.exists", True)],
        effects=[Effect("Order.exists", True), Effect("Order.status", "CREATED")],
        resources=["Database", "Network"],
        quality=QualityAttributes(time_ms=120.0, resource_cost=2.0, monetary_cost=0.02, risk=0.02, energy_cost=0.01),
        reliability=0.99,
        availability=1.0,
        mechanism=ExecutionMechanism("HTTP_API", {"method": "POST", "endpoint": "/api/v2/orders"}),
        description="Microservice REST endpoint creating order record."
    )

    # 2. CreateOrder via Database (Direct SQL procedure)
    c_db = Capability(
        id="CreateOrder_DB",
        name="CreateOrder (Direct DB SQL)",
        type=CapabilityType.DATABASE,
        inputs=[InputSpec("cart_id", "UUID", "valid UUIDs", True)],
        outputs=[OutputSpec("order_id", "UUID", "valid UUIDs")],
        preconditions=[Precondition("Cart.exists", True)],
        effects=[Effect("Order.exists", True), Effect("Order.status", "CREATED")],
        resources=["Database"],
        quality=QualityAttributes(time_ms=18.0, resource_cost=1.0, monetary_cost=0.001, risk=0.01, energy_cost=0.003),
        reliability=0.999,
        availability=1.0,
        mechanism=ExecutionMechanism("SQL_PROCEDURE", {"procedure": "sp_create_order", "table": "orders"}),
        description="Direct relational database stored procedure inserting order."
    )

    # 3. CreateOrder via GUI (Browser Automation / UI click)
    c_gui = Capability(
        id="CreateOrder_GUI",
        name="CreateOrder (Web GUI Automation)",
        type=CapabilityType.GUI,
        inputs=[InputSpec("cart_id", "UUID", "valid UUIDs", True)],
        outputs=[OutputSpec("order_id", "UUID", "valid UUIDs")],
        preconditions=[Precondition("Cart.exists", True)],
        effects=[Effect("Order.exists", True), Effect("Order.status", "CREATED")],
        resources=["Network", "AuthToken"],
        quality=QualityAttributes(time_ms=650.0, resource_cost=4.0, monetary_cost=0.00, risk=0.08, energy_cost=0.05),
        reliability=0.94,
        availability=0.99,
        mechanism=ExecutionMechanism("SELENIUM_GUI", {"action": "CLICK", "selector": "#btn-confirm-order"}),
        description="Headless browser robotic process automation clicking checkout button."
    )

    # Payment variants
    p_api = Capability(
        id="MakePayment_API",
        name="MakePayment (Stripe API)",
        type=CapabilityType.API,
        inputs=[InputSpec("order_id", "UUID", "valid UUIDs", True)],
        outputs=[OutputSpec("receipt_id", "UUID", "valid UUIDs")],
        preconditions=[Precondition("Order.exists", True)],
        effects=[Effect("Payment.status", "SUCCESS")],
        resources=["PaymentGateway", "Network"],
        quality=QualityAttributes(time_ms=220.0, resource_cost=2.5, monetary_cost=0.04, risk=0.03, energy_cost=0.01),
        reliability=0.985,
        availability=1.0,
        mechanism=ExecutionMechanism("HTTP_API", {"endpoint": "https://api.stripe.com/v1/charges"}),
        description="Payment processing via Stripe REST API."
    )

    p_gui = Capability(
        id="MakePayment_GUI",
        name="MakePayment (GUI Checkout Form)",
        type=CapabilityType.GUI,
        inputs=[InputSpec("order_id", "UUID", "valid UUIDs", True)],
        outputs=[OutputSpec("receipt_id", "UUID", "valid UUIDs")],
        preconditions=[Precondition("Order.exists", True)],
        effects=[Effect("Payment.status", "SUCCESS")],
        resources=["Network"],
        quality=QualityAttributes(time_ms=850.0, resource_cost=5.0, monetary_cost=0.01, risk=0.09, energy_cost=0.06),
        reliability=0.92,
        availability=0.98,
        mechanism=ExecutionMechanism("SELENIUM_GUI", {"action": "SUBMIT", "selector": "#payment-form"}),
        description="Automated GUI form interaction for payment entry."
    )

    return [c_api, c_db, c_gui, p_api, p_gui]


def create_cloud_devops_benchmark() -> ApplicationProblem:
    """
    Constructs a Cloud DevOps / Infrastructure as Code capability problem.
    """
    state_vars = [
        StateVariable("VPC.configured", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("Subnet.created", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("SecurityGroup.open", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("VM.provisioned", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("Storage.attached", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("App.deployed", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("HealthCheck.passing", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("Alert.active", StateVariableType.BOOLEAN, default_value=False),
    ]

    initial_state = ApplicationState(
        name="CloudInitialState",
        values={
            "VPC.configured": False,
            "Subnet.created": False,
            "SecurityGroup.open": False,
            "VM.provisioned": False,
            "Storage.attached": False,
            "App.deployed": False,
            "HealthCheck.passing": False,
            "Alert.active": False,
        }
    )

    goal = GoalSpecification(
        name="Goal_ServiceOnline",
        conditions=[
            GoalCondition("App.deployed", True),
            GoalCondition("HealthCheck.passing", True)
        ]
    )

    k1 = Capability(
        id="DevOps_CreateVPC",
        name="CreateVPC",
        type=CapabilityType.API,
        preconditions=[],
        effects=[Effect("VPC.configured", True), Effect("Subnet.created", True)],
        resources=["Network"],
        quality=QualityAttributes(time_ms=800.0, resource_cost=1.0, monetary_cost=0.05, risk=0.01, energy_cost=0.02),
        reliability=0.999,
        availability=1.0,
        mechanism=ExecutionMechanism("TERRAFORM_PROVIDER", {"provider": "aws_vpc"}),
    )

    k2 = Capability(
        id="DevOps_ProvisionVM",
        name="ProvisionVM",
        type=CapabilityType.SERVICE,
        preconditions=[Precondition("VPC.configured", True), Precondition("Subnet.created", True)],
        effects=[Effect("VM.provisioned", True)],
        resources=["Network", "GPU"],
        quality=QualityAttributes(time_ms=2500.0, resource_cost=8.0, monetary_cost=0.25, risk=0.03, energy_cost=0.15),
        reliability=0.98,
        availability=0.995,
        mechanism=ExecutionMechanism("CLOUD_API", {"action": "RunInstances", "instance_type": "g5.xlarge"}),
    )

    k3 = Capability(
        id="DevOps_AttachStorage",
        name="AttachStorage",
        type=CapabilityType.SERVICE,
        preconditions=[Precondition("VM.provisioned", True)],
        effects=[Effect("Storage.attached", True)],
        resources=["FileSystem"],
        quality=QualityAttributes(time_ms=450.0, resource_cost=3.0, monetary_cost=0.08, risk=0.01, energy_cost=0.03),
        reliability=0.995,
        availability=1.0,
        mechanism=ExecutionMechanism("CLOUD_API", {"action": "AttachVolume"}),
    )

    k4 = Capability(
        id="DevOps_DeployApp",
        name="DeployApp",
        type=CapabilityType.FUNCTION,
        preconditions=[Precondition("VM.provisioned", True), Precondition("Storage.attached", True)],
        effects=[Effect("App.deployed", True)],
        resources=["Network", "AuthToken"],
        quality=QualityAttributes(time_ms=1200.0, resource_cost=4.0, monetary_cost=0.02, risk=0.04, energy_cost=0.08),
        reliability=0.97,
        availability=1.0,
        mechanism=ExecutionMechanism("CONTAINER_ORCHESTRATOR", {"runtime": "docker", "image": "api:v2"}),
    )

    k5 = Capability(
        id="DevOps_RunHealthCheck",
        name="RunHealthCheck",
        type=CapabilityType.API,
        preconditions=[Precondition("App.deployed", True)],
        effects=[Effect("HealthCheck.passing", True)],
        resources=["Network"],
        quality=QualityAttributes(time_ms=150.0, resource_cost=1.0, monetary_cost=0.001, risk=0.01, energy_cost=0.01),
        reliability=0.99,
        availability=1.0,
        mechanism=ExecutionMechanism("HTTP_HEALTH", {"endpoint": "/healthz"}),
    )

    # Distractor capability
    k6_distractor = Capability(
        id="DevOps_MineCrypto",
        name="MineCryptoWorker",
        type=CapabilityType.COMPUTATION,
        preconditions=[Precondition("VM.provisioned", True)],
        effects=[Effect("Alert.active", True)],
        resources=["GPU"],
        quality=QualityAttributes(time_ms=10000.0, resource_cost=10.0, monetary_cost=1.50, risk=0.95, energy_cost=5.0),
        reliability=0.50,
        availability=0.90,
        mechanism=ExecutionMechanism("BACKGROUND_DAEMON", {"binary": "xmrig"}),
        description="Unauthorized worker that consumes energy and triggers alerts."
    )

    return ApplicationProblem(
        name="CloudInfrastructure_Deployment",
        description="Cloud DevOps infrastructure provisioning and microservice deployment benchmark.",
        state_variables=state_vars,
        initial_state=initial_state,
        goal=goal,
        available_resources=["Network", "GPU", "FileSystem", "AuthToken"],
        capabilities=[k1, k2, k3, k4, k5, k6_distractor]
    )


def create_fintech_kyc_benchmark() -> ApplicationProblem:
    """
    Constructs a FinTech KYC, Compliance & Settlement capability problem.
    """
    state_vars = [
        StateVariable("Identity.submitted", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("Documents.verified", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("Risk.assessed", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("AML.cleared", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("Account.activated", StateVariableType.BOOLEAN, default_value=False),
        StateVariable("Transfer.settled", StateVariableType.BOOLEAN, default_value=False),
    ]

    initial_state = ApplicationState(
        name="FintechInitialState",
        values={
            "Identity.submitted": True,
            "Documents.verified": False,
            "Risk.assessed": False,
            "AML.cleared": False,
            "Account.activated": False,
            "Transfer.settled": False,
        }
    )

    goal = GoalSpecification(
        name="Goal_KYCAndSettlement",
        conditions=[
            GoalCondition("Account.activated", True),
            GoalCondition("Transfer.settled", True)
        ]
    )

    f1 = Capability(
        id="FinTech_VerifyDocs",
        name="VerifyDocuments",
        type=CapabilityType.SERVICE,
        preconditions=[Precondition("Identity.submitted", True)],
        effects=[Effect("Documents.verified", True)],
        resources=["ExternalService", "Network"],
        quality=QualityAttributes(time_ms=1500.0, resource_cost=2.0, monetary_cost=0.50, risk=0.02, energy_cost=0.03),
        reliability=0.98,
        availability=0.999,
        mechanism=ExecutionMechanism("ID_VERIFICATION_SERVICE", {"provider": "Onfido"}),
    )

    f2 = Capability(
        id="FinTech_AMLScreening",
        name="AMLScreening",
        type=CapabilityType.SERVICE,
        preconditions=[Precondition("Documents.verified", True)],
        effects=[Effect("AML.cleared", True), Effect("Risk.assessed", True)],
        resources=["ExternalService", "Database"],
        quality=QualityAttributes(time_ms=800.0, resource_cost=2.0, monetary_cost=0.30, risk=0.01, energy_cost=0.02),
        reliability=0.995,
        availability=1.0,
        mechanism=ExecutionMechanism("AML_WATCHLIST", {"provider": "LexisNexis"}),
    )

    f3 = Capability(
        id="FinTech_ActivateAccount",
        name="ActivateAccount",
        type=CapabilityType.DATABASE,
        preconditions=[Precondition("AML.cleared", True), Precondition("Risk.assessed", True)],
        effects=[Effect("Account.activated", True)],
        resources=["Database"],
        quality=QualityAttributes(time_ms=50.0, resource_cost=1.0, monetary_cost=0.005, risk=0.005, energy_cost=0.005),
        reliability=0.999,
        availability=1.0,
        mechanism=ExecutionMechanism("CORE_BANKING_DB", {"table": "accounts", "action": "ACTIVATE"}),
    )

    f4 = Capability(
        id="FinTech_InstantSettlement",
        name="InstantSettlement",
        type=CapabilityType.SERVICE,
        preconditions=[Precondition("Account.activated", True)],
        effects=[Effect("Transfer.settled", True)],
        resources=["PaymentGateway", "Network"],
        quality=QualityAttributes(time_ms=350.0, resource_cost=3.0, monetary_cost=0.15, risk=0.01, energy_cost=0.02),
        reliability=0.992,
        availability=1.0,
        mechanism=ExecutionMechanism("FEDNOW_ACH", {"network": "FedNow", "type": "INSTANT"}),
    )

    return ApplicationProblem(
        name="Fintech_KYC_Settlement",
        description="Regulated financial customer onboarding and instant payment settlement domain.",
        state_variables=state_vars,
        initial_state=initial_state,
        goal=goal,
        available_resources=["ExternalService", "Database", "PaymentGateway", "Network"],
        capabilities=[f1, f2, f3, f4]
    )


def save_benchmarks_to_disk(data_dir: str = "data"):
    os.makedirs(data_dir, exist_ok=True)

    # 1. E-commerce
    ecom = create_ecommerce_benchmark()
    with open(os.path.join(data_dir, "ecommerce_benchmark.json"), "w") as f:
        json.dump(ecom.to_dict(), f, indent=2)

    # 2. Alternative implementations
    alts = create_alternative_implementations_benchmark()
    with open(os.path.join(data_dir, "alternative_implementations.json"), "w") as f:
        json.dump([c.to_dict() for c in alts], f, indent=2)

    # 3. Cloud DevOps
    devops = create_cloud_devops_benchmark()
    with open(os.path.join(data_dir, "cloud_devops_benchmark.json"), "w") as f:
        json.dump(devops.to_dict(), f, indent=2)

    # 4. FinTech KYC
    fintech = create_fintech_kyc_benchmark()
    with open(os.path.join(data_dir, "fintech_kyc_benchmark.json"), "w") as f:
        json.dump(fintech.to_dict(), f, indent=2)

    print(f"Successfully generated all benchmark datasets in '{data_dir}/'")


if __name__ == "__main__":
    save_benchmarks_to_disk()
