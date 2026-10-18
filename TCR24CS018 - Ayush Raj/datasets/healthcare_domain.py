"""
Healthcare Clinical Pathway Domain Dataset.
Models patient triage, lab diagnostics, physician consultation, medication authorization,
and pharmacy dispensing.
"""

from capembed.core import (
    Capability,
    CapabilityType,
    InputSpec,
    OutputSpec,
    OperationalProfile,
    ExecutionMechanism,
    State,
    Goal,
    DomainSchema,
)


def get_healthcare_domain():
    state_variables = [
        "Patient.registered",
        "Patient.verified",
        "Vitals.triaged",
        "Lab.results_ready",
        "Diagnosis.confirmed",
        "Prescription.authorized",
        "Pharmacy.dispensed",
        "Insurance.billed",
        "HospitalFacility.cleaned",
    ]

    resources = [
        "EMRDatabase",
        "LabEquipment",
        "PhysicianStation",
        "PharmacySystem",
        "InsuranceClearinghouse",
    ]

    schema = DomainSchema(
        name="HealthcareDomain",
        state_variables=state_variables,
        data_types=["PATIENT_ID", "VITALS_DATA", "LAB_PANEL", "DIAGNOSIS_CODE", "RX_TOKEN", "CLAIM_ID"],
        data_names=[
            "patient_id", "vitals_record", "lab_report", "diagnosis_code",
            "prescription_token", "claim_id"
        ],
        resource_names=resources,
    )

    initial_state = State(variables={
        "Patient.registered": True,
        "Patient.verified": False,
        "Vitals.triaged": False,
        "Lab.results_ready": False,
        "Diagnosis.confirmed": False,
        "Prescription.authorized": False,
        "Pharmacy.dispensed": False,
        "Insurance.billed": False,
        "HospitalFacility.cleaned": True,
    })

    goal = Goal(
        name="ClinicalTreatmentGoal",
        conditions={
            "Diagnosis.confirmed": True,
            "Pharmacy.dispensed": True,
            "Insurance.billed": True,
        }
    )

    c_verify = Capability(
        name="VerifyPatientIdentity",
        cap_type=CapabilityType.SERVICE,
        inputs=[InputSpec(name="patient_id", data_type="PATIENT_ID", required=True)],
        outputs=[OutputSpec(name="patient_id", data_type="PATIENT_ID")],
        preconditions={"Patient.registered": True},
        effects={"Patient.verified": True},
        resources={"EMRDatabase"},
        operational_profile=OperationalProfile(execution_time_ms=50.0, monetary_cost=0.0, reliability=0.999),
        mechanism=ExecutionMechanism(CapabilityType.SERVICE, {"method": "auth_identity"}),
    )

    c_triage = Capability(
        name="TriageVitals",
        cap_type=CapabilityType.GUI,
        inputs=[InputSpec(name="patient_id", data_type="PATIENT_ID", required=True)],
        outputs=[OutputSpec(name="vitals_record", data_type="VITALS_DATA")],
        preconditions={"Patient.verified": True},
        effects={"Vitals.triaged": True},
        resources={"PhysicianStation"},
        operational_profile=OperationalProfile(execution_time_ms=3000.0, monetary_cost=15.0, reliability=0.98),
        mechanism=ExecutionMechanism(CapabilityType.GUI, {"component": "triage_intake"}),
    )

    c_lab = Capability(
        name="RunBloodLab",
        cap_type=CapabilityType.SERVICE,
        inputs=[InputSpec(name="patient_id", data_type="PATIENT_ID", required=True)],
        outputs=[OutputSpec(name="lab_report", data_type="LAB_PANEL")],
        preconditions={"Vitals.triaged": True},
        effects={"Lab.results_ready": True},
        resources={"LabEquipment", "EMRDatabase"},
        operational_profile=OperationalProfile(execution_time_ms=15000.0, monetary_cost=80.0, reliability=0.97),
        mechanism=ExecutionMechanism(CapabilityType.SERVICE, {"device": "spectrometer"}),
    )

    c_diagnose = Capability(
        name="DiagnoseCondition",
        cap_type=CapabilityType.FUNCTION,
        inputs=[
            InputSpec(name="vitals_record", data_type="VITALS_DATA", required=True),
            InputSpec(name="lab_report", data_type="LAB_PANEL", required=True),
        ],
        outputs=[OutputSpec(name="diagnosis_code", data_type="DIAGNOSIS_CODE")],
        preconditions={"Vitals.triaged": True, "Lab.results_ready": True},
        effects={"Diagnosis.confirmed": True},
        resources={"PhysicianStation"},
        operational_profile=OperationalProfile(execution_time_ms=6000.0, monetary_cost=100.0, reliability=0.99),
        mechanism=ExecutionMechanism(CapabilityType.FUNCTION, {"function": "physician_evaluate"}),
    )

    c_prescribe = Capability(
        name="AuthorizePrescription",
        cap_type=CapabilityType.API,
        inputs=[
            InputSpec(name="patient_id", data_type="PATIENT_ID", required=True),
            InputSpec(name="diagnosis_code", data_type="DIAGNOSIS_CODE", required=True),
        ],
        outputs=[OutputSpec(name="prescription_token", data_type="RX_TOKEN")],
        preconditions={"Diagnosis.confirmed": True},
        effects={"Prescription.authorized": True},
        resources={"EMRDatabase"},
        operational_profile=OperationalProfile(execution_time_ms=200.0, monetary_cost=5.0, reliability=0.995),
        mechanism=ExecutionMechanism(CapabilityType.API, {"endpoint": "/rx/authorize", "method": "POST"}),
    )

    c_dispense = Capability(
        name="DispenseMedication",
        cap_type=CapabilityType.SERVICE,
        inputs=[InputSpec(name="prescription_token", data_type="RX_TOKEN", required=True)],
        outputs=[],
        preconditions={"Prescription.authorized": True},
        effects={"Pharmacy.dispensed": True},
        resources={"PharmacySystem"},
        operational_profile=OperationalProfile(execution_time_ms=4000.0, monetary_cost=25.0, reliability=0.992),
        mechanism=ExecutionMechanism(CapabilityType.SERVICE, {"station": "pharmacy_dispenser"}),
    )

    c_bill = Capability(
        name="BillInsurance",
        cap_type=CapabilityType.API,
        inputs=[
            InputSpec(name="patient_id", data_type="PATIENT_ID", required=True),
            InputSpec(name="diagnosis_code", data_type="DIAGNOSIS_CODE", required=True),
        ],
        outputs=[OutputSpec(name="claim_id", data_type="CLAIM_ID")],
        preconditions={"Diagnosis.confirmed": True},
        effects={"Insurance.billed": True},
        resources={"InsuranceClearinghouse"},
        operational_profile=OperationalProfile(execution_time_ms=800.0, monetary_cost=2.0, reliability=0.985),
        mechanism=ExecutionMechanism(CapabilityType.API, {"endpoint": "/claims/submit", "method": "POST"}),
    )

    irr_clean = Capability(
        name="CleanFacility",
        cap_type=CapabilityType.FUNCTION,
        inputs=[],
        outputs=[],
        preconditions={},
        effects={"HospitalFacility.cleaned": True},
        resources=set(),
        operational_profile=OperationalProfile(execution_time_ms=10000.0, monetary_cost=30.0, reliability=0.999),
        mechanism=ExecutionMechanism(CapabilityType.FUNCTION, {"task": "janitorial"}),
    )

    all_caps = [c_verify, c_triage, c_lab, c_diagnose, c_prescribe, c_dispense, c_bill, irr_clean]

    return {
        "schema": schema,
        "initial_state": initial_state,
        "goal": goal,
        "capabilities": all_caps,
        "treatment_chain": [c_verify, c_triage, c_lab, c_diagnose, c_prescribe, c_dispense, c_bill],
        "irrelevant": [irr_clean],
    }
