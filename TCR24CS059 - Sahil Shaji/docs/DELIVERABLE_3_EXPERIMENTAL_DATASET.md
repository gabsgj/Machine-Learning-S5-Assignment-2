# Deliverable 3: Experimental Benchmark Datasets

## 1. Dataset Overview

To rigorously evaluate the vector representation across diverse operational environments, we developed four formally specified application problems spanning e-commerce, cloud DevOps, clinical healthcare, and IoT home automation. Each dataset contains formal state variables, goal conditions, atomic capabilities, constraints, resources, and operational quality attributes.

All datasets are serialized into standalone JSON files in `datasets/json/`:
- `ecommerce_problem.json`
- `devops_problem.json`
- `healthcare_problem.json`
- `smarthome_problem.json`

---

## 2. Domain 1: E-Commerce Order-to-Cash (Primary Benchmark)

### 2.1 State Space $\mathcal{S}$ and Initial State $S_I$
- `User.authenticated` (Boolean): `true`
- `User.role` (Categorical: CUSTOMER, ADMIN): `"CUSTOMER"`
- `Cart.exists` (Boolean): `true`
- `Cart.item_count` (Integer): `3`
- `Order.exists` (Boolean): `false`
- `Payment.status` (Categorical: NOT_STARTED, PENDING, SUCCESS, FAILED): `"NOT_STARTED"`
- `Inventory.available` (Boolean): `true`
- `Notification.sent` (Boolean): `false`
- `Order.status` (Categorical: NONE, CREATED, CANCELLED): `"NONE"`

### 2.2 Goal Specification $G$
$$G = \{\text{Order.exists} = \text{true}, \; \text{Payment.status} = \text{"SUCCESS"}, \; \text{Notification.sent} = \text{true}\}$$

### 2.3 Capability Inventory

| Capability | Type | Preconditions | Effects | Inputs $\to$ Outputs | Quality ($T$, Cost, Rel) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CreateOrder_API` | API | Cart.exists=T, Auth=T | Order.exists=T, Order.status=CREATED | cart_id, token $\to$ order_id | 120ms, $0.015, 0.995 |
| `CreateOrder_DB` | DATABASE | Cart.exists=T, Auth=T | Order.exists=T, Order.status=CREATED | cart_id $\to$ order_id | 25ms, $0.003, 0.999 |
| `CreateOrder_GUI` | GUI | Cart.exists=T, Auth=T | Order.exists=T, Order.status=CREATED | cart_id $\to$ order_id | 650ms, $0.050, 0.960 |
| `MakePayment` | SERVICE | Order.exists=T | Payment.status=SUCCESS | order_id, amt $\to$ receipt | 350ms, $0.050, 0.985 |
| `CancelCart` | FUNCTION | Order.exists=F | Cart.exists=F | cart_id $\to$ $\emptyset$ | 30ms, $0.001, 0.999 |
| `SendNotification`| MESSAGE | Payment.status=SUCCESS | Notification.sent=T | order_id, receipt $\to$ notif_id | 80ms, $0.005, 0.992 |
| `CheckInventory` | DATABASE | Cart.exists=T | Inventory.available=T | cart_id $\to$ stock_ok | 45ms, $0.002, 0.999 |
| `UpdateAvatar` | FILE | Auth=T | Avatar.updated=T | img_bytes $\to$ url | 180ms, $0.004, 0.980 |
| `TaxAuditReport` | COMPUTATION | Role=ADMIN | TaxReport.done=T | fiscal_year $\to$ pdf | 2500ms, $0.200, 0.950 |
| `BrowseCatalog` | SERVICE | $\emptyset$ | Catalog.viewed=T | category $\to$ items | 90ms, $0.008, 0.990 |
| `ResetOrderState`| FUNCTION | Order.exists=T | Order.exists=F, Pay=NOT_STARTED | $\emptyset \to \emptyset$ | 40ms, $0.001, 0.990 |

---

## 3. Domain 2: Cloud DevOps CI/CD Pipeline

### 3.1 State Space and Goal
- **Initial State**: `Code.committed=true`, `Lint.passed=false`, `Tests.passed=false`, `Docker.built=false`, `K8s.deployed=false`, `Alert.sent=false`
- **Goal**: `Tests.passed=true`, `Docker.built=true`, `K8s.deployed=true`

### 3.2 Pipeline Capabilities
1. `RunLinter`: Pre: `Code.committed=T` $\implies$ Eff: `Lint.passed=T` (15s, $0.005, Rel=0.99)
2. `RunUnitTests`: Pre: `Lint.passed=T` $\implies$ Eff: `Tests.passed=T` (45s, $0.020, Rel=0.97)
3. `BuildDockerImage`: Pre: `Tests.passed=T` $\implies$ Eff: `Docker.built=T` (60s, $0.040, Rel=0.98)
4. `DeployKubernetes`: Pre: `Docker.built=T` $\implies$ Eff: `K8s.deployed=T` (30s, $0.030, Rel=0.995)
5. `SendSlackAlert`: Pre: `K8s.deployed=T` $\implies$ Eff: `Alert.sent=T` (0.5s, $0.001, Rel=0.999)
6. `BackupPostgresDatabase`: (Irrelevant capability for deployment goal)

---

## 4. Domain 3: Clinical Patient Healthcare Workflow

### 4.1 State Space and Goal
- **Initial State**: `Patient.triaged=true`, `Lab.ordered=false`, `Lab.completed=false`, `Diagnosis.ready=false`, `Prescription.issued=false`, `Pharmacy.dispensed=false`
- **Goal**: `Diagnosis.ready=true`, `Prescription.issued=true`, `Pharmacy.dispensed=true`

### 4.2 Clinical Capabilities
1. `OrderLabTests`: Pre: `Patient.triaged=T` $\implies$ Eff: `Lab.ordered=T` (200ms, $5.0, Rel=0.999)
2. `AnalyzeBiomarkers`: Pre: `Lab.ordered=T` $\implies$ Eff: `Lab.completed=T` (1800s, $45.0, Rel=0.992)
3. `GenerateDiagnosis`: Pre: `Lab.completed=T` $\implies$ Eff: `Diagnosis.ready=T` (150ms, $2.0, Rel=0.985)
4. `IssuePrescription`: Pre: `Diagnosis.ready=T` $\implies$ Eff: `Prescription.issued=T` (300ms, $1.5, Rel=0.998)
5. `DispenseMedication`: Pre: `Prescription.issued=T` $\implies$ Eff: `Pharmacy.dispensed=T` (45s, $12.0, Rel=0.990)
6. `ArchivePatientHistory`: Pre: $\emptyset \implies$ Eff: `Archive.saved=T` (Irrelevant)

---

## 5. Domain 4: Smart Home IoT Automation

### 5.1 State Space and Goal
- **Initial State**: `Motion.detected=true`, `Room.illuminated=false`, `Camera.recording=false`, `Alarm.siren_active=false`, `Guard.dispatched=false`
- **Goal**: `Room.illuminated=true`, `Camera.recording=true`, `Alarm.siren_active=true`

### 5.2 IoT Capabilities
1. `TurnOnSmartBulb`: Pre: `Motion.detected=T` $\implies$ Eff: `Room.illuminated=T` (50ms, $0.0001, Rel=0.999)
2. `StartCameraRecording`: Pre: `Motion.detected=T` $\implies$ Eff: `Camera.recording=T` (120ms, $0.0005, Rel=0.995)
3. `TriggerAlarmSiren`: Pre: `Camera.recording=T` $\implies$ Eff: `Alarm.siren_active=T` (20ms, $0.0, Rel=0.999)
4. `DispatchSecurityGuard`: Pre: `Alarm.siren_active=T` $\implies$ Eff: `Guard.dispatched=T` (1500ms, $25.0, Rel=0.990)
5. `PlayRelaxingMusic`: (Irrelevant capability)
