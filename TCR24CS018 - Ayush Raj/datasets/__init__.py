"""
Datasets package initialization.
"""

from .ecommerce_domain import get_ecommerce_domain
from .devops_domain import get_devops_domain
from .healthcare_domain import get_healthcare_domain

__all__ = [
    "get_ecommerce_domain",
    "get_devops_domain",
    "get_healthcare_domain",
]
