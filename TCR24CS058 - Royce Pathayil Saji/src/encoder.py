from __future__ import annotations

from typing import Any
import hashlib
import numpy as np

from src.models import Capability, CapabilityType, Constraint, Goal, IOField, Predicate, Resource, State

# Dimension Constants
TOTAL_DIM = 160
MECH_DIM = 16
IO_DIM = 24
COND_DIM = 32
CONSTRAINT_DIM = 12
RESOURCE_DIM = 12
OPS_DIM = 8

# Block Slice Offsets
MECH_SLICE = slice(0, 16)
INPUT_SLICE = slice(16, 40)
OUTPUT_SLICE = slice(40, 64)
PRE_SLICE = slice(64, 96)
EFFECT_SLICE = slice(96, 128)
CONSTRAINT_SLICE = slice(128, 140)
RESOURCE_SLICE = slice(140, 152)
OPS_SLICE = slice(152, 160)

# Canonical Boolean State Variables (Dimensions 0 to 7)
BOOLEAN_VARS: dict[str, int] = {
    "User.authenticated": 0,
    "user.authenticated": 0,
    "authenticated": 0,
    "Cart.exists": 1,
    "cart.exists": 1,
    "cart_exists": 1,
    "CartExists": 1,
    "Cart.locked": 2,
    "cart.locked": 2,
    "cart_locked": 2,
    "CartLocked": 2,
    "Order.exists": 3,
    "order.exists": 3,
    "order_exists": 3,
    "OrderExists": 3,
    "Inventory.available": 4,
    "inventory.available": 4,
    "inventory_available": 4,
    "InventoryAvailable": 4,
    "Inventory.reserved": 5,
    "inventory.reserved": 5,
    "inventory_reserved": 5,
    "InventoryReserved": 5,
    "Notification.sent": 6,
    "notification.sent": 6,
    "notification_sent": 6,
    "NotificationSent": 6,
    "Order.archived": 7,
    "order.archived": 7,
    "order_archived": 7,
    "OrderArchived": 7,
}

# Canonical Categorical States (Dimensions 8 to 18)
CATEGORICAL_VARS: dict[str, dict[str, int]] = {
    "Payment.status": {
        "NOT_STARTED": 8,
        "PENDING": 9,
        "SUCCESS": 10,
        "REFUNDED": 11,
    },
    "payment.status": {
        "NOT_STARTED": 8,
        "PENDING": 9,
        "SUCCESS": 10,
        "REFUNDED": 11,
    },
    "PaymentStatus": {
        "NOT_STARTED": 8,
        "PENDING": 9,
        "SUCCESS": 10,
        "REFUNDED": 11,
    },
    "Order.status": {
        "NONE": 12,
        "CREATED": 13,
        "COMPLETED": 14,
    },
    "order.status": {
        "NONE": 12,
        "CREATED": 13,
        "COMPLETED": 14,
    },
    "OrderStatus": {
        "NONE": 12,
        "CREATED": 13,
        "COMPLETED": 14,
    },
    "User.role": {
        "CUSTOMER": 15,
        "ADMIN": 16,
    },
    "user.role": {
        "CUSTOMER": 15,
        "ADMIN": 16,
    },
    "UserRole": {
        "CUSTOMER": 15,
        "ADMIN": 16,
    },
    "Cart.status": {
        "ACTIVE": 17,
        "CANCELLED": 18,
    },
    "cart.status": {
        "ACTIVE": 17,
        "CANCELLED": 18,
    },
    "CartStatus": {
        "ACTIVE": 17,
        "CANCELLED": 18,
    },
}

# Canonical Numerical Variables (Dimensions 19 to 22)
NUMERICAL_VARS: dict[str, tuple[int, int]] = {
    "Cart.item_count": (19, 20),
    "cart.item_count": (19, 20),
    "cart_item_count": (19, 20),
    "CartItemCount": (19, 20),
    "quantity": (21, 22),
    "Quantity": (21, 22),
}

# Canonical Data Fields (Dimensions 0 to 9 in IO block)
IO_FIELDS: dict[str, int] = {
    "cart_id": 0,
    "order_id": 1,
    "payment_id": 2,
    "payment_method": 3,
    "cancelled_cart_id": 4,
    "notification_id": 5,
    "inventory_txn_id": 6,
    "archive_id": 7,
    "refund_id": 8,
    "reservation_id": 9,
    "sku": 10,
}

# Capability Type indices [0 to 9 in mech block]
CAPABILITY_TYPES: dict[CapabilityType, int] = {
    CapabilityType.API: 0,
    CapabilityType.DATABASE: 1,
    CapabilityType.GUI: 2,
    CapabilityType.EVENT: 3,
    CapabilityType.FUNCTION: 4,
    CapabilityType.FILE: 5,
    CapabilityType.COMPUTATION: 6,
    CapabilityType.MESSAGE: 7,
    CapabilityType.SERVICE: 8,
    CapabilityType.COMPOSITE: 9,
}

# Canonical Constraints [0 to 5 in constraint block]
CONSTRAINTS_MAP: dict[str, int] = {
    "quantity>0": 0,
    "quantity > 0": 0,
    "quantity<=inventory_available": 1,
    "quantity <= inventory_available": 1,
    "payment_amount<=transaction_limit": 2,
    "payment_amount <= transaction_limit": 2,
    "user.role in {CUSTOMER, ADMIN}": 3,
    "user.role in {CUSTOMER,ADMIN}": 3,
    "retention_days>=30": 4,
    "retention_days >= 30": 4,
    "refund_amount<=paid_amount": 5,
    "refund_amount <= paid_amount": 5,
}

# Canonical Resources [0 to 6 in resource block]
RESOURCES_MAP: dict[str, int] = {
    "Database": 0,
    "database": 0,
    "AuthenticationToken": 1,
    "authentication_token": 1,
    "PaymentGateway": 2,
    "payment_gateway": 2,
    "Network": 3,
    "network": 3,
    "FileSystem": 4,
    "file_system": 4,
    "ExternalService": 5,
    "external_service": 5,
    "GPU": 6,
    "gpu": 6,
}


def _operator_direction(op: str) -> float:
    if op in {">", ">="}:
        return 1.0
    if op in {"<", "<="}:
        return -1.0
    return 0.0


def _parse_bool_value(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v == "true":
            return True
        if v == "false":
            return False
    return None


def encode_condition_predicates(predicates: list[Predicate]) -> np.ndarray:
    """Encode a list of predicates into the canonical 32-dimensional condition vector."""
    vec = np.zeros(COND_DIM, dtype=np.float64)
    for p in predicates:
        # 1. Check Boolean variables
        if p.name in BOOLEAN_VARS:
            idx = BOOLEAN_VARS[p.name]
            b_val = _parse_bool_value(p.value)
            if b_val is True:
                vec[idx] = 1.0
            elif b_val is False:
                vec[idx] = -1.0
            continue

        # 2. Check Categorical variables
        if p.name in CATEGORICAL_VARS:
            cat_map = CATEGORICAL_VARS[p.name]
            val_str = str(p.value).strip().upper()
            if val_str in cat_map:
                vec[cat_map[val_str]] = 1.0
            continue

        # 3. Check Numerical variables
        if p.name in NUMERICAL_VARS:
            val_idx, op_idx = NUMERICAL_VARS[p.name]
            try:
                num_val = float(p.value)
                vec[val_idx] = min(1.0, max(0.0, num_val / 10.0))
            except (ValueError, TypeError):
                vec[val_idx] = 0.0
            vec[op_idx] = _operator_direction(p.operator)
            continue

    if not np.isfinite(vec).all():
        raise ValueError("Non-finite values encountered in condition vector")
    return vec


def encode_state(state: State) -> np.ndarray:
    """Encode an application state into the canonical 32-dimensional condition space."""
    predicates: list[Predicate] = []
    for key, value in state.values.items():
        predicates.append(Predicate(name=key, operator="=", value=value))
    return encode_condition_predicates(predicates)


def encode_goal(goal: Goal) -> np.ndarray:
    """Encode a goal specification into the canonical 32-dimensional condition space."""
    return encode_condition_predicates(goal.conditions)


def encode_io_fields(fields: list[IOField], is_input: bool) -> np.ndarray:
    """Encode input or output fields into a 24-dimensional data-flow vector."""
    vec = np.zeros(IO_DIM, dtype=np.float64)
    for f in fields:
        field_name = f.name.strip()
        idx = IO_FIELDS.get(field_name)
        if idx is None:
            # Deterministic fallback into reserved slots [11:24]
            idx = 11 + (int.from_bytes(hashlib.md5(field_name.encode()).digest()[:4], "big") % 13)
        if idx < IO_DIM:
            if is_input:
                vec[idx] = 1.0 if f.required else 0.5
            else:
                vec[idx] = 1.0
    return vec


def encode_capability(c: Capability) -> np.ndarray:
    """Encode a formal capability into the 160-dimensional PSD-160 vector."""
    vec = np.zeros(TOTAL_DIM, dtype=np.float64)

    # 1. Mechanism and Type block [0:16]
    type_idx = CAPABILITY_TYPES.get(c.T)
    if type_idx is not None:
        vec[type_idx] = 1.0

    # Mechanism features
    if c.M:
        mech_str = " ".join(f"{k}:{v}" for k, v in c.M.items()).lower()
        if "post" in mech_str or "get" in mech_str or "http" in mech_str:
            vec[10] = 1.0
        if "insert" in mech_str or "update" in mech_str or "select" in mech_str:
            vec[11] = 1.0
        if "click" in mech_str or "submit" in mech_str:
            vec[12] = 1.0
        if "trigger" in mech_str or "event" in mech_str or "handler" in mech_str:
            vec[13] = 1.0
        if "service" in mech_str or "reserve" in mech_str:
            vec[14] = 1.0
        if "sequential" in mech_str or "ordered" in mech_str or "composition" in mech_str:
            vec[15] = 1.0

    # 2. Inputs block [16:40]
    vec[INPUT_SLICE] = encode_io_fields(c.I, is_input=True)

    # 3. Outputs block [40:64]
    vec[OUTPUT_SLICE] = encode_io_fields(c.O, is_input=False)

    # 4. Preconditions block [64:96]
    vec[PRE_SLICE] = encode_condition_predicates(c.P)

    # 5. Effects block [96:128]
    vec[EFFECT_SLICE] = encode_condition_predicates(c.E)

    # 6. Constraints block [128:140]
    for k in c.K:
        c_expr = k.expression.strip()
        idx = CONSTRAINTS_MAP.get(c_expr)
        if idx is None:
            idx = 6 + (int.from_bytes(hashlib.md5(c_expr.encode()).digest()[:4], "big") % 6)
        if idx < CONSTRAINT_DIM:
            vec[128 + idx] = 1.0

    # 7. Resources block [140:152]
    for r in c.R:
        r_name = r.name.strip()
        idx = RESOURCES_MAP.get(r_name)
        if idx is None:
            idx = 7 + (int.from_bytes(hashlib.md5(r_name.encode()).digest()[:4], "big") % 5)
        if idx < RESOURCE_DIM:
            vec[140 + idx] = 1.0

    # 8. Operational Quality block [152:160]
    norm_time = min(1.0, max(0.0, c.Q.execution_time_ms / 1000.0))
    norm_money = min(1.0, max(0.0, c.Q.monetary_cost / 0.10))
    norm_resource = min(1.0, max(0.0, c.Q.resource_cost / 5.0))
    risk = min(1.0, max(0.0, c.Q.risk))
    norm_energy = min(1.0, max(0.0, c.Q.energy_cost / 10.0))
    unreliability = min(1.0, max(0.0, 1.0 - c.Rel))
    unavailability = min(1.0, max(0.0, 1.0 - c.A))
    composite_cost = (norm_time + norm_money + norm_resource + risk + unreliability) / 5.0

    vec[152] = norm_time
    vec[153] = norm_money
    vec[154] = norm_resource
    vec[155] = risk
    vec[156] = norm_energy
    vec[157] = unreliability
    vec[158] = unavailability
    vec[159] = composite_cost

    if not np.isfinite(vec).all():
        raise ValueError("Non-finite values encountered in capability vector")
    if len(vec) != TOTAL_DIM:
        raise ValueError(f"Expected capability vector dimension {TOTAL_DIM}, got {len(vec)}")

    return vec
