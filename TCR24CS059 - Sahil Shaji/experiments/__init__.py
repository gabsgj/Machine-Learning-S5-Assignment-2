"""
Experimental test suite for Assignment 2.
Includes modules for Experiments 1 through 5 and the master runner.
"""

from .exp1_compatibility import run_experiment_1
from .exp2_composition import run_experiment_2
from .exp3_alternatives import run_experiment_3
from .exp4_irrelevance import run_experiment_4
from .exp5_operational import run_experiment_5
from .run_all_experiments import run_all

__all__ = [
    "run_experiment_1",
    "run_experiment_2",
    "run_experiment_3",
    "run_experiment_4",
    "run_experiment_5",
    "run_all",
]
