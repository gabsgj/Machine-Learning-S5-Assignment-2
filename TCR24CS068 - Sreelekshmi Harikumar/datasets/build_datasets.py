"""Builds the formally specified application problems (Deliverable 3).

Run:  python datasets/build_datasets.py
Each problem is a JSON file with A = (S, C, S_I, G, R, K) and capabilities
C_i = (T, I, O, P, E, K, R, Q, Rel, A, M).  Natural-language `description`
fields are documentation only and are never read by the embedding.
"""
import json, os

HERE = os.path.dirname(__file__)


# ---- tiny constructors ------------------------------------------------------
def L(var, op, value):
    return {"var": var, "op": op, "value": value}


def E(var, value):
    return {"var": var, "value": value}


def P(name, type_, domain, required=True):
    return {"name": name, "type": type_, "domain": domain, "required": required}


def B(name):
    return {"name": name, "type": "bool"}


def EN(name, *vals):
    return {"name": name, "type": "enum", "values": list(vals)}


def IN(name, lo, hi):
    return {"name": name, "type": "int", "lo": lo, "hi": hi}


def cap(id, type_, desc, pre=(), eff=(), cons=(), inp=(), out=(), res=(),
        t=10, money=0.0, rc=1, risk=0.01, en=0.1, rel=0.99, avail=True,
        window=(0, 24), mech=None, alt=None):
    return {"id": id, "type": type_, "description": desc,
            "inputs": list(inp), "outputs": list(out),
            "preconditions": list(pre), "effects": list(eff),
            "constraints": list(cons), "resources": list(res),
            "qos": {"time_ms": t, "money": money, "resource_cost": rc,
                    "risk": risk, "energy": en},
            "reliability": rel,
            "availability": {"available": avail, "window": list(window)},
            "mechanism": mech or {}, **({"alt_group": alt} if alt else {})}


def dump(name, obj):
    with open(os.path.join(HERE, name), "w") as f:
        json.dump(obj, f, indent=1)
    print("wrote", name, len(obj["capabilities"]), "capabilities")


# =============================================================================
# P0  Minimal problem: exactly the pattern of Experiment 1 in the assignment
# =============================================================================
p0 = {
    "problem_id": "P0_assignment_minimal", "domain": "e-commerce (minimal)",
    "description": "C1=CreateOrder, C2=MakePayment, C3=CancelCart exactly as in Sec.7 Exp.1.",
    "state_variables": [B("Order.exists"), B("Cart.exists"),
                        EN("Payment.status", "NOT_STARTED", "SUCCESS")],
    "initial_state": {"Order.exists": False, "Cart.exists": True,
                      "Payment.status": "NOT_STARTED"},
    "goals": {"main": [L("Payment.status", "==", "SUCCESS")]},
    "goal_text": {"main": "payment succeeds for the order"},
    "resources": ["Database", "PaymentGateway"], "environment": ["Database", "PaymentGateway"],
    "domain_parent": {}, "context_ports": [P("cart_id", "UUID", "valid_uuid")],
    "capabilities": [
        cap("CreateOrder", "API", "create an order from the cart",
            eff=[E("Order.exists", True)], inp=[P("cart_id", "UUID", "valid_uuid")],
            out=[P("order_id", "UUID", "valid_uuid")], res=["Database"],
            t=60, money=0.01, rc=2, rel=0.999, mech={"method": "POST", "endpoint": "/orders"}),
        cap("MakePayment", "API", "pay for the order",
            pre=[L("Order.exists", "==", True)], eff=[E("Payment.status", "SUCCESS")],
            inp=[P("order_id", "UUID", "valid_uuid")], out=[P("payment_id", "UUID", "valid_uuid")],
            res=["PaymentGateway"], t=180, money=0.03, rc=2, rel=0.995,
            mech={"method": "POST", "endpoint": "/payments"}),
        cap("CancelCart", "API", "cancel the cart (only before an order exists)",
            pre=[L("Order.exists", "==", False)], eff=[E("Cart.exists", False)],
            res=["Database"], t=30, rc=1, rel=0.999,
            mech={"method": "DELETE", "endpoint": "/carts"}),
    ]}
dump("P0_assignment_minimal.json", p0)

# =============================================================================
# P1  E-commerce checkout (primary problem)
# =============================================================================
p1_vars = [B("User.authenticated"), EN("User.role", "GUEST", "CUSTOMER", "ADMIN"),
           B("Cart.exists"), IN("Cart.item_count", 0, 99), B("Cart.locked"),
           B("Order.exists"), EN("Order.status", "NONE", "CREATED", "PAID", "SHIPPED", "CANCELLED"),
           B("Inventory.available"), B("Inventory.reserved"),
           EN("Payment.status", "NOT_STARTED", "PENDING", "SUCCESS", "FAILED"),
           B("Payment.within_limit"), B("Notification.sent"), B("Invoice.generated"),
           B("Shipment.dispatched"), B("Catalog.viewed"), B("Audit.logged"), B("Wishlist.updated")]
p1_init = {"User.authenticated": True, "User.role": "CUSTOMER", "Cart.exists": True,
           "Cart.item_count": 3, "Cart.locked": False, "Order.exists": False,
           "Order.status": "NONE", "Inventory.available": True, "Inventory.reserved": False,
           "Payment.status": "NOT_STARTED", "Payment.within_limit": False,
           "Notification.sent": False, "Invoice.generated": False,
           "Shipment.dispatched": False, "Catalog.viewed": False, "Audit.logged": False,
           "Wishlist.updated": False}
UUID = lambda n, req=True: P(n, "UUID", "valid_uuid", req)
role_ok = L("User.role", "in", ["CUSTOMER", "ADMIN"])
pay_pre = [L("Order.exists", "==", True), L("Payment.status", "==", "NOT_STARTED"),
           L("Payment.within_limit", "==", True)]
pay_eff = [E("Payment.status", "SUCCESS"), E("Order.status", "PAID")]
pay_in = [UUID("order_id"), P("amount", "DECIMAL", "decimal"), P("payment_token", "STRING", "token")]
p1 = {
    "problem_id": "P1_ecommerce_checkout", "domain": "e-commerce",
    "description": "Checkout: from an authenticated cart to a paid order and a notification.",
    "state_variables": p1_vars, "initial_state": p1_init,
    "goals": {
        "main": [L("Order.exists", "==", True), L("Payment.status", "==", "SUCCESS"),
                 L("Notification.sent", "==", True)],
        "fulfilment": [L("Order.exists", "==", True), L("Payment.status", "==", "SUCCESS"),
                       L("Invoice.generated", "==", True), L("Shipment.dispatched", "==", True),
                       L("Notification.sent", "==", True)]},
    "goal_text": {"main": "create an order, pay for it and notify the customer",
                  "fulfilment": "create an order, pay for it, invoice it, ship it and notify the customer"},
    "resources": ["Database", "AuthToken", "PaymentGateway", "Network", "FileSystem",
                  "ExternalService", "EventBus", "Browser"],
    "environment": ["Database", "AuthToken", "PaymentGateway", "Network", "FileSystem",
                    "ExternalService", "EventBus", "Browser"],
    "global_constraints": [
        {"id": "K1", "description": "never dispatch before payment succeeded",
         "forbid": [L("Shipment.dispatched", "==", True), L("Payment.status", "!=", "SUCCESS")]}],
    "domain_parent": {"positive_decimal": "decimal", "valid_uuid": "uuid", "pdf": "file"},
    "context_ports": [UUID("cart_id"), P("amount", "DECIMAL", "positive_decimal"),
                      P("payment_token", "STRING", "token"), UUID("user_id")],
    "capabilities": [
        cap("CreateOrder", "API", "create an order from the authenticated customer's cart",
            pre=[L("User.authenticated", "==", True), L("Cart.exists", "==", True),
                 L("Cart.item_count", ">", 0), L("Inventory.available", "==", True),
                 L("Order.exists", "==", False)],
            eff=[E("Order.exists", True), E("Order.status", "CREATED"), E("Cart.locked", True)],
            cons=[role_ok], inp=[UUID("cart_id")], out=[UUID("order_id")],
            res=["Database", "AuthToken", "Network"], t=60, money=0.010, rc=2, risk=0.01,
            en=0.5, rel=0.999, mech={"method": "POST", "endpoint": "/orders"}),
        cap("ReserveInventory", "DATABASE", "reserve stock for the order",
            pre=[L("Order.status", "==", "CREATED"), L("Inventory.available", "==", True)],
            eff=[E("Inventory.reserved", True)], inp=[UUID("order_id")],
            out=[UUID("reservation_id")], res=["Database"], t=35, money=0.002, rc=2,
            risk=0.02, en=0.3, rel=0.998, mech={"operation": "UPDATE", "table": "inventory"}),
        cap("ValidatePaymentLimit", "FUNCTION", "check that the amount is within the limit",
            pre=[L("Order.exists", "==", True)], eff=[E("Payment.within_limit", True)],
            inp=[UUID("order_id"), P("amount", "DECIMAL", "decimal")],
            out=[P("limit_token", "STRING", "token")], t=8, money=0.0, rc=1, risk=0.005,
            en=0.05, rel=0.9995, mech={"function": "validate_limit", "module": "payments"}),
        cap("MakePayment_API", "API", "pay through the payment gateway API",
            pre=pay_pre, eff=pay_eff, cons=[role_ok], inp=pay_in, out=[UUID("payment_id")],
            res=["PaymentGateway", "Network", "AuthToken"], t=180, money=0.030, rc=2,
            risk=0.02, en=0.6, rel=0.995, mech={"method": "POST", "endpoint": "/payments"},
            alt="payment"),
        cap("MakePayment_DB", "DATABASE", "record the payment directly in the ledger",
            pre=pay_pre, eff=pay_eff, cons=[role_ok], inp=pay_in, out=[UUID("payment_id")],
            res=["Database"], t=40, money=0.002, rc=3, risk=0.08, en=0.4, rel=0.970,
            mech={"operation": "INSERT", "table": "ledger"}, alt="payment"),
        cap("MakePayment_GUI", "GUI", "pay by clicking through the checkout page",
            pre=pay_pre, eff=pay_eff, cons=[role_ok], inp=pay_in, out=[UUID("payment_id")],
            res=["Browser", "Network"], t=1500, money=0.0, rc=5, risk=0.05, en=2.0, rel=0.900,
            window=(8, 22), mech={"action": "CLICK", "component": "pay_button"}, alt="payment"),
        cap("GenerateInvoice", "FILE", "render a PDF invoice",
            pre=[L("Payment.status", "==", "SUCCESS")], eff=[E("Invoice.generated", True)],
            inp=[UUID("order_id"), UUID("payment_id")],
            out=[P("invoice_pdf", "FILE", "pdf")], res=["FileSystem"], t=120, money=0.004,
            rc=2, risk=0.01, en=0.8, rel=0.998, mech={"format": "PDF", "template": "invoice_v2"}),
        cap("DispatchShipment", "SERVICE", "hand the parcel to the carrier",
            pre=[L("Payment.status", "==", "SUCCESS"), L("Inventory.reserved", "==", True),
                 L("Invoice.generated", "==", True)],
            eff=[E("Shipment.dispatched", True), E("Order.status", "SHIPPED")],
            inp=[UUID("order_id"), UUID("reservation_id"), P("invoice_pdf", "FILE", "file")],
            out=[P("tracking_no", "STRING", "token")], res=["ExternalService", "Network"],
            t=300, money=0.050, rc=3, risk=0.04, en=1.0, rel=0.985,
            mech={"method": "POST", "endpoint": "/shipments"}),
        cap("SendNotification", "EVENT", "tell the customer the payment succeeded",
            pre=[L("Payment.status", "==", "SUCCESS"), L("Order.exists", "==", True)],
            eff=[E("Notification.sent", True)], inp=[UUID("order_id")], out=[UUID("message_id")],
            res=["EventBus"], t=25, money=0.001, rc=1, risk=0.01, en=0.1, rel=0.999,
            mech={"trigger": "PaymentSucceeded", "handler": "SendNotification"}),
        cap("CancelCart", "API", "cancel the cart (only before an order exists)",
            pre=[L("Order.exists", "==", False), L("Cart.exists", "==", True)],
            eff=[E("Cart.exists", False), E("Cart.item_count", 0)], res=["Database"],
            t=30, rc=1, risk=0.01, en=0.1, rel=0.999, mech={"method": "DELETE", "endpoint": "/carts"}),
        cap("CancelOrder", "API", "cancel an unpaid order",
            pre=[L("Order.exists", "==", True), L("Payment.status", "!=", "SUCCESS")],
            eff=[E("Order.exists", False), E("Order.status", "CANCELLED"),
                 E("Inventory.reserved", False)],
            inp=[UUID("order_id")], res=["Database"], t=70, money=0.005, rc=2, risk=0.03,
            en=0.4, rel=0.995, mech={"method": "DELETE", "endpoint": "/orders"}),
        cap("ViewCatalog", "GUI", "browse the product catalogue",
            eff=[E("Catalog.viewed", True)], res=["Browser", "Network"], t=200, rc=1, risk=0.0,
            en=0.3, rel=0.999, mech={"action": "OPEN", "component": "catalog_page"}),
        cap("UpdateWishlist", "DATABASE", "store a wishlist entry",
            pre=[L("User.authenticated", "==", True)], eff=[E("Wishlist.updated", True)],
            res=["Database"], t=20, rc=1, risk=0.005, en=0.1, rel=0.999,
            mech={"operation": "UPSERT", "table": "wishlist"}),
        cap("AuditLog", "EVENT", "append an audit record",
            eff=[E("Audit.logged", True)], res=["EventBus"], t=5, money=0.0001, rc=1, risk=0.0,
            en=0.02, rel=0.9999, mech={"trigger": "AnyAction", "handler": "AuditWriter"}),
    ]}
dump("P1_ecommerce_checkout.json", p1)

# =============================================================================
# P2  Data / ML pipeline (FILE, COMPUTATION, GPU resource, integer thresholds)
# =============================================================================
p2 = {
    "problem_id": "P2_ml_pipeline", "domain": "data/ML engineering",
    "description": "Load data, clean, engineer features, train, evaluate, deploy, report.",
    "state_variables": [B("Data.loaded"), EN("Data.format", "NONE", "CSV", "PARQUET"),
                        B("Data.schema_valid"), IN("Data.missing_pct", 0, 100),
                        B("Features.ready"), B("Model.trained"), IN("Model.accuracy_pct", 0, 100),
                        B("Model.validated"), B("Model.deployed"), B("Report.generated"),
                        B("Alert.sent"), B("Tmp.cleaned"), B("Logs.compressed"), B("Plot.made")],
    "initial_state": {"Data.loaded": False, "Data.format": "NONE", "Data.schema_valid": False,
                      "Data.missing_pct": 0, "Features.ready": False, "Model.trained": False,
                      "Model.accuracy_pct": 0, "Model.validated": False, "Model.deployed": False,
                      "Report.generated": False, "Alert.sent": False, "Tmp.cleaned": False,
                      "Logs.compressed": False, "Plot.made": False},
    "goals": {"main": [L("Model.deployed", "==", True), L("Report.generated", "==", True)],
              "train_only": [L("Model.trained", "==", True), L("Model.accuracy_pct", ">=", 90)]},
    "goal_text": {"main": "deploy a validated model and generate the evaluation report",
                  "train_only": "train a model with at least ninety percent accuracy"},
    "resources": ["FileSystem", "GPU", "CPU", "Network", "ObjectStore", "ExternalService"],
    "environment": ["FileSystem", "GPU", "CPU", "Network", "ObjectStore", "ExternalService"],
    "global_constraints": [
        {"id": "K1", "description": "never deploy an unvalidated model",
         "forbid": [L("Model.deployed", "==", True), L("Model.validated", "==", False)]}],
    "domain_parent": {"csv_frame": "dataframe", "parquet_frame": "dataframe", "clean_frame": "dataframe"},
    "context_ports": [P("source_path", "STRING", "path")],
    "capabilities": [
        cap("LoadCSV", "FILE", "read the raw dataset from a local csv file",
            pre=[L("Data.loaded", "==", False)],
            eff=[E("Data.loaded", True), E("Data.format", "CSV"), E("Data.missing_pct", 12)],
            inp=[P("source_path", "STRING", "path")], out=[P("raw_df", "DATAFRAME", "csv_frame")],
            res=["FileSystem"], t=900, rc=2, risk=0.01, en=1.0, rel=0.995,
            mech={"reader": "pandas.read_csv"}, alt="load"),
        cap("LoadParquetS3", "SERVICE", "read the raw dataset from object storage",
            pre=[L("Data.loaded", "==", False)],
            eff=[E("Data.loaded", True), E("Data.format", "PARQUET"), E("Data.missing_pct", 12)],
            inp=[P("source_path", "STRING", "path")], out=[P("raw_df", "DATAFRAME", "parquet_frame")],
            res=["ObjectStore", "Network"], t=1500, money=0.002, rc=3, risk=0.03, en=1.5,
            rel=0.985, mech={"method": "GET", "bucket": "datasets"}, alt="load"),
        cap("ValidateSchema", "FUNCTION", "check column names and types",
            pre=[L("Data.loaded", "==", True)], eff=[E("Data.schema_valid", True)],
            inp=[P("raw_df", "DATAFRAME", "dataframe")], res=[], t=40, rc=1, risk=0.005,
            en=0.1, rel=0.999, mech={"function": "validate_schema"}),
        cap("CleanData", "COMPUTATION", "impute / drop missing values",
            pre=[L("Data.loaded", "==", True), L("Data.schema_valid", "==", True),
                 L("Data.missing_pct", ">=", 1)],
            eff=[E("Data.missing_pct", 0)], inp=[P("raw_df", "DATAFRAME", "dataframe")],
            out=[P("clean_df", "DATAFRAME", "clean_frame")], res=["CPU"], t=2500, rc=3,
            risk=0.02, en=3.0, rel=0.99, mech={"function": "impute_median"}),
        cap("ConvertToParquet", "FILE", "convert a csv dataset to parquet",
            pre=[L("Data.format", "==", "CSV")], eff=[E("Data.format", "PARQUET")],
            inp=[P("raw_df", "DATAFRAME", "dataframe")], res=["FileSystem"], t=1100, rc=2,
            risk=0.01, en=1.2, rel=0.995, mech={"writer": "to_parquet"}),
        cap("EngineerFeatures", "COMPUTATION", "derive model features",
            pre=[L("Data.loaded", "==", True), L("Data.schema_valid", "==", True),
                 L("Data.missing_pct", "<=", 5)],
            eff=[E("Features.ready", True)], inp=[P("clean_df", "DATAFRAME", "dataframe")],
            out=[P("feature_matrix", "MATRIX", "dense")], res=["CPU"], t=4000, rc=3,
            risk=0.02, en=5.0, rel=0.99, mech={"function": "build_features"}),
        cap("TrainModel_GPU", "COMPUTATION", "train the model on a GPU",
            pre=[L("Features.ready", "==", True)],
            eff=[E("Model.trained", True), E("Model.accuracy_pct", 93)],
            inp=[P("feature_matrix", "MATRIX", "dense")], out=[P("model_blob", "FILE", "model")],
            res=["GPU", "FileSystem"], t=20000, money=0.40, rc=8, risk=0.03, en=60.0,
            rel=0.97, mech={"device": "cuda", "framework": "torch"}, alt="train"),
        cap("TrainModel_CPU", "COMPUTATION", "train the model on CPU only",
            pre=[L("Features.ready", "==", True)],
            eff=[E("Model.trained", True), E("Model.accuracy_pct", 91)],
            inp=[P("feature_matrix", "MATRIX", "dense")], out=[P("model_blob", "FILE", "model")],
            res=["CPU", "FileSystem"], t=240000, money=0.05, rc=6, risk=0.02, en=300.0,
            rel=0.99, mech={"device": "cpu", "framework": "sklearn"}, alt="train"),
        cap("EvaluateModel", "COMPUTATION", "evaluate on the hold-out set",
            pre=[L("Model.trained", "==", True)], eff=[E("Model.validated", True)],
            inp=[P("model_blob", "FILE", "file")], out=[P("metrics", "JSON", "metrics")],
            res=["CPU"], t=1500, rc=2, risk=0.01, en=2.0, rel=0.995,
            mech={"function": "evaluate_holdout"}),
        cap("DeployModel", "SERVICE", "publish the model behind the serving endpoint",
            pre=[L("Model.trained", "==", True), L("Model.validated", "==", True)],
            eff=[E("Model.deployed", True)], cons=[L("Model.accuracy_pct", ">=", 90)],
            inp=[P("model_blob", "FILE", "file")], out=[P("endpoint_url", "STRING", "url")],
            res=["ExternalService", "Network"], t=6000, money=0.10, rc=4, risk=0.06, en=4.0,
            rel=0.98, mech={"method": "PUT", "endpoint": "/models"}),
        cap("GenerateReport", "FILE", "write the evaluation report",
            pre=[L("Model.validated", "==", True)], eff=[E("Report.generated", True)],
            inp=[P("metrics", "JSON", "metrics")], out=[P("report_pdf", "FILE", "pdf")],
            res=["FileSystem"], t=800, rc=1, risk=0.005, en=0.6, rel=0.998,
            mech={"format": "PDF", "template": "model_card"}),
        cap("SendSlackAlert", "MESSAGE", "announce the deployment",
            pre=[L("Model.deployed", "==", True)], eff=[E("Alert.sent", True)],
            inp=[P("endpoint_url", "STRING", "url")], res=["Network"], t=300, rc=1, risk=0.01,
            en=0.1, rel=0.99, mech={"channel": "ml-ops", "method": "webhook"}),
        cap("ClearTempFiles", "FILE", "delete temporary files", eff=[E("Tmp.cleaned", True)],
            res=["FileSystem"], t=100, rc=1, risk=0.01, en=0.2, rel=0.999,
            mech={"command": "rm_tmp"}),
        cap("CompressLogs", "FILE", "gzip old logs", eff=[E("Logs.compressed", True)],
            res=["FileSystem"], t=600, rc=1, risk=0.0, en=0.8, rel=0.999,
            mech={"command": "gzip_logs"}),
        cap("PlotTSNE", "COMPUTATION", "plot a t-SNE projection of the features",
            pre=[L("Features.ready", "==", True)], eff=[E("Plot.made", True)],
            inp=[P("feature_matrix", "MATRIX", "dense")], res=["CPU"], t=8000, rc=3, risk=0.01,
            en=9.0, rel=0.99, mech={"function": "tsne_plot"}),
    ]}
dump("P2_ml_pipeline.json", p2)

# =============================================================================
# P3  Loan application (SERVICE, MESSAGE, enum/int guards, human-in-loop window)
# =============================================================================
p3 = {
    "problem_id": "P3_loan_approval", "domain": "banking / loan processing",
    "description": "From an application to a signed and disbursed loan with a decision e-mail.",
    "state_variables": [B("App.submitted"), B("Docs.uploaded"),
                        EN("Applicant.identity", "UNVERIFIED", "VERIFIED", "REJECTED"),
                        B("Credit.checked"), EN("Risk.band", "UNSET", "LOW", "MEDIUM", "HIGH"),
                        EN("Loan.decision", "PENDING", "APPROVED", "DECLINED"),
                        IN("Applicant.income", 0, 500000), IN("Loan.amount", 0, 1000000),
                        B("Contract.signed"), B("Funds.disbursed"), B("Email.sent"),
                        B("Archive.done"), B("Marketing.updated")],
    "initial_state": {"App.submitted": False, "Docs.uploaded": False,
                      "Applicant.identity": "UNVERIFIED", "Credit.checked": False,
                      "Risk.band": "UNSET", "Loan.decision": "PENDING",
                      "Applicant.income": 60000, "Loan.amount": 20000,
                      "Contract.signed": False, "Funds.disbursed": False, "Email.sent": False,
                      "Archive.done": False, "Marketing.updated": False},
    "goals": {"main": [L("Funds.disbursed", "==", True), L("Email.sent", "==", True)],
              "decline": [L("Loan.decision", "==", "DECLINED"), L("Email.sent", "==", True)]},
    "goal_text": {"main": "disburse the approved loan and e-mail the applicant",
                  "decline": "decline the application and e-mail the applicant"},
    "resources": ["Browser", "ExternalService", "PaymentGateway", "Network", "Database", "FileSystem",
                  "MailServer"],
    "environment": ["Browser", "ExternalService", "PaymentGateway", "Network", "Database",
                    "FileSystem", "MailServer"],
    "global_constraints": [
        {"id": "K1", "description": "never disburse without a signed contract",
         "forbid": [L("Funds.disbursed", "==", True), L("Contract.signed", "==", False)]}],
    "domain_parent": {"pdf": "file"},
    "context_ports": [P("applicant_data", "JSON", "form")],
    "capabilities": [
        cap("SubmitApplication", "GUI", "applicant submits the web form",
            pre=[L("App.submitted", "==", False)], eff=[E("App.submitted", True)],
            inp=[P("applicant_data", "JSON", "form")], out=[UUID("application_id")],
            res=["Browser", "Network"], t=1200, rc=2, risk=0.01, en=0.5, rel=0.995,
            mech={"action": "CLICK", "component": "submit_button"}),
        cap("UploadDocuments", "FILE", "upload proof of identity and income",
            pre=[L("App.submitted", "==", True)], eff=[E("Docs.uploaded", True)],
            inp=[UUID("application_id")], out=[P("doc_bundle", "FILE", "pdf")],
            res=["FileSystem", "Network"], t=2500, rc=2, risk=0.02, en=1.0, rel=0.99,
            mech={"operation": "UPLOAD", "path": "/docs"}),
        cap("VerifyIdentity_API", "API", "automated identity check",
            pre=[L("Docs.uploaded", "==", True), L("Applicant.identity", "==", "UNVERIFIED")],
            eff=[E("Applicant.identity", "VERIFIED")], inp=[P("doc_bundle", "FILE", "file")],
            out=[P("kyc_report", "JSON", "kyc")], res=["ExternalService", "Network"],
            t=900, money=0.50, rc=2, risk=0.04, en=0.4, rel=0.980,
            mech={"method": "POST", "endpoint": "/kyc"}, alt="verify"),
        cap("VerifyIdentity_Manual", "GUI", "officer reviews documents by hand",
            pre=[L("Docs.uploaded", "==", True), L("Applicant.identity", "==", "UNVERIFIED")],
            eff=[E("Applicant.identity", "VERIFIED")], inp=[P("doc_bundle", "FILE", "file")],
            out=[P("kyc_report", "JSON", "kyc")], res=["Browser"], t=600000, money=4.0, rc=5,
            risk=0.01, en=2.0, rel=0.995, window=(9, 17),
            mech={"action": "REVIEW", "component": "officer_console"}, alt="verify"),
        cap("FetchCreditScore", "API", "query the credit bureau",
            pre=[L("Applicant.identity", "==", "VERIFIED")], eff=[E("Credit.checked", True)],
            inp=[P("kyc_report", "JSON", "kyc")], out=[P("credit_report", "JSON", "bureau")],
            res=["ExternalService", "Network"], t=1100, money=0.75, rc=2, risk=0.03, en=0.4,
            rel=0.985, mech={"method": "GET", "endpoint": "/bureau"}),
        cap("AssessRisk", "COMPUTATION", "score and band the applicant",
            pre=[L("Credit.checked", "==", True)], eff=[E("Risk.band", "LOW")],
            inp=[P("credit_report", "JSON", "bureau")], out=[P("risk_score", "DECIMAL", "decimal")],
            res=["Database"], t=300, rc=2, risk=0.02, en=0.5, rel=0.995,
            mech={"function": "risk_model_v3"}),
        cap("ApproveLoan", "SERVICE", "approve within policy",
            pre=[L("Risk.band", "in", ["LOW", "MEDIUM"]), L("Loan.decision", "==", "PENDING")],
            eff=[E("Loan.decision", "APPROVED")],
            cons=[L("Loan.amount", "<=", 50000), L("Applicant.income", ">=", 30000)],
            inp=[P("risk_score", "DECIMAL", "decimal")], res=["Database"], t=200, rc=2,
            risk=0.05, en=0.3, rel=0.995, mech={"method": "POST", "endpoint": "/decisions/approve"}),
        cap("DeclineLoan", "SERVICE", "decline the application",
            pre=[L("Risk.band", "!=", "UNSET"), L("Loan.decision", "==", "PENDING")],
            eff=[E("Loan.decision", "DECLINED")], inp=[P("risk_score", "DECIMAL", "decimal")],
            res=["Database"], t=200, rc=2, risk=0.02, en=0.3, rel=0.995,
            mech={"method": "POST", "endpoint": "/decisions/decline"}),
        cap("SignContract", "API", "applicant e-signs the loan contract",
            pre=[L("Loan.decision", "==", "APPROVED")], eff=[E("Contract.signed", True)],
            inp=[UUID("application_id")], out=[P("contract_pdf", "FILE", "pdf")],
            res=["ExternalService", "Network"], t=1800, money=0.30, rc=2, risk=0.03, en=0.4,
            rel=0.99, mech={"method": "POST", "endpoint": "/esign"}),
        cap("DisburseFunds", "SERVICE", "transfer the loan amount",
            pre=[L("Contract.signed", "==", True), L("Loan.decision", "==", "APPROVED")],
            eff=[E("Funds.disbursed", True)], cons=[L("Loan.amount", "<=", 50000)],
            inp=[P("contract_pdf", "FILE", "file")], out=[UUID("transfer_id")],
            res=["PaymentGateway", "Network"], t=2200, money=1.00, rc=3, risk=0.06, en=0.6,
            rel=0.99, mech={"method": "POST", "endpoint": "/transfers"}),
        cap("SendDecisionEmail", "MESSAGE", "e-mail the decision to the applicant",
            pre=[L("Loan.decision", "!=", "PENDING")], eff=[E("Email.sent", True)],
            res=["MailServer"], t=250, money=0.001, rc=1, risk=0.01, en=0.1, rel=0.995,
            mech={"protocol": "SMTP", "template": "decision"}),
        cap("ArchiveRecords", "FILE", "archive the case file", eff=[E("Archive.done", True)],
            res=["FileSystem"], t=400, rc=1, risk=0.0, en=0.5, rel=0.999,
            mech={"operation": "ARCHIVE", "path": "/archive"}),
        cap("UpdateMarketingPrefs", "DATABASE", "store marketing preferences",
            eff=[E("Marketing.updated", True)], res=["Database"], t=20, rc=1, risk=0.0, en=0.1,
            rel=0.999, mech={"operation": "UPSERT", "table": "marketing"}),
    ]}
dump("P3_loan_approval.json", p3)
