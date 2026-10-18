import numpy as np

STATE_FEATURES = ["authenticated", "cart_exists", "cart_nonempty", "inventory_available", "order_exists", "payment_success", "notification_sent", "cart_cancelled"]
CAPABILITY_TYPES = ["API", "DATABASE", "GUI", "EVENT", "FUNCTION", "FILE", "COMPUTATION", "MESSAGE", "SERVICE"]
RESOURCE_TYPES = ["Database", "Payment Gateway", "Network", "File System", "Authentication Token", "External Service"]
ALL_INPUTS = ["cart_id", "order_id", "amount", "message", "product_id"]
ALL_OUTPUTS = ["order_id", "payment_id", "message", "notification_id", "product_details"]

class Capability:
    def __init__(self, name, capability_type, inputs, outputs, preconditions, effects, resources=None, cost=0.0, reliability=1.0, availability=1):
        self.name = name
        self.capability_type = capability_type
        self.inputs = inputs
        self.outputs = outputs
        self.preconditions = preconditions
        self.effects = effects
        self.resources = resources or []
        self.cost = cost
        self.reliability = reliability
        self.availability = availability

    def display(self):
        print("\nCapability:", self.name)
        print("Type:", self.capability_type)
        print("Inputs:", self.inputs)
        print("Outputs:", self.outputs)
        print("Preconditions:", self.preconditions)
        print("Effects:", self.effects)
        print("Resources:", self.resources)
        print("Cost:", self.cost)
        print("Reliability:", self.reliability)
        print("Availability:", self.availability)

def encode_state(state):
    return np.array([1 if state.get(x, False) else 0 for x in STATE_FEATURES], dtype=float)

def encode_goal(goal):
    return np.array([1 if goal.get(x, False) else 0 for x in STATE_FEATURES], dtype=float)

def encode_capability(capability):
    vector = []
    vector.extend(1 if capability.capability_type == x else 0 for x in CAPABILITY_TYPES)
    vector.extend(1 if x in capability.inputs else 0 for x in ALL_INPUTS)
    vector.extend(1 if x in capability.outputs else 0 for x in ALL_OUTPUTS)
    vector.extend(1 if x in capability.preconditions else 0 for x in STATE_FEATURES)
    vector.extend(1 if x in capability.effects else 0 for x in STATE_FEATURES)
    vector.extend(1 if x in capability.resources else 0 for x in RESOURCE_TYPES)
    vector.extend([capability.cost, capability.reliability, capability.availability])
    return np.array(vector, dtype=float)

def similarity(v1, v2):
    denominator = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denominator == 0:
        return 0.0
    return float(np.dot(v1, v2) / denominator)

def compatibility(c1, c2):
    if not c2.preconditions:
        return 1.0
    matched = sum(1 for key, value in c2.preconditions.items() if c1.effects.get(key) == value)
    return matched / len(c2.preconditions)

def input_output_compatibility(c1, c2):
    if not c2.inputs:
        return 1.0
    matched = sum(1 for item in c2.inputs if item in c1.outputs)
    return matched / len(c2.inputs)

def is_composable(c1, c2):
    return compatibility(c1, c2) == 1.0

def compose(capabilities):
    if not capabilities:
        return None
    name = " -> ".join(c.name for c in capabilities)
    produced = set()
    for c in capabilities:
        produced.update(c.outputs)
    inputs = []
    for c in capabilities:
        for item in c.inputs:
            if item not in produced and item not in inputs:
                inputs.append(item)
    outputs = []
    for c in capabilities:
        for item in c.outputs:
            if item not in outputs:
                outputs.append(item)
    preconditions = dict(capabilities[0].preconditions)
    effects = {}
    for c in capabilities:
        effects.update(c.effects)
    resources = []
    for c in capabilities:
        for resource in c.resources:
            if resource not in resources:
                resources.append(resource)
    cost = sum(c.cost for c in capabilities)
    reliability = 1.0
    for c in capabilities:
        reliability *= c.reliability
    availability = int(all(c.availability == 1 for c in capabilities))
    return Capability(name, "COMPOSITE", inputs, outputs, preconditions, effects, resources, cost, reliability, availability)

initial_state = {"authenticated": True, "cart_exists": True, "cart_nonempty": True, "inventory_available": True, "order_exists": False, "payment_success": False, "notification_sent": False, "cart_cancelled": False}
goal = {"order_exists": True, "payment_success": True, "notification_sent": True}

CreateOrder = Capability("CreateOrder", "API", ["cart_id"], ["order_id"], {"authenticated": True, "cart_exists": True, "cart_nonempty": True, "inventory_available": True, "order_exists": False}, {"order_exists": True}, ["Database", "Authentication Token", "Network"], 0.02, 0.99, 1)
MakePayment = Capability("MakePayment", "API", ["order_id", "amount"], ["payment_id"], {"order_exists": True}, {"payment_success": True}, ["Payment Gateway", "Network"], 0.50, 0.97, 1)
CancelCart = Capability("CancelCart", "FUNCTION", ["cart_id"], ["message"], {"order_exists": False}, {"cart_cancelled": True}, ["Database"], 0.01, 0.99, 1)
SendNotification = Capability("SendNotification", "MESSAGE", ["message"], ["notification_id"], {"payment_success": True}, {"notification_sent": True}, ["Network", "External Service"], 0.05, 0.95, 1)
ViewProduct = Capability("ViewProduct", "GUI", ["product_id"], ["product_details"], {"authenticated": True}, {}, ["Database", "Network"], 0.01, 0.99, 1)
CAPABILITIES = [CreateOrder, MakePayment, CancelCart, SendNotification, ViewProduct]

def goal_relevance(capability, goal):
    if not capability.effects:
        return 0.0
    matched = sum(1 for key, value in capability.effects.items() if goal.get(key) == value)
    return matched / len(goal)
