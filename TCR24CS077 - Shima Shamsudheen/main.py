"""
Assignment 2 - Vector Embedding for Capability Composition
===========================================================

DESIGN SUMMARY (Deliverable 1, short form)
------------------------------------------
Condition space  R^nv : one dimension per Boolean state variable.
                        +1 = variable is True, -1 = False, 0 = unknown/unspecified.
                        States S and goals G live here. Negation is handled
                        natively: Order.exists=True and Order.exists=False are
                        opposite signs on the SAME dimension.

Capability space R^d  : semantic vector, concatenation of weighted blocks
                        [ w_P*P | w_E*E | w_I*I | w_O*O | w_T*T | w_R*R ]
    P (nv)  preconditions   (+1/-1/0, condition space)
    E (nv)  effects         (+1/-1/0, condition space)
    I (nd)  required inputs (multi-hot over data names)
    O (nd)  produced outputs(multi-hot over data names)
    T (nm)  mechanism/type  (multi-hot; small weight so that API/DB/GUI
                             versions stay close but not identical)
    R (nr)  resources       (multi-hot)

Operational space R^4 : [cost/COST_SCALE, reliability, availability, 1-risk].
    Kept SEPARATE from the semantic vector so that cost/reliability can never
    distort functional similarity (raw cost values would dominate cosine).

Similarity    : cosine similarity of semantic vectors  (functional resemblance).
Compatibility : logical test on the blocks  (E1 => P2, O1 covers I2, available,
                non-redundant). Similarity != compatibility (Property 5).
Composition   : C2 o C1 via block algebra
                P = P1 ; E = E2 overrides E1 ; I = I1 + (I2 - O1) ; O = O1 + O2 ;
                T, R = union ; cost = sum ; reliability = product ;
                availability = product ; risk = 1 - (1-r1)(1-r2).
Goal relevance: progress of a capability's effects on the UNMET goal literals.
"""

import json
import operator
import os
import time
from functools import reduce

import matplotlib
import numpy as np
import pandas as pd

# Set SHOW_PLOTS=0 in the environment to run without opening plot windows.
SHOW_PLOTS = os.environ.get("SHOW_PLOTS", "1") == "1"
if not SHOW_PLOTS:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

MECHANISMS = ["API", "DATABASE", "GUI", "EVENT", "FUNCTION",
              "FILE", "COMPUTATION", "MESSAGE", "SERVICE"]
WEIGHTS = {"P": 1.0, "E": 1.0, "I": 0.5, "O": 0.5, "T": 0.3, "R": 0.3}
COST_SCALE = 10.0
BLOCKS = "PEIOTR"
OPS = {">": operator.gt, ">=": operator.ge, "<": operator.lt,
       "<=": operator.le, "==": operator.eq, "!=": operator.ne}


# ----------------------------------------------------------------------------
# Formal capability constructor
# ----------------------------------------------------------------------------
def make_capability(name, mechanism, pre, eff, inputs, outputs, cost,
                    reliability, available=1, risk=0.0,
                    resources=(), constraints=()):
    return {
        "name": name,
        "mechanisms": [mechanism],
        "preconditions": dict(pre),      # {"Order.exists": True}
        "effects": dict(eff),
        "inputs": list(inputs),
        "outputs": list(outputs),
        "cost": cost,
        "reliability": reliability,
        "available": available,
        "risk": risk,
        "resources": list(resources),
        "constraints": [list(k) for k in constraints],  # (var, op, value)
    }
# ----------------------------------------------------------------------------
# State helpers (constraints, applying effects)
# ----------------------------------------------------------------------------
def check_constraints(state, constraints):
    for var, op, val in constraints:
        lhs = state.get(var)
        rhs = state.get(val, val) if isinstance(val, str) else val
        if lhs is None or rhs is None or not OPS[op](lhs, rhs):
            return False
    return True


def apply_capability(state, cap):
    new_state = dict(state)
    new_state.update(cap["effects"])
    return new_state


def goal_satisfied(state, goal):
    return all(state.get(k) == v for k, v in goal.items())


# ----------------------------------------------------------------------------
# The embedder
# ----------------------------------------------------------------------------
class CapabilityEmbedder:
    def __init__(self, capabilities, states=(), goals=(), weights=WEIGHTS):
        self.w = dict(weights)
        variables, data, resources = set(), set(), set()
        for c in capabilities:
            variables |= set(c["preconditions"]) | set(c["effects"])
            data |= set(c["inputs"]) | set(c["outputs"])
            resources |= set(c["resources"])
        for s in states:
            variables |= {k for k, v in s.items() if isinstance(v, bool)}
        for g in goals:
            variables |= set(g)

        self.vars = sorted(variables)
        self.data = sorted(data)
        self.res = sorted(resources)
        self.mech = MECHANISMS
        sizes = {"P": len(self.vars), "E": len(self.vars),
                 "I": len(self.data), "O": len(self.data),
                 "T": len(self.mech), "R": len(self.res)}
        self.slices, start = {}, 0
        for k in BLOCKS:
            self.slices[k] = slice(start, start + sizes[k])
            start += sizes[k]
        self.dim = start

    # ---- low-level helpers -------------------------------------------------
    def _cond(self, conditions):
        v = np.zeros(len(self.vars))
        for var, val in conditions.items():
            if var in self.vars and isinstance(val, bool):
                v[self.vars.index(var)] = 1.0 if val else -1.0
        return v

    @staticmethod
    def _multi(names, vocab):
        v = np.zeros(len(vocab))
        for n in names:
            if n in vocab:
                v[vocab.index(n)] = 1.0
        return v

    def blocks(self, cap):
        return {
            "P": self._cond(cap["preconditions"]),
            "E": self._cond(cap["effects"]),
            "I": self._multi(cap["inputs"], self.data),
            "O": self._multi(cap["outputs"], self.data),
            "T": self._multi(cap["mechanisms"], self.mech),
            "R": self._multi(cap["resources"], self.res),
        }

    def _assemble(self, b):
        return np.concatenate([self.w[k] * b[k] for k in BLOCKS])

    def split(self, vec):
        return {k: vec[self.slices[k]] / self.w[k] for k in BLOCKS}

    # ---- required interface ------------------------------------------------
    def encode_state(self, state):
        """State -> condition-space vector (+1 true, -1 false, 0 unknown)."""
        return self._cond(state)

    def encode_goal(self, goal):
        """Goal -> condition-space vector."""
        return self._cond(goal)

    def encode(self, cap):
        """Atomic or composite capability -> semantic vector in R^d."""
        return self._assemble(self.blocks(cap))

    def goal_in_capability_space(self, goal):
        """Goal placed in the effect block of R^d so it can be compared
        with whole capability vectors."""
        b = {k: np.zeros(self.slices[k].stop - self.slices[k].start) for k in BLOCKS}
        b["E"] = self.encode_goal(goal)
        return self._assemble(b)

    @staticmethod
    def similarity(v1, v2):
        """Cosine similarity (functional resemblance)."""
        n = np.linalg.norm(v1) * np.linalg.norm(v2)
        return 0.0 if n == 0 else float(np.dot(v1, v2) / n)

    def operational(self, cap):
        """Operational vector, kept apart from the semantic vector."""
        return np.array([cap["cost"] / COST_SCALE, cap["reliability"],
                         float(cap["available"]), 1.0 - cap["risk"]])

    # ---- compatibility -----------------------------------------------------
    def compatibility(self, c1, c2):
        """Can c2 run right after c1?  Returns the individual checks."""
        b1, b2 = self.blocks(c1), self.blocks(c2)

        # What is known to hold after c1: its effects, else what it required.
        known = np.where(b1["E"] != 0, b1["E"], b1["P"])
        need = b2["P"] != 0
        logic_ok = bool(np.all(known[need] == b2["P"][need]))
        logic_score = float(np.mean(known[need] * b2["P"][need])) if need.any() else 1.0

        # Data c2 needs must be produced (or still in scope as c1's input).
        in_scope = np.maximum(b1["O"], b1["I"])
        req = b2["I"] > 0
        io_ok = bool(np.all(in_scope[req] > 0))

        avail_ok = c1["available"] == 1 and c2["available"] == 1

        # Non-redundant: c2 must establish something not already true.
        eff2 = b2["E"] != 0
        useful = bool(np.any(known[eff2] != b2["E"][eff2])) if eff2.any() else False

        return {"logic_score": logic_score, "logic_ok": logic_ok, "io_ok": io_ok,
                "available": avail_ok, "useful": useful,
                "compatible": logic_ok and io_ok and avail_ok and useful}

    def is_compatible(self, c1, c2):
        return self.compatibility(c1, c2)["compatible"]

    # ---- composition -------------------------------------------------------
    def _compose2(self, a, b):
        if a is None or not self.is_compatible(a, b):
            return None
        return {
            "name": f'{a["name"]} -> {b["name"]}',
            "mechanisms": sorted(set(a["mechanisms"]) | set(b["mechanisms"])),
            "preconditions": dict(a["preconditions"]),
            "effects": {**a["effects"], **b["effects"]},
            "inputs": list(dict.fromkeys(
                a["inputs"] + [i for i in b["inputs"] if i not in a["outputs"]])),
            "outputs": list(dict.fromkeys(a["outputs"] + b["outputs"])),
            "cost": a["cost"] + b["cost"],
            "reliability": a["reliability"] * b["reliability"],
            "available": a["available"] * b["available"],
            "risk": 1 - (1 - a["risk"]) * (1 - b["risk"]),
            "resources": sorted(set(a["resources"]) | set(b["resources"])),
            "constraints": a["constraints"] + [k for k in b["constraints"]
                                               if k not in a["constraints"]],
        }

    def compose(self, *caps):
        """compose(C1, C2, ..., Cn) -> composite capability, or None."""
        return reduce(self._compose2, caps[1:], caps[0]) if caps else None

    def compose_vectors(self, v1, v2):
        """Block algebra on semantic vectors (no compatibility check)."""
        a, b = self.split(v1), self.split(v2)
        out = {
            "P": a["P"],
            "E": np.where(b["E"] != 0, b["E"], a["E"]),
            "I": np.maximum(a["I"], b["I"] * (1 - a["O"])),
            "O": np.maximum(a["O"], b["O"]),
            "T": np.maximum(a["T"], b["T"]),
            "R": np.maximum(a["R"], b["R"]),
        }
        return self._assemble(out)

    # ---- state awareness ---------------------------------------------------
    def is_applicable(self, state, cap, data):
        s, p = self.encode_state(state), self.blocks(cap)["P"]
        need = p != 0
        return bool(np.all(s[need] == p[need])
                    and check_constraints(state, cap["constraints"])
                    and all(i in data for i in cap["inputs"])
                    and cap["available"] == 1)

    # ---- goal relevance ----------------------------------------------------
    def goal_relevance(self, cap, goal, state):
        """Fraction of the UNMET goal literals advanced by the effects.
        +1 = achieves all of them, 0 = irrelevant, <0 = works against the goal."""
        g, s = self.encode_goal(goal), self.encode_state(state)
        gap = np.where(g != s, g, 0.0)
        if not gap.any():
            return 0.0
        return float(np.dot(self.blocks(cap)["E"], gap) / np.abs(gap).sum())

# ----------------------------------------------------------------------------
# PROBLEM 1: e-commerce ordering (main experimental dataset)
# ----------------------------------------------------------------------------
INITIAL_STATE = {
    "User.authenticated": True, "User.role": "CUSTOMER",
    "Cart.exists": True, "Cart.item_count": 3,
    "Order.exists": False, "Payment.success": False,
    "Inventory.available": True, "Notification.sent": False,
    "payment_amount": 120.0, "transaction_limit": 500.0,
}
INITIAL_DATA = {"cart_id"}
GOAL = {"Order.exists": True, "Payment.success": True, "Notification.sent": True}

CREATE_ORDER = make_capability(
    "CreateOrder", "API",
    pre={"Cart.exists": True, "User.authenticated": True},
    eff={"Order.exists": True, "Cart.locked": True},
    inputs=["cart_id"], outputs=["order_id"], cost=2, reliability=0.99, risk=0.05,
    resources=["Database", "AuthToken"], constraints=[("Cart.item_count", ">", 0)])
MAKE_PAYMENT = make_capability(
    "MakePayment", "API",
    pre={"Order.exists": True}, eff={"Payment.success": True},
    inputs=["order_id"], outputs=["payment_id"], cost=5, reliability=0.95, risk=0.20,
    resources=["PaymentGateway", "Network"],
    constraints=[("payment_amount", "<=", "transaction_limit")])
SEND_NOTIFICATION = make_capability(
    "SendNotification", "MESSAGE",
    pre={"Payment.success": True}, eff={"Notification.sent": True},
    inputs=["payment_id"], outputs=["notification_id"], cost=1, reliability=0.98,
    risk=0.02, resources=["Network"])
CANCEL_CART = make_capability(
    "CancelCart", "FUNCTION",
    pre={"Cart.exists": True, "Order.exists": False},
    eff={"Cart.cancelled": True, "Cart.exists": False},
    inputs=["cart_id"], outputs=["cancellation_status"], cost=1, reliability=0.97,
    risk=0.01)
UPDATE_INVENTORY = make_capability(
    "UpdateInventory", "DATABASE",
    pre={"Order.exists": True}, eff={"Inventory.updated": True},
    inputs=["order_id"], outputs=["inventory_status"], cost=3, reliability=0.96,
    risk=0.08, resources=["Database"])
# Irrelevant to the goal (Experiment 4)
GENERATE_REPORT = make_capability(
    "GenerateReport", "COMPUTATION",
    pre={"Order.exists": True}, eff={"Report.generated": True},
    inputs=["order_id"], outputs=["report_file"], cost=4, reliability=0.90,
    risk=0.03, resources=["FileSystem"])
SEND_MARKETING = make_capability(
    "SendMarketingEmail", "MESSAGE",
    pre={"User.authenticated": True}, eff={"Marketing.sent": True},
    inputs=[], outputs=["campaign_id"], cost=1.5, reliability=0.90, risk=0.30,
    resources=["Network"])

CAPABILITIES = [CREATE_ORDER, MAKE_PAYMENT, SEND_NOTIFICATION, CANCEL_CART,
                UPDATE_INVENTORY, GENERATE_REPORT, SEND_MARKETING]

# Experiment 3: same effect, different mechanisms
ALTERNATIVES = [
    make_capability("CreateOrder_API", "API", CREATE_ORDER["preconditions"],
                    CREATE_ORDER["effects"], ["cart_id"], ["order_id"], 2, 0.99,
                    risk=0.05, resources=["Database", "AuthToken"]),
    make_capability("CreateOrder_DB", "DATABASE", CREATE_ORDER["preconditions"],
                    CREATE_ORDER["effects"], ["cart_id"], ["order_id"], 3, 0.97,
                    risk=0.08, resources=["Database"]),
    make_capability("CreateOrder_GUI", "GUI", CREATE_ORDER["preconditions"],
                    CREATE_ORDER["effects"], ["cart_id"], ["order_id"], 4, 0.95,
                    risk=0.12, resources=["Browser", "Network"]),
]

# Expected compatibilities, used to measure consistency (ground truth by hand)
EXPECTED_1 = [
    (CREATE_ORDER, MAKE_PAYMENT, True), (CREATE_ORDER, CANCEL_CART, False),
    (CREATE_ORDER, SEND_NOTIFICATION, False), (MAKE_PAYMENT, SEND_NOTIFICATION, True),
    (CREATE_ORDER, UPDATE_INVENTORY, True), (MAKE_PAYMENT, CREATE_ORDER, False),
    (CANCEL_CART, CREATE_ORDER, False), (CANCEL_CART, MAKE_PAYMENT, False),
    (CREATE_ORDER, CREATE_ORDER, False), (UPDATE_INVENTORY, SEND_NOTIFICATION, False),
]

# ----------------------------------------------------------------------------
# PROBLEM 2: file-processing pipeline (consistency across problems)
# ----------------------------------------------------------------------------
STATE_2 = {"User.authenticated": True, "File.uploaded": False,
           "File.clean": False, "File.stored": False}
GOAL_2 = {"File.stored": True}
UPLOAD = make_capability("UploadFile", "FILE", {"User.authenticated": True},
                         {"File.uploaded": True}, [], ["file_id"], 2, 0.98,
                         resources=["Network"])
SCAN = make_capability("ScanFile", "SERVICE", {"File.uploaded": True},
                       {"File.clean": True}, ["file_id"], ["scan_id"], 3, 0.96,
                       risk=0.05, resources=["ExternalService"])
STORE = make_capability("StoreFile", "DATABASE", {"File.clean": True},
                        {"File.stored": True}, ["file_id"], ["record_id"], 2, 0.99,
                        resources=["Database"])
DELETE = make_capability("DeleteFile", "FILE", {"File.uploaded": True},
                         {"File.uploaded": False}, ["file_id"], ["delete_status"], 1, 0.97)
CAPS_2 = [UPLOAD, SCAN, STORE, DELETE]
EXPECTED_2 = [(UPLOAD, SCAN, True), (SCAN, STORE, True), (UPLOAD, STORE, False),
              (STORE, UPLOAD, False), (SCAN, UPLOAD, False), (UPLOAD, DELETE, True)]


# ----------------------------------------------------------------------------
# Output helpers
# ----------------------------------------------------------------------------
def section(title):
    print("\n" + "=" * 72 + f"\n{title}\n" + "=" * 72)


def short(cap):
    return {k: cap[k] for k in ("name", "preconditions", "effects", "inputs",
                                "outputs", "cost", "reliability", "risk",
                                "resources", "constraints")}


def main():
    emb = CapabilityEmbedder(CAPABILITIES + ALTERNATIVES,
                             states=[INITIAL_STATE], goals=[GOAL])
    by_name = {c["name"]: c for c in CAPABILITIES}
    vec = {c["name"]: emb.encode(c) for c in CAPABILITIES}

    section("EMBEDDING SPACE")
    print(f"Condition space dim (states/goals): {len(emb.vars)}")
    print(f"Capability space dim d            : {emb.dim}")
    print("State variables:", emb.vars)
    print("Data names     :", emb.data)
    print("Resources      :", emb.res)
    print("\nInitial state vector:", emb.encode_state(INITIAL_STATE))
    print("Goal vector         :", emb.encode_goal(GOAL))

    # ---- Capability identity ----------------------------------------------
    section("CAPABILITY IDENTITY: pairwise cosine similarity (distinct = < 1)")
    names = [c["name"] for c in CAPABILITIES]
    sim_matrix = pd.DataFrame(
        [[emb.similarity(vec[a], vec[b]) for b in names] for a in names],
        index=names, columns=names)
    print(sim_matrix.round(2).to_string())
    off_diag = sim_matrix.values[~np.eye(len(names), dtype=bool)]
    print(f"\nMax off-diagonal similarity: {off_diag.max():.3f} "
          f"(all capabilities distinguishable: {off_diag.max() < 0.999})")

    # ---- State awareness ----------------------------------------------------
    section("STATE AWARENESS: which capabilities are applicable?")
    state_after = apply_capability(INITIAL_STATE, CREATE_ORDER)
    data_after = INITIAL_DATA | set(CREATE_ORDER["outputs"])
    rows = [{"Capability": c["name"],
             "Initial state": emb.is_applicable(INITIAL_STATE, c, INITIAL_DATA),
             "After CreateOrder": emb.is_applicable(state_after, c, data_after)}
            for c in CAPABILITIES]
    print(pd.DataFrame(rows).to_string(index=False))

    # ---- Experiment 1 -------------------------------------------------------
    section("EXPERIMENT 1: CAPABILITY COMPATIBILITY (C1=CreateOrder)")
    rows = []
    for c in (MAKE_PAYMENT, CANCEL_CART, SEND_NOTIFICATION):
        r = emb.compatibility(CREATE_ORDER, c)
        rows.append({"C1": "CreateOrder", "C2": c["name"],
                     "Similarity": round(emb.similarity(vec["CreateOrder"], vec[c["name"]]), 3),
                     "LogicScore": round(r["logic_score"], 2), "IO": r["io_ok"],
                     "Compatible": r["compatible"]})
    print(pd.DataFrame(rows).to_string(index=False))

    pair_rows = []
    for a in CAPABILITIES:
        for b in CAPABILITIES:
            r = emb.compatibility(a, b)
            pair_rows.append({"First": a["name"], "Second": b["name"],
                              "Similarity": round(emb.similarity(vec[a["name"]], vec[b["name"]]), 3),
                              "LogicScore": round(r["logic_score"], 2),
                              "LogicOK": r["logic_ok"], "IO_OK": r["io_ok"],
                              "Available": r["available"], "Useful": r["useful"],
                              "Compatible": r["compatible"]})
    compat_df = pd.DataFrame(pair_rows)
    compat_df.to_csv("compatibility_results.csv", index=False)
    print("\nCompatible pairs:")
    print(compat_df[compat_df.Compatible][["First", "Second", "Similarity"]].to_string(index=False))

    # ---- Property 5: similarity vs compatibility ---------------------------
    section("SIMILARITY vs COMPATIBILITY (they are not the same thing)")
    others = compat_df[compat_df.First != compat_df.Second]
    print("Most similar pairs that CANNOT compose:")
    print(others[~others.Compatible].nlargest(4, "Similarity")
          [["First", "Second", "Similarity", "Compatible"]].to_string(index=False))
    print("\nLeast similar pairs that CAN compose:")
    print(others[others.Compatible].nsmallest(4, "Similarity")
          [["First", "Second", "Similarity", "Compatible"]].to_string(index=False))
    corr = np.corrcoef(others.Similarity, others.Compatible.astype(float))[0, 1]
    print(f"\nCorrelation(similarity, compatibility) = {corr:.3f} -> similarity alone "
          "cannot decide composability.")

    # ---- Experiment 2 -------------------------------------------------------
    section("EXPERIMENT 2: CAPABILITY COMPOSITION")
    pair = emb.compose(CREATE_ORDER, MAKE_PAYMENT)
    chain = emb.compose(CREATE_ORDER, MAKE_PAYMENT, SEND_NOTIFICATION)
    print("Valid pair   :", short(pair)["name"], "| cost", pair["cost"],
          "| reliability", round(pair["reliability"], 4))
    print("Invalid pair :", emb.compose(CREATE_ORDER, CANCEL_CART))
    print("Invalid chain:", emb.compose(CREATE_ORDER, SEND_NOTIFICATION, MAKE_PAYMENT))
    print("\nThree-step composite:")
    for k, v in short(chain).items():
        print(f"  {k}: {v}")
    cv = emb.encode(chain)
    print("\nCosine(composite, component):")
    for c in (CREATE_ORDER, MAKE_PAYMENT, SEND_NOTIFICATION):
        print(f"  {c['name']:<18} {emb.similarity(cv, vec[c['name']]):.3f}")
    naive_sum = vec["CreateOrder"] + vec["MakePayment"] + vec["SendNotification"]
    print(f"  naive vector SUM    {emb.similarity(cv, naive_sum):.3f}  "
          "(high overlap, but a plain sum ignores order and validity)")
    algebra = emb.compose_vectors(emb.compose_vectors(vec["CreateOrder"], vec["MakePayment"]),
                                  vec["SendNotification"])
    print("Block-algebra composition equals encode(composite):", np.allclose(algebra, cv))
    final_state = INITIAL_STATE
    for c in (CREATE_ORDER, MAKE_PAYMENT, SEND_NOTIFICATION):
        final_state = apply_capability(final_state, c)
    print("Composite applicable from initial state:",
          emb.is_applicable(INITIAL_STATE, chain, INITIAL_DATA))
    print("Goal satisfied after executing the composite:", goal_satisfied(final_state, GOAL))

    # ---- Experiment 3 -------------------------------------------------------
    section("EXPERIMENT 3: ALTERNATIVE IMPLEMENTATIONS (API / DATABASE / GUI)")
    alt_vec = {c["name"]: emb.encode(c) for c in ALTERNATIVES}
    alt_names = list(alt_vec)
    alt_sim = pd.DataFrame(
        [[emb.similarity(alt_vec[a], alt_vec[b]) for b in alt_names] for a in alt_names],
        index=alt_names, columns=alt_names)
    print(alt_sim.round(3).to_string())
    print(f"\nCosine(CreateOrder_API, MakePayment) = "
          f"{emb.similarity(alt_vec['CreateOrder_API'], vec['MakePayment']):.3f} "
          "(unrelated capability, much lower)")
    print("Same compatibility with MakePayment:",
          [emb.is_compatible(a, MAKE_PAYMENT) for a in ALTERNATIVES])
    print("Identical vectors?:",
          np.allclose(alt_vec["CreateOrder_API"], alt_vec["CreateOrder_DB"]))
    alt_ops = pd.DataFrame([{"Alternative": a["name"], "Mechanism": a["mechanisms"][0],
                             "Cost": a["cost"], "Reliability": a["reliability"],
                             "Risk": a["risk"],
                             "Utility": round(a["reliability"] * (1 - a["risk"]) / a["cost"], 3)}
                            for a in ALTERNATIVES])
    print("\n" + alt_ops.to_string(index=False))

    # ---- Experiment 4 -------------------------------------------------------
    section("EXPERIMENT 4: GOAL RELEVANCE (useful vs irrelevant)")
    goal_full = emb.goal_in_capability_space(GOAL)
    cands = CAPABILITIES + [pair, chain]
    rel_rows = [{"Capability": c["name"],
                 "Relevance": round(emb.goal_relevance(c, GOAL, INITIAL_STATE), 3),
                 "Cosine(full, goal)": round(emb.similarity(emb.encode(c), goal_full), 3)}
                for c in cands]
    rel_df = pd.DataFrame(rel_rows).sort_values("Relevance", ascending=False)
    print(rel_df.to_string(index=False))
    print("\nRelevance = share of unmet goal literals advanced by the effects.")
    print("Irrelevant (relevance = 0):",
          [r["Capability"] for r in rel_rows if r["Relevance"] == 0])

    # ---- Experiment 5 -------------------------------------------------------
    section("EXPERIMENT 5: OPERATIONAL ATTRIBUTES")
    op_df = pd.DataFrame([{"Capability": c["name"], "Cost": c["cost"],
                           "Reliability": c["reliability"], "Availability": c["available"],
                           "Risk": c["risk"], "Resources": ", ".join(c["resources"]) or "-"}
                          for c in CAPABILITIES + [chain]])
    print(op_df.to_string(index=False))
    op_df.to_csv("operational_results.csv", index=False)
    print("\nOperational vector [cost/10, reliability, availability, 1-risk]:")
    print("  chain:", np.round(emb.operational(chain), 4))
    print(f"  chain cost = sum = {chain['cost']}, reliability = product = "
          f"{chain['reliability']:.4f}, risk = {chain['risk']:.4f}")
    print("  chain resources:", chain["resources"])

    down = dict(MAKE_PAYMENT, name="MakePayment(down)", available=0)
    print("\nAvailability test (MakePayment unavailable):")
    print("  semantic cosine unchanged :",
          round(emb.similarity(emb.encode(MAKE_PAYMENT), emb.encode(down)), 3))
    print("  CreateOrder -> MakePayment :", emb.is_compatible(CREATE_ORDER, MAKE_PAYMENT))
    print("  CreateOrder -> MakePayment(down):", emb.is_compatible(CREATE_ORDER, down))
    print("  composition result         :", emb.compose(CREATE_ORDER, down))

    over = dict(INITIAL_STATE, payment_amount=900.0)
    print("\nConstraint test (payment_amount > transaction_limit):")
    print("  MakePayment applicable after CreateOrder, amount=120:",
          emb.is_applicable(apply_capability(INITIAL_STATE, CREATE_ORDER), MAKE_PAYMENT, data_after))
    print("  MakePayment applicable after CreateOrder, amount=900:",
          emb.is_applicable(apply_capability(over, CREATE_ORDER), MAKE_PAYMENT, data_after))

    # ---- Consistency across problems ---------------------------------------
    section("CONSISTENCY ACROSS PROBLEMS")
    emb2 = CapabilityEmbedder(CAPS_2, states=[STATE_2], goals=[GOAL_2])
    ok1 = [emb.is_compatible(a, b) == exp for a, b, exp in EXPECTED_1]
    ok2 = [emb2.is_compatible(a, b) == exp for a, b, exp in EXPECTED_2]
    print(f"Problem 1 (e-commerce)      : {sum(ok1)}/{len(ok1)} expected relations reproduced")
    print(f"Problem 2 (file processing) : {sum(ok2)}/{len(ok2)} expected relations reproduced")
    pipe = emb2.compose(UPLOAD, SCAN, STORE)
    print("Problem 2 composite:", pipe["name"] if pipe else None)
    print("Problem 2 relevance of composite:",
          emb2.goal_relevance(pipe, GOAL_2, STATE_2),
          "| DeleteFile:", emb2.goal_relevance(DELETE, GOAL_2, STATE_2))

    # ---- Efficiency ---------------------------------------------------------
    section("EFFICIENCY")
    n = 2000
    t0 = time.perf_counter()
    for _ in range(n):
        emb.encode(CREATE_ORDER)
    t_enc = (time.perf_counter() - t0) / n * 1e6
    t0 = time.perf_counter()
    for _ in range(n):
        emb.compatibility(CREATE_ORDER, MAKE_PAYMENT)
    t_cmp = (time.perf_counter() - t0) / n * 1e6
    print(f"Vector size: {emb.dim} dims = {emb.dim * 8} bytes (float64) per capability")
    print(f"encode(): ~{t_enc:.1f} us | compatibility(): ~{t_cmp:.1f} us per pair")
    print(f"Storage for N capabilities: O(N*d); all-pairs compatibility: O(N^2*d)")

    # ---- Save dataset (Deliverable 3) --------------------------------------
    dataset = {
        "problem_1_ecommerce": {"initial_state": INITIAL_STATE,
                                "initial_data": sorted(INITIAL_DATA), "goal": GOAL,
                                "capabilities": CAPABILITIES, "alternatives": ALTERNATIVES},
        "problem_2_file_pipeline": {"initial_state": STATE_2, "goal": GOAL_2,
                                    "capabilities": CAPS_2},
    }
    with open("experimental_dataset.json", "w") as f:
        json.dump(dataset, f, indent=2)

    # ---- Figures -------------------------------------------------------------
    plot_caps = CAPABILITIES + [chain]
    labels = [c["name"].replace(" -> ", "\n->") if c is chain else c["name"] for c in plot_caps]
    labels[-1] = "Composite\n(3-step)"

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    ax[0].bar(labels, [c["cost"] for c in plot_caps], color="#1f77b4")
    ax[0].set_title("Capability Cost Comparison")
    ax[0].set_ylabel("Cost")
    ax[1].bar(labels, [c["reliability"] for c in plot_caps], color="#2ca02c")
    ax[1].set_title("Capability Reliability Comparison")
    ax[1].set_ylabel("Reliability")
    ax[1].set_ylim(0.8, 1.0)
    for a in ax:
        a.tick_params(axis="x", rotation=40)
    plt.tight_layout()
    plt.savefig("cost_comparison.png", dpi=150)

    comp_matrix = compat_df.pivot(index="First", columns="Second",
                                  values="Compatible").loc[names, names].astype(float)
    fig, ax = plt.subplots(1, 2, figsize=(14, 6))
    for a, data_m, title, cmap in ((ax[0], sim_matrix.values, "Cosine similarity", "viridis"),
                                   (ax[1], comp_matrix.values, "Compatibility (First -> Second)", "Greens")):
        im = a.imshow(data_m, cmap=cmap, vmin=(-1 if title.startswith("Cosine") else 0), vmax=1)
        a.set_xticks(range(len(names)))
        a.set_yticks(range(len(names)))
        a.set_xticklabels(names, rotation=60, ha="right", fontsize=8)
        a.set_yticklabels(names, fontsize=8)
        a.set_title(title)
        for i in range(len(names)):
            for j in range(len(names)):
                a.text(j, i, f"{data_m[i, j]:.2f}" if title.startswith("Cosine") else int(data_m[i, j]),
                       ha="center", va="center", fontsize=7,
                       color="white" if data_m[i, j] < (0.0 if title.startswith("Cosine") else 0.5) else "black")
        plt.colorbar(im, ax=a, fraction=0.046)
    plt.tight_layout()
    plt.savefig("similarity_vs_compatibility.png", dpi=150)

    fig = plt.figure(figsize=(9, 5))
    plt.barh(rel_df["Capability"], rel_df["Relevance"], color="#ff7f0e")
    plt.gca().invert_yaxis()
    plt.xlabel("Goal relevance")
    plt.title("Goal Relevance of Capabilities")
    plt.tight_layout()
    plt.savefig("goal_relevance.png", dpi=150)

    print("\nSaved: compatibility_results.csv, operational_results.csv, "
          "experimental_dataset.json, cost_comparison.png, "
          "similarity_vs_compatibility.png, goal_relevance.png")
    print("\nAll experiments completed.")
    if SHOW_PLOTS:
        plt.show()


if __name__ == "__main__":
    main()