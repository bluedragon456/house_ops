"""Config flow for HouseOps."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_AREA,
    CONF_ASSETS,
    CONF_ASSET_ID,
    CONF_ASSET_NAME,
    CONF_BASE_INTERVAL_DAYS,
    CONF_BATTERY_INTERVAL_DAYS,
    CONF_BATTERY_SENSOR,
    CONF_BATTERY_THRESHOLD,
    CONF_ENABLE_ANODE_TASK,
    CONF_EQUIPMENT_TYPE,
    CONF_INSTALL_DATE,
    CONF_INSTANCE_NAME,
    CONF_LAST_SERVICED,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_NOTES,
    CONF_RUNTIME_SENSOR,
    CONF_RUNTIME_THRESHOLD,
    CONF_USAGE_SENSOR,
    CONF_USAGE_THRESHOLD,
    DEFAULT_BATTERY_THRESHOLD,
    DEFAULT_INSTANCE_NAME,
    DOMAIN,
    EQUIPMENT_TYPE_FIRE_ALARMS,
    EQUIPMENT_TYPE_FURNACE,
    EQUIPMENT_TYPE_WATER_HEATER,
)
from .registry import build_asset_from_input, dump_assets, find_asset, load_assets, upsert_asset


def _asset_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = dict(defaults or {})
    equipment_type = defaults.get(CONF_EQUIPMENT_TYPE, EQUIPMENT_TYPE_FURNACE)

    schema: dict[Any, Any] = {
        vol.Required(CONF_EQUIPMENT_TYPE, default=equipment_type): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value=EQUIPMENT_TYPE_FURNACE, label="Furnace"),
                    selector.SelectOptionDict(value=EQUIPMENT_TYPE_WATER_HEATER, label="Water heater"),
                    selector.SelectOptionDict(value=EQUIPMENT_TYPE_FIRE_ALARMS, label="Fire alarms"),
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(CONF_ASSET_NAME, default=str(defaults.get(CONF_ASSET_NAME, ""))): selector.TextSelector(),
        vol.Optional(CONF_AREA, default=str(defaults.get(CONF_AREA, ""))): selector.TextSelector(),
        vol.Optional(CONF_MANUFACTURER, default=str(defaults.get(CONF_MANUFACTURER, ""))): selector.TextSelector(),
        vol.Optional(CONF_MODEL, default=str(defaults.get(CONF_MODEL, ""))): selector.TextSelector(),
        vol.Optional(CONF_INSTALL_DATE, default=defaults.get(CONF_INSTALL_DATE)): selector.DateSelector(),
        vol.Required(CONF_LAST_SERVICED, default=defaults.get(CONF_LAST_SERVICED)): selector.DateSelector(),
        vol.Required(
            CONF_BASE_INTERVAL_DAYS,
            default=int(defaults.get(CONF_BASE_INTERVAL_DAYS, _default_base_interval(equipment_type))),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=3650, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(CONF_NOTES, default=str(defaults.get(CONF_NOTES, ""))): selector.TextSelector(),
        vol.Optional(CONF_RUNTIME_SENSOR, default=defaults.get(CONF_RUNTIME_SENSOR)): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "number", "input_number"])
        ),
        vol.Optional(
            CONF_RUNTIME_THRESHOLD,
            default=defaults.get(CONF_RUNTIME_THRESHOLD) if defaults.get(CONF_RUNTIME_THRESHOLD) is not None else 0,
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100000, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(CONF_USAGE_SENSOR, default=defaults.get(CONF_USAGE_SENSOR)): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "number", "input_number"])
        ),
        vol.Optional(
            CONF_USAGE_THRESHOLD,
            default=defaults.get(CONF_USAGE_THRESHOLD) if defaults.get(CONF_USAGE_THRESHOLD) is not None else 0,
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100000, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(CONF_BATTERY_SENSOR, default=defaults.get(CONF_BATTERY_SENSOR)): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "number"])
        ),
        vol.Optional(
            CONF_BATTERY_THRESHOLD,
            default=float(defaults.get(CONF_BATTERY_THRESHOLD, DEFAULT_BATTERY_THRESHOLD)),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(
            CONF_ENABLE_ANODE_TASK,
            default=bool(defaults.get(CONF_ENABLE_ANODE_TASK, equipment_type == EQUIPMENT_TYPE_WATER_HEATER)),
        ): selector.BooleanSelector(),
        vol.Optional(
            CONF_BATTERY_INTERVAL_DAYS,
            default=int(defaults.get(CONF_BATTERY_INTERVAL_DAYS, 180)),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(min=30, max=730, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
    }
    return vol.Schema(schema)


def _default_base_interval(equipment_type: str) -> int:
    if equipment_type == EQUIPMENT_TYPE_FURNACE:
        return 90
    if equipment_type == EQUIPMENT_TYPE_WATER_HEATER:
        return 365
    if equipment_type == EQUIPMENT_TYPE_FIRE_ALARMS:
        return 30
    return 90


def _asset_defaults_from_asset(asset) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        CONF_ASSET_NAME: asset.name,
        CONF_AREA: asset.area or "",
        CONF_EQUIPMENT_TYPE: asset.equipment_type,
        CONF_MANUFACTURER: asset.manufacturer or "",
        CONF_MODEL: asset.model or "",
        CONF_INSTALL_DATE: asset.install_date,
        CONF_LAST_SERVICED: asset.last_serviced,
        CONF_BASE_INTERVAL_DAYS: asset.base_interval_days,
        CONF_NOTES: asset.notes or "",
        CONF_RUNTIME_SENSOR: None,
        CONF_RUNTIME_THRESHOLD: None,
        CONF_USAGE_SENSOR: None,
        CONF_USAGE_THRESHOLD: None,
        CONF_BATTERY_SENSOR: None,
        CONF_BATTERY_THRESHOLD: DEFAULT_BATTERY_THRESHOLD,
        CONF_ENABLE_ANODE_TASK: any(task.key == "anode" for task in asset.tasks),
        CONF_BATTERY_INTERVAL_DAYS: next(
            (task.base_interval_days for task in asset.tasks if task.key == "battery"),
            180,
        ),
    }
    for task in asset.tasks:
        for link in task.sensor_links:
            if link.role == "runtime":
                defaults[CONF_RUNTIME_SENSOR] = link.entity_id
                defaults[CONF_RUNTIME_THRESHOLD] = link.threshold
            elif link.role == "usage":
                defaults[CONF_USAGE_SENSOR] = link.entity_id
                defaults[CONF_USAGE_THRESHOLD] = link.threshold
            elif link.role == "battery":
                defaults[CONF_BATTERY_SENSOR] = link.entity_id
                defaults[CONF_BATTERY_THRESHOLD] = link.threshold or DEFAULT_BATTERY_THRESHOLD
    return defaults


class HouseOpsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HouseOps."""

    VERSION = 1

    def __init__(self) -> None:
        self._instance_name = DEFAULT_INSTANCE_NAME

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HouseOpsOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            self._instance_name = str(user_input[CONF_INSTANCE_NAME]).strip() or DEFAULT_INSTANCE_NAME
            return await self.async_step_asset()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_INSTANCE_NAME, default=DEFAULT_INSTANCE_NAME): selector.TextSelector(),
                }
            ),
        )

    async def async_step_asset(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            if not str(user_input[CONF_ASSET_NAME]).strip():
                errors[CONF_ASSET_NAME] = "required"
            else:
                asset = build_asset_from_input(user_input)
                return self.async_create_entry(
                    title=self._instance_name,
                    data={
                        CONF_INSTANCE_NAME: self._instance_name,
                        CONF_ASSETS: dump_assets([asset]),
                    },
                )

        defaults = {
            CONF_EQUIPMENT_TYPE: EQUIPMENT_TYPE_FURNACE,
            CONF_BASE_INTERVAL_DAYS: 90,
        }
        return self.async_show_form(step_id="asset", data_schema=_asset_schema(defaults), errors=errors)


class HouseOpsOptionsFlow(config_entries.OptionsFlow):
    """Manage assets inside HouseOps."""

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry
        self._selected_asset_id: str | None = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        assets = load_assets(self._config_entry.options.get(CONF_ASSETS, self._config_entry.data.get(CONF_ASSETS, [])))
        menu = ["add_asset"]
        if assets:
            menu.append("edit_asset")
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_add_asset(self, user_input: dict[str, Any] | None = None):
        return await self._async_handle_asset_form(user_input, existing_asset=None)

    async def async_step_edit_asset(self, user_input: dict[str, Any] | None = None):
        assets = load_assets(self._config_entry.options.get(CONF_ASSETS, self._config_entry.data.get(CONF_ASSETS, [])))
        if user_input is not None:
            self._selected_asset_id = user_input[CONF_ASSET_ID]
            return await self.async_step_edit_asset_details()

        options = [
            selector.SelectOptionDict(value=asset.asset_id, label=asset.name)
            for asset in assets
        ]
        return self.async_show_form(
            step_id="edit_asset",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ASSET_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
                    )
                }
            ),
        )

    async def async_step_edit_asset_details(self, user_input: dict[str, Any] | None = None):
        assets = load_assets(self._config_entry.options.get(CONF_ASSETS, self._config_entry.data.get(CONF_ASSETS, [])))
        asset = find_asset(assets, self._selected_asset_id or "")
        if asset is None:
            return self.async_abort(reason="asset_not_found")
        return await self._async_handle_asset_form(user_input, existing_asset=asset)

    async def _async_handle_asset_form(self, user_input: dict[str, Any] | None, existing_asset=None):
        assets = load_assets(self._config_entry.options.get(CONF_ASSETS, self._config_entry.data.get(CONF_ASSETS, [])))
        errors: dict[str, str] = {}

        if user_input is not None:
            if not str(user_input[CONF_ASSET_NAME]).strip():
                errors[CONF_ASSET_NAME] = "required"
            else:
                asset = build_asset_from_input(user_input, existing_assets=assets, existing_asset=existing_asset)
                updated_assets = upsert_asset(assets, asset)
                return self.async_create_entry(title="", data={CONF_ASSETS: dump_assets(updated_assets)})

        defaults = _asset_defaults_from_asset(existing_asset) if existing_asset else {
            CONF_EQUIPMENT_TYPE: EQUIPMENT_TYPE_FURNACE,
            CONF_BASE_INTERVAL_DAYS: 90,
        }
        step_id = "edit_asset_details" if existing_asset else "add_asset"
        return self.async_show_form(step_id=step_id, data_schema=_asset_schema(defaults), errors=errors)
