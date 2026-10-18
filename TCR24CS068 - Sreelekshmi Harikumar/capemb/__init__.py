"""capemb -- a problem-specific vector embedding for capability composition.

    E = CapabilityEmbedder(problem)
    E.encode(state | goal | capability)   E.compose([C1, C2, ...])
    E.similarity(x, y)                    E.compat(a, b, ctx)
"""
from .spec import Problem, Capability, Lit, Port, Var, load_problem
from .atoms import AtomUniverse
from .embedding import (CapabilityEmbedder, CapEmb, StateEmb, GoalEmb, Context,
                        CONFLICT, INDEPENDENT, PARTIAL, STRICT, LABELS)
