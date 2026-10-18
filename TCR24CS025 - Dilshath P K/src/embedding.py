import numpy as np
import hashlib
from sklearn.metrics.pairwise import cosine_similarity


class CapabilityEmbedding:

    def __init__(self, dimensions=128):
        self.dimensions = dimensions

    def _add_feature(self, vector, feature, weight=1.0):
        digest = hashlib.sha256(
            str(feature).encode("utf-8")
        ).hexdigest()

        index = int(digest[:8], 16) % (self.dimensions - 3)
        vector[index] += weight

    def encode_capability(self, capability):
        vector = np.zeros(self.dimensions)

        self._add_feature(
            vector, "name:" + capability.get("name", "")
        )
        self._add_feature(
            vector, "type:" + capability.get("type", "")
        )

        for item in capability.get("inputs", []):
            self._add_feature(vector, "input:" + str(item))

        for item in capability.get("outputs", []):
            self._add_feature(vector, "output:" + str(item))

        for key, value in capability.get("preconditions", {}).items():
            self._add_feature(
                vector, f"precondition:{key}={value}"
            )

        for key, value in capability.get("effects", {}).items():
            self._add_feature(
                vector, f"effect:{key}={value}"
            )

        for resource in capability.get("resources", []):
            self._add_feature(vector, "resource:" + str(resource))

        vector[-3] = capability.get("cost", 0)
        vector[-2] = capability.get("reliability", 0)
        vector[-1] = capability.get("availability", 0)

        return vector

    def encode_state(self, state):
        vector = np.zeros(self.dimensions)

        for key, value in state.items():
            self._add_feature(
                vector, f"state:{key}={value}"
            )

        return vector

    def encode_goal(self, goal):
        vector = np.zeros(self.dimensions)

        for key, value in goal.items():
            self._add_feature(
                vector, f"goal:{key}={value}"
            )

        return vector

    def similarity(self, vector1, vector2):
        vector1 = np.array(vector1).reshape(1, -1)
        vector2 = np.array(vector2).reshape(1, -1)

        return float(
            cosine_similarity(vector1, vector2)[0][0]
        )
