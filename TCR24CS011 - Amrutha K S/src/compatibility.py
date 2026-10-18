import numpy as np

def cosine_similarity(a, b):
    d = np.linalg.norm(a) * np.linalg.norm(b)
    return 0.0 if d == 0 else float(np.dot(a, b) / d)

def _compatible_value(produced, required):
    if produced == required: return True
    if isinstance(required, str):
        try:
            if required.startswith(">"):
                return float(produced) > float(required[1:])
            if required.startswith("<"):
                return float(produced) < float(required[1:])
        except (ValueError, TypeError):
            pass
    return False

def precondition_effect_score(first, second):
    if not second.preconditions: return 1.0
    matched = 0
    for key, required in second.preconditions.items():
        if key in first.effects and _compatible_value(first.effects[key], required):
            matched += 1
    return matched / len(second.preconditions)

def input_output_score(first, second):
    required = [x for x in second.inputs if x.required]
    if not required: return 1.0
    matched = 0
    for inp in required:
        if any(out.type == inp.type and out.domain == inp.domain for out in first.outputs):
            matched += 1
    return matched / len(required)

def compatibility_score(first, second):
    return 0.7 * precondition_effect_score(first, second) + 0.3 * input_output_score(first, second)

def is_composable(first, second, threshold=0.7):
    return compatibility_score(first, second) >= threshold
