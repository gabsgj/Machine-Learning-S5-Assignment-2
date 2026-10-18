"""
composition.py
==============
Formal Capability Composition Engine.
Constructs composite capabilities: C_comp = Cn o ... o C2 o C1
Aggregates functional contracts, operational metrics, and generates composite vector embeddings.
"""

from __future__ import annotations
from typing import List, Dict, Set, Optional, Tuple, Any
import numpy as np
from models import (
    Capability, CompositeCapability, CapabilityType,
    InputSpec, OutputSpec, Precondition, Effect, Resource,
    Constraint, QualityAttributes, ExecutionMechanism, State
)
from compatibility import CompatibilityEngine, CompatibilityResult
from embedding import CapabilityEmbedder, cosine_similarity


class CompositionEngine:
    """
    Constructs and evaluates composite capabilities from atomic or sub-composite sequences.
    """

    def __init__(
        self,
        embedder: Optional[CapabilityEmbedder] = None,
        compat_engine: Optional[CompatibilityEngine] = None
    ):
        self.embedder = embedder or CapabilityEmbedder()
        self.compat_engine = compat_engine or CompatibilityEngine(embedder=self.embedder)

    def validate_sequence(
        self,
        sequence: List[Capability],
        initial_state: Optional[State] = None
    ) -> Tuple[bool, List[CompatibilityResult]]:
        """
        Validates whether each consecutive pair in the sequence [C1, C2, ..., Cn] is compatible.
        """
        if len(sequence) < 2:
            return True, []

        results: List[CompatibilityResult] = []
        all_compatible = True
        curr_state = initial_state.clone() if initial_state is not None else None

        for i in range(len(sequence) - 1):
            c_curr = sequence[i]
            c_next = sequence[i + 1]

            res = self.compat_engine.evaluate(c_curr, c_next, context_state=curr_state)
            results.append(res)
            if not res.is_compatible:
                all_compatible = False

            if curr_state is not None and c_curr.can_execute_on(curr_state):
                curr_state = c_curr.execute(curr_state)

        return all_compatible, results

    def compose(
        self,
        sequence: List[Capability],
        name: Optional[str] = None,
        initial_state: Optional[State] = None,
        validate: bool = True
    ) -> CompositeCapability:
        """
        Constructs a formal CompositeCapability = Cn o ... o C2 o C1.
        """
        if not sequence:
            raise ValueError("Cannot compose an empty capability sequence.")

        if len(sequence) == 1:
            cap = sequence[0]
            return CompositeCapability(
                name=name or f"Composite_{cap.name}",
                capability_type=cap.capability_type,
                inputs=list(cap.inputs),
                outputs=list(cap.outputs),
                preconditions=list(cap.preconditions),
                effects=list(cap.effects),
                constraints=list(cap.constraints),
                resources=list(cap.resources),
                quality=cap.quality,
                reliability=cap.reliability,
                availability=cap.availability,
                mechanism=cap.mechanism,
                description=f"Composite wrapper around {cap.name}",
                sequence=[cap]
            )

        # 1. Validation
        if validate:
            is_valid, comp_results = self.validate_sequence(sequence, initial_state=initial_state)
            if not is_valid:
                failures = [f"{r.c1_name}->{r.c2_name}: {r.explanation}" for r in comp_results if not r.is_compatible]
                raise ValueError(f"Composition failed validation: {'; '.join(failures)}")

        # 2. Sequential State Simulation & Cumulative Effects
        sim_state: Dict[str, Any] = {}
        if initial_state is not None:
            sim_state = dict(initial_state.variables)

        # Track outputs produced so far
        accumulated_outputs: Dict[str, OutputSpec] = {}
        for cap in sequence:
            for out in cap.outputs:
                accumulated_outputs[out.name] = out

        # Aggregate Inputs: needed by component k not produced by components 1..(k-1)
        composite_inputs: Dict[str, InputSpec] = {}
        available_outputs: Set[str] = set()

        for cap in sequence:
            for inp in cap.inputs:
                if inp.name not in available_outputs:
                    composite_inputs[inp.name] = inp
            for out in cap.outputs:
                available_outputs.add(out.name)

        # Aggregate Preconditions: initial preconditions not established by intermediate effects
        composite_preconditions: List[Precondition] = []
        established_effects: Dict[str, Any] = {}

        for cap in sequence:
            for pre in cap.preconditions:
                # If precondition variable was already set to expected value by earlier effect, skip
                if pre.variable in established_effects:
                    eff_val = established_effects[pre.variable]
                    if pre.operator == "==" and eff_val == pre.value:
                        continue
                if pre not in composite_preconditions:
                    composite_preconditions.append(pre)
            for eff in cap.effects:
                if eff.operation == "SET":
                    established_effects[eff.variable] = eff.value

        # Aggregate Net Effects: state modifications from the sequence
        net_effects_dict: Dict[str, Effect] = {}
        for cap in sequence:
            for eff in cap.effects:
                net_effects_dict[eff.variable] = eff  # Later effect overrides earlier on same variable
        composite_effects = list(net_effects_dict.values())

        # Aggregate Resources: distinct resource union
        resource_dict: Dict[str, Resource] = {}
        for cap in sequence:
            for res in cap.resources:
                if res.name not in resource_dict:
                    resource_dict[res.name] = res
                else:
                    # Sum quantities if same resource
                    prev = resource_dict[res.name]
                    resource_dict[res.name] = Resource(
                        name=res.name,
                        resource_type=res.resource_type,
                        quantity=prev.quantity + res.quantity
                    )
        composite_resources = list(resource_dict.values())

        # Aggregate Constraints
        constraint_names: Set[str] = set()
        composite_constraints: List[Constraint] = []
        for cap in sequence:
            for c in cap.constraints:
                if c.name not in constraint_names:
                    constraint_names.add(c.name)
                    composite_constraints.append(c)

        # 3. Operational Property Aggregation
        # Monetary Cost: additive sum
        total_monetary_cost = sum(c.quality.monetary_cost for c in sequence)
        # Execution Time: additive sum (serial pipeline)
        total_execution_time = sum(c.quality.execution_time_ms for c in sequence)
        # Resource Cost: max peak or sum
        total_resource_cost = sum(c.quality.resource_cost for c in sequence)
        # Risk: union model 1 - Prod(1 - Risk_k)
        total_risk = 1.0 - float(np.prod([1.0 - c.quality.risk for c in sequence]))
        # Energy Cost: additive sum
        total_energy_cost = sum(c.quality.energy_cost for c in sequence)

        composite_quality = QualityAttributes(
            monetary_cost=round(total_monetary_cost, 4),
            execution_time_ms=round(total_execution_time, 2),
            resource_cost=round(total_resource_cost, 2),
            risk=round(total_risk, 4),
            energy_cost=round(total_energy_cost, 4)
        )

        # Reliability: independent success product model Rel_total = Prod(Rel_k)
        composite_reliability = float(np.prod([c.reliability for c in sequence]))

        # Availability: serial availability product model A_total = Prod(A_k)
        composite_availability = float(np.prod([c.availability for c in sequence]))

        # Capability Type: SERVICE or FUNCTION
        composite_type = CapabilityType.SERVICE

        composite_name = name or " o ".join(c.name for c in reversed(sequence))

        composite_mechanism = ExecutionMechanism(
            mechanism_type="COMPOSITE_PIPELINE",
            endpoint_or_target=f"pipeline:[{', '.join(c.name for c in sequence)}]",
            protocol_or_action="ORCHESTRATED_SEQUENCE",
            details={"step_count": len(sequence), "steps": [c.name for c in sequence]}
        )

        comp_cap = CompositeCapability(
            name=composite_name,
            capability_type=composite_type,
            inputs=list(composite_inputs.values()),
            outputs=list(accumulated_outputs.values()),
            preconditions=composite_preconditions,
            effects=composite_effects,
            constraints=composite_constraints,
            resources=composite_resources,
            quality=composite_quality,
            reliability=round(composite_reliability, 5),
            availability=round(composite_availability, 5),
            mechanism=composite_mechanism,
            description=f"Composite capability constructed from pipeline ({' -> '.join(c.name for c in sequence)})",
            sequence=list(sequence),
            composition_method="SEQUENTIAL"
        )

        return comp_cap

    def compare_composition_vectors(
        self,
        composite: CompositeCapability
    ) -> Dict[str, Any]:
        """
        Analyzes the vector representation of a composite capability relative to its components:
        1. Encodes composite capability phi_C(C_comp)
        2. Encodes each component phi_C(C_k)
        3. Computes component-composite cosine similarities
        4. Evaluates subspace preservation
        """
        v_comp = self.embedder.encode_capability(composite)
        comp_subspaces = self.embedder.get_subspaces(v_comp)

        component_vectors = [self.embedder.encode_capability(c) for c in composite.sequence]
        component_names = [c.name for c in composite.sequence]

        similarities = {}
        for name, vec in zip(component_names, component_vectors):
            sim = cosine_similarity(vec, v_comp)
            similarities[name] = round(sim, 4)

        # Average component vector
        v_avg = np.mean(component_vectors, axis=0)
        avg_similarity = cosine_similarity(v_avg, v_comp)

        # Vector sum normalized
        v_sum = np.sum(component_vectors, axis=0)
        sum_similarity = cosine_similarity(v_sum, v_comp)

        return {
            "composite_name": composite.name,
            "composite_vector_norm": round(float(np.linalg.norm(v_comp)), 4),
            "component_similarities": similarities,
            "average_vector_similarity": round(avg_similarity, 4),
            "sum_vector_similarity": round(sum_similarity, 4),
            "total_monetary_cost": composite.quality.monetary_cost,
            "total_reliability": composite.reliability,
            "total_availability": composite.availability,
            "input_count": len(composite.inputs),
            "output_count": len(composite.outputs),
            "effect_count": len(composite.effects)
        }
