"""
DevOps CI/CD Application Domain.
Formally specifies code integration, containerization, automated testing,
and cloud orchestration capabilities.
"""

from typing import Dict
from capability_embedding.core.types import CapabilityType, ExecutionMechanism, InputSpec, OutputSpec
from capability_embedding.core.operational import OperationalQuality, ResourceRequirement, CapabilityConstraint
from capability_embedding.core.state import State, Goal
from capability_embedding.core.capability import Capability


def get_devops_initial_state() -> State:
    return State({
        "Code.committed": True,
        "Lint.passed": False,
        "Tests.passed": False,
        "Docker.built": False,
        "K8s.deployed": False,
        "Alert.sent": False,
        "Deployment.version": "1.0.0"
    })


def get_devops_goal() -> Goal:
    return Goal({
        "Tests.passed": True,
        "Docker.built": True,
        "K8s.deployed": True
    })


def get_devops_capabilities() -> Dict[str, Capability]:
    caps = {}

    caps["RunLinter"] = Capability(
        name="RunLinter",
        capability_type=CapabilityType.FUNCTION,
        preconditions={"Code.committed": True},
        effects={"Lint.passed": True},
        resources=[ResourceRequirement("CI_Runner", "COMPUTE")],
        quality=OperationalQuality(execution_time_ms=15000.0, monetary_cost=0.005, reliability=0.99)
    )

    caps["RunUnitTests"] = Capability(
        name="RunUnitTests",
        capability_type=CapabilityType.COMPUTATION,
        preconditions={"Lint.passed": True},
        effects={"Tests.passed": True},
        resources=[ResourceRequirement("CI_Runner", "COMPUTE")],
        quality=OperationalQuality(execution_time_ms=45000.0, monetary_cost=0.02, reliability=0.97)
    )

    caps["BuildDockerImage"] = Capability(
        name="BuildDockerImage",
        capability_type=CapabilityType.SERVICE,
        preconditions={"Tests.passed": True},
        effects={"Docker.built": True},
        resources=[ResourceRequirement("DockerDaemon", "SYSTEM")],
        quality=OperationalQuality(execution_time_ms=60000.0, monetary_cost=0.04, reliability=0.98)
    )

    caps["DeployKubernetes"] = Capability(
        name="DeployKubernetes",
        capability_type=CapabilityType.API,
        preconditions={"Docker.built": True},
        effects={"K8s.deployed": True},
        resources=[ResourceRequirement("K8sCluster", "CLUSTER")],
        quality=OperationalQuality(execution_time_ms=30000.0, monetary_cost=0.03, reliability=0.995)
    )

    caps["SendSlackAlert"] = Capability(
        name="SendSlackAlert",
        capability_type=CapabilityType.MESSAGE,
        preconditions={"K8s.deployed": True},
        effects={"Alert.sent": True},
        resources=[ResourceRequirement("SlackWebhook", "EXTERNAL")],
        quality=OperationalQuality(execution_time_ms=500.0, monetary_cost=0.001, reliability=0.999)
    )

    # Irrelevant
    caps["BackupPostgresDatabase"] = Capability(
        name="BackupPostgresDatabase",
        capability_type=CapabilityType.DATABASE,
        preconditions={},
        effects={"DB.backup_saved": True},
        resources=[ResourceRequirement("S3Storage", "STORAGE")],
        quality=OperationalQuality(execution_time_ms=90000.0, monetary_cost=0.10, reliability=0.99)
    )

    return caps
