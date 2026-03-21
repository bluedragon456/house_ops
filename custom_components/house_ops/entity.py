"""Entity helpers for HouseOps."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import HouseOpsCoordinator


class HouseOpsEntity(CoordinatorEntity[HouseOpsCoordinator], Entity):
    """Base HouseOps entity."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: HouseOpsCoordinator, asset_id: str) -> None:
        super().__init__(coordinator)
        self._asset_id = asset_id

    @property
    def asset(self):
        return self.coordinator.data.assets[self._asset_id]

    @property
    def asset_state(self):
        return self.coordinator.data.computed[self._asset_id]

    @property
    def device_info(self) -> DeviceInfo:
        asset = self.asset
        return DeviceInfo(
            identifiers={(DOMAIN, asset.asset_id)},
            name=asset.name,
            manufacturer=asset.manufacturer or NAME,
            model=asset.model or asset.equipment_type.replace("_", " ").title(),
            suggested_area=asset.area,
        )


class HouseOpsTaskEntity(HouseOpsEntity):
    """Base HouseOps task entity."""

    def __init__(self, coordinator: HouseOpsCoordinator, asset_id: str, task_key: str) -> None:
        super().__init__(coordinator, asset_id)
        self._task_key = task_key

    @property
    def task(self):
        return next(task for task in self.asset.tasks if task.key == self._task_key)

    @property
    def task_state(self):
        return self.asset_state.tasks[self._task_key]
