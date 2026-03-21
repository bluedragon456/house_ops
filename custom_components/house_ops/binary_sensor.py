"""Binary sensors for HouseOps."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import STATE_DUE, STATE_OVERDUE
from .coordinator import HouseOpsConfigEntry
from .entity import HouseOpsEntity, HouseOpsTaskEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HouseOpsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up HouseOps binary sensors."""
    coordinator = entry.runtime_data.coordinator
    entities: list[BinarySensorEntity] = []

    for asset_id, asset_state in coordinator.data.computed.items():
        entities.append(HouseOpsDueBinarySensor(coordinator, asset_id))
        for task_key in asset_state.tasks:
            entities.append(HouseOpsTaskDueBinarySensor(coordinator, asset_id, task_key))

    async_add_entities(entities)


class HouseOpsDueBinarySensor(HouseOpsEntity, BinarySensorEntity):
    _attr_translation_key = "due"
    _attr_icon = "mdi:alert-circle-outline"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, asset_id: str) -> None:
        super().__init__(coordinator, asset_id)
        self._attr_name = "Due"
        self._attr_unique_id = f"{asset_id}_due"

    @property
    def is_on(self) -> bool:
        return self.asset_state.state in {STATE_DUE, STATE_OVERDUE}


class HouseOpsTaskDueBinarySensor(HouseOpsTaskEntity, BinarySensorEntity):
    _attr_icon = "mdi:alarm-light-outline"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator, asset_id: str, task_key: str) -> None:
        super().__init__(coordinator, asset_id, task_key)
        self._attr_name = f"{self.task.title} Due"
        self._attr_unique_id = f"{asset_id}_{task_key}_due"

    @property
    def is_on(self) -> bool:
        return self.task_state.state in {STATE_DUE, STATE_OVERDUE}
