import numpy as np

# A simple global vocabulary to map features to vector indices
VOCAB = {}
VECTOR_SIZE = 50

def get_feature_vector(features):
    """Converts a list of string features into a multi-hot vector embedding."""
    vec = np.zeros(VECTOR_SIZE)
    for f in features:
        if f not in VOCAB:
            # Assign a consistent index in the vector for this feature
            VOCAB[f] = len(VOCAB) % VECTOR_SIZE
        vec[VOCAB[f]] += 1
    return vec

class State:
    def __init__(self, variables):
        self.variables = variables

class Goal:
    def __init__(self, conditions):
        self.conditions = conditions

class Capability:
    def __init__(self, name, preconditions, effects, mech_type="API", cost=1.0, reliability=0.99):
        self.name = name
        self.preconditions = preconditions
        self.effects = effects
        self.mech_type = mech_type
        self.cost = cost
        self.reliability = reliability

def encode(entity):
    """Encodes a formal entity (State, Goal, Capability) into a numerical vector."""
    features = []
    
    if isinstance(entity, State):
        for k, v in entity.variables.items():
            features.append(f"STATE_{k}_{v}")
            
    elif isinstance(entity, Goal):
        for k, v in entity.conditions.items():
            features.append(f"GOAL_{k}_{v}")
            
    elif isinstance(entity, Capability):
        for k, v in entity.preconditions.items():
            features.append(f"PRE_{k}_{v}")
        for k, v in entity.effects.items():
            features.append(f"EFF_{k}_{v}")
        features.append(f"MECH_{entity.mech_type}")
        
    return get_feature_vector(features)

def compose(cap1, cap2):
    """Composes two capabilities into a complex capability."""
    # A composite capability takes preconditions of first, effects of second
    return Capability(
        name=f"{cap1.name}_then_{cap2.name}",
        preconditions=cap1.preconditions,
        effects=cap2.effects,
        mech_type="COMPOSITE",
        cost=cap1.cost + cap2.cost,
        reliability=cap1.reliability * cap2.reliability
    )

def similarity(v1, v2):
    """Calculates the cosine similarity between two vectors."""
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return np.dot(v1, v2) / (norm1 * norm2)

if __name__ == "__main__":
    print("--- Assignment 2: Vector Embedding for Capability Composition ---\n")
    
    # 1. Capability compatibility
    print("Experiment 1: Capability compatibility")
    c1 = Capability("CreateOrder", {}, {"OrderExists": True})
    c2 = Capability("MakePayment", {"OrderExists": True}, {"PaymentStatus": "SUCCESS"})
    c3 = Capability("CancelCart", {"OrderExists": False}, {"CartExists": False})

    v1 = encode(c1)
    v2 = encode(c2)
    v3 = encode(c3)

    # Note: C1 and C2 have shared variables logically, but since they are Pre/Eff respectively, 
    # we can see how they relate. If we wanted a perfect compatibility match, we'd check if EFF of C1 matches PRE of C2.
    print(f"Vector representation generated for C1, C2, C3.")
    
    # 2. Capability composition
    print("\nExperiment 2: Capability composition")
    c12 = compose(c1, c2)
    v12 = encode(c12)
    print(f"Vector for composite (C1 -> C2) generated successfully.")
    
    # Let's compare similarities to see if composite is somewhat similar to its parts
    print(f"Similarity of C1 to composite: {similarity(v1, v12):.4f}")
    print(f"Similarity of C2 to composite: {similarity(v2, v12):.4f}")

    # 3. Alternative implementations
    print("\nExperiment 3: Alternative implementations")
    c_api = Capability("CreateOrderAPI", {}, {"OrderExists": True}, mech_type="API")
    c_db = Capability("CreateOrderDB", {}, {"OrderExists": True}, mech_type="DATABASE")

    v_api = encode(c_api)
    v_db = encode(c_db)
    print(f"Similarity between API and DB implementations (should be high): {similarity(v_api, v_db):.4f}")

    # 4. Irrelevant capabilities
    print("\nExperiment 4: Irrelevant capabilities")
    c_irr = Capability("PlayMusic", {}, {"MusicPlaying": True})
    v_irr = encode(c_irr)
    print(f"Similarity C1 and Irrelevant (should be low): {similarity(v1, v_irr):.4f}")

    # 5. Operational attributes
    print("\nExperiment 5: Operational attributes")
    print(f"Cost of C1: {c1.cost}, Reliability of C1: {c1.reliability}")
    print(f"Cost of C12 composite: {c12.cost}, Reliability of C12 composite: {c12.reliability:.4f}")
    print("Operational attributes are tracked independently from the semantic vector embedding to preserve logic.")
