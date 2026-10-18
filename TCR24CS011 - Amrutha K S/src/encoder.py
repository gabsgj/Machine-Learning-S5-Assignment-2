import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import MinMaxScaler
from .models import Capability, State, Goal

class CapabilityEncoder:
    """Problem-specific structured feature embedding."""
    def __init__(self):
        self.vectorizer = DictVectorizer(sparse=False)
        self.scaler = MinMaxScaler()
        self.fitted = False

    def _features(self, c: Capability):
        f = {}
        def cat(group, value):
            f[f"{group}={value}"] = 1.0
        cat("capability_type", c.type)
        for x in c.inputs:
            cat("input_name", x.name); cat("input_type", x.type); cat("input_domain", x.domain)
        for x in c.outputs:
            cat("output_name", x.name); cat("output_type", x.type); cat("output_domain", x.domain)
        for k, v in c.preconditions.items():
            cat("precondition_key", k); cat("precondition_value", v)
        for k, v in c.effects.items():
            cat("effect_key", k); cat("effect_value", v)
        for x in c.constraints: cat("constraint", x)
        for x in c.resources: cat("resource", x)
        for k, v in c.mechanism.items():
            cat("mechanism", f"{k}:{v}")
        f["cost_time"] = c.cost.time
        f["cost_resource"] = c.cost.resource
        f["cost_money"] = c.cost.money
        f["cost_risk"] = c.cost.risk
        f["cost_energy"] = c.cost.energy
        f["reliability"] = c.reliability
        f["availability"] = c.availability
        return f

    def fit(self, capabilities):
        matrix = self.vectorizer.fit_transform([self._features(c) for c in capabilities])
        self.scaler.fit(matrix)
        self.fitted = True
        return self.scaler.transform(matrix)

    def encode_capability(self, capability):
        if not self.fitted: raise RuntimeError("Call fit() before encoding.")
        x = self.vectorizer.transform([self._features(capability)])
        return self.scaler.transform(x)[0]

    def encode_state(self, state: State):
        return self._sparse_named_vector({f"state={k}:{v}": 1.0 for k,v in state.values.items()})

    def encode_goal(self, goal: Goal):
        return self._sparse_named_vector({f"goal={k}:{v}": 1.0 for k,v in goal.conditions.items()})

    def _sparse_named_vector(self, features):
        if not self.fitted: raise RuntimeError("Fit the encoder first.")
        names = self.vectorizer.get_feature_names_out()
        out = np.zeros(len(names), dtype=float)
        for i, name in enumerate(names):
            for key, value in features.items():
                if key in name:
                    out[i] = value
        return out
