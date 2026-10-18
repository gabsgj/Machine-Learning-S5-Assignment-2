"""
Clinical Patient Healthcare Workflow Domain.
Formal specification of diagnostic pipelines, clinical lab requests,
prescription issuance, and medication dispensing.
"""

from typing import Dict
from capability_embedding.core.types import CapabilityType, ExecutionMechanism, InputSpec, OutputSpec
from capability_embedding.core.operational import OperationalQuality, ResourceRequirement, CapabilityConstraint
from capability_embedding.core.state import State, Goal
from capability_embedding.core.capability import Capability


def get_healthcare_initial_state() -> State:
    return State({
        "Patient.triaged": True,
        "Lab.ordered": False,
        "Lab.completed": False,
        "Diagnosis.ready": False,
        "Prescription.issued": False,
        "Pharmacy.dispensed": False
    })


def get_healthcare_goal() -> Goal:
    return Goal({
        "Diagnosis.ready": True,
        "Prescription.issued": True,
        "Pharmacy.dispensed": True
    })


def get_healthcare_capabilities() -> Dict[str, Capability]:
    caps = {}

    caps["OrderLabTests"] = Capability(
        name="OrderLabTests",
        capability_type=CapabilityType.SERVICE,
        preconditions={"Patient.triaged": True},
        effects={"Lab.ordered": True},
        resources=[ResourceRequirement("EHR_System", "DATABASE")],
        quality=OperationalQuality(execution_time_ms=200.0, monetary_cost=5.0, reliability=0.999)
    )

    caps["AnalyzeBiomarkers"] = Capability(
        name="AnalyzeBiomarkers",
        capability_type=CapabilityType.COMPUTATION,
        preconditions={"Lab.ordered": True},
        effects={"Lab.completed": True},
        resources=[ResourceRequirement("LabAnalyzer", "HARDWARE")],
        quality=OperationalQuality(execution_time_ms=1800000.0, monetary_cost=45.0, reliability=0.992)
    )

    caps["GenerateDiagnosis"] = Capability(
        name="GenerateDiagnosis",
        capability_type=CapabilityType.FUNCTION,
        preconditions={"Lab.completed": True},
        effects={"Diagnosis.ready": True},
        resources=[ResourceRequirement("ClinicalRulesEngine", "SERVICE")],
        quality=OperationalQuality(execution_time_ms=150.0, monetary_cost=2.0, reliability=0.985)
    )

    caps["IssuePrescription"] = Capability(
        name="IssuePrescription",
        capability_type=CapabilityType.API,
        preconditions={"Diagnosis.ready": True},
        effects={"Prescription.issued": True},
        resources=[ResourceRequirement("PrescriptionDB", "STORAGE")],
        quality=OperationalQuality(execution_time_ms=300.0, monetary_cost=1.5, reliability=0.998)
    )

    caps["DispenseMedication"] = Capability(
        name="DispenseMedication",
        capability_type=CapabilityType.SERVICE,
        preconditions={"Prescription.issued": True},
        effects={"Pharmacy.dispensed": True},
        resources=[ResourceRequirement("RoboticDispenser", "HARDWARE")],
        quality=OperationalQuality(execution_time_ms=45000.0, monetary_cost=12.0, reliability=0.99)
    )

    caps["ArchivePatientHistory"] = Capability(
        name="ArchivePatientHistory",
        capability_type=CapabilityType.FILE,
        preconditions={},
        effects={"Archive.saved": True},
        resources=[ResourceRequirement("ColdStorage", "STORAGE")],
        quality=OperationalQuality(execution_time_ms=5000.0, monetary_cost=0.5, reliability=0.999)
    )

    return caps
