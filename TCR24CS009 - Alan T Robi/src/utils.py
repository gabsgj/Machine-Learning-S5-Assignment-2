import os
import json
from typing import Dict, List, Any
import numpy as np
import pandas as pd

def ensure_dir(path: str) -> None:
    """Ensure directory exists."""
    os.makedirs(path, exist_ok=True)

def save_json(data: Any, filepath: str, indent: int = 2) -> None:
    """Save data to JSON file with directory creation."""
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent)

def save_csv(df: pd.DataFrame, filepath: str) -> None:
    """Save DataFrame to CSV with directory creation."""
    ensure_dir(os.path.dirname(filepath))
    df.to_csv(filepath, index=False)

def min_max_normalize(val: float, min_val: float, max_val: float) -> float:
    """Min-max normalize a scalar value to range [0, 1]."""
    if max_val <= min_val:
        return 0.0
    norm = (val - min_val) / (max_val - min_val)
    return float(np.clip(norm, 0.0, 1.0))

def canonicalize_predicate(pred: str) -> str:
    """
    Canonicalize predicate strings to unify semantically equivalent predicates
    across states, goals, preconditions, and effects.
    
    Examples:
      'Order.exists=true' -> 'orderexists=true'
      'OrderExists=true' -> 'orderexists=true'
      'Payment.status=SUCCESS' -> 'paymentstatus=success'
      'PaymentStatus=SUCCESS' -> 'paymentstatus=success'
      'Cart_Item_Count > 0' -> 'cartitemcount>0'
    """
    if not pred or not isinstance(pred, str):
        return ""
    
    pred = pred.strip()
    for op in [">=", "<=", "==", "=", ">", "<"]:
        if op in pred:
            parts = pred.split(op, 1)
            var_part = parts[0].replace(".", "").replace("_", "").lower().strip()
            val_part = parts[1].lower().strip()
            if val_part in ["true", "t", "1"]:
                val_part = "true"
            elif val_part in ["false", "f", "0"]:
                val_part = "false"
            norm_op = "=" if op in ["==", "="] else op
            return f"{var_part}{norm_op}{val_part}"
    
    return pred.replace(".", "").replace("_", "").lower().strip()

