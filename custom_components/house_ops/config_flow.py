"""Config flow for HouseOps."""
from __future__ import annotations

from datetime import date
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ANODE_INTERVAL_DAYS,
    CONF_AREA_ID,
    CONF_ASSETS,
    CONF_ASSET_ID,
    CONF_ASSET_NAME,
    CONF_BASE_INTERVAL_DAYS,
    CONF_BATTERY_INTERVAL_DAYS,
    CONF_BATTERY_SENSOR,
    CONF_BATTERY_THRESHOLD,
    CONF_CONFIRM_REMOVE,
    CONF_CUSTOM_AREA,
    CONF_ENABLE_ANODE_TASK,
    CONF_EQUIPMENT_TYPE,
    CONF_INSTALL_DATE,
    CONF_INSPECTION_INTERVAL_DAYS,
    CONF_INSTANCE_NAME,
    CONF_LAST_SERVICED_DATE,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_NEXT_DUE_OVERRIDE,
    CONF_NOTES,
    CONF_POWER_TYPE,
    CONF_REPLACEMENT_INTERVAL_DAYS,
    CONF_RUNTIME_SENSOR,
    CONF_RUNTIME_THRESHOLD,
    CONF_USAGE_SENSOR,
    CONF_USAGE_THRESHOLD,
    DEFAULT_BATTERY_THRESHOLD,
    DEFAULT_INSTANCE_NAME,
    DOMAIN,
    TASK_ANODE,
    TASK_BATTERY,
    TASK_INSPECTION,
    TASK_REPLACEMENT,
)
from .equipment_catalog import POWER_TYPE_LABELS, get_equipment_definition, get_supported_definitions, supports_battery
from .registry import asset_summary, build_asset_from_input, dump_assets, find_asset, load_assets, remove_asset, upsert_asset

CONF_NEXT_ACTION = "next_action"


class HouseOpsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HouseOps."""

    VERSION = 1

    def __init__(self) -> None:
        self._instance_name = DEFAULT_INSTANCE_NAME
        self._selected_equipment_type: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HouseOpsOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            instance_name = str(user_input[CONF_INSTANCE_NAME]).strip()
            self._instance_name = instance_name or DEFAULT_INSTANCE_NAME
            return await self.async_step_add_equipment()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_INSTANCE_NAME, default=DEFAULT_INSTANCE_NAME): selector.TextSelector(),
                }
            ),
        )

    async def async_step_add_equipment(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._selected_equipment_type = str(user_input[CONF_EQUIPMENT_TYPE])
            return await self.async_step_add_equipment_details()

        return self.async_show_form(
            step_id="add_equipment",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EQUIPMENT_TYPE): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=definition.key, label=definition.label)
                                for definition in get_supported_definitions()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def async_step_add_equipment_details(self, user_input: dict[str, Any] | None = None):
        definition = get_equipment_definition(self._selected_equipment_type or get_supported_definitions()[0].key)
        errors: dict[str, str] = {}

        if user_input is not None:
            cleaned = _sanitize_asset_input(user_input)
            if not cleaned[CONF_ASSET_NAME]:
                errors[CONF_ASSET_NAME] = "required"
            else:
                asset = build_asset_from_input(self.hass, cleaned)
                return self.async_create_entry(
                    title=self._instance_name,
                    data={CONF_INSTANCE_NAME: self._instance_name, CONF_ASSETS: dump_assets([asset])},
                )

        defaults = _defaults_for_new_asset(definition.key)
        return self.async_show_form(
            step_id="add_equipment_details",
            data_schema=_build_asset_schema(self.hass, definition.key, defaults),
            errors=errors,
            description_placeholders={
                "equipment_label": definition.label,
                "equipment_description": definition.description,
                "primary_task": _primary_task_label(definition.key),
            },
        )


class HouseOpsOptionsFlow(config_entries.OptionsFlow):
    """Manage equipment inside HouseOps."""

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry
        self._selected_asset_id: str | None = None
        self._selected_equipment_type: str | None = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        if user_input is not None:
            return await self._async_handle_manage_action(user_input[CONF_NEXT_ACTION])
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NEXT_ACTION): _action_selector(
                        [
                            ("review_equipment", "Review equipment"),
                            ("add_equipment", "Add equipment"),
                            ("edit_equipment", "Edit equipment"),
                            ("remove_equipment", "Remove equipment"),
                        ]
                    )
                }
            ),
            description_placeholders={"equipment_summary": _equipment_summary_text(assets)},
        )

    async def async_step_review_equipment(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        if not assets:
            return await self.async_step_init()
        if user_input is not None:
            self._selected_asset_id = str(user_input[CONF_ASSET_ID])
            return await self.async_step_review_equipment_details()
        return self.async_show_form(
            step_id="review_equipment",
            data_schema=_asset_select_schema(assets),
            description_placeholders={"equipment_summary": _equipment_summary_text(assets)},
        )

    async def async_step_review_equipment_details(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        asset = find_asset(assets, self._selected_asset_id or "")
        if asset is None:
            return self.async_abort(reason="asset_not_found")
        if user_input is not None:
            selected_action = user_input[CONF_NEXT_ACTION]
            if selected_action == "back_to_manage":
                return await self.async_step_init()
            if selected_action == "edit_selected_equipment":
                return await self.async_step_edit_equipment_details()
            return await self.async_step_remove_selected_equipment()
        return self.async_show_form(
            step_id="review_equipment_details",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NEXT_ACTION): _action_selector(
                        [
                            ("edit_selected_equipment", "Edit this equipment"),
                            ("remove_selected_equipment", "Remove this equipment"),
                            ("back_to_manage", "Back to equipment manager"),
                        ]
                    )
                }
            ),
            description_placeholders={"asset_summary": asset_summary(asset)},
        )

    async def async_step_add_equipment(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._selected_equipment_type = str(user_input[CONF_EQUIPMENT_TYPE])
            return await self.async_step_add_equipment_details()
        return self.async_show_form(
            step_id="add_equipment",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EQUIPMENT_TYPE): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=definition.key, label=definition.label)
                                for definition in get_supported_definitions()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def async_step_add_equipment_details(self, user_input: dict[str, Any] | None = None):
        definition = get_equipment_definition(self._selected_equipment_type or get_supported_definitions()[0].key)
        assets = _load_entry_assets(self._config_entry)
        errors: dict[str, str] = {}
        if user_input is not None:
            cleaned = _sanitize_asset_input(user_input)
            if not cleaned[CONF_ASSET_NAME]:
                errors[CONF_ASSET_NAME] = "required"
            else:
                asset = build_asset_from_input(self.hass, cleaned, existing_assets=assets)
                updated_assets = upsert_asset(assets, asset)
                return self.async_create_entry(title="", data={CONF_ASSETS: dump_assets(updated_assets)})
        return self.async_show_form(
            step_id="add_equipment_details",
            data_schema=_build_asset_schema(self.hass, definition.key, _defaults_for_new_asset(definition.key)),
            errors=errors,
            description_placeholders={
                "equipment_label": definition.label,
                "equipment_description": definition.description,
                "primary_task": _primary_task_label(definition.key),
            },
        )

    async def async_step_edit_equipment(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        if not assets:
            return await self.async_step_init()
        if user_input is not None:
            self._selected_asset_id = str(user_input[CONF_ASSET_ID])
            return await self.async_step_edit_equipment_details()
        return self.async_show_form(
            step_id="edit_equipment",
            data_schema=_asset_select_schema(assets),
            description_placeholders={"equipment_summary": _equipment_summary_text(assets)},
        )

    async def async_step_edit_selected_equipment(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_edit_equipment_details()

    async def async_step_edit_equipment_details(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        asset = find_asset(assets, self._selected_asset_id or "")
        if asset is None:
            return self.async_abort(reason="asset_not_found")

        errors: dict[str, str] = {}
        if user_input is not None:
            cleaned = _sanitize_asset_input(user_input)
            if not cleaned[CONF_ASSET_NAME]:
                errors[CONF_ASSET_NAME] = "required"
            else:
                updated = build_asset_from_input(
                    self.hass,
                    cleaned,
                    existing_assets=assets,
                    existing_asset=asset,
                )
                updated_assets = upsert_asset(assets, updated)
                return self.async_create_entry(title="", data={CONF_ASSETS: dump_assets(updated_assets)})

        return self.async_show_form(
            step_id="edit_equipment_details",
            data_schema=_build_asset_schema(self.hass, asset.equipment_type, _defaults_from_asset(asset)),
            errors=errors,
            description_placeholders={
                "equipment_label": asset.name,
                "equipment_description": asset_summary(asset),
                "primary_task": _primary_task_label(asset.equipment_type),
            },
        )

    async def async_step_remove_equipment(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        if not assets:
            return await self.async_step_init()
        if user_input is not None:
            self._selected_asset_id = str(user_input[CONF_ASSET_ID])
            return await self.async_step_remove_selected_equipment()
        return self.async_show_form(
            step_id="remove_equipment",
            data_schema=_asset_select_schema(assets),
            description_placeholders={"equipment_summary": _equipment_summary_text(assets)},
        )

    async def async_step_remove_selected_equipment(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        asset = find_asset(assets, self._selected_asset_id or "")
        if asset is None:
            return self.async_abort(reason="asset_not_found")
        if user_input is not None and user_input.get(CONF_CONFIRM_REMOVE):
            updated_assets = remove_asset(assets, asset.asset_id)
            return self.async_create_entry(title="", data={CONF_ASSETS: dump_assets(updated_assets)})
        return self.async_show_form(
            step_id="remove_selected_equipment",
            data_schema=vol.Schema({vol.Required(CONF_CONFIRM_REMOVE, default=False): selector.BooleanSelector()}),
            description_placeholders={"asset_summary": asset_summary(asset)},
        )

    async def _async_handle_manage_action(self, selected_action: str):
        if selected_action == "review_equipment":
            return await self.async_step_review_equipment()
        if selected_action == "add_equipment":
            return await self.async_step_add_equipment()
        if selected_action == "edit_equipment":
            return await self.async_step_edit_equipment()
        return await self.async_step_remove_equipment()


def _build_asset_schema(hass, equipment_type: str, defaults: dict[str, Any]) -> vol.Schema:
    definition = get_equipment_definition(equipment_type)
    power_type = str(defaults.get(CONF_POWER_TYPE, definition.default_power_type))
    schema: dict[Any, Any] = {}

    _add_required(schema, CONF_EQUIPMENT_TYPE, _equipment_selector(), default=equipment_type)
    _add_required(schema, CONF_ASSET_NAME, selector.TextSelector(), default=defaults.get(CONF_ASSET_NAME, ""))
    _add_optional(schema, CONF_AREA_ID, selector.AreaSelector(), default=defaults.get(CONF_AREA_ID))
    _add_optional(schema, CONF_CUSTOM_AREA, selector.TextSelector(), default=defaults.get(CONF_CUSTOM_AREA))

    if len(definition.supported_power_types) > 1:
        _add_required(schema, CONF_POWER_TYPE, _power_selector(definition), default=power_type)

    _add_optional(schema, CONF_MANUFACTURER, selector.TextSelector(), default=defaults.get(CONF_MANUFACTURER))
    _add_optional(schema, CONF_MODEL, selector.TextSelector(), default=defaults.get(CONF_MODEL))
    _add_optional(schema, CONF_NOTES, selector.TextSelector(selector.TextSelectorConfig(multiline=True)), default=defaults.get(CONF_NOTES))
    _add_optional(schema, CONF_INSTALL_DATE, selector.DateSelector(), default=defaults.get(CONF_INSTALL_DATE))
    _add_optional(schema, CONF_LAST_SERVICED_DATE, selector.DateSelector(), default=defaults.get(CONF_LAST_SERVICED_DATE))
    _add_optional(schema, CONF_NEXT_DUE_OVERRIDE, selector.DateSelector(), default=defaults.get(CONF_NEXT_DUE_OVERRIDE))
    _add_required(schema, CONF_BASE_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults[CONF_BASE_INTERVAL_DAYS])

    if _task_exists(definition.key, TASK_INSPECTION):
        _add_optional(schema, CONF_INSPECTION_INTERVAL_DAYS, _number_selector(30, 3650, 1), default=defaults.get(CONF_INSPECTION_INTERVAL_DAYS))

    if _task_exists(definition.key, TASK_ANODE):
        _add_optional(schema, CONF_ENABLE_ANODE_TASK, selector.BooleanSelector(), default=defaults.get(CONF_ENABLE_ANODE_TASK, False))
        if defaults.get(CONF_ENABLE_ANODE_TASK):
            _add_optional(schema, CONF_ANODE_INTERVAL_DAYS, _number_selector(180, 3650, 1), default=defaults.get(CONF_ANODE_INTERVAL_DAYS))

    if _show_sensor_section(definition.key):
        _add_optional(schema, CONF_RUNTIME_SENSOR, _entity_selector(["sensor", "number", "input_number"]), default=defaults.get(CONF_RUNTIME_SENSOR))
        _add_optional(schema, CONF_RUNTIME_THRESHOLD, _number_selector(0, 100000, 1), default=defaults.get(CONF_RUNTIME_THRESHOLD))
        _add_optional(schema, CONF_USAGE_SENSOR, _entity_selector(["sensor", "number", "input_number"]), default=defaults.get(CONF_USAGE_SENSOR))
        _add_optional(schema, CONF_USAGE_THRESHOLD, _number_selector(0, 100000, 1), default=defaults.get(CONF_USAGE_THRESHOLD))

    if supports_battery(definition, power_type):
        _add_optional(schema, CONF_BATTERY_SENSOR, _entity_selector(["sensor", "number"]), default=defaults.get(CONF_BATTERY_SENSOR))
        _add_optional(schema, CONF_BATTERY_THRESHOLD, _number_selector(1, 100, 1), default=defaults.get(CONF_BATTERY_THRESHOLD, DEFAULT_BATTERY_THRESHOLD))
        _add_optional(schema, CONF_BATTERY_INTERVAL_DAYS, _number_selector(30, 730, 1), default=defaults.get(CONF_BATTERY_INTERVAL_DAYS))

    if _task_exists(definition.key, TASK_REPLACEMENT):
        _add_optional(schema, CONF_REPLACEMENT_INTERVAL_DAYS, _number_selector(365, 7300, 1), default=defaults.get(CONF_REPLACEMENT_INTERVAL_DAYS))

    return vol.Schema(schema)


def _defaults_for_new_asset(equipment_type: str) -> dict[str, Any]:
    definition = get_equipment_definition(equipment_type)
    defaults: dict[str, Any] = {
        CONF_EQUIPMENT_TYPE: equipment_type,
        CONF_BASE_INTERVAL_DAYS: next(task.default_interval_days for task in definition.tasks if task.key == definition.primary_task_key),
        CONF_POWER_TYPE: definition.default_power_type,
        CONF_BATTERY_THRESHOLD: DEFAULT_BATTERY_THRESHOLD,
    }
    for task in definition.tasks:
        if task.key == TASK_INSPECTION:
            defaults[CONF_INSPECTION_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_ANODE:
            defaults[CONF_ENABLE_ANODE_TASK] = False
            defaults[CONF_ANODE_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_BATTERY:
            defaults[CONF_BATTERY_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_REPLACEMENT:
            defaults[CONF_REPLACEMENT_INTERVAL_DAYS] = task.default_interval_days
    return defaults


def _defaults_from_asset(asset) -> dict[str, Any]:
    defaults = {
        CONF_EQUIPMENT_TYPE: asset.equipment_type,
        CONF_ASSET_NAME: asset.name,
        CONF_AREA_ID: asset.area_id,
        CONF_CUSTOM_AREA: None if asset.area_id else asset.area,
        CONF_POWER_TYPE: asset.power_type,
        CONF_MANUFACTURER: asset.manufacturer,
        CONF_MODEL: asset.model,
        CONF_NOTES: asset.notes,
        CONF_INSTALL_DATE: asset.install_date,
        CONF_LAST_SERVICED_DATE: asset.last_serviced_date,
        CONF_BASE_INTERVAL_DAYS: next(task.base_interval_days for task in asset.tasks if task.key == asset.primary_task_key),
        CONF_NEXT_DUE_OVERRIDE: next(
            (task.next_due_override for task in asset.tasks if task.key == asset.primary_task_key),
            None,
        ),
    }
    for task in asset.tasks:
        if task.key == TASK_INSPECTION:
            defaults[CONF_INSPECTION_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_ANODE:
            defaults[CONF_ENABLE_ANODE_TASK] = True
            defaults[CONF_ANODE_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_BATTERY:
            defaults[CONF_BATTERY_INTERVAL_DAYS] = task.base_interval_days
            if task.sensor_links:
                defaults[CONF_BATTERY_SENSOR] = task.sensor_links[0].entity_id
                defaults[CONF_BATTERY_THRESHOLD] = task.sensor_links[0].threshold
        elif task.key == TASK_REPLACEMENT:
            defaults[CONF_REPLACEMENT_INTERVAL_DAYS] = task.base_interval_days
        for link in task.sensor_links:
            if link.role == "runtime":
                defaults[CONF_RUNTIME_SENSOR] = link.entity_id
                defaults[CONF_RUNTIME_THRESHOLD] = link.threshold
            elif link.role == "usage":
                defaults[CONF_USAGE_SENSOR] = link.entity_id
                defaults[CONF_USAGE_THRESHOLD] = link.threshold
    return defaults


def _sanitize_asset_input(user_input: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(user_input)
    cleaned[CONF_ASSET_NAME] = str(cleaned.get(CONF_ASSET_NAME, "")).strip()
    cleaned[CONF_EQUIPMENT_TYPE] = str(cleaned[CONF_EQUIPMENT_TYPE])

    for key in (
        CONF_MANUFACTURER,
        CONF_MODEL,
        CONF_NOTES,
        CONF_CUSTOM_AREA,
        CONF_AREA_ID,
        CONF_RUNTIME_SENSOR,
        CONF_USAGE_SENSOR,
        CONF_BATTERY_SENSOR,
    ):
        value = cleaned.get(key)
        if value in (None, ""):
            cleaned.pop(key, None)
        else:
            cleaned[key] = str(value).strip()

    for key in (CONF_INSTALL_DATE, CONF_LAST_SERVICED_DATE, CONF_NEXT_DUE_OVERRIDE):
        value = cleaned.get(key)
        if value in (None, ""):
            cleaned.pop(key, None)
        elif not isinstance(value, date):
            cleaned[key] = date.fromisoformat(str(value))

    for key in (
        CONF_BASE_INTERVAL_DAYS,
        CONF_INSPECTION_INTERVAL_DAYS,
        CONF_ANODE_INTERVAL_DAYS,
        CONF_BATTERY_INTERVAL_DAYS,
        CONF_REPLACEMENT_INTERVAL_DAYS,
        CONF_RUNTIME_THRESHOLD,
        CONF_USAGE_THRESHOLD,
    ):
        value = cleaned.get(key)
        if value in (None, ""):
            cleaned.pop(key, None)
        else:
            cleaned[key] = int(value)

    if cleaned.get(CONF_BATTERY_THRESHOLD) not in (None, ""):
        cleaned[CONF_BATTERY_THRESHOLD] = float(cleaned[CONF_BATTERY_THRESHOLD])
    else:
        cleaned.pop(CONF_BATTERY_THRESHOLD, None)

    if CONF_POWER_TYPE in cleaned and cleaned[CONF_POWER_TYPE] in (None, ""):
        cleaned.pop(CONF_POWER_TYPE, None)

    cleaned[CONF_ENABLE_ANODE_TASK] = bool(cleaned.get(CONF_ENABLE_ANODE_TASK, False))
    return cleaned


def _add_required(schema: dict[Any, Any], key: str, field_selector: Any, *, default: Any) -> None:
    schema[vol.Required(key, default=default)] = field_selector


def _add_optional(schema: dict[Any, Any], key: str, field_selector: Any, *, default: Any | None = None) -> None:
    if default is None:
        schema[vol.Optional(key)] = field_selector
    else:
        schema[vol.Optional(key, default=default)] = field_selector


def _number_selector(min_value: int | float, max_value: int | float, step: int | float):
    return selector.NumberSelector(
        selector.NumberSelectorConfig(min=min_value, max=max_value, step=step, mode=selector.NumberSelectorMode.BOX)
    )


def _entity_selector(domains: list[str]):
    return selector.EntitySelector(selector.EntitySelectorConfig(domain=domains))


def _equipment_selector():
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=definition.key, label=definition.label)
                for definition in get_supported_definitions()
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _power_selector(definition):
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=power_type, label=POWER_TYPE_LABELS[power_type])
                for power_type in definition.supported_power_types
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _asset_select_schema(assets) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_ASSET_ID): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[selector.SelectOptionDict(value=asset.asset_id, label=asset.name) for asset in assets],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )


def _equipment_summary_text(assets) -> str:
    if not assets:
        return "No equipment has been added yet."
    return "\n".join(
        f"- {asset.name} | {asset.equipment_type.replace('_', ' ')} | "
        f"{asset.power_type.replace('_', ' ')} | {asset.area or 'No area'} | "
        f"{', '.join(task.title for task in asset.tasks)}"
        for asset in assets
    )


def _load_entry_assets(config_entry):
    return load_assets(config_entry.options.get(CONF_ASSETS, config_entry.data.get(CONF_ASSETS, [])))


def _primary_task_label(equipment_type: str) -> str:
    definition = get_equipment_definition(equipment_type)
    return next(task.title for task in definition.tasks if task.key == definition.primary_task_key)


def _task_exists(equipment_type: str, task_key: str) -> bool:
    definition = get_equipment_definition(equipment_type)
    return any(task.key == task_key for task in definition.tasks)


def _show_sensor_section(equipment_type: str) -> bool:
    return equipment_type != "fire_alarms"


def _action_selector(options: list[tuple[str, str]]):
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[selector.SelectOptionDict(value=value, label=label) for value, label in options],
            mode=selector.SelectSelectorMode.LIST,
        )
    )
