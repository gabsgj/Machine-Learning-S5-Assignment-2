"""
encode.py
=========
Encodes states, goals, and capabilities into fixed-length numpy vectors.

Vector layout for capability (concatenation order):
  [0:12]   - type_onehot         : one-hot over 9 capability types (padded to 12)
  [12:16]  - io_features         : [input_count, output_count, required_input_count,
                                    optional_input_count]
  [16:17]  - io_name_match       : fraction of input names appearing in output names
  [17:22]  - resource_multihot   : multi-hot over global resource vocabulary (5 slots)
  [22:27]  - cost_normalized     : [time_ms, money, resource, risk, energy] each in [0,1]
  [27:28]  - reliability         : scalar in [0,1]
  [28:40]  - precondition_vector : +1/0/-1 over the state-variable vocab (12 slots)
  [40:52]  - effect_vector       : +1/0/-1 over the state-variable vocab (12 slots)

Total: 52 dimensions per capability.

State/Goal vectors:
  Each is a 12-dim vector over the domain's state-variable vocabulary.
  True  ->  +1.0
  False -> -1.0
  None/absent -> 0.0
"""

import json
import os
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CAPABILITY_TYPES = ["API", "DATABASE", "GUI", "EVENT", "FUNCTION", "FILE",
                    "COMPUTATION", "MESSAGE", "SERVICE"]
NUM_TYPE_SLOTS = 12          # 9 types + 3 spare padding slots

# Global resource vocabulary (union across all domains)
GLOBAL_RESOURCE_VOCAB = [
    "database", "payment_gateway", "email_service", "inventory_system", "shipping_api",
    "catalog_db", "member_db", "rfid_scanner", "payment_terminal",
    "pms_db", "housekeeping_system", "kitchen_system"
]
GLOBAL_RESOURCE_VOCAB_SIZE = 12   # 12 resources

NUM_IO_FEATURES = 4          # input_count, output_count, required_count, optional_count
NUM_IO_MATCH    = 1          # io_name_match fraction
NUM_COST_DIMS   = 5          # time_ms, money, resource, risk, energy
NUM_RELIABILITY = 1
NUM_STATE_VARS  = 12         # max state-variable vocabulary size per domain

# Indices (start:end) — must match vector layout described in the docstring
IDX_TYPE     = (0,  12)
IDX_IO       = (12, 16)
IDX_IOMATCH  = (16, 17)
IDX_RESOURCE = (17, 29)      # 12 slots for global resource vocab
IDX_COST     = (29, 34)
IDX_RELY     = (34, 35)
IDX_PRECOND  = (35, 47)      # 12 state-var slots
IDX_EFFECT   = (47, 59)      # 12 state-var slots

VECTOR_DIM = 59              # total capability vector length

# Global cost range statistics (updated after loading all domains)
_COST_STATS = {
    "time_ms": {"min": 0.0, "max": 1.0},
    "money":   {"min": 0.0, "max": 1.0},
    "resource":{"min": 0.0, "max": 1.0},
    "risk":    {"min": 0.0, "max": 1.0},
    "energy":  {"min": 0.0, "max": 1.0},
}


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def load_domain(filepath: str) -> dict:
    """Load a domain JSON file and return the parsed dict."""
    with open(filepath, "r", encoding="utf-8") as fh:
        return json.load(fh)


def collect_cost_stats(domains: list[dict]) -> None:
    """
    Scan all capability costs across domains and update _COST_STATS
    with global min/max for each cost field. Must be called before
    encode_capability() to ensure proper normalization.
    """
    fields = ["time_ms", "money", "resource", "risk", "energy"]
    values = {f: [] for f in fields}
    for domain in domains:
        for cap in domain.get("capabilities", []):
            cost = cap.get("cost", {})
            for f in fields:
                if f in cost:
                    values[f].append(float(cost[f]))
    for f in fields:
        if values[f]:
            _COST_STATS[f]["min"] = min(values[f])
            _COST_STATS[f]["max"] = max(values[f])


def _normalize(value: float, field: str) -> float:
    """Min-max normalize a cost field to [0, 1]."""
    lo = _COST_STATS[field]["min"]
    hi = _COST_STATS[field]["max"]
    if hi == lo:
        return 0.0
    return float(np.clip((value - lo) / (hi - lo), 0.0, 1.0))


# ---------------------------------------------------------------------------
# State / Goal encoders
# ---------------------------------------------------------------------------

def encode_state(state: dict, state_vars: list[str]) -> np.ndarray:
    """
    Encode a state dict into a fixed-length vector over state_vars.

    Parameters
    ----------
    state      : {variable_name: bool_value}
    state_vars : ordered list of variable names (the domain vocabulary)

    Returns
    -------
    np.ndarray of shape (len(state_vars),) with values in {-1, 0, +1}
      +1  if state[var] is True
      -1  if state[var] is False
       0  if var not in state
    """
    vec = np.zeros(len(state_vars), dtype=float)
    for i, var in enumerate(state_vars):
        if var in state:
            vec[i] = 1.0 if state[var] else -1.0
    return vec


def encode_goal(goal: dict, state_vars: list[str]) -> np.ndarray:
    """
    Encode a goal dict into a fixed-length vector over state_vars.
    Semantics identical to encode_state — a goal is simply a partial
    assignment of desired variable values.

    Parameters
    ----------
    goal       : {variable_name: desired_bool_value}
    state_vars : ordered list of variable names (the domain vocabulary)

    Returns
    -------
    np.ndarray of shape (len(state_vars),)
    """
    return encode_state(goal, state_vars)


# ---------------------------------------------------------------------------
# Precondition / Effect helpers (internal)
# ---------------------------------------------------------------------------

def _encode_condition(condition: dict, state_vars: list[str]) -> np.ndarray:
    """
    Encode a precondition or effect dict over a padded 12-slot vector.

    condition  : {variable_name: bool_value}
    state_vars : ordered list of variable names (at most 12)

    Slots beyond len(state_vars) are left as 0.
    """
    vec = np.zeros(NUM_STATE_VARS, dtype=float)
    for i, var in enumerate(state_vars[:NUM_STATE_VARS]):
        if var in condition:
            vec[i] = 1.0 if condition[var] else -1.0
    return vec


# ---------------------------------------------------------------------------
# Capability encoder
# ---------------------------------------------------------------------------

def encode_capability(capability: dict, state_vars: list[str],
                      resource_vocab: list[str] | None = None) -> np.ndarray:
    """
    Encode a capability dict into a fixed-length VECTOR_DIM-dimensional vector.

    Parameters
    ----------
    capability    : capability dict (as defined in the domain JSON schema)
    state_vars    : ordered list of state variable names for the domain
    resource_vocab: optional domain-level resource vocabulary; if None uses
                    GLOBAL_RESOURCE_VOCAB

    Returns
    -------
    np.ndarray of shape (VECTOR_DIM,)

    Vector layout (see module docstring):
      [0:12]   type_onehot (9 types padded to 12)
      [12:16]  io_features [in_count, out_count, req_count, opt_count]
      [16:17]  io_name_match fraction
      [17:29]  resource_multihot (12 slots, global vocab)
      [29:34]  cost_normalized [time_ms, money, resource, risk, energy]
      [34:35]  reliability
      [35:47]  precondition_vector (+1/0/-1 over state_vars, padded to 12)
      [47:59]  effect_vector      (+1/0/-1 over state_vars, padded to 12)
    """
    vec = np.zeros(VECTOR_DIM, dtype=float)
    rvocab = resource_vocab if resource_vocab is not None else GLOBAL_RESOURCE_VOCAB

    # --- Type one-hot ---------------------------------------------------
    cap_type = capability.get("type", "API").upper()
    if cap_type in CAPABILITY_TYPES:
        vec[CAPABILITY_TYPES.index(cap_type)] = 1.0
    # else stays zero (unknown type)

    # --- IO features ----------------------------------------------------
    inputs   = capability.get("inputs",  [])
    outputs  = capability.get("outputs", [])
    required = [inp for inp in inputs if inp.get("required", True)]
    optional = [inp for inp in inputs if not inp.get("required", True)]

    io_vec = np.array([
        len(inputs),
        len(outputs),
        len(required),
        len(optional),
    ], dtype=float)
    # Normalise counts: clamp to a reasonable max (10)
    io_vec = np.clip(io_vec / 10.0, 0.0, 1.0)
    s, e = IDX_IO
    vec[s:e] = io_vec

    # --- IO name match --------------------------------------------------
    input_names  = {inp.get("name", "").lower() for inp in inputs}
    output_names = {out.get("name", "").lower() for out in outputs}
    if input_names:
        match_frac = len(input_names & output_names) / len(input_names)
    else:
        match_frac = 0.0
    vec[IDX_IOMATCH[0]] = match_frac

    # --- Resource multi-hot ---------------------------------------------
    resources = [r.lower() for r in capability.get("resources", [])]
    s, e = IDX_RESOURCE
    # Use GLOBAL_RESOURCE_VOCAB always for consistent encoding
    for r in resources:
        if r in GLOBAL_RESOURCE_VOCAB:
            idx = GLOBAL_RESOURCE_VOCAB.index(r)
            if s + idx < e:
                vec[s + idx] = 1.0

    # --- Cost normalised ------------------------------------------------
    cost   = capability.get("cost", {})
    fields = ["time_ms", "money", "resource", "risk", "energy"]
    s, e   = IDX_COST
    for k, field in enumerate(fields):
        raw_val = float(cost.get(field, 0.0))
        vec[s + k] = _normalize(raw_val, field)

    # --- Reliability ----------------------------------------------------
    vec[IDX_RELY[0]] = float(capability.get("reliability", 1.0))

    # --- Precondition vector --------------------------------------------
    precond = capability.get("preconditions", {})
    s, e    = IDX_PRECOND
    vec[s:e] = _encode_condition(precond, state_vars)

    # --- Effect vector --------------------------------------------------
    effects = capability.get("effects", {})
    s, e    = IDX_EFFECT
    vec[s:e] = _encode_condition(effects, state_vars)

    return vec


# ---------------------------------------------------------------------------
# Similarity
# ---------------------------------------------------------------------------

def similarity(vector_x: np.ndarray, vector_y: np.ndarray) -> float:
    """
    Cosine similarity over the full concatenated capability vector.

    Returns a float in [-1, 1].  Returns 0.0 if either vector is all zeros.

    This measures structural similarity between two capabilities (same type,
    similar resource usage, comparable cost/reliability, overlapping
    pre/effects). It is intentionally DIFFERENT from compatibility():
      - Two API capabilities that both flip 'payment_complete' will score
        high similarity even if one cannot follow the other in sequence.
      - compatibility() measures sequential fitness; similarity() measures
        representational closeness.
    """
    norm_x = np.linalg.norm(vector_x)
    norm_y = np.linalg.norm(vector_y)
    if norm_x == 0.0 or norm_y == 0.0:
        return 0.0
    return float(np.dot(vector_x, vector_y) / (norm_x * norm_y))


# ---------------------------------------------------------------------------
# Compatibility
# ---------------------------------------------------------------------------

def compatibility(cap_i_vec: np.ndarray, cap_j_vec: np.ndarray) -> float:
    """
    Measure how well capability i can be directly followed by capability j.

    Formula
    -------
      effect_i    = cap_i_vec[IDX_EFFECT[0]:IDX_EFFECT[1]]
      precond_j   = cap_j_vec[IDX_PRECOND[0]:IDX_PRECOND[1]]
      denom       = sum(|precond_j|)

      compatibility = dot(effect_i, precond_j) / denom   if denom > 0
                    = 0.0                                  otherwise

    Interpretation
    --------------
      +1.0  effect of i exactly satisfies all preconditions of j
       0.0  effect of i is orthogonal to preconditions of j
              (or j has no preconditions in the vocabulary)
      -1.0  effect of i actively contradicts all preconditions of j

    Note: this is DISTINCT from similarity().
      Two capabilities can be structurally similar (high similarity score)
      but sequentially incompatible (low/negative compatibility score), e.g.
      CreateOrder and CancelCart are both single-API capabilities touching
      the cart but CancelCart needs cart_active=True which CreateOrder sets
      to False, giving a negative compatibility score.
    """
    s_e, e_e = IDX_EFFECT
    s_p, e_p = IDX_PRECOND

    effect_i  = cap_i_vec[s_e:e_e]
    precond_j = cap_j_vec[s_p:e_p]

    denom = float(np.sum(np.abs(precond_j)))
    if denom == 0.0:
        return 0.0
    return float(np.dot(effect_i, precond_j) / denom)


# ---------------------------------------------------------------------------
# Compose
# ---------------------------------------------------------------------------

def compose(capability_vectors: list[np.ndarray],
            capability_dicts: list[dict],
            state_vars: list[str],
            resource_vocab: list[str] | None = None) -> np.ndarray:
    """
    Compose an ordered chain of capability vectors into one composite vector.

    Algorithm
    ---------
    Given C1, C2, ..., Cn in execution order:

    Type (one-hot):
      Use the type of the FIRST capability in the chain (the "entry point").

    IO features:
      Sum inputs of all caps; outputs are the outputs of the LAST cap.
      Required = required inputs of C1 plus any that later Ci need but
      earlier caps' effects don't already satisfy.

    IO name match:
      Recompute over the merged input/output name sets.

    Resources:
      Union (logical OR) of all resource multi-hot vectors.

    Cost:
      Element-wise sum (clipped to [0,1]) — composite cost accumulates.

    Reliability:
      Product of all individual reliabilities — degrades along the chain.

    Precondition vector:
      Start with C1's precondition.  For each subsequent Ci, add any
      dimension that Ci requires but that the running accumulated effect
      does not yet satisfy (i.e. if accumulated_effect[d] != precond_i[d]
      and precond_i[d] != 0, include precond_i[d] in composite precond).

    Effect vector:
      Apply effects in sequence; later effects overwrite earlier ones
      where they conflict (last-writer-wins per dimension).

    Parameters
    ----------
    capability_vectors : ordered list of encoded capability vectors
    capability_dicts   : corresponding capability dicts (for IO metadata)
    state_vars         : domain state-variable vocabulary
    resource_vocab     : optional resource vocabulary

    Returns
    -------
    np.ndarray of shape (VECTOR_DIM,) — the composite capability vector
    """
    if not capability_vectors:
        return np.zeros(VECTOR_DIM, dtype=float)
    if len(capability_vectors) == 1:
        return capability_vectors[0].copy()

    composite = np.zeros(VECTOR_DIM, dtype=float)
    rvocab = resource_vocab if resource_vocab is not None else GLOBAL_RESOURCE_VOCAB

    # ---- Type: use first cap's type one-hot ----------------------------
    s, e = IDX_TYPE
    composite[s:e] = capability_vectors[0][s:e]

    # ---- IO features ---------------------------------------------------
    all_inputs  = []
    all_outputs = []
    for cd in capability_dicts:
        all_inputs  += cd.get("inputs",  [])
        all_outputs += cd.get("outputs", [])
    # Required = inputs of C1 only (those are externally required)
    first_required = [i for i in capability_dicts[0].get("inputs", [])
                      if i.get("required", True)]
    first_optional = [i for i in capability_dicts[0].get("inputs", [])
                      if not i.get("required", True)]
    io_vec = np.array([
        len(all_inputs),
        len(capability_dicts[-1].get("outputs", [])),
        len(first_required),
        len(first_optional),
    ], dtype=float)
    io_vec = np.clip(io_vec / 10.0, 0.0, 1.0)
    s, e   = IDX_IO
    composite[s:e] = io_vec

    # ---- IO name match -------------------------------------------------
    in_names  = {i.get("name", "").lower() for i in capability_dicts[0].get("inputs", [])}
    out_names = {o.get("name", "").lower() for o in capability_dicts[-1].get("outputs", [])}
    composite[IDX_IOMATCH[0]] = (len(in_names & out_names) / len(in_names)
                                  if in_names else 0.0)

    # ---- Resources: union multi-hot ------------------------------------
    s, e = IDX_RESOURCE
    for cv in capability_vectors:
        composite[s:e] = np.maximum(composite[s:e], cv[s:e])

    # ---- Cost: sum (clipped) ------------------------------------------
    s, e = IDX_COST
    cost_sum = np.zeros(e - s, dtype=float)
    for cv in capability_vectors:
        cost_sum += cv[s:e]
    composite[s:e] = np.clip(cost_sum, 0.0, 1.0)

    # ---- Reliability: product -----------------------------------------
    reliability = 1.0
    for cv in capability_vectors:
        reliability *= float(cv[IDX_RELY[0]])
    composite[IDX_RELY[0]] = reliability

    # ---- Precondition: C1's base + unsatisfied requirements of later caps
    s_p, e_p = IDX_PRECOND
    s_e, e_e = IDX_EFFECT

    composite_precond  = capability_vectors[0][s_p:e_p].copy()
    accumulated_effect = capability_vectors[0][s_e:e_e].copy()

    for cv in capability_vectors[1:]:
        precond_i = cv[s_p:e_p]
        effect_i  = cv[s_e:e_e]

        for d in range(len(precond_i)):
            if precond_i[d] != 0.0 and accumulated_effect[d] != precond_i[d]:
                # This dimension is required by cap i but not yet satisfied
                if composite_precond[d] == 0.0:
                    composite_precond[d] = precond_i[d]

        # Later effect overwrites earlier (last-writer-wins)
        for d in range(len(effect_i)):
            if effect_i[d] != 0.0:
                accumulated_effect[d] = effect_i[d]

    composite[s_p:e_p] = composite_precond
    composite[s_e:e_e] = accumulated_effect

    return composite


# ---------------------------------------------------------------------------
# Convenience: load all domains and fit cost stats
# ---------------------------------------------------------------------------

def load_all_domains(data_dir: str) -> tuple[list[dict], list[str]]:
    """
    Load all domain JSON files from data_dir, fit cost normalisation stats,
    and return (domains_list, domain_filenames).
    """
    import glob
    files   = sorted(glob.glob(os.path.join(data_dir, "domain*.json")))
    domains = [load_domain(f) for f in files]
    collect_cost_stats(domains)
    return domains, [os.path.basename(f) for f in files]
