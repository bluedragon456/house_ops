"""Buttons for HouseOps."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import HouseOpsConfigEntry
from .entity import HouseOpsEntity, HouseOpsTaskEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HouseOpsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up HouseOps buttons."""
    coordinator = entry.runtime_data.coordinator
    entities: list[ButtonEntity] = []

    for asset_id, asset_state in coordinator.data.computed.items():
        entities.extend(
            [
                HouseOpsMarkServicedButton(coordinator, asset_id),
                HouseOpsSnoozeButton(coordinator, asset_id),
            ]
        )
        for task_key in asset_state.tasks:
            entities.extend(
                [
                    HouseOpsTaskMarkServicedButton(coordinator, asset_id, task_key),
                    HouseOpsTaskSnoozeButton(coordinator, asset_id, task_key),
                ]
            )

    async_add_entities(entities)


class HouseOpsMarkServicedButton(HouseOpsEntity, ButtonEntity):
    _attr_translation_key = "mark_serviced"
    _attr_icon = "mdi:check-decagram-outline"

    def __init__(self, coordinator, asset_id: str) -> None:
        super().__init__(coordinator, asset_id)
        self._attr_name = "Mark Serviced"
        self._attr_unique_id = f"{asset_id}_mark_serviced"

    async def async_press(self) -> None:
        task_key = self.asset_state.primary_task_key or next(iter(self.asset_state.tasks))
        await self.coordinator.async_mark_serviced(self._asset_id, task_key)


class HouseOpsSnoozeButton(HouseOpsEntity, ButtonEntity):
    _attr_translation_key = "snooze"
    _attr_icon = "mdi:alarm-snooze"

    def __init__(self, coordinator, asset_id: str) -> None:
        super().__init__(coordinator, asset_id)
        self._attr_name = "Snooze"
        self._attr_unique_id = f"{asset_id}_snooze"

    async def async_press(self) -> None:
        task_key = self.asset_state.primary_task_key or next(iter(self.asset_state.tasks))
        await self.coordinator.async_snooze_task(self._asset_id, task_key)


class HouseOpsTaskMarkServicedButton(HouseOpsTaskEntity, ButtonEntity):
    _attr_icon = "mdi:clipboard-check"

    def __init__(self, coordinator, asset_id: str, task_key: str) -> None:
        super().__init__(coordinator, asset_id, task_key)
        self._attr_name = f"{self.task.title} Mark Serviced"
        self._attr_unique_id = f"{asset_id}_{task_key}_mark_serviced"

    async def async_press(self) -> None:
        await self.coordinator.async_mark_serviced(self._asset_id, self._task_key)


class HouseOpsTaskSnoozeButton(HouseOpsTaskEntity, ButtonEntity):
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator, asset_id: str, task_key: str) -> None:
        super().__init__(coordinator, asset_id, task_key)
        self._attr_name = f"{self.task.title} Snooze"
        self._attr_unique_id = f"{asset_id}_{task_key}_snooze"

    async def async_press(self) -> None:
        await self.coordinator.async_snooze_task(self._asset_id, self._task_key)
