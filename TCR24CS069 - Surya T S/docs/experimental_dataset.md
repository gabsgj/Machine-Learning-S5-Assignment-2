# PCCST503 Machine Learning Assignment 2
## Deliverable 3: Experimental Dataset Specification

**Application Name:** E-Commerce Order Fulfillment & Payment Pipeline  
**Domain:** Enterprise Transaction Processing  
**Dataset Files:** `data/ecommerce_basic.json`, `data/alternative_implementations.json`  

---

## 1. Domain Specification & Application Problem

The formal application problem $\mathcal{A} = (\mathcal{S}, \mathcal{C}, S_I, G, \mathcal{R}, \mathcal{K})$ represents a commercial purchase workflow where a verified customer converts an active cart into a confirmed, paid order with dispatched notifications.

### 1.1. State Variable Universe ($d = 11$)

| Index | Name | Type | Initial Valuation $S_I$ | Description |
| :---: | :--- | :---: | :---: | :--- |
| **0** | `authenticated` | Boolean | `true` (+1) | Customer identity verified |
| **1** | `customer_exists` | Boolean | `true` (+1) | Persistent customer record exists |
| **2** | `cart_exists` | Boolean | `true` (+1) | Active shopping cart initialized |
| **3** | `cart_has_items` | Boolean | `true` (+1) | Cart contains items |
| **4** | `inventory_available` | Boolean | `true` (+1) | Inventory available and reserved |
| **5** | `order_exists` | Boolean | `false` (-1) | Formal order record initialized |
| **6** | `order_created` | Boolean | `false` (-1) | Order marked CREATED |
| **7** | `payment_success` | Boolean | `false` (-1) | Payment captured successfully |
| **8** | `notification_sent` | Boolean | `false` (-1) | Customer notification sent |
| **9** | `order_cancelled` | Boolean | `false` (-1) | Cart/order abandoned |
| **10** | `shipment_dispatched`| Boolean | `false` (-1) | Shipment logistics released |

### 1.2. Goal Specification $G$
The system seeks a state satisfying:
* $g_1$: `order_exists == true`
* $g_2$: `payment_success == true`
* $g_3$: `notification_sent == true`

Goal vector: $\phi_G(G) = [0, 0, 0, 0, 0, +1, 0, +1, +1, 0, 0]^T$.

### 1.3. Resources & Constraints
* **Resources ($\mathcal{R}$):** `PostgresDatabase`, `StripePaymentGateway`, `KafkaNotificationQueue`.
* **Global Constraints ($\mathcal{K}$):** `cart_has_items == true`, `inventory_available == true`.

---

## 2. Capability Catalog

### 2.1. Core Workflow Capabilities (`data/ecommerce_basic.json`)

#### 1. `CreateOrder`
* **Type:** API
* **Mechanism:** `POST /api/v1/orders`
* **Inputs:** `cart_id` (UUID, required)
* **Outputs:** `order_id` (UUID)
* **Preconditions:** `cart_exists == true`, `cart_has_items == true`
* **Effects:** `order_exists = true`, `order_created = true`
* **QoS:** Time: $80.0\text{ ms}$, Cost: $\$0.01$, Resource: $1.0$, Risk: $0.01$
* **Reliability:** $0.999$, **Availability:** $1.0$

#### 2. `MakePayment`
* **Type:** SERVICE
* **Mechanism:** `POST /api/v1/payments/charge`
* **Inputs:** `order_id` (UUID, required)
* **Outputs:** `payment_id` (UUID)
* **Preconditions:** `order_exists == true`
* **Effects:** `payment_success = true`
* **QoS:** Time: $120.0\text{ ms}$, Cost: $\$0.05$, Resource: $1.0$, Risk: $0.02$
* **Reliability:** $0.995$, **Availability:** $1.0$

#### 3. `SendNotification`
* **Type:** EVENT
* **Mechanism:** `EVENT_BUS publish OrderPaidEvent`
* **Inputs:** `payment_id` (UUID, required)
* **Outputs:** `notification_id` (UUID)
* **Preconditions:** `payment_success == true`
* **Effects:** `notification_sent = true`
* **QoS:** Time: $50.0\text{ ms}$, Cost: $\$0.005$, Resource: $1.0$, Risk: $0.005$
* **Reliability:** $0.999$, **Availability:** $1.0$

#### 4. `CancelCart`
* **Type:** API
* **Mechanism:** `DELETE /api/v1/cart`
* **Inputs:** None, **Outputs:** None
* **Preconditions:** `order_exists == false`
* **Effects:** `cart_exists = false`, `order_cancelled = true`
* **QoS:** Time: $20.0\text{ ms}$, Cost: $\$0.00$, Resource: $1.0$, Risk: $0.00$
* **Reliability:** $0.999$, **Availability:** $1.0$

---

### 2.2. Extended Benchmark Capabilities (`data/alternative_implementations.json`)

#### Alternative Implementations (Experiment 3)
* `MakePayment_API`: External REST Stripe integration. Latency: $120\text{ ms}$, Cost: $\$0.050$, Rel: $0.992$.
* `MakePayment_DATABASE`: Internal SQL database ledger transaction. Latency: $30\text{ ms}$, Cost: $\$0.002$, Rel: $0.965$.
* `MakePayment_GUI`: Client-side form modal submit. Latency: $450\text{ ms}$, Cost: $\$0.000$, Rel: $0.985$.

#### Irrelevant Capabilities (Experiment 4)
* `BrowseCatalog`: Views category catalog. Type: API. Pre: $\emptyset$, Eff: $\emptyset$.
* `UpdateWishlist`: Adds item to user wishlist. Type: API. Pre: `authenticated == true`, Eff: $\emptyset$.
* `ViewProfile`: Shows user settings. Type: GUI. Pre: `authenticated == true`, Eff: $\emptyset$.
* `ChangeTheme`: Switches dark/light mode. Type: GUI. Pre: $\emptyset$, Eff: $\emptyset$.

#### Operational Trade-Off Capabilities (Experiment 5)
* `FastPayment`: High-speed fiber route. Latency: $20\text{ ms}$, Cost: $\$0.100$, Rel: $0.998$, Risk: $0.005$.
* `CheapPayment`: Batch ACH transfer. Latency: $800\text{ ms}$, Cost: $\$0.001$, Rel: $0.930$, Risk: $0.060$.

---

## 3. Experimental Setup & Hypotheses

### Experiment 1: Capability Compatibility
* **Hypothesis:** $\text{Comp}(\text{CreateOrder}, \text{MakePayment}) = +1.0000$ (causally enables); $\text{Comp}(\text{CreateOrder}, \text{CancelCart}) = -1.0000$ (violates precondition).

### Experiment 2: Capability Composition
* **Hypothesis:** Sequentially composing $\text{SendNotification} \circ (\text{MakePayment} \circ \text{CreateOrder})$ yields a composite capability whose internal preconditions (`order_exists`, `payment_success`) are eliminated, while external preconditions (`cart_exists`, `cart_has_items`) are preserved.

### Experiment 3: Alternative Implementations
* **Hypothesis:** Alternative payment mechanisms share high cosine similarity ($> 0.70$) due to identical state effects, but their sequential composability among each other is $0.0000$, proving that **Similarity $\neq$ Composability**.

### Experiment 4: Irrelevant Capabilities
* **Hypothesis:** $\text{Relevance}(C, G) = \mathbf{e}(C) \cdot \phi_G(G)$ assigns positive values ($+1.00$) to goal-advancing steps and $0.00$ to catalog browsing, wishlist updates, and theme toggling.

### Experiment 5: Operational Trade-offs
* **Hypothesis:** Operational features differentiate `FastPayment` and `CheapPayment` in the QoS embedding slice, capturing multi-objective Pareto trade-offs.
