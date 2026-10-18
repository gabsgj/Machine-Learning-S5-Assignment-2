"""Secondary Experimental Domain: Cloud DevOps CI/CD Deployment Pipeline.

Demonstrates problem independence and consistency of the embedding architecture.
Variables: Repo.cloned, Code.compiled, Tests.passed, Image.built, Image.scanned, Cluster.deployed, Team.notified.
"""

from __future__ import annotations
import json
from typing import Dict, Any, List

from src.models.state import State, Goal, Condition, Effect
from src.models.capability import Capability, CapabilityType, ExecutionMechanism, DataParameter
from src.models.operational import CostProfile, ResourceRequirement, Constraint
from src.embedding.schema import EmbeddingSchema


def build_cloud_pipeline_domain() -> Dict[str, Any]:
    state_variables = [
        "Repo.cloned",
        "Code.compiled",
        "Tests.passed",
        "Image.built",
        "Image.scanned",
        "Cluster.deployed",
        "Team.notified",
        "Metrics.exported",
        "Disk.cleaned"
    ]

    data_types = [
        "commit_hash",
        "binary_artifact",
        "test_report",
        "container_image_tag",
        "cve_scan_report",
        "deployment_manifest",
        "alert_message"
    ]

    resource_types = [
        "BuildRunner",
        "DockerDaemon",
        "SecurityScanner",
        "K8sCluster",
        "SlackWebhook",
        "Network"
    ]

    capability_types = [
        "API",
        "DATABASE",
        "GUI",
        "EVENT",
        "FUNCTION",
        "FILE",
        "COMPUTATION",
        "MESSAGE",
        "SERVICE"
    ]

    schema = EmbeddingSchema(
        state_variables=state_variables,
        data_types=data_types,
        resource_types=resource_types,
        capability_types=capability_types,
        latent_dim=16
    )

    initial_state = State(
        name="S_DevOps_Initial",
        variables={
            "Repo.cloned": True,
            "Code.compiled": False,
            "Tests.passed": False,
            "Image.built": False,
            "Image.scanned": False,
            "Cluster.deployed": False,
            "Team.notified": False,
            "Metrics.exported": False,
            "Disk.cleaned": False
        }
    )

    goal = Goal(
        name="DevOpsGoal",
        conditions=[
            Condition(variable="Cluster.deployed", operator="==", value=True),
            Condition(variable="Team.notified", operator="==", value=True)
        ]
    )

    # C1: CompileCode
    c1_compile = Capability(
        name="CompileCode",
        capability_type=CapabilityType.COMPUTATION,
        inputs=[DataParameter(name="commit_hash", data_type="commit_hash", domain="SHA1")],
        outputs=[DataParameter(name="binary_artifact", data_type="binary_artifact", domain="ELF")],
        preconditions=[Condition(variable="Repo.cloned", operator="==", value=True)],
        effects=[Condition(variable="Code.compiled", operator="==", value=True).to_effect() if hasattr(Condition, 'to_effect') else Effect(variable="Code.compiled", action="set", value=True)],
        resources=[ResourceRequirement(name="BuildRunner", amount=1.0)],
        cost=CostProfile(execution_time_ms=45000.0, monetary_cost=0.05, resource_units=4.0, risk=0.01, energy_joules=500.0),
        reliability=0.99,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(type=CapabilityType.COMPUTATION, details={"cmd": "go build ./..."})
    )

    # C2: BuildContainer
    c2_build_image = Capability(
        name="BuildContainer",
        capability_type=CapabilityType.SERVICE,
        inputs=[DataParameter(name="binary_artifact", data_type="binary_artifact", domain="ELF")],
        outputs=[DataParameter(name="container_image_tag", data_type="container_image_tag", domain="DockerTag")],
        preconditions=[Condition(variable="Code.compiled", operator="==", value=True)],
        effects=[Effect(variable="Image.built", action="set", value=True)],
        resources=[ResourceRequirement(name="DockerDaemon", amount=1.0)],
        cost=CostProfile(execution_time_ms=60000.0, monetary_cost=0.08, resource_units=6.0, risk=0.02, energy_joules=800.0),
        reliability=0.985,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(type=CapabilityType.SERVICE, details={"engine": "kaniko"})
    )

    # C3: DeployK8s
    c3_deploy = Capability(
        name="DeployK8s",
        capability_type=CapabilityType.API,
        inputs=[DataParameter(name="container_image_tag", data_type="container_image_tag", domain="DockerTag")],
        outputs=[DataParameter(name="deployment_manifest", data_type="deployment_manifest", domain="YAML")],
        preconditions=[Condition(variable="Image.built", operator="==", value=True)],
        effects=[Effect(variable="Cluster.deployed", action="set", value=True)],
        resources=[ResourceRequirement(name="K8sCluster", amount=1.0), ResourceRequirement(name="Network", amount=1.0)],
        cost=CostProfile(execution_time_ms=15000.0, monetary_cost=0.10, resource_units=2.0, risk=0.01, energy_joules=150.0),
        reliability=0.995,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(type=CapabilityType.API, details={"method": "PATCH", "endpoint": "/apis/apps/v1/deployments"})
    )

    # C4: NotifyTeam
    c4_notify = Capability(
        name="NotifySlack",
        capability_type=CapabilityType.MESSAGE,
        inputs=[DataParameter(name="deployment_manifest", data_type="deployment_manifest", domain="YAML")],
        outputs=[DataParameter(name="alert_message", data_type="alert_message", domain="String")],
        preconditions=[Condition(variable="Cluster.deployed", operator="==", value=True)],
        effects=[Effect(variable="Team.notified", action="set", value=True)],
        resources=[ResourceRequirement(name="SlackWebhook", amount=1.0)],
        cost=CostProfile(execution_time_ms=500.0, monetary_cost=0.001, resource_units=1.0, risk=0.005, energy_joules=5.0),
        reliability=0.999,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(type=CapabilityType.MESSAGE, details={"channel": "#deployments"})
    )

    # Irrelevant
    c_clean_disk = Capability(
        name="CleanDiskCaches",
        capability_type=CapabilityType.FILE,
        inputs=[],
        outputs=[],
        preconditions=[],
        effects=[Effect(variable="Disk.cleaned", action="set", value=True)],
        resources=[],
        cost=CostProfile(execution_time_ms=2000.0, monetary_cost=0.0, resource_units=1.0, risk=0.0, energy_joules=10.0),
        reliability=1.0,
        availability=1.0,
        execution_mechanism=ExecutionMechanism(type=CapabilityType.FILE, details={"cmd": "rm -rf /tmp/*"})
    )

    capabilities = [c1_compile, c2_build_image, c3_deploy, c4_notify, c_clean_disk]

    return {
        "domain_name": "CloudDevOpsPipeline",
        "schema": schema,
        "initial_state": initial_state,
        "goal": goal,
        "capabilities": capabilities,
        "named_capabilities": {c.name: c for c in capabilities}
    }


def save_cloud_pipeline_dataset(output_path: str = "datasets/cloud_pipeline_domain.json"):
    data = build_cloud_pipeline_domain()
    serializable = {
        "domain_name": data["domain_name"],
        "schema": {
            "state_variables": data["schema"].state_variables,
            "data_types": data["schema"].data_types,
            "resource_types": data["schema"].resource_types,
            "capability_types": data["schema"].capability_types,
            "total_dim": data["schema"].total_dim,
        },
        "initial_state": data["initial_state"].model_dump(),
        "goal": data["goal"].model_dump(),
        "capabilities": [c.model_dump() for c in data["capabilities"]]
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)
    return output_path
