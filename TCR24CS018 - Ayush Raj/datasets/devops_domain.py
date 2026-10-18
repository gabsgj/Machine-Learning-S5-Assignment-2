"""
Cloud DevOps CI/CD Pipeline Dataset.
Models source checkout, linting, testing, Docker image building, registry push,
and Kubernetes cluster deployment.
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


def get_devops_domain():
    state_variables = [
        "Code.checked_out",
        "Code.lint_passed",
        "Tests.unit_passed",
        "Artifact.docker_built",
        "Artifact.pushed_to_registry",
        "Cluster.deployed",
        "HealthCheck.passed",
        "Slack.notified",
        "Docs.generated",
        "OldLogs.archived",
    ]

    resources = [
        "GitServer",
        "BuildServer",
        "DockerDaemon",
        "ContainerRegistry",
        "KubernetesCluster",
        "SlackWebhook",
    ]

    schema = DomainSchema(
        name="DevopsDomain",
        state_variables=state_variables,
        data_types=["STRING", "SHA256", "IMAGE_TAG", "BOOLEAN", "URL"],
        data_names=[
            "commit_hash", "lint_report", "test_report", "image_tag",
            "registry_digest", "deploy_id", "slack_msg"
        ],
        resource_names=resources,
    )

    initial_state = State(variables={
        "Code.checked_out": False,
        "Code.lint_passed": False,
        "Tests.unit_passed": False,
        "Artifact.docker_built": False,
        "Artifact.pushed_to_registry": False,
        "Cluster.deployed": False,
        "HealthCheck.passed": False,
        "Slack.notified": False,
        "Docs.generated": False,
        "OldLogs.archived": False,
    })

    goal = Goal(
        name="ProductionDeployGoal",
        conditions={
            "Artifact.pushed_to_registry": True,
            "Cluster.deployed": True,
            "HealthCheck.passed": True,
        }
    )

    # 1. Checkout
    c_checkout = Capability(
        name="GitCheckout",
        cap_type=CapabilityType.FUNCTION,
        inputs=[InputSpec(name="commit_hash", data_type="SHA256", required=True)],
        outputs=[OutputSpec(name="commit_hash", data_type="SHA256")],
        preconditions={},
        effects={"Code.checked_out": True},
        resources={"GitServer"},
        operational_profile=OperationalProfile(execution_time_ms=500.0, monetary_cost=0.001, reliability=0.999),
        mechanism=ExecutionMechanism(CapabilityType.FUNCTION, {"tool": "git", "command": "checkout"}),
    )

    # 2. Lint
    c_lint = Capability(
        name="LintCode",
        cap_type=CapabilityType.FUNCTION,
        inputs=[InputSpec(name="commit_hash", data_type="SHA256", required=True)],
        outputs=[OutputSpec(name="lint_report", data_type="STRING")],
        preconditions={"Code.checked_out": True},
        effects={"Code.lint_passed": True},
        resources={"BuildServer"},
        operational_profile=OperationalProfile(execution_time_ms=1200.0, monetary_cost=0.002, reliability=0.99),
        mechanism=ExecutionMechanism(CapabilityType.FUNCTION, {"linter": "flake8"}),
    )

    # 3. Unit Tests
    c_test = Capability(
        name="RunUnitTests",
        cap_type=CapabilityType.COMPUTATION,
        inputs=[InputSpec(name="commit_hash", data_type="SHA256", required=True)],
        outputs=[OutputSpec(name="test_report", data_type="STRING")],
        preconditions={"Code.lint_passed": True},
        effects={"Tests.unit_passed": True},
        resources={"BuildServer"},
        operational_profile=OperationalProfile(execution_time_ms=4500.0, monetary_cost=0.01, reliability=0.98),
        mechanism=ExecutionMechanism(CapabilityType.COMPUTATION, {"runner": "pytest"}),
    )

    # 4. Docker Build
    c_build = Capability(
        name="BuildDockerImage",
        cap_type=CapabilityType.SERVICE,
        inputs=[InputSpec(name="commit_hash", data_type="SHA256", required=True)],
        outputs=[OutputSpec(name="image_tag", data_type="IMAGE_TAG")],
        preconditions={"Tests.unit_passed": True},
        effects={"Artifact.docker_built": True},
        resources={"DockerDaemon", "BuildServer"},
        operational_profile=OperationalProfile(execution_time_ms=8000.0, monetary_cost=0.02, reliability=0.99),
        mechanism=ExecutionMechanism(CapabilityType.SERVICE, {"engine": "docker", "file": "Dockerfile"}),
    )

    # 5. Push to Registry
    c_push = Capability(
        name="PushToRegistry",
        cap_type=CapabilityType.API,
        inputs=[InputSpec(name="image_tag", data_type="IMAGE_TAG", required=True)],
        outputs=[OutputSpec(name="registry_digest", data_type="SHA256")],
        preconditions={"Artifact.docker_built": True},
        effects={"Artifact.pushed_to_registry": True},
        resources={"ContainerRegistry"},
        operational_profile=OperationalProfile(execution_time_ms=3000.0, monetary_cost=0.015, reliability=0.995),
        mechanism=ExecutionMechanism(CapabilityType.API, {"endpoint": "/v2/images/push", "method": "POST"}),
    )

    # 6. Deploy to K8s
    c_deploy = Capability(
        name="DeployKubernetes",
        cap_type=CapabilityType.API,
        inputs=[InputSpec(name="registry_digest", data_type="SHA256", required=True)],
        outputs=[OutputSpec(name="deploy_id", data_type="STRING")],
        preconditions={"Artifact.pushed_to_registry": True},
        effects={"Cluster.deployed": True},
        resources={"KubernetesCluster"},
        operational_profile=OperationalProfile(execution_time_ms=5000.0, monetary_cost=0.05, reliability=0.97),
        mechanism=ExecutionMechanism(CapabilityType.API, {"endpoint": "/apis/apps/v1/namespaces/prod/deployments", "method": "PATCH"}),
    )

    # 7. Smoke Test
    c_smoke = Capability(
        name="RunHealthCheck",
        cap_type=CapabilityType.API,
        inputs=[InputSpec(name="deploy_id", data_type="STRING", required=True)],
        outputs=[],
        preconditions={"Cluster.deployed": True},
        effects={"HealthCheck.passed": True},
        resources={"KubernetesCluster"},
        operational_profile=OperationalProfile(execution_time_ms=1000.0, monetary_cost=0.001, reliability=0.99),
        mechanism=ExecutionMechanism(CapabilityType.API, {"endpoint": "/healthz", "method": "GET"}),
    )

    # Irrelevant
    irr_docs = Capability(
        name="GenerateDocumentation",
        cap_type=CapabilityType.FUNCTION,
        inputs=[],
        outputs=[],
        preconditions={"Code.checked_out": True},
        effects={"Docs.generated": True},
        resources={"BuildServer"},
        operational_profile=OperationalProfile(execution_time_ms=2000.0, monetary_cost=0.001, reliability=0.999),
        mechanism=ExecutionMechanism(CapabilityType.FUNCTION, {"tool": "sphinx"}),
    )

    irr_archive = Capability(
        name="ArchiveOldLogs",
        cap_type=CapabilityType.FILE,
        inputs=[],
        outputs=[],
        preconditions={},
        effects={"OldLogs.archived": True},
        resources={"BuildServer"},
        operational_profile=OperationalProfile(execution_time_ms=800.0, monetary_cost=0.0005, reliability=0.999),
        mechanism=ExecutionMechanism(CapabilityType.FILE, {"tool": "tar"}),
    )

    all_caps = [c_checkout, c_lint, c_test, c_build, c_push, c_deploy, c_smoke, irr_docs, irr_archive]

    return {
        "schema": schema,
        "initial_state": initial_state,
        "goal": goal,
        "capabilities": all_caps,
        "pipeline_chain": [c_checkout, c_lint, c_test, c_build, c_push, c_deploy, c_smoke],
        "irrelevant": [irr_docs, irr_archive],
    }
