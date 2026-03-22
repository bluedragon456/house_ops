"""Registry helpers for HouseOps assets."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

from .const import (
    BATTERY_SERVICE_REPLACEABLE,
    CONF_ANODE_INTERVAL_DAYS,
    CONF_AREA_ID,
    CONF_ASSET_NAME,
    CONF_BASE_INTERVAL_DAYS,
    CONF_BATTERY_INTERVAL_DAYS,
    CONF_BATTERY_SENSOR,
    CONF_BATTERY_SERVICE_MODE,
    CONF_BATTERY_THRESHOLD,
    CONF_CUSTOM_AREA,
    CONF_ENABLE_ANODE_TASK,
    CONF_EQUIPMENT_TYPE,
    CONF_INSTALL_DATE,
    CONF_INSPECTION_INTERVAL_DAYS,
    CONF_LAST_SERVICED,
    CONF_LAST_SERVICED_DATE,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_NEXT_DUE_OVERRIDE,
    CONF_NOTES,
    CONF_POWER_TYPE,
    CONF_REPLACEMENT_INTERVAL_DAYS,
    CONF_RUNTIME_SENSOR,
    CONF_RUNTIME_THRESHOLD,
    CONF_SOURCE_ENTITY,
    CONF_USAGE_SENSOR,
    CONF_USAGE_THRESHOLD,
    DEFAULT_BATTERY_THRESHOLD,
    DEFAULT_FIRE_ALARM_BATTERY_INTERVAL_DAYS,
    DEFAULT_FIRE_ALARM_REPLACEMENT_INTERVAL_DAYS,
    DEFAULT_WATER_HEATER_ANODE_INTERVAL_DAYS,
    SENSOR_ROLE_BATTERY,
    SENSOR_ROLE_RUNTIME,
    SENSOR_ROLE_USAGE,
    TASK_ANODE,
    TASK_BATTERY,
    TASK_FILTER,
    TASK_FLUSH,
    TASK_INSPECTION,
    TASK_REPLACEMENT,
    TASK_TEST,
)
from .equipment_catalog import (
    BATTERY_SERVICE_MODE_LABELS,
    POWER_TYPE_LABELS,
    available_task_definitions,
    get_equipment_definition,
)
from .models import Asset, MaintenanceTask, SensorLink


def load_assets(items: list[dict[str, Any]] | None) -> list[Asset]:
    return [Asset.from_dict(item) for item in items or []]


def dump_assets(assets: list[Asset]) -> list[dict[str, Any]]:
    return [asset.as_dict() for asset in assets]


def build_asset_from_input(
    hass: HomeAssistant,
    user_input: dict[str, Any],
    *,
    existing_assets: list[Asset] | None = None,
    existing_asset: Asset | None = None,
) -> Asset:
    current_assets = existing_assets or []
    equipment_type = str(user_input[CONF_EQUIPMENT_TYPE])
    definition = get_equipment_definition(equipment_type)
    power_type = str(user_input.get(CONF_POWER_TYPE) or definition.default_power_type)
    source_device = _clean_optional(user_input.get(CONF_SOURCE_ENTITY))
    derived = _derive_source_context(hass, source_device)
    asset_name = _resolve_asset_name(user_input, derived)
    battery_service_mode = _resolve_battery_service_mode(user_input, existing_asset, equipment_type, power_type)
    asset_id = existing_asset.asset_id if existing_asset else _generate_asset_id(user_input, current_assets, asset_name)
    install_date = _as_date(user_input.get(CONF_INSTALL_DATE))
    last_serviced_date = _as_date(user_input.get(CONF_LAST_SERVICED_DATE) or user_input.get(CONF_LAST_SERVICED))
    area_id = _clean_optional(user_input.get(CONF_AREA_ID)) or derived["area_id"]
    area = _resolve_area_name(hass, area_id, user_input.get(CONF_CUSTOM_AREA), existing_asset)

    previous_tasks = {task.key: task for task in (existing_asset.tasks if existing_asset else [])}
    primary_task_key = definition.primary_task_key
    primary_override = _as_date(user_input.get(CONF_NEXT_DUE_OVERRIDE))
    include_anode = bool(user_input.get(CONF_ENABLE_ANODE_TASK)) or TASK_ANODE in previous_tasks

    effective_input = dict(user_input)
    if not effective_input.get(CONF_BATTERY_SENSOR) and derived["battery_sensor"]:
        effective_input[CONF_BATTERY_SENSOR] = derived["battery_sensor"]

    tasks: list[MaintenanceTask] = []
    for task_definition in available_task_definitions(definition, power_type, battery_service_mode):
        if task_definition.key == TASK_ANODE and not include_anode:
            continue

        previous = previous_tasks.get(task_definition.key)
        interval = _interval_for_task(task_definition.key, effective_input, previous)
        if task_definition.key == TASK_REPLACEMENT:
            task_last_serviced = previous.last_serviced_date if previous and previous.last_serviced_date else install_date
        else:
            task_last_serviced = previous.last_serviced_date if previous and previous.last_serviced_date else last_serviced_date
        override = previous.next_due_override if previous else None
        if task_definition.key == primary_task_key:
            override = primary_override

        tasks.append(
            MaintenanceTask(
                key=task_definition.key,
                title=task_definition.title,
                base_interval_days=interval,
                last_serviced_date=task_last_serviced,
                next_due_override=override,
                snoozed_until=previous.snoozed_until if previous else None,
                sensor_links=_sensor_links_for_task(task_definition.key, effective_input),
                enabled=True,
            )
        )

    return Asset(
        asset_id=asset_id,
        name=asset_name,
        area=area,
        area_id=area_id,
        source_entity=source_device,
        equipment_type=equipment_type,
        power_type=power_type,
        battery_service_mode=battery_service_mode,
        manufacturer=_clean_optional(user_input.get(CONF_MANUFACTURER)) or derived["manufacturer"],
        model=_clean_optional(user_input.get(CONF_MODEL)) or derived["model"],
        install_date=install_date,
        last_serviced_date=last_serviced_date,
        notes=_clean_optional(user_input.get(CONF_NOTES)),
        primary_task_key=primary_task_key,
        tasks=tasks,
    )


def upsert_asset(assets: list[Asset], updated_asset: Asset) -> list[Asset]:
    result = deepcopy(assets)
    for idx, asset in enumerate(result):
        if asset.asset_id == updated_asset.asset_id:
            result[idx] = updated_asset
            return result
    result.append(updated_asset)
    return result


def remove_asset(assets: list[Asset], asset_id: str) -> list[Asset]:
    return [asset for asset in deepcopy(assets) if asset.asset_id != asset_id]


def find_asset(assets: list[Asset], asset_id: str) -> Asset | None:
    return next((asset for asset in assets if asset.asset_id == asset_id), None)


def mark_task_serviced(assets: list[Asset], asset_id: str, task_key: str, serviced_on: date) -> list[Asset]:
    updated = deepcopy(assets)
    for asset in updated:
        if asset.asset_id != asset_id:
            continue
        asset.last_serviced_date = serviced_on
        for task in asset.tasks:
            if task.key == task_key:
                task.last_serviced_date = serviced_on
                task.next_due_override = None
                task.snoozed_until = None
                return updated
    raise ValueError(f"Unknown task '{task_key}' for asset '{asset_id}'")


def snooze_task(assets: list[Asset], asset_id: str, task_key: str, snoozed_until: date) -> list[Asset]:
    updated = deepcopy(assets)
    for asset in updated:
        if asset.asset_id != asset_id:
            continue
        for task in asset.tasks:
            if task.key == task_key:
                task.snoozed_until = snoozed_until
                return updated
    raise ValueError(f"Unknown task '{task_key}' for asset '{asset_id}'")


def asset_summary(asset: Asset) -> str:
    task_bits = ", ".join(f"{task.title} every {task.base_interval_days}d" for task in asset.tasks)
    area = asset.area or "No area"
    definition = get_equipment_definition(asset.equipment_type)
    equipment_label = definition.label
    power_label = POWER_TYPE_LABELS.get(asset.power_type, asset.power_type.replace("_", " "))
    battery_suffix = ""
    if asset.battery_service_mode in BATTERY_SERVICE_MODE_LABELS:
        battery_suffix = f", {BATTERY_SERVICE_MODE_LABELS[asset.battery_service_mode].lower()}"
    return f"{asset.name} ({equipment_label}, {power_label}{battery_suffix}) in {area}. Tasks: {task_bits or 'none'}."


def _interval_for_task(task_key: str, user_input: dict[str, Any], previous: MaintenanceTask | None) -> int:
    interval_map = {
        TASK_FILTER: CONF_BASE_INTERVAL_DAYS,
        TASK_FLUSH: CONF_BASE_INTERVAL_DAYS,
        TASK_TEST: CONF_BASE_INTERVAL_DAYS,
        TASK_INSPECTION: CONF_INSPECTION_INTERVAL_DAYS,
        TASK_ANODE: CONF_ANODE_INTERVAL_DAYS,
        TASK_BATTERY: CONF_BATTERY_INTERVAL_DAYS,
        TASK_REPLACEMENT: CONF_REPLACEMENT_INTERVAL_DAYS,
    }
    defaults = {
        TASK_INSPECTION: 365,
        TASK_ANODE: DEFAULT_WATER_HEATER_ANODE_INTERVAL_DAYS,
        TASK_BATTERY: DEFAULT_FIRE_ALARM_BATTERY_INTERVAL_DAYS,
        TASK_REPLACEMENT: DEFAULT_FIRE_ALARM_REPLACEMENT_INTERVAL_DAYS,
    }
    field = interval_map.get(task_key)
    if field and user_input.get(field) not in (None, ""):
        return int(user_input[field])
    if previous is not None:
        return previous.base_interval_days
    return defaults.get(task_key, int(user_input.get(CONF_BASE_INTERVAL_DAYS, 90)))


def _sensor_links_for_task(task_key: str, user_input: dict[str, Any]) -> list[SensorLink]:
    links: list[SensorLink] = []
    if task_key in {TASK_FILTER, TASK_FLUSH}:
        runtime_sensor = _clean_optional(user_input.get(CONF_RUNTIME_SENSOR))
        usage_sensor = _clean_optional(user_input.get(CONF_USAGE_SENSOR))
        if runtime_sensor:
            links.append(
                SensorLink(
                    role=SENSOR_ROLE_RUNTIME,
                    entity_id=runtime_sensor,
                    threshold=_normalize_threshold(user_input.get(CONF_RUNTIME_THRESHOLD)),
                    accelerate_days=30,
                    label="Runtime",
                )
            )
        if usage_sensor:
            links.append(
                SensorLink(
                    role=SENSOR_ROLE_USAGE,
                    entity_id=usage_sensor,
                    threshold=_normalize_threshold(user_input.get(CONF_USAGE_THRESHOLD)),
                    accelerate_days=30,
                    label="Usage",
                )
            )
    if task_key == TASK_BATTERY:
        sensor = _clean_optional(user_input.get(CONF_BATTERY_SENSOR))
        if sensor:
            links.append(
                SensorLink(
                    role=SENSOR_ROLE_BATTERY,
                    entity_id=sensor,
                    threshold=float(user_input.get(CONF_BATTERY_THRESHOLD, DEFAULT_BATTERY_THRESHOLD)),
                    accelerate_days=365,
                    label="Battery level",
                )
            )
    return links


def _resolve_battery_service_mode(
    user_input: dict[str, Any],
    existing_asset: Asset | None,
    equipment_type: str,
    power_type: str,
) -> str | None:
    if equipment_type != "fire_alarms" or power_type == "wired":
        return None
    requested = _clean_optional(user_input.get(CONF_BATTERY_SERVICE_MODE))
    if requested:
        return requested
    if existing_asset and existing_asset.battery_service_mode:
        return existing_asset.battery_service_mode
    if existing_asset and any(task.key == TASK_BATTERY for task in existing_asset.tasks):
        return BATTERY_SERVICE_REPLACEABLE
    return BATTERY_SERVICE_REPLACEABLE


def _resolve_asset_name(user_input: dict[str, Any], derived: dict[str, str | None]) -> str:
    return str(user_input.get(CONF_ASSET_NAME) or derived["name"] or "").strip()


def _derive_source_context(hass: HomeAssistant, source_device: str | None) -> dict[str, str | None]:
    context = {
        "name": None,
        "manufacturer": None,
        "model": None,
        "area_id": None,
        "battery_sensor": None,
    }
    if not source_device:
        return context

    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    entity_entry = entity_registry.async_get(source_device) if "." in source_device else None
    device_id = source_device
    state = hass.states.get(source_device) if entity_entry else None
    if entity_entry and entity_entry.device_id:
        device_id = entity_entry.device_id
    device_entry = device_registry.async_get(device_id) if device_id else None

    if device_entry:
        context["name"] = device_entry.name_by_user or device_entry.name
        context["manufacturer"] = device_entry.manufacturer
        context["model"] = device_entry.model
        context["area_id"] = device_entry.area_id

    if entity_entry and entity_entry.area_id:
        context["area_id"] = entity_entry.area_id

    if not context["name"] and entity_entry:
        context["name"] = entity_entry.original_name or entity_entry.name
    if not context["name"] and state:
        context["name"] = state.name
    if not context["manufacturer"] and state:
        context["manufacturer"] = state.attributes.get("manufacturer")
    if not context["model"] and state:
        context["model"] = state.attributes.get("model")

    if entity_entry and source_device.startswith(("sensor.", "number.")) and _looks_like_battery_state(state):
        context["battery_sensor"] = source_device
    elif device_id:
        for candidate in er.async_entries_for_device(entity_registry, device_id):
            candidate_state = hass.states.get(candidate.entity_id)
            if candidate.entity_id.startswith(("sensor.", "number.")) and _looks_like_battery_state(candidate_state):
                context["battery_sensor"] = candidate.entity_id
                break

    return context


def _looks_like_battery_state(state: Any) -> bool:
    if state is None:
        return False
    if str(state.attributes.get("device_class", "")).lower() == "battery":
        return True
    return "battery" in str(state.entity_id).lower()


def _resolve_area_name(
    hass: HomeAssistant,
    area_id: str | None,
    custom_area: Any,
    existing_asset: Asset | None,
) -> str | None:
    custom = _clean_optional(custom_area)
    if custom:
        return custom
    if area_id:
        area_registry = ar.async_get(hass)
        area = area_registry.async_get_area(area_id)
        if area:
            return area.name
    if existing_asset:
        return existing_asset.area
    return None


def _generate_asset_id(user_input: dict[str, Any], assets: list[Asset], asset_name: str) -> str:
    base_name = asset_name or _clean_optional(user_input.get(CONF_SOURCE_ENTITY)) or "item"
    base = slugify(f"{user_input[CONF_EQUIPMENT_TYPE]}_{base_name}")
    existing_ids = {asset.asset_id for asset in assets}
    candidate = base
    idx = 2
    while candidate in existing_ids:
        candidate = f"{base}_{idx}"
        idx += 1
    return candidate


def _as_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _clean_optional(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_threshold(value: Any) -> float | None:
    if value in (None, "", "0", "0.0"):
        return None
    return float(value)
