import numpy as np
from data.features import FEATURES


class Encoder:

    @staticmethod
    def encode_capability(capability):

        vector = np.zeros(len(FEATURES))

        # ----------------------------
        # Capability Type
        # ----------------------------
        if capability.capability_type in FEATURES:
            vector[FEATURES[capability.capability_type]] = 1

        # ----------------------------
        # Inputs
        # ----------------------------
        for inp in capability.inputs:
            if inp in FEATURES:
                vector[FEATURES[inp]] = 1

        # ----------------------------
        # Outputs
        # ----------------------------
        for out in capability.outputs:
            if out in FEATURES:
                vector[FEATURES[out]] = 1

        # ----------------------------
        # Preconditions
        # ----------------------------
        for key in capability.preconditions:
            if key in FEATURES:
                vector[FEATURES[key]] = 1

        # ----------------------------
        # Effects
        # ----------------------------
        for key in capability.effects:
            if key in FEATURES:
                vector[FEATURES[key]] = 1

        # ----------------------------
        # Resources
        # ----------------------------
        for resource in capability.resources:
            if resource in FEATURES:
                vector[FEATURES[resource]] = 1

        # ----------------------------
        # Quality Features
        # ----------------------------
        vector[FEATURES["Execution Time"]] = capability.cost.get("time", 0) / 1000

        vector[FEATURES["Money Cost"]] = capability.cost.get("money", 0) / 10

        vector[FEATURES["Reliability"]] = capability.reliability

        vector[FEATURES["Availability"]] = capability.availability

        return vector