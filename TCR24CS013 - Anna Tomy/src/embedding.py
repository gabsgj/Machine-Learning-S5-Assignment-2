import math
from typing import Any, Dict, List, Iterable

from models import State, Goal, Capability


class EmbeddingModel:
    """
    Structured vector representation for states, goals and capabilities.

    Capability vector layout:
        [preconditions]
        [effects]
        [inputs]
        [outputs]
        [capability type]
        [time cost]
        [money cost]
        [resource cost]
        [risk]
        [reliability]

    The representation deliberately separates:
        1. vector similarity
        2. functional compatibility

    Similarity tells us whether two capabilities have similar
    representations. Compatibility checks whether one capability
    can functionally follow another.
    """

    def __init__(
        self,
        states: List[State],
        goals: List[Goal],
        capabilities: List[Capability]
    ):
        self.states = states
        self.goals = goals
        self.capabilities = capabilities

        self.variable_values = self._collect_variable_values()
        self.input_features = self._collect_port_features("inputs")
        self.output_features = self._collect_port_features("outputs")

        self.types = sorted(
            set(cap.type for cap in capabilities)
        )

        self.variables = sorted(self.variable_values.keys())

    # ---------------------------------------------------------
    # Vocabulary construction
    # ---------------------------------------------------------

    def _collect_variable_values(self) -> Dict[str, set]:
        result: Dict[str, set] = {}

        def add_pair(variable: str, value: Any):
            result.setdefault(variable, set()).add(str(value))

        for state in self.states:
            for variable, value in state.values.items():
                add_pair(variable, value)

        for goal in self.goals:
            for variable, value in goal.conditions.items():
                add_pair(variable, value)

        for capability in self.capabilities:
            for variable, value in capability.preconditions.items():
                add_pair(variable, value)

            for variable, value in capability.effects.items():
                add_pair(variable, value)

        return result

    def _collect_port_features(self, attribute: str) -> List[str]:
        features = set()

        for capability in self.capabilities:
            ports = getattr(capability, attribute)

            for port in ports:
                name = port.get("name", "")
                port_type = port.get("type", "")

                if name:
                    features.add(f"name:{name}")

                if port_type:
                    features.add(f"type:{port_type}")

        return sorted(features)

    # ---------------------------------------------------------
    # Encoding helpers
    # ---------------------------------------------------------

    def _encode_conditions(
        self,
        conditions: Dict[str, Any]
    ) -> List[float]:

        vector = []

        for variable in self.variables:
            values = sorted(self.variable_values[variable])

            for value in values:
                if variable not in conditions:
                    vector.append(0.0)

                elif str(conditions[variable]) == value:
                    vector.append(1.0)

                else:
                    vector.append(-1.0)

        return vector

    def _port_set(
        self,
        ports: List[Dict[str, Any]]
    ) -> set:

        result = set()

        for port in ports:
            if port.get("name"):
                result.add(f"name:{port['name']}")

            if port.get("type"):
                result.add(f"type:{port['type']}")

        return result

    # ---------------------------------------------------------
    # State embedding
    # ---------------------------------------------------------

    def encode_state(self, state: State) -> List[float]:
        return self._encode_conditions(state.values)

    # ---------------------------------------------------------
    # Goal embedding
    # ---------------------------------------------------------

    def encode_goal(self, goal: Goal) -> List[float]:
        return self._encode_conditions(goal.conditions)

    # ---------------------------------------------------------
    # Capability embedding
    # ---------------------------------------------------------

    def encode_capability(
        self,
        capability: Capability
    ) -> List[float]:

        precondition_vector = self._encode_conditions(
            capability.preconditions
        )

        effect_vector = self._encode_conditions(
            capability.effects
        )

        input_features_present = self._port_set(
            capability.inputs
        )

        output_features_present = self._port_set(
            capability.outputs
        )

        input_vector = [
            1.0 if feature in input_features_present else 0.0
            for feature in self.input_features
        ]

        output_vector = [
            1.0 if feature in output_features_present else 0.0
            for feature in self.output_features
        ]

        type_vector = [
            1.0 if capability.type == capability_type else 0.0
            for capability_type in self.types
        ]

        # Operational attributes.
        #
        # Scaling keeps operational information visible in the
        # overall capability representation while preventing large
        # raw values from dominating the structural representation.

        normalized_time = math.log1p(
            capability.time_cost
        ) / 10.0

        normalized_money = capability.money_cost

        normalized_resource = (
            capability.resource_cost / 10.0
        )

        normalized_risk = capability.risk

        reliability = capability.reliability

        operational_vector = [
            normalized_time,
            normalized_money,
            normalized_resource,
            normalized_risk,
            reliability,
        ]

        return (
            precondition_vector
            + effect_vector
            + input_vector
            + output_vector
            + type_vector
            + operational_vector
        )

    # ---------------------------------------------------------
    # Similarity
    # ---------------------------------------------------------

    @staticmethod
    def cosine_similarity(
        vector_a: Iterable[float],
        vector_b: Iterable[float]
    ) -> float:

        a = list(vector_a)
        b = list(vector_b)

        if len(a) != len(b):
            raise ValueError(
                "Vectors must have equal dimensions."
            )

        dot = sum(
            x * y
            for x, y in zip(a, b)
        )

        norm_a = math.sqrt(
            sum(x * x for x in a)
        )

        norm_b = math.sqrt(
            sum(y * y for y in b)
        )

        denominator = norm_a * norm_b

        if denominator == 0:
            return 0.0

        return dot / denominator

    def similarity(
        self,
        capability_a: Capability,
        capability_b: Capability
    ) -> float:

        vector_a = self.encode_capability(
            capability_a
        )

        vector_b = self.encode_capability(
            capability_b
        )

        return self.cosine_similarity(
            vector_a,
            vector_b
        )

    # ---------------------------------------------------------
    # Functional compatibility
    # ---------------------------------------------------------

    @staticmethod
    def precondition_effect_compatibility(
        first: Capability,
        second: Capability
    ) -> float:
        """
        Measures how many of second's preconditions are satisfied
        by effects produced by first.

        If second has no preconditions, it does not require any
        state condition from the first capability.
        """

        if not second.preconditions:
            return 1.0

        satisfied = 0

        for variable, required_value in (
            second.preconditions.items()
        ):
            if (
                variable in first.effects
                and first.effects[variable] == required_value
            ):
                satisfied += 1

        return satisfied / len(second.preconditions)

    @staticmethod
    def input_output_compatibility(
        first: Capability,
        second: Capability
    ) -> float:
        """
        Measures whether outputs of the first capability can
        satisfy inputs of the second capability.
        """

        if not second.inputs:
            return 1.0

        matches = 0

        for required_input in second.inputs:

            required_type = required_input.get("type")
            required_name = required_input.get("name")

            for output in first.outputs:

                output_type = output.get("type")
                output_name = output.get("name")

                type_match = (
                    required_type is not None
                    and output_type == required_type
                )

                name_match = (
                    required_name is not None
                    and output_name == required_name
                )

                if type_match or name_match:
                    matches += 1
                    break

        return matches / len(second.inputs)

    @staticmethod
    def dependency_score(
        first: Capability,
        second: Capability
    ) -> float:
        """
        Measures how strongly the second capability depends on
        outputs/effects of the first capability.

        This is different from composition validity.

        A capability with no requirements can execute independently,
        so its dependency score is 0 rather than incorrectly
        suggesting that the first capability enabled it.
        """

        precondition_count = len(second.preconditions)
        input_count = len(second.inputs)

        if precondition_count == 0 and input_count == 0:
            return 0.0

        precondition_score = (
            EmbeddingModel.precondition_effect_compatibility(
                first,
                second
            )
            if precondition_count > 0
            else 1.0
        )

        io_score = (
            EmbeddingModel.input_output_compatibility(
                first,
                second
            )
            if input_count > 0
            else 1.0
        )

        total_requirements = (
            precondition_count + input_count
        )

        satisfied_requirements = 0.0

        if precondition_count > 0:
            satisfied_requirements += (
                precondition_score * precondition_count
            )

        if input_count > 0:
            satisfied_requirements += (
                io_score * input_count
            )

        return (
            satisfied_requirements
            / total_requirements
        )

    def compatibility(
        self,
        first: Capability,
        second: Capability
    ) -> float:
        """
        Functional composition compatibility.

        A capability can follow another when its requirements are
        either satisfied by the first capability or absent.

        Therefore, capabilities with no requirements can still
        legally execute after another capability.
        """

        precondition_score = (
            self.precondition_effect_compatibility(
                first,
                second
            )
        )

        io_score = (
            self.input_output_compatibility(
                first,
                second
            )
        )

        return (
            0.7 * precondition_score
            + 0.3 * io_score
        )