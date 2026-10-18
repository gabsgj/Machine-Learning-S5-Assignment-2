"""
Unified Dataset Loader and JSON Exporter (Deliverable 3).
"""

from typing import Dict, Any, Tuple
import json
import os

from capability_embedding.core.state import State, Goal
from capability_embedding.core.capability import Capability
from .ecommerce import get_ecommerce_initial_state, get_ecommerce_goal, get_ecommerce_capabilities
from .devops import get_devops_initial_state, get_devops_goal, get_devops_capabilities
from .healthcare import get_healthcare_initial_state, get_healthcare_goal, get_healthcare_capabilities
from .smarthome import get_smarthome_initial_state, get_smarthome_goal, get_smarthome_capabilities


AVAILABLE_DOMAINS = {
    "ecommerce": (get_ecommerce_initial_state, get_ecommerce_goal, get_ecommerce_capabilities),
    "devops": (get_devops_initial_state, get_devops_goal, get_devops_capabilities),
    "healthcare": (get_healthcare_initial_state, get_healthcare_goal, get_healthcare_capabilities),
    "smarthome": (get_smarthome_initial_state, get_smarthome_goal, get_smarthome_capabilities),
}


def load_domain(domain_name: str) -> Tuple[State, Goal, Dict[str, Capability]]:
    """Loads initial state, goal, and capability dictionary for a specified domain."""
    if domain_name not in AVAILABLE_DOMAINS:
        raise ValueError(f"Unknown domain: {domain_name}. Available: {list(AVAILABLE_DOMAINS.keys())}")
    get_s, get_g, get_c = AVAILABLE_DOMAINS[domain_name]
    return get_s(), get_g(), get_c()


def export_domain_to_json(domain_name: str, output_path: str) -> None:
    """Exports a formally specified domain to a standardized JSON file."""
    state, goal, caps = load_domain(domain_name)
    data = {
        "domain": domain_name,
        "initial_state": state.to_dict(),
        "goal": goal.to_dict(),
        "capabilities": {k: c.to_dict() for k, c in caps.items()}
    }
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def export_all_datasets(output_dir: str) -> None:
    """Exports all benchmark datasets to JSON files."""
    for domain_name in AVAILABLE_DOMAINS:
        out_file = os.path.join(output_dir, f"{domain_name}_problem.json")
        export_domain_to_json(domain_name, out_file)
