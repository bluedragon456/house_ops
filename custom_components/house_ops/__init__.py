"""Set up the HouseOps integration."""
from __future__ import annotations

from typing import TypeAlias

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import PLATFORMS
from .coordinator import HouseOpsCoordinator
from .models import HouseOpsRuntimeData
from .services import async_register_services

HouseOpsConfigEntry: TypeAlias = ConfigEntry[HouseOpsRuntimeData]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up HouseOps."""
    async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: HouseOpsConfigEntry) -> bool:
    """Set up HouseOps from a config entry."""
    coordinator = HouseOpsCoordinator(hass, entry)
    await coordinator.async_setup()
    entry.runtime_data = HouseOpsRuntimeData(coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HouseOpsConfigEntry) -> bool:
    """Unload HouseOps config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and entry.runtime_data is not None:
        await entry.runtime_data.coordinator.async_shutdown()
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: HouseOpsConfigEntry) -> None:
    """Reload HouseOps when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
