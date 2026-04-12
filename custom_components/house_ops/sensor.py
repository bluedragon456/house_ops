"""Sensor platform for HouseOps."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    ATTR_CATALOG_TIER,
    ATTR_CATEGORY,
    ATTR_DUE_DETAILS,
    ATTR_DUE_SOURCE,
    ATTR_DOCK_SOURCE_ENTITY,
    ATTR_EQUIPMENT_TYPE,
    ATTR_IS_CUSTOM,
    ATTR_LINKED_SENSORS,
    ATTR_OVERRIDE_ACTIVE,
    ATTR_POWER_TYPE,
    ATTR_REASON,
    ATTR_ROBOT_DOCK_TYPE,
    ATTR_ROBOT_MOP_STYLE,
    ATTR_TASKS,
    ATTR_TASK_TITLE,
    MAINTENANCE_STATES,
)
from .coordinator import HouseOpsConfigEntry
from .entity import HouseOpsEntity, HouseOpsTaskEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HouseOpsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up HouseOps sensors."""
    coordinator = entry.runtime_data.coordinator
    entities: list[SensorEntity] = []

    for asset_id, asset_state in coordinator.data.computed.items():
        entities.extend(
            [
                HouseOpsMaintenanceStatusSensor(coordinator, asset_id),
                HouseOpsNextServiceDateSensor(coordinator, asset_id),
                HouseOpsDaysRemainingSensor(coordinator, asset_id),
                HouseOpsMaintenanceReasonSensor(coordinator, asset_id),
            ]
        )
        for task_key in asset_state.tasks:
            entities.extend(
                [
                    HouseOpsTaskStatusSensor(coordinator, asset_id, task_key),
                    HouseOpsTaskNextServiceDateSensor(coordinator, asset_id, task_key),
                    HouseOpsTaskDaysRemainingSensor(coordinator, asset_id, task_key),
                    HouseOpsTaskReasonSensor(coordinator, asset_id, task_key),
                ]
            )

    async_add_entities(entities)


class HouseOpsMaintenanceStatusSensor(HouseOpsEntity, SensorEntity):
    _attr_translation_key = "maintenance_status"
    _attr_icon = "mdi:clipboard-text-clock-outline"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = MAINTENANCE_STATES

    def __init__(self, coordinator, asset_id: str) -> None:
        super().__init__(coordinator, asset_id)
        self._attr_name = "Maintenance Status"
        self._attr_unique_id = f"{asset_id}_maintenance_status"

    @property
    def native_value(self) -> str:
        return self.asset_state.state

    @property
    def extra_state_attributes(self) -> dict:
        return {
            ATTR_REASON: self.asset_state.reason,
            ATTR_DUE_SOURCE: self.asset_state.due_source,
            ATTR_DUE_DETAILS: self.asset_state.due_details,
            ATTR_EQUIPMENT_TYPE: self.asset.equipment_type,
            ATTR_CATEGORY: self.asset.custom_category or self.asset.category,
            ATTR_CATALOG_TIER: self.asset.catalog_tier,
            ATTR_IS_CUSTOM: self.asset.is_custom,
            ATTR_POWER_TYPE: self.asset.power_type,
            ATTR_ROBOT_MOP_STYLE: self.asset.robot_mop_style,
            ATTR_ROBOT_DOCK_TYPE: self.asset.robot_dock_type,
            ATTR_DOCK_SOURCE_ENTITY: self.asset.dock_source_entity,
            ATTR_TASKS: {
                key: {
                    "title": task.task_title,
                    "state": task.state,
                    "next_service_date": task.next_service_date.isoformat() if task.next_service_date else None,
                    "days_remaining": task.days_remaining,
                    ATTR_REASON: task.reason,
                    ATTR_DUE_SOURCE: task.due_source,
                    ATTR_DUE_DETAILS: task.due_details,
                    ATTR_OVERRIDE_ACTIVE: task.override_active,
                }
                for key, task in self.asset_state.tasks.items()
            },
        }


class HouseOpsNextServiceDateSensor(HouseOpsEntity, SensorEntity):
    _attr_translation_key = "next_service_date"
    _attr_icon = "mdi:calendar-clock"
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator, asset_id: str) -> None:
        super().__init__(coordinator, asset_id)
        self._attr_name = "Next Service Date"
        self._attr_unique_id = f"{asset_id}_next_service_date"

    @property
    def native_value(self):
        return self.asset_state.next_service_date

    @property
    def extra_state_attributes(self) -> dict:
        return {
            ATTR_DUE_SOURCE: self.asset_state.due_source,
            ATTR_DUE_DETAILS: self.asset_state.due_details,
        }


class HouseOpsDaysRemainingSensor(HouseOpsEntity, SensorEntity):
    _attr_translation_key = "days_remaining"
    _attr_icon = "mdi:timer-sand"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, asset_id: str) -> None:
        super().__init__(coordinator, asset_id)
        self._attr_name = "Days Remaining"
        self._attr_unique_id = f"{asset_id}_days_remaining"

    @property
    def native_value(self) -> int | None:
        return self.asset_state.days_remaining


class HouseOpsMaintenanceReasonSensor(HouseOpsEntity, SensorEntity):
    _attr_translation_key = "maintenance_reason"
    _attr_icon = "mdi:text-box-search-outline"

    def __init__(self, coordinator, asset_id: str) -> None:
        super().__init__(coordinator, asset_id)
        self._attr_name = "Maintenance Reason"
        self._attr_unique_id = f"{asset_id}_maintenance_reason"

    @property
    def native_value(self) -> str:
        return self.asset_state.reason


class HouseOpsTaskStatusSensor(HouseOpsTaskEntity, SensorEntity):
    _attr_icon = "mdi:clipboard-check-outline"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = MAINTENANCE_STATES

    def __init__(self, coordinator, asset_id: str, task_key: str) -> None:
        super().__init__(coordinator, asset_id, task_key)
        self._attr_name = f"{self.task.title} Status"
        self._attr_unique_id = f"{asset_id}_{task_key}_status"

    @property
    def native_value(self) -> str:
        return self.task_state.state

    @property
    def extra_state_attributes(self) -> dict:
        return {
            ATTR_TASK_TITLE: self.task_state.task_title,
            ATTR_REASON: self.task_state.reason,
            ATTR_DUE_SOURCE: self.task_state.due_source,
            ATTR_DUE_DETAILS: self.task_state.due_details,
            ATTR_OVERRIDE_ACTIVE: self.task_state.override_active,
            ATTR_LINKED_SENSORS: self.task_state.linked_sensors,
        }


class HouseOpsTaskNextServiceDateSensor(HouseOpsTaskEntity, SensorEntity):
    _attr_icon = "mdi:calendar-arrow-right"
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator, asset_id: str, task_key: str) -> None:
        super().__init__(coordinator, asset_id, task_key)
        self._attr_name = f"{self.task.title} Next Service Date"
        self._attr_unique_id = f"{asset_id}_{task_key}_next_service_date"

    @property
    def native_value(self):
        return self.task_state.next_service_date


class HouseOpsTaskDaysRemainingSensor(HouseOpsTaskEntity, SensorEntity):
    _attr_icon = "mdi:calendar-range"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.DAYS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, asset_id: str, task_key: str) -> None:
        super().__init__(coordinator, asset_id, task_key)
        self._attr_name = f"{self.task.title} Days Remaining"
        self._attr_unique_id = f"{asset_id}_{task_key}_days_remaining"

    @property
    def native_value(self) -> int | None:
        return self.task_state.days_remaining


class HouseOpsTaskReasonSensor(HouseOpsTaskEntity, SensorEntity):
    _attr_icon = "mdi:comment-alert-outline"

    def __init__(self, coordinator, asset_id: str, task_key: str) -> None:
        super().__init__(coordinator, asset_id, task_key)
        self._attr_name = f"{self.task.title} Reason"
        self._attr_unique_id = f"{asset_id}_{task_key}_reason"

    @property
    def native_value(self) -> str:
        return self.task_state.reason
