import numpy as np
from typing import Dict, Iterable, List

from .models import Capability, Goal, State


class StructuredEmbedding:
    """
    Problem-specific embedding.

    Each capability is converted into a fixed-length numerical vector containing
    separate blocks for:
      type, inputs, outputs, preconditions, effects,
      constraints, resources, and operational attributes.

    This is intentionally a structured embedding rather than a generic
    language-model embedding.
    """

    def __init__(self, capabilities: Iterable[Capability], states: Iterable[State], goals: Iterable[Goal]):
        self.capabilities = list(capabilities)
        self.states = list(states)
        self.goals = list(goals)

        self.type_vocab = sorted({c.type for c in self.capabilities})

        self.input_vocab = sorted({
            f"{x.name}:{x.type}" for c in self.capabilities for x in c.inputs
        })
        self.output_vocab = sorted({
            f"{x.name}:{x.type}" for c in self.capabilities for x in c.outputs
        })
        self.precondition_vocab = sorted({
            x.key() for c in self.capabilities for x in c.preconditions
        })
        self.effect_vocab = sorted({
            x.key() for c in self.capabilities for x in c.effects
        })
        self.constraint_vocab = sorted({
            x for c in self.capabilities for x in c.constraints
        })
        self.resource_vocab = sorted({
            x for c in self.capabilities for x in c.resources
        })

        self.state_vocab = sorted({
            f"{k}={str(v).lower()}"
            for s in self.states
            for k, v in s.values.items()
        } | {
            x.key() for g in self.goals for x in g.conditions
        })

        # Maximum observed cost is used for simple [0,1] normalization.
        max_cost = max([c.cost for c in self.capabilities] + [1.0])
        self.max_cost = max(max_cost, 1e-9)

    @staticmethod
    def _multi_hot(items: Iterable[str], vocab: List[str]) -> np.ndarray:
        item_set = set(items)
        return np.array([1.0 if token in item_set else 0.0 for token in vocab], dtype=float)

    @staticmethod
    def _condition_items(conditions) -> List[str]:
        return [c.key() for c in conditions]

    def encode_capability(self, capability: Capability) -> np.ndarray:
        type_vec = self._multi_hot([capability.type], self.type_vocab)
        input_vec = self._multi_hot(
            [f"{x.name}:{x.type}" for x in capability.inputs],
            self.input_vocab,
        )
        output_vec = self._multi_hot(
            [f"{x.name}:{x.type}" for x in capability.outputs],
            self.output_vocab,
        )
        pre_vec = self._multi_hot(
            self._condition_items(capability.preconditions),
            self.precondition_vocab,
        )
        effect_vec = self._multi_hot(
            self._condition_items(capability.effects),
            self.effect_vocab,
        )
        constraint_vec = self._multi_hot(capability.constraints, self.constraint_vocab)
        resource_vec = self._multi_hot(capability.resources, self.resource_vocab)

        # Operational block:
        # cost normalized to [0,1], reliability, availability, risk
        op_vec = np.array([
            capability.cost / self.max_cost,
            capability.reliability,
            capability.availability,
            capability.risk,
        ], dtype=float)

        return np.concatenate([
            type_vec,
            input_vec,
            output_vec,
            pre_vec,
            effect_vec,
            constraint_vec,
            resource_vec,
            op_vec,
        ])

    def encode_state(self, state: State) -> np.ndarray:
        items = [f"{k}={str(v).lower()}" for k, v in state.values.items()]
        return self._multi_hot(items, self.state_vocab)

    def encode_goal(self, goal: Goal) -> np.ndarray:
        items = [c.key() for c in goal.conditions]
        return self._multi_hot(items, self.state_vocab)

    def feature_block_sizes(self) -> Dict[str, int]:
        return {
            "type": len(self.type_vocab),
            "inputs": len(self.input_vocab),
            "outputs": len(self.output_vocab),
            "preconditions": len(self.precondition_vocab),
            "effects": len(self.effect_vocab),
            "constraints": len(self.constraint_vocab),
            "resources": len(self.resource_vocab),
            "operational": 4,
        }

    def feature_names(self) -> List[str]:
        names = []
        names += [f"type::{x}" for x in self.type_vocab]
        names += [f"input::{x}" for x in self.input_vocab]
        names += [f"output::{x}" for x in self.output_vocab]
        names += [f"precondition::{x}" for x in self.precondition_vocab]
        names += [f"effect::{x}" for x in self.effect_vocab]
        names += [f"constraint::{x}" for x in self.constraint_vocab]
        names += [f"resource::{x}" for x in self.resource_vocab]
        names += ["cost_normalized", "reliability", "availability", "risk"]
        return names
