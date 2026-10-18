"""
Smart Home IoT Domain.
Formal specification of sensory automation, security monitoring, and actuator controls.
"""

from typing import Dict
from capability_embedding.core.types import CapabilityType, ExecutionMechanism, InputSpec, OutputSpec
from capability_embedding.core.operational import OperationalQuality, ResourceRequirement
from capability_embedding.core.state import State, Goal
from capability_embedding.core.capability import Capability


def get_smarthome_initial_state() -> State:
    return State({
        "Motion.detected": True,
        "Room.illuminated": False,
        "Camera.recording": False,
        "Alarm.siren_active": False,
        "Guard.dispatched": False
    })


def get_smarthome_goal() -> Goal:
    return Goal({
        "Room.illuminated": True,
        "Camera.recording": True,
        "Alarm.siren_active": True
    })


def get_smarthome_capabilities() -> Dict[str, Capability]:
    caps = {}

    caps["TurnOnSmartBulb"] = Capability(
        name="TurnOnSmartBulb",
        capability_type=CapabilityType.SERVICE,
        preconditions={"Motion.detected": True},
        effects={"Room.illuminated": True},
        resources=[ResourceRequirement("ZigbeeGateway", "IOT_GATEWAY")],
        quality=OperationalQuality(execution_time_ms=50.0, monetary_cost=0.0001, reliability=0.999)
    )

    caps["StartCameraRecording"] = Capability(
        name="StartCameraRecording",
        capability_type=CapabilityType.SERVICE,
        preconditions={"Motion.detected": True},
        effects={"Camera.recording": True},
        resources=[ResourceRequirement("LocalNVR", "STORAGE")],
        quality=OperationalQuality(execution_time_ms=120.0, monetary_cost=0.0005, reliability=0.995)
    )

    caps["TriggerAlarmSiren"] = Capability(
        name="TriggerAlarmSiren",
        capability_type=CapabilityType.EVENT,
        preconditions={"Camera.recording": True},
        effects={"Alarm.siren_active": True},
        resources=[ResourceRequirement("SirenActuator", "HARDWARE")],
        quality=OperationalQuality(execution_time_ms=20.0, monetary_cost=0.0, reliability=0.999)
    )

    caps["DispatchSecurityGuard"] = Capability(
        name="DispatchSecurityGuard",
        capability_type=CapabilityType.MESSAGE,
        preconditions={"Alarm.siren_active": True},
        effects={"Guard.dispatched": True},
        resources=[ResourceRequirement("CellularModem", "NETWORK")],
        quality=OperationalQuality(execution_time_ms=1500.0, monetary_cost=25.0, reliability=0.99)
    )

    # Irrelevant
    caps["PlayRelaxingMusic"] = Capability(
        name="PlayRelaxingMusic",
        capability_type=CapabilityType.SERVICE,
        preconditions={},
        effects={"Music.playing": True},
        resources=[ResourceRequirement("Speaker", "AUDIO")],
        quality=OperationalQuality(execution_time_ms=200.0, monetary_cost=0.001, reliability=0.98)
    )

    return caps
