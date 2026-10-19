from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Tuple
import numpy as np

STANDARD_TYPES = [
    "API",
    "DATABASE",
    "GUI",
    "EVENT",
    "FUNCTION",
    "FILE",
    "COMPUTATION",
    "MESSAGE",
    "SERVICE",
    "COMPOSITE",
]


class Domain:
    """
    Defines the vocabulary of state variables and capability types for an application.
    """
    def __init__(self, variables: List[str], types: Optional[List[str]] = None):
        self.variables = list(variables)
        self.var_to_idx = {var: i for i, var in enumerate(self.variables)}
        self.types = list(types) if types else list(STANDARD_TYPES)
        self.type_to_idx = {t: i for i, t in enumerate(self.types)}

    @property
    def num_variables(self) -> int:
        return len(self.variables)

    @property
    def num_types(self) -> int:
        return len(self.types)

    @property
    def capability_vector_dim(self) -> int:
        # Preconditions (num_vars) + Effects (num_vars) + Type one-hot (num_types) + QoS (4)
        return 2 * self.num_variables + self.num_types + 4


@dataclass
class State:
    """
    Represents an application state S = {(x_1, v_1), ..., (x_n, v_n)}.
    Variables are typically boolean (True/False mapped to +1/-1) or numeric.
    """
    name: str
    values: Dict[str, Union[bool, float, int]]

    def __getitem__(self, item: str):
        return self.values.get(item, 0.0)


@dataclass
class Goal:
    """
    Represents a goal specification G = {g_1, ..., g_m}.
    Desired target conditions on state variables.
    """
    name: str
    target_conditions: Dict[str, Union[bool, float, int]]


@dataclass
class QoS:
    """
    Operational attributes of a capability (Section 4.5 & 4.6 of PDF).
    """
    execution_time_ms: float = 100.0   # latency in milliseconds
    monetary_cost: float = 0.01        # cost in dollars
    reliability: float = 0.99          # probability of success in [0, 1]
    availability: float = 1.0          # availability flag in {0, 1}


@dataclass
class Capability:
    """
    Formal Capability Representation C_i = (T_i, I_i, O_i, P_i, E_i, K_i, R_i, Q_i, Rel_i, A_i, M_i).
    """
    name: str
    cap_type: str                      # e.g. 'API', 'DATABASE', 'GUI', etc.
    preconditions: Dict[str, Union[bool, float, int]] = field(default_factory=dict)
    effects: Dict[str, Union[bool, float, int]] = field(default_factory=dict)
    inputs: Dict[str, str] = field(default_factory=dict)     # name -> type
    outputs: Dict[str, str] = field(default_factory=dict)    # name -> type
    qos: QoS = field(default_factory=QoS)
    mechanism: Dict[str, str] = field(default_factory=dict)  # endpoint, table, action etc.


# ==============================================================================
# ENCODING FUNCTIONS (Deliverable 2)
# ==============================================================================

def _val_to_signed_float(v: Union[bool, float, int]) -> float:
    """
    Converts boolean/numeric values to a clean signed float:
    True -> +1.0, False -> -1.0, numeric values preserved as float.
    """
    if isinstance(v, bool):
        return 1.0 if v else -1.0
    return float(v)


def encode_state(state: State, domain: Domain) -> np.ndarray:
    """
    Encodes an application state S into a 1D vector of length domain.num_variables.
    Unspecified variables default to 0.0.
    """
    vec = np.zeros(domain.num_variables, dtype=np.float32)
    for var, val in state.values.items():
        if var in domain.var_to_idx:
            vec[domain.var_to_idx[var]] = _val_to_signed_float(val)
    return vec


def encode_goal(goal: Goal, domain: Domain) -> np.ndarray:
    """
    Encodes a goal specification G into a 1D vector of length domain.num_variables.
    Target variables have +1.0 (True) or -1.0 (False). Non-goal variables are 0.0.
    """
    vec = np.zeros(domain.num_variables, dtype=np.float32)
    for var, val in goal.target_conditions.items():
        if var in domain.var_to_idx:
            vec[domain.var_to_idx[var]] = _val_to_signed_float(val)
    return vec


def encode_capability(cap: Capability, domain: Domain) -> np.ndarray:
    """
    Encodes a capability into a concatenated numerical vector:
      v = [ preconditions (N_v) || effects (N_v) || type_one_hot (N_t) || qos (4) ]
    Total dimension = 2 * N_v + N_t + 4.
    """
    # 1. Precondition Subvector
    p_vec = np.zeros(domain.num_variables, dtype=np.float32)
    for var, val in cap.preconditions.items():
        if var in domain.var_to_idx:
            p_vec[domain.var_to_idx[var]] = _val_to_signed_float(val)

    # 2. Effect Subvector
    e_vec = np.zeros(domain.num_variables, dtype=np.float32)
    for var, val in cap.effects.items():
        if var in domain.var_to_idx:
            e_vec[domain.var_to_idx[var]] = _val_to_signed_float(val)

    # 3. Type One-Hot Subvector
    t_vec = np.zeros(domain.num_types, dtype=np.float32)
    t_idx = domain.type_to_idx.get(cap.cap_type, -1)
    if t_idx != -1:
        t_vec[t_idx] = 1.0

    # 4. QoS Operational Subvector
    # Normalized: time in seconds, monetary cost, reliability in [0, 1], availability in {0, 1}
    q_vec = np.array([
        cap.qos.execution_time_ms / 1000.0,
        cap.qos.monetary_cost,
        cap.qos.reliability,
        cap.qos.availability,
    ], dtype=np.float32)

    return np.concatenate([p_vec, e_vec, t_vec, q_vec])


def encode(entity: Union[State, Goal, Capability], domain: Domain) -> np.ndarray:
    """
    Universal encoder dispatch matching Deliverable 2: encode(state), encode(goal), encode(capability).
    """
    if isinstance(entity, State):
        return encode_state(entity, domain)
    elif isinstance(entity, Goal):
        return encode_goal(entity, domain)
    elif isinstance(entity, Capability):
        return encode_capability(entity, domain)
    else:
        raise TypeError(f"Unsupported entity type for encoding: {type(entity)}")


# ==============================================================================
# SIMILARITY & COMPATIBILITY MEASURES (Deliverable 1 & 2)
# ==============================================================================

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Computes standard cosine similarity between two 1D vectors:
      cos(v1, v2) = (v1 . v2) / (||v1|| * ||v2||)
    """
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))


def similarity(
    c1: Union[Capability, np.ndarray],
    c2: Union[Capability, np.ndarray],
    domain: Optional[Domain] = None,
    mode: str = "functional"
) -> float:
    """
    Compares two capabilities or vectors.
    - 'functional': Cosine similarity of effects subvectors (functional equivalence / substitutability).
    - 'total': Cosine similarity of the entire concatenated vector (including type & QoS).
    """
    v1 = encode_capability(c1, domain) if isinstance(c1, Capability) else c1
    v2 = encode_capability(c2, domain) if isinstance(c2, Capability) else c2

    if mode == "functional" and domain is not None:
        # Extract effect slices: indices [num_variables : 2 * num_variables]
        nv = domain.num_variables
        eff1 = v1[nv : 2 * nv]
        eff2 = v2[nv : 2 * nv]
        return cosine_similarity(eff1, eff2)
    
    return cosine_similarity(v1, v2)


def compatibility(c1: Capability, c2: Capability, domain: Domain) -> float:
    """
    Directional Precondition-Effect Compatibility Score for C_1 -> C_2:
    Does executing C_1 help satisfy the preconditions of C_2?

    Let e_1 be C_1's effect subvector, and p_2 be C_2's precondition subvector.
    Compatibility = (e_1 . p_2) / sum(|p_2|)

    Properties:
    - If C_1 produces what C_2 requires, score > 0 (max +1.0).
    - If C_1 produces what contradicts C_2, score < 0 (conflict).
    - If C_1 has no effect on C_2's preconditions, score = 0.0.
    - Asymmetric: compatibility(c1, c2) != compatibility(c2, c1).
    """
    v1 = encode_capability(c1, domain)
    v2 = encode_capability(c2, domain)

    nv = domain.num_variables
    eff1 = v1[nv : 2 * nv]      # Effect vector of C_1
    pre2 = v2[:nv]              # Precondition vector of C_2

    active_preconditions = np.sum(np.abs(pre2))
    if active_preconditions == 0.0:
        return 1.0  # C_2 requires nothing; it can run trivially

    dot_prod = np.dot(eff1, pre2)
    return float(dot_prod / active_preconditions)


def goal_relevance(cap: Capability, goal: Goal, domain: Domain) -> float:
    """
    Goal Relevance Score:
    Measures how directly C_i's effects contribute to achieving Goal G.
    
    Relevance = (effects(C_i) . encode(G)) / sum(|encode(G)|)
    - Positive: C_i satisfies one or more goal variables.
    - Zero: C_i has no effect on goal variables (irrelevant).
    - Negative: C_i reverses a goal variable.
    """
    v_cap = encode_capability(cap, domain)
    v_goal = encode_goal(goal, domain)

    nv = domain.num_variables
    eff = v_cap[nv : 2 * nv]

    goal_magnitude = np.sum(np.abs(v_goal))
    if goal_magnitude == 0.0:
        return 0.0

    return float(np.dot(eff, v_goal) / goal_magnitude)


# ==============================================================================
# CAPABILITY COMPOSITION ALGEBRA (Deliverable 1 & 2)
# ==============================================================================

def compose_two(c1: Capability, c2: Capability) -> Capability:
    """
    Composes two capabilities sequentially: C_12 = C_2 o C_1.
    Execution order: First C_1 runs, then C_2 runs.
    """
   
    # 1. Composite Preconditions
    comp_pre = dict(c1.preconditions)
    for var, val in c2.preconditions.items():
        # If C_1's effect already satisfies this precondition, it is resolved internally
        if var in c1.effects:
            if c1.effects[var] == val:
                continue  # Satisfied by C_1
        # Otherwise, the composite capability still requires it externally
        comp_pre[var] = val

    # 2. Composite Effects (C_2's effects take precedence / override C_1)
    comp_eff = dict(c1.effects)
    comp_eff.update(c2.effects)

    # 3. Composite Inputs & Outputs
    comp_in = dict(c1.inputs)
    for inp, typ in c2.inputs.items():
        if inp not in c1.outputs:
            comp_in[inp] = typ

    comp_out = dict(c1.outputs)
    comp_out.update(c2.outputs)

    # 4. Composite QoS
    comp_qos = QoS(
        execution_time_ms=c1.qos.execution_time_ms + c2.qos.execution_time_ms,
        monetary_cost=round(c1.qos.monetary_cost + c2.qos.monetary_cost, 4),
        reliability=round(c1.qos.reliability * c2.qos.reliability, 4),
        availability=min(c1.qos.availability, c2.qos.availability),
    )

    name = f"({c2.name} o {c1.name})"
    return Capability(
        name=name,
        cap_type="COMPOSITE",
        preconditions=comp_pre,
        effects=comp_eff,
        inputs=comp_in,
        outputs=comp_out,
        qos=comp_qos,
        mechanism={"composed_from": f"{c1.name} -> {c2.name}"},
    )


def compose(capabilities: List[Capability], domain: Optional[Domain] = None) -> Tuple[Capability, Optional[np.ndarray]]:
    """
    Constructs a composite capability from a sequence [C_1, C_2, ..., C_n].
    Returns (composite_capability, composite_vector).
    """
    if not capabilities:
        raise ValueError("Cannot compose an empty list of capabilities.")

    current = capabilities[0]
    for nxt in capabilities[1:]:
        current = compose_two(current, nxt)

    vec = encode_capability(current, domain) if domain is not None else None
    return current, vec
