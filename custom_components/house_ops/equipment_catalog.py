"""Equipment catalog for HouseOps."""
from __future__ import annotations

from dataclasses import dataclass

from .const import (
    BATTERY_SERVICE_REPLACEABLE,
    BATTERY_SERVICE_SEALED_LIFE,
    DEFAULT_FIRE_ALARM_BATTERY_INTERVAL_DAYS,
    DEFAULT_FIRE_ALARM_REPLACEMENT_INTERVAL_DAYS,
    DEFAULT_WATER_HEATER_ANODE_INTERVAL_DAYS,
    EQUIPMENT_TYPE_FIRE_ALARMS,
    EQUIPMENT_TYPE_FURNACE,
    EQUIPMENT_TYPE_WATER_HEATER,
    POWER_TYPE_BATTERY,
    POWER_TYPE_WIRED,
    POWER_TYPE_WIRED_WITH_BATTERY_BACKUP,
    SENSOR_ROLE_BATTERY,
    SENSOR_ROLE_RUNTIME,
    SENSOR_ROLE_USAGE,
    TASK_ANODE,
    TASK_BATTERY,
    TASK_FILTER,
    TASK_FLUSH,
    TASK_INSPECTION,
    TASK_REPLACEMENT,
    TASK_TEST,
)


@dataclass(frozen=True, slots=True)
class TaskDefinition:
    key: str
    title: str
    default_interval_days: int
    sensor_roles: tuple[str, ...] = ()
    allowed_power_types: tuple[str, ...] | None = None
    optional: bool = False


@dataclass(frozen=True, slots=True)
class EquipmentDefinition:
    key: str
    label: str
    description: str
    primary_task_key: str
    supported_power_types: tuple[str, ...]
    default_power_type: str
    tasks: tuple[TaskDefinition, ...]
    ui_enabled: bool = True


SUPPORTED_EQUIPMENT: tuple[EquipmentDefinition, ...] = (
    EquipmentDefinition(
        key=EQUIPMENT_TYPE_FURNACE,
        label="Furnace / HVAC",
        description="Track filter changes, annual inspections, and optional runtime-based acceleration.",
        primary_task_key=TASK_FILTER,
        supported_power_types=(POWER_TYPE_WIRED,),
        default_power_type=POWER_TYPE_WIRED,
        tasks=(
            TaskDefinition(
                key=TASK_FILTER,
                title="Filter replacement",
                default_interval_days=90,
                sensor_roles=(SENSOR_ROLE_RUNTIME, SENSOR_ROLE_USAGE),
            ),
            TaskDefinition(
                key=TASK_INSPECTION,
                title="Annual inspection",
                default_interval_days=365,
            ),
        ),
    ),
    EquipmentDefinition(
        key=EQUIPMENT_TYPE_WATER_HEATER,
        label="Water heater",
        description="Track annual flushes, optional anode rod inspections, and usage-based acceleration.",
        primary_task_key=TASK_FLUSH,
        supported_power_types=(POWER_TYPE_WIRED,),
        default_power_type=POWER_TYPE_WIRED,
        tasks=(
            TaskDefinition(
                key=TASK_FLUSH,
                title="Annual flush",
                default_interval_days=365,
                sensor_roles=(SENSOR_ROLE_USAGE,),
            ),
            TaskDefinition(
                key=TASK_ANODE,
                title="Anode rod inspection",
                default_interval_days=DEFAULT_WATER_HEATER_ANODE_INTERVAL_DAYS,
                optional=True,
            ),
        ),
    ),
    EquipmentDefinition(
        key=EQUIPMENT_TYPE_FIRE_ALARMS,
        label="Fire alarms / smoke detectors",
        description="Track alarm tests, battery service when batteries exist, and long-term replacement advisory.",
        primary_task_key=TASK_TEST,
        supported_power_types=(
            POWER_TYPE_BATTERY,
            POWER_TYPE_WIRED,
            POWER_TYPE_WIRED_WITH_BATTERY_BACKUP,
        ),
        default_power_type=POWER_TYPE_WIRED_WITH_BATTERY_BACKUP,
        tasks=(
            TaskDefinition(
                key=TASK_TEST,
                title="Monthly alarm test",
                default_interval_days=30,
            ),
            TaskDefinition(
                key=TASK_BATTERY,
                title="Battery replacement",
                default_interval_days=DEFAULT_FIRE_ALARM_BATTERY_INTERVAL_DAYS,
                sensor_roles=(SENSOR_ROLE_BATTERY,),
                allowed_power_types=(POWER_TYPE_BATTERY, POWER_TYPE_WIRED_WITH_BATTERY_BACKUP),
            ),
            TaskDefinition(
                key=TASK_REPLACEMENT,
                title="Detector replacement advisory",
                default_interval_days=DEFAULT_FIRE_ALARM_REPLACEMENT_INTERVAL_DAYS,
            ),
        ),
    ),
)

FUTURE_EQUIPMENT_TYPES: tuple[str, ...] = (
    "dishwasher",
    "refrigerator",
    "washer",
    "dryer",
    "sump_pump",
    "air_purifier",
    "water_softener",
    "septic_system",
    "roof_gutters",
    "garage_door_opener",
    "range_hood",
    "plumbing_fixtures",
    "hvac_accessories",
    "dehumidifier",
    "humidifier",
    "well_system",
    "sprinkler_system",
    "pool_hot_tub_equipment",
)

_CATALOG = {definition.key: definition for definition in SUPPORTED_EQUIPMENT}

POWER_TYPE_LABELS = {
    POWER_TYPE_BATTERY: "Battery-powered",
    POWER_TYPE_WIRED: "Wired",
    POWER_TYPE_WIRED_WITH_BATTERY_BACKUP: "Wired with battery backup",
}

BATTERY_SERVICE_MODE_LABELS = {
    BATTERY_SERVICE_REPLACEABLE: "Replaceable battery",
    BATTERY_SERVICE_SEALED_LIFE: "Sealed 10-year battery",
}


def get_equipment_definition(key: str) -> EquipmentDefinition:
    return _CATALOG[key]


def get_supported_definitions() -> tuple[EquipmentDefinition, ...]:
    return SUPPORTED_EQUIPMENT


def supports_battery(definition: EquipmentDefinition, power_type: str, battery_service_mode: str | None = None) -> bool:
    battery_task = next((task for task in definition.tasks if task.key == TASK_BATTERY), None)
    if battery_task is None:
        return False
    if definition.key == EQUIPMENT_TYPE_FIRE_ALARMS and battery_service_mode == BATTERY_SERVICE_SEALED_LIFE:
        return False
    if battery_task.allowed_power_types is None:
        return True
    return power_type in battery_task.allowed_power_types


def available_task_definitions(
    definition: EquipmentDefinition,
    power_type: str,
    battery_service_mode: str | None = None,
) -> tuple[TaskDefinition, ...]:
    return tuple(
        task
        for task in definition.tasks
        if (task.allowed_power_types is None or power_type in task.allowed_power_types)
        and not (
            definition.key == EQUIPMENT_TYPE_FIRE_ALARMS
            and task.key == TASK_BATTERY
            and battery_service_mode == BATTERY_SERVICE_SEALED_LIFE
        )
    )
