"""
Benchmark Datasets for Capability Composition (Deliverable 3).
Domains:
  - E-Commerce (Order-to-Cash)
  - DevOps CI/CD
  - Healthcare Clinical Patient Workflow
  - Smart Home IoT
"""

from .loader import load_domain, export_domain_to_json, export_all_datasets, AVAILABLE_DOMAINS
from .ecommerce import get_ecommerce_initial_state, get_ecommerce_goal, get_ecommerce_capabilities
from .devops import get_devops_initial_state, get_devops_goal, get_devops_capabilities
from .healthcare import get_healthcare_initial_state, get_healthcare_goal, get_healthcare_capabilities
from .smarthome import get_smarthome_initial_state, get_smarthome_goal, get_smarthome_capabilities

__all__ = [
    "load_domain",
    "export_domain_to_json",
    "export_all_datasets",
    "AVAILABLE_DOMAINS",
    "get_ecommerce_initial_state",
    "get_ecommerce_goal",
    "get_ecommerce_capabilities",
    "get_devops_initial_state",
    "get_devops_goal",
    "get_devops_capabilities",
    "get_healthcare_initial_state",
    "get_healthcare_goal",
    "get_healthcare_capabilities",
    "get_smarthome_initial_state",
    "get_smarthome_goal",
    "get_smarthome_capabilities",
]
