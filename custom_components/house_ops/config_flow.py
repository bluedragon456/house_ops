"""Config flow for HouseOps."""
from __future__ import annotations

from datetime import date
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

_OPTIONAL_TEXT_FIELDS = (
    CONF_AREA,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_NOTES,
)
_OPTIONAL_ENTITY_FIELDS = (
    CONF_RUNTIME_SENSOR,
    CONF_USAGE_SENSOR,
    CONF_BATTERY_SENSOR,
)
_OPTIONAL_DATE_FIELDS = (CONF_INSTALL_DATE,)
_OPTIONAL_INT_FIELDS = (
    CONF_RUNTIME_THRESHOLD,
    CONF_USAGE_THRESHOLD,
    CONF_BATTERY_INTERVAL_DAYS,
)
_OPTIONAL_FLOAT_FIELDS = (CONF_BATTERY_THRESHOLD,)


def _asset_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the asset form schema with Home Assistant-safe defaults."""
    defaults = dict(defaults or {})
    equipment_type = str(defaults.get(CONF_EQUIPMENT_TYPE, EQUIPMENT_TYPE_FURNACE))

    schema: dict[Any, Any] = {}
    _add_required(
        schema,
        CONF_EQUIPMENT_TYPE,
        selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value=EQUIPMENT_TYPE_FURNACE, label="Furnace"),
                    selector.SelectOptionDict(value=EQUIPMENT_TYPE_WATER_HEATER, label="Water heater"),
                    selector.SelectOptionDict(value=EQUIPMENT_TYPE_FIRE_ALARMS, label="Fire alarms"),
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        default=equipment_type,
    )
    _add_required(
        schema,
        CONF_ASSET_NAME,
        selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)),
        default=str(defaults.get(CONF_ASSET_NAME, "")),
    )

    _add_optional_text(schema, CONF_AREA, defaults.get(CONF_AREA))
    _add_optional_text(schema, CONF_MANUFACTURER, defaults.get(CONF_MANUFACTURER))
    _add_optional_text(schema, CONF_MODEL, defaults.get(CONF_MODEL))
    _add_optional_date(schema, CONF_INSTALL_DATE, defaults.get(CONF_INSTALL_DATE))
    _add_required(
        schema,
        CONF_LAST_SERVICED,
        selector.DateSelector(),
        default=_normalize_date_default(defaults.get(CONF_LAST_SERVICED)) or date.today(),
    )
    _add_required(
        schema,
        CONF_BASE_INTERVAL_DAYS,
        _number_selector(min_value=1, max_value=3650, step=1),
        default=int(defaults.get(CONF_BASE_INTERVAL_DAYS, _default_base_interval(equipment_type))),
    )
    _add_optional_text(
        schema,
        CONF_NOTES,
        defaults.get(CONF_NOTES),
        config=selector.TextSelectorConfig(multiline=True, type=selector.TextSelectorType.TEXT),
    )
    _add_optional_entity(schema, CONF_RUNTIME_SENSOR, defaults.get(CONF_RUNTIME_SENSOR))
    _add_optional_number(
        schema,
        CONF_RUNTIME_THRESHOLD,
        defaults.get(CONF_RUNTIME_THRESHOLD),
        min_value=0,
        max_value=100000,
        step=1,
    )
    _add_optional_entity(schema, CONF_USAGE_SENSOR, defaults.get(CONF_USAGE_SENSOR))
    _add_optional_number(
        schema,
        CONF_USAGE_THRESHOLD,
        defaults.get(CONF_USAGE_THRESHOLD),
        min_value=0,
        max_value=100000,
        step=1,
    )
    _add_optional_entity(schema, CONF_BATTERY_SENSOR, defaults.get(CONF_BATTERY_SENSOR))
    _add_optional_number(
        schema,
        CONF_BATTERY_THRESHOLD,
        defaults.get(CONF_BATTERY_THRESHOLD, DEFAULT_BATTERY_THRESHOLD),
        min_value=1,
        max_value=100,
        step=1,
    )
    _add_optional(
        schema,
        CONF_ENABLE_ANODE_TASK,
        selector.BooleanSelector(),
        default=bool(defaults.get(CONF_ENABLE_ANODE_TASK, equipment_type == EQUIPMENT_TYPE_WATER_HEATER)),
    )
    _add_optional_number(
        schema,
        CONF_BATTERY_INTERVAL_DAYS,
        defaults.get(CONF_BATTERY_INTERVAL_DAYS, 180),
        min_value=30,
        max_value=730,
        step=1,
    )

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
    """Flatten an asset into selector-safe defaults."""
    defaults: dict[str, Any] = {
        CONF_ASSET_NAME: asset.name,
        CONF_AREA: asset.area,
        CONF_EQUIPMENT_TYPE: asset.equipment_type,
        CONF_MANUFACTURER: asset.manufacturer,
        CONF_MODEL: asset.model,
        CONF_INSTALL_DATE: asset.install_date,
        CONF_LAST_SERVICED: asset.last_serviced or date.today(),
        CONF_BASE_INTERVAL_DAYS: asset.base_interval_days,
        CONF_NOTES: asset.notes,
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


def _sanitize_asset_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Normalize config-flow input before asset creation."""
    cleaned = dict(user_input)

    cleaned[CONF_ASSET_NAME] = str(cleaned[CONF_ASSET_NAME]).strip()
    cleaned[CONF_EQUIPMENT_TYPE] = str(cleaned[CONF_EQUIPMENT_TYPE])
    cleaned[CONF_BASE_INTERVAL_DAYS] = int(cleaned[CONF_BASE_INTERVAL_DAYS])
    cleaned[CONF_LAST_SERVICED] = _normalize_date_value(cleaned[CONF_LAST_SERVICED])
    cleaned[CONF_ENABLE_ANODE_TASK] = bool(cleaned.get(CONF_ENABLE_ANODE_TASK, False))

    for key in _OPTIONAL_TEXT_FIELDS:
        value = cleaned.get(key)
        if value is None:
            cleaned.pop(key, None)
            continue
        text = str(value).strip()
        if text:
            cleaned[key] = text
        else:
            cleaned.pop(key, None)

    for key in _OPTIONAL_ENTITY_FIELDS:
        value = cleaned.get(key)
        if value:
            cleaned[key] = str(value)
        else:
            cleaned.pop(key, None)

    for key in _OPTIONAL_DATE_FIELDS:
        value = cleaned.get(key)
        normalized = _normalize_date_value(value)
        if normalized is None:
            cleaned.pop(key, None)
        else:
            cleaned[key] = normalized

    for key in _OPTIONAL_INT_FIELDS:
        value = cleaned.get(key)
        normalized = _normalize_number_value(value, cast=int)
        if normalized is None:
            cleaned.pop(key, None)
        else:
            cleaned[key] = normalized

    for key in _OPTIONAL_FLOAT_FIELDS:
        value = cleaned.get(key)
        normalized = _normalize_number_value(value, cast=float)
        if normalized is None:
            cleaned.pop(key, None)
        else:
            cleaned[key] = normalized

    return cleaned


def _normalize_date_default(value: Any) -> date | None:
    """Return a date default Home Assistant can render."""
    return _normalize_date_value(value)


def _normalize_date_value(value: Any) -> date | None:
    """Normalize date selector values from HA."""
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _normalize_number_value(value: Any, *, cast: type[int] | type[float]) -> int | float | None:
    """Normalize optional numeric fields from HA selectors."""
    if value in (None, ""):
        return None
    return cast(value)


def _number_selector(*, min_value: int | float, max_value: int | float, step: int | float):
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=min_value,
            max=max_value,
            step=step,
            mode=selector.NumberSelectorMode.BOX,
        )
    )


def _entity_selector() -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain=["sensor", "number", "input_number"])
    )


def _battery_entity_selector() -> selector.EntitySelector:
    return selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "number"]))


def _add_required(schema: dict[Any, Any], key: str, field_selector: Any, *, default: Any) -> None:
    schema[vol.Required(key, default=default)] = field_selector


def _add_optional(schema: dict[Any, Any], key: str, field_selector: Any, *, default: Any | None = None) -> None:
    if default is None:
        schema[vol.Optional(key)] = field_selector
        return
    schema[vol.Optional(key, default=default)] = field_selector


def _add_optional_text(
    schema: dict[Any, Any],
    key: str,
    default: Any,
    *,
    config: selector.TextSelectorConfig | None = None,
) -> None:
    text_selector = selector.TextSelector(
        config or selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
    )
    normalized = str(default).strip() if default not in (None, "") else None
    _add_optional(schema, key, text_selector, default=normalized)


def _add_optional_date(schema: dict[Any, Any], key: str, default: Any) -> None:
    _add_optional(schema, key, selector.DateSelector(), default=_normalize_date_default(default))


def _add_optional_entity(schema: dict[Any, Any], key: str, default: Any) -> None:
    entity_selector = _battery_entity_selector() if key == CONF_BATTERY_SENSOR else _entity_selector()
    normalized = str(default) if default not in (None, "") else None
    _add_optional(schema, key, entity_selector, default=normalized)


def _add_optional_number(
    schema: dict[Any, Any],
    key: str,
    default: Any,
    *,
    min_value: int | float,
    max_value: int | float,
    step: int | float,
) -> None:
    _add_optional(
        schema,
        key,
        _number_selector(min_value=min_value, max_value=max_value, step=step),
        default=_normalize_number_value(default, cast=float if isinstance(default, float) else int)
        if default not in (None, "")
        else None,
    )


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
            instance_name = str(user_input[CONF_INSTANCE_NAME]).strip()
            self._instance_name = instance_name or DEFAULT_INSTANCE_NAME
            return await self.async_step_asset()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_INSTANCE_NAME, default=DEFAULT_INSTANCE_NAME): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                }
            ),
        )

    async def async_step_asset(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            cleaned = _sanitize_asset_input(user_input)
            if not cleaned[CONF_ASSET_NAME]:
                errors[CONF_ASSET_NAME] = "required"
            else:
                asset = build_asset_from_input(cleaned)
                return self.async_create_entry(
                    title=self._instance_name,
                    data={
                        CONF_INSTANCE_NAME: self._instance_name,
                        CONF_ASSETS: dump_assets([asset]),
                    },
                )

        defaults = {
            CONF_EQUIPMENT_TYPE: EQUIPMENT_TYPE_FURNACE,
            CONF_LAST_SERVICED: date.today(),
            CONF_BASE_INTERVAL_DAYS: 90,
            CONF_BATTERY_THRESHOLD: DEFAULT_BATTERY_THRESHOLD,
            CONF_BATTERY_INTERVAL_DAYS: 180,
        }
        return self.async_show_form(step_id="asset", data_schema=_asset_schema(defaults), errors=errors)


class HouseOpsOptionsFlow(config_entries.OptionsFlow):
    """Manage assets inside HouseOps."""

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry
        self._selected_asset_id: str | None = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        assets = load_assets(
            self._config_entry.options.get(CONF_ASSETS, self._config_entry.data.get(CONF_ASSETS, []))
        )
        menu = ["add_asset"]
        if assets:
            menu.append("edit_asset")
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_add_asset(self, user_input: dict[str, Any] | None = None):
        return await self._async_handle_asset_form(user_input, existing_asset=None)

    async def async_step_edit_asset(self, user_input: dict[str, Any] | None = None):
        assets = load_assets(
            self._config_entry.options.get(CONF_ASSETS, self._config_entry.data.get(CONF_ASSETS, []))
        )
        if user_input is not None:
            self._selected_asset_id = str(user_input[CONF_ASSET_ID])
            return await self.async_step_edit_asset_details()

        options = [selector.SelectOptionDict(value=asset.asset_id, label=asset.name) for asset in assets]
        return self.async_show_form(
            step_id="edit_asset",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ASSET_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def async_step_edit_asset_details(self, user_input: dict[str, Any] | None = None):
        assets = load_assets(
            self._config_entry.options.get(CONF_ASSETS, self._config_entry.data.get(CONF_ASSETS, []))
        )
        asset = find_asset(assets, self._selected_asset_id or "")
        if asset is None:
            return self.async_abort(reason="asset_not_found")
        return await self._async_handle_asset_form(user_input, existing_asset=asset)

    async def _async_handle_asset_form(self, user_input: dict[str, Any] | None, existing_asset=None):
        assets = load_assets(
            self._config_entry.options.get(CONF_ASSETS, self._config_entry.data.get(CONF_ASSETS, []))
        )
        errors: dict[str, str] = {}

        if user_input is not None:
            cleaned = _sanitize_asset_input(user_input)
            if not cleaned[CONF_ASSET_NAME]:
                errors[CONF_ASSET_NAME] = "required"
            else:
                asset = build_asset_from_input(
                    cleaned,
                    existing_assets=assets,
                    existing_asset=existing_asset,
                )
                updated_assets = upsert_asset(assets, asset)
                return self.async_create_entry(title="", data={CONF_ASSETS: dump_assets(updated_assets)})

        defaults = (
            _asset_defaults_from_asset(existing_asset)
            if existing_asset
            else {
                CONF_EQUIPMENT_TYPE: EQUIPMENT_TYPE_FURNACE,
                CONF_LAST_SERVICED: date.today(),
                CONF_BASE_INTERVAL_DAYS: 90,
                CONF_BATTERY_THRESHOLD: DEFAULT_BATTERY_THRESHOLD,
                CONF_BATTERY_INTERVAL_DAYS: 180,
            }
        )
        step_id = "edit_asset_details" if existing_asset else "add_asset"
        return self.async_show_form(step_id=step_id, data_schema=_asset_schema(defaults), errors=errors)
