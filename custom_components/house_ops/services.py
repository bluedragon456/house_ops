"""Services for HouseOps."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_DAYS,
    ATTR_OCCURRED_ON,
    ATTR_TASK_KEY,
    CONF_ANODE_INTERVAL_DAYS,
    CONF_AREA_ID,
    CONF_ASSET_ID,
    CONF_ASSET_NAME,
    CONF_BASE_INTERVAL_DAYS,
    CONF_BATTERY_INTERVAL_DAYS,
    CONF_BATTERY_SENSOR,
    CONF_BATTERY_SERVICE_MODE,
    CONF_BATTERY_THRESHOLD,
    CONF_CONTACT_CLEANING_INTERVAL_DAYS,
    CONF_CUSTOM_AREA,
    CONF_DOCK_SOURCE_ENTITY,
    CONF_DOCK_AIR_PATH_INTERVAL_DAYS,
    CONF_DOCK_CLEAN_WATER_TANK_INTERVAL_DAYS,
    CONF_DOCK_DIRTY_WATER_TANK_INTERVAL_DAYS,
    CONF_DOCK_DUST_BAG_INTERVAL_DAYS,
    CONF_DOCK_WASH_TRAY_INTERVAL_DAYS,
    CONF_DOCK_WATER_FILTER_INTERVAL_DAYS,
    CONF_DUST_BIN_INTERVAL_DAYS,
    CONF_ENABLE_ANODE_TASK,
    CONF_EQUIPMENT_TYPE,
    CONF_INSTALL_DATE,
    CONF_INSPECTION_INTERVAL_DAYS,
    CONF_LAST_SERVICED_DATE,
    CONF_MAIN_BRUSH_INTERVAL_DAYS,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_MOP_SERVICE_INTERVAL_DAYS,
    CONF_NEXT_DUE_OVERRIDE,
    CONF_NOTES,
    CONF_POWER_TYPE,
    CONF_REPLACEMENT_INTERVAL_DAYS,
    CONF_ROBOT_DOCK_TYPE,
    CONF_ROBOT_HAS_MOP,
    CONF_ROBOT_MOP_STYLE,
    CONF_RUNTIME_SENSOR,
    CONF_RUNTIME_THRESHOLD,
    CONF_SENSOR_CLEANING_INTERVAL_DAYS,
    CONF_SIDE_BRUSH_INTERVAL_DAYS,
    CONF_SOURCE_ENTITY,
    CONF_USAGE_SENSOR,
    CONF_USAGE_THRESHOLD,
    CONF_WATER_TANK_INTERVAL_DAYS,
    CONF_WHEEL_CLEAN_INTERVAL_DAYS,
    DOMAIN,
    SERVICE_ADD_ASSET,
    SERVICE_MARK_SERVICED,
    SERVICE_RECALCULATE,
    SERVICE_SNOOZE_TASK,
)
from .equipment_catalog import get_supported_definitions
from .registry import build_asset_from_input


def async_register_services(hass: HomeAssistant) -> None:
    """Register service handlers."""
    if hass.services.has_service(DOMAIN, SERVICE_MARK_SERVICED):
        return

    mark_schema = vol.Schema(
        {
            vol.Required(CONF_ASSET_ID): cv.string,
            vol.Required(ATTR_TASK_KEY): cv.string,
            vol.Optional(ATTR_OCCURRED_ON): cv.date,
        }
    )
    snooze_schema = vol.Schema(
        {
            vol.Required(CONF_ASSET_ID): cv.string,
            vol.Required(ATTR_TASK_KEY): cv.string,
            vol.Optional(ATTR_DAYS): vol.Coerce(int),
        }
    )
    add_asset_schema = vol.Schema(
        {
            vol.Required(CONF_EQUIPMENT_TYPE): vol.In([definition.key for definition in get_supported_definitions()]),
            vol.Optional(CONF_ASSET_NAME): cv.string,
            vol.Optional(CONF_AREA_ID): cv.string,
            vol.Optional(CONF_CUSTOM_AREA): cv.string,
            vol.Optional(CONF_SOURCE_ENTITY): cv.string,
            vol.Optional(CONF_DOCK_SOURCE_ENTITY): cv.string,
            vol.Optional(CONF_POWER_TYPE): cv.string,
            vol.Optional(CONF_BATTERY_SERVICE_MODE): cv.string,
            vol.Optional(CONF_MANUFACTURER): cv.string,
            vol.Optional(CONF_MODEL): cv.string,
            vol.Optional(CONF_INSTALL_DATE): cv.date,
            vol.Optional(CONF_LAST_SERVICED_DATE): cv.date,
            vol.Optional(CONF_NEXT_DUE_OVERRIDE): cv.date,
            vol.Required(CONF_BASE_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_INSPECTION_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_ANODE_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_BATTERY_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_REPLACEMENT_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_DUST_BIN_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_MAIN_BRUSH_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_SIDE_BRUSH_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_WHEEL_CLEAN_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_SENSOR_CLEANING_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_CONTACT_CLEANING_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_MOP_SERVICE_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_WATER_TANK_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_DOCK_DUST_BAG_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_DOCK_AIR_PATH_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_DOCK_CLEAN_WATER_TANK_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_DOCK_DIRTY_WATER_TANK_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_DOCK_WASH_TRAY_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_DOCK_WATER_FILTER_INTERVAL_DAYS): vol.Coerce(int),
            vol.Optional(CONF_NOTES): cv.string,
            vol.Optional(CONF_RUNTIME_SENSOR): cv.entity_id,
            vol.Optional(CONF_RUNTIME_THRESHOLD): vol.Coerce(int),
            vol.Optional(CONF_USAGE_SENSOR): cv.entity_id,
            vol.Optional(CONF_USAGE_THRESHOLD): vol.Coerce(int),
            vol.Optional(CONF_BATTERY_SENSOR): cv.entity_id,
            vol.Optional(CONF_BATTERY_THRESHOLD): vol.Coerce(float),
            vol.Optional(CONF_ENABLE_ANODE_TASK): cv.boolean,
            vol.Optional(CONF_ROBOT_HAS_MOP): cv.boolean,
            vol.Optional(CONF_ROBOT_MOP_STYLE): cv.string,
            vol.Optional(CONF_ROBOT_DOCK_TYPE): cv.string,
        }
    )

    async def async_handle_mark_serviced(call: ServiceCall) -> None:
        coordinator = _get_single_coordinator(hass)
        try:
            await coordinator.async_mark_serviced(
                call.data[CONF_ASSET_ID],
                call.data[ATTR_TASK_KEY],
                call.data.get(ATTR_OCCURRED_ON),
            )
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err

    async def async_handle_snooze(call: ServiceCall) -> None:
        coordinator = _get_single_coordinator(hass)
        try:
            await coordinator.async_snooze_task(
                call.data[CONF_ASSET_ID],
                call.data[ATTR_TASK_KEY],
                call.data.get(ATTR_DAYS),
            )
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err

    async def async_handle_recalculate(call: ServiceCall) -> None:
        coordinator = _get_single_coordinator(hass)
        await coordinator.async_refresh()

    async def async_handle_add_asset(call: ServiceCall) -> None:
        coordinator = _get_single_coordinator(hass)
        asset = build_asset_from_input(
            hass,
            dict(call.data),
            existing_assets=list(coordinator.data.assets.values()),
        )
        if not asset.name:
            raise HomeAssistantError("Equipment name is required unless the linked device provides one.")
        await coordinator.async_add_or_update_asset(asset)

    hass.services.async_register(DOMAIN, SERVICE_MARK_SERVICED, async_handle_mark_serviced, schema=mark_schema)
    hass.services.async_register(DOMAIN, SERVICE_SNOOZE_TASK, async_handle_snooze, schema=snooze_schema)
    hass.services.async_register(DOMAIN, SERVICE_RECALCULATE, async_handle_recalculate, schema=vol.Schema({}))
    hass.services.async_register(DOMAIN, SERVICE_ADD_ASSET, async_handle_add_asset, schema=add_asset_schema)


def _get_single_coordinator(hass: HomeAssistant):
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise HomeAssistantError("HouseOps must be configured before calling services.")
    entry = entries[0]
    if entry.runtime_data is None:
        raise HomeAssistantError("HouseOps is not ready yet.")
    return entry.runtime_data.coordinator
