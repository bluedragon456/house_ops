"""Coordinator for HouseOps."""
from __future__ import annotations

from datetime import date, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_ASSETS, DEFAULT_SNOOZE_DAYS, DOMAIN
from .engine import build_snapshot, collect_linked_entities
from .models import HouseOpsRuntimeData, RegistrySnapshot
from .registry import dump_assets, find_asset, load_assets, mark_task_serviced, remove_asset, snooze_task, upsert_asset


class HouseOpsCoordinator(DataUpdateCoordinator[RegistrySnapshot]):
    """Coordinate HouseOps data and refreshes."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, logger=logging.getLogger(__name__), name=DOMAIN)
        self.entry = entry
        self._unsub_sensor_listener: CALLBACK_TYPE | None = None

    async def async_setup(self) -> None:
        """Load initial state and subscribe to linked sensors."""
        await self.async_refresh()
        self._async_resubscribe()

    async def _async_update_data(self) -> RegistrySnapshot:
        assets = load_assets(self.entry.options.get(CONF_ASSETS, self.entry.data.get(CONF_ASSETS, [])))
        return build_snapshot(self.hass, assets)

    async def async_mark_serviced(
        self,
        asset_id: str,
        task_key: str,
        serviced_on: date | None = None,
    ) -> None:
        assets = load_assets(self.entry.options.get(CONF_ASSETS, self.entry.data.get(CONF_ASSETS, [])))
        updated_assets = mark_task_serviced(assets, asset_id, task_key, serviced_on or date.today())
        self.hass.config_entries.async_update_entry(
            self.entry,
            options={**self.entry.options, CONF_ASSETS: dump_assets(updated_assets)},
        )
        await self.async_refresh()
        self._async_resubscribe()

    async def async_snooze_task(
        self,
        asset_id: str,
        task_key: str,
        days: int | None = None,
    ) -> None:
        assets = load_assets(self.entry.options.get(CONF_ASSETS, self.entry.data.get(CONF_ASSETS, [])))
        until = date.today() + timedelta(days=days or DEFAULT_SNOOZE_DAYS)
        updated_assets = snooze_task(assets, asset_id, task_key, until)
        self.hass.config_entries.async_update_entry(
            self.entry,
            options={**self.entry.options, CONF_ASSETS: dump_assets(updated_assets)},
        )
        await self.async_refresh()
        self._async_resubscribe()

    async def async_add_or_update_asset(self, asset: Any) -> None:
        assets = load_assets(self.entry.options.get(CONF_ASSETS, self.entry.data.get(CONF_ASSETS, [])))
        updated_assets = upsert_asset(assets, asset)
        self.hass.config_entries.async_update_entry(
            self.entry,
            options={**self.entry.options, CONF_ASSETS: dump_assets(updated_assets)},
        )
        await self.async_refresh()
        self._async_resubscribe()

    async def async_remove_asset(self, asset_id: str) -> None:
        assets = load_assets(self.entry.options.get(CONF_ASSETS, self.entry.data.get(CONF_ASSETS, [])))
        updated_assets = remove_asset(assets, asset_id)
        self.hass.config_entries.async_update_entry(
            self.entry,
            options={**self.entry.options, CONF_ASSETS: dump_assets(updated_assets)},
        )
        await self.async_refresh()
        self._async_resubscribe()

    def get_asset_state(self, asset_id: str):
        return self.data.computed[asset_id]

    def get_task_state(self, asset_id: str, task_key: str):
        return self.data.computed[asset_id].tasks[task_key]

    def find_asset(self, asset_id: str):
        return find_asset(list(self.data.assets.values()), asset_id)

    async def async_shutdown(self) -> None:
        if self._unsub_sensor_listener:
            self._unsub_sensor_listener()
            self._unsub_sensor_listener = None

    @callback
    def _async_resubscribe(self) -> None:
        if self._unsub_sensor_listener:
            self._unsub_sensor_listener()
            self._unsub_sensor_listener = None

        entity_ids = collect_linked_entities(self.data)
        if not entity_ids:
            return

        self._unsub_sensor_listener = async_track_state_change_event(
            self.hass,
            list(entity_ids),
            self._async_handle_sensor_change,
        )

    @callback
    def _async_handle_sensor_change(self, event: Event[EventStateChangedData]) -> None:
        self.async_set_updated_data(build_snapshot(self.hass, list(self.data.assets.values())))


HouseOpsConfigEntry = ConfigEntry[HouseOpsRuntimeData]
