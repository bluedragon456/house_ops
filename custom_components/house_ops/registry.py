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
    CATALOG_TIER_ADVANCED,
    CATALOG_TIER_BASIC,
    CONF_ANODE_INTERVAL_DAYS,
    CONF_AREA_ID,
    CONF_ASSET_NAME,
    CONF_BASE_INTERVAL_DAYS,
    CONF_BATTERY_INTERVAL_DAYS,
    CONF_BATTERY_SENSOR,
    CONF_BATTERY_SERVICE_MODE,
    CONF_BATTERY_THRESHOLD,
    CONF_CATEGORY,
    CONF_CATALOG_TIER,
    CONF_CONTACT_CLEANING_INTERVAL_DAYS,
    CONF_CUSTOM_AREA,
    CONF_CUSTOM_CATEGORY,
    CONF_DOCK_AIR_PATH_INTERVAL_DAYS,
    CONF_DOCK_CLEAN_WATER_TANK_INTERVAL_DAYS,
    CONF_DOCK_DIRTY_WATER_TANK_INTERVAL_DAYS,
    CONF_DOCK_DUST_BAG_INTERVAL_DAYS,
    CONF_DOCK_WASH_TRAY_INTERVAL_DAYS,
    CONF_DOCK_WATER_FILTER_INTERVAL_DAYS,
    CONF_DUST_BIN_INTERVAL_DAYS,
    CONF_DWELLING_TYPE,
    CONF_ENABLE_ANODE_TASK,
    CONF_EQUIPMENT_TYPE,
    CONF_FILTER_INTERVAL_DAYS,
    CONF_HOME_PROFILE,
    CONF_INSTALL_DATE,
    CONF_INSPECTION_INTERVAL_DAYS,
    CONF_LAST_SERVICED,
    CONF_LAST_SERVICED_DATE,
    CONF_MAIN_BRUSH_INTERVAL_DAYS,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_MOP_SERVICE_INTERVAL_DAYS,
    CONF_NEXT_DUE_OVERRIDE,
    CONF_NOTES,
    CONF_OWNERSHIP_TYPE,
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
    CONF_TASK_INTERVAL_DAYS,
    CONF_TASK_LAST_SERVICED_DATE,
    CONF_TASK_NEXT_DUE_OVERRIDE,
    CONF_TASK_TITLE,
    CONF_USAGE_SENSOR,
    CONF_USAGE_THRESHOLD,
    CONF_WATER_TANK_INTERVAL_DAYS,
    CONF_WHEEL_CLEAN_INTERVAL_DAYS,
    DEFAULT_BATTERY_THRESHOLD,
    DEFAULT_FIRE_ALARM_BATTERY_INTERVAL_DAYS,
    DEFAULT_FIRE_ALARM_REPLACEMENT_INTERVAL_DAYS,
    DEFAULT_WATER_HEATER_ANODE_INTERVAL_DAYS,
    DWELLING_TYPE_SINGLE_FAMILY,
    EQUIPMENT_TYPE_CUSTOM,
    EQUIPMENT_TYPE_ROBOT_VACUUM,
    OWNERSHIP_TYPE_OWNER,
    POWER_TYPE_WIRED,
    ROBOT_DOCK_TYPE_AUTO_EMPTY,
    ROBOT_DOCK_TYPE_CHARGE_ONLY,
    ROBOT_DOCK_TYPE_FULL_SERVICE,
    ROBOT_MOP_STYLE_DUAL_PAD,
    ROBOT_MOP_STYLE_NONE,
    ROBOT_MOP_STYLE_SINGLE_PAD_OR_ROLLER,
    SENSOR_ROLE_BATTERY,
    SENSOR_ROLE_RUNTIME,
    SENSOR_ROLE_USAGE,
    TASK_ANODE,
    TASK_BATTERY,
    TASK_CONTACT_CLEANING,
    TASK_DOCK_AIR_PATH,
    TASK_DOCK_CLEAN_WATER_TANK,
    TASK_DOCK_DIRTY_WATER_TANK,
    TASK_DOCK_DUST_BAG,
    TASK_DOCK_WASH_TRAY,
    TASK_DOCK_WATER_FILTER,
    TASK_DUST_BIN,
    TASK_FILTER,
    TASK_FLUSH,
    TASK_INSPECTION,
    TASK_MAIN_BRUSH,
    TASK_MOP_SERVICE,
    TASK_REPLACEMENT,
    TASK_SENSOR_CLEANING,
    TASK_SERVICE,
    TASK_SIDE_BRUSH,
    TASK_TEST,
    TASK_WATER_TANK_CLEANING,
    TASK_WHEEL_CLEAN,
)
from .equipment_catalog import (
    BATTERY_SERVICE_MODE_LABELS,
    POWER_TYPE_LABELS,
    available_task_definitions,
    build_custom_definition,
    get_equipment_definition,
)
from .models import Asset, HomeProfile, MaintenanceTask, SensorLink


def load_assets(items: list[dict[str, Any]] | None) -> list[Asset]:
    return [Asset.from_dict(item) for item in items or []]


def dump_assets(assets: list[Asset]) -> list[dict[str, Any]]:
    return [asset.as_dict() for asset in assets]


def load_home_profile(payload: dict[str, Any] | None) -> HomeProfile:
    return HomeProfile.from_dict(payload)


def dump_home_profile(profile: HomeProfile) -> dict[str, str]:
    return profile.as_dict()


def default_home_profile() -> HomeProfile:
    return HomeProfile(dwelling_type=DWELLING_TYPE_SINGLE_FAMILY, ownership_type=OWNERSHIP_TYPE_OWNER)


def build_home_profile_from_input(user_input: dict[str, Any]) -> HomeProfile:
    return HomeProfile(
        dwelling_type=str(user_input[CONF_DWELLING_TYPE]),
        ownership_type=str(user_input[CONF_OWNERSHIP_TYPE]),
    )


def build_asset_from_input(
    hass: HomeAssistant,
    user_input: dict[str, Any],
    *,
    existing_assets: list[Asset] | None = None,
    existing_asset: Asset | None = None,
) -> Asset:
    current_assets = existing_assets or []
    equipment_type = str(user_input[CONF_EQUIPMENT_TYPE])
    if equipment_type == EQUIPMENT_TYPE_CUSTOM:
        return _build_custom_asset_from_input(
            hass,
            user_input,
            existing_assets=current_assets,
            existing_asset=existing_asset,
        )

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
    robot_mop_style = _resolve_robot_mop_style(user_input, existing_asset, equipment_type)
    robot_dock_type = _resolve_robot_dock_type(user_input, existing_asset, equipment_type)

    effective_input = dict(user_input)
    if not effective_input.get(CONF_BATTERY_SENSOR) and derived["battery_sensor"]:
        effective_input[CONF_BATTERY_SENSOR] = derived["battery_sensor"]

    tasks: list[MaintenanceTask] = []
    for task_definition in available_task_definitions(definition, power_type, battery_service_mode):
        if task_definition.key == TASK_ANODE and not include_anode:
            continue
        if not _robot_task_enabled(task_definition.key, equipment_type, robot_mop_style, robot_dock_type):
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
        category=definition.category,
        catalog_tier=definition.tier,
        manufacturer=_clean_optional(user_input.get(CONF_MANUFACTURER)) or derived["manufacturer"],
        model=_clean_optional(user_input.get(CONF_MODEL)) or derived["model"],
        install_date=install_date,
        last_serviced_date=last_serviced_date,
        notes=_clean_optional(user_input.get(CONF_NOTES)),
        primary_task_key=primary_task_key,
        tasks=tasks,
        is_custom=False,
        custom_category=None,
        robot_has_mop=robot_mop_style != ROBOT_MOP_STYLE_NONE if equipment_type == EQUIPMENT_TYPE_ROBOT_VACUUM else False,
        robot_mop_style=robot_mop_style if equipment_type == EQUIPMENT_TYPE_ROBOT_VACUUM else None,
        robot_dock_type=robot_dock_type if equipment_type == EQUIPMENT_TYPE_ROBOT_VACUUM else None,
    )


def _build_custom_asset_from_input(
    hass: HomeAssistant,
    user_input: dict[str, Any],
    *,
    existing_assets: list[Asset],
    existing_asset: Asset | None,
) -> Asset:
    category = _clean_optional(user_input.get(CONF_CUSTOM_CATEGORY) or user_input.get(CONF_CATEGORY)) or "Custom"
    definition = build_custom_definition(str(user_input.get(CONF_ASSET_NAME) or "Custom system"), category)
    source_device = _clean_optional(user_input.get(CONF_SOURCE_ENTITY))
    derived = _derive_source_context(hass, source_device)
    asset_name = _resolve_asset_name(user_input, derived)
    asset_id = existing_asset.asset_id if existing_asset else _generate_asset_id(user_input, existing_assets, asset_name)
    install_date = _as_date(user_input.get(CONF_INSTALL_DATE))
    last_serviced_date = _as_date(user_input.get(CONF_LAST_SERVICED_DATE) or user_input.get(CONF_LAST_SERVICED))
    area_id = _clean_optional(user_input.get(CONF_AREA_ID)) or derived["area_id"]
    area = _resolve_area_name(hass, area_id, user_input.get(CONF_CUSTOM_AREA), existing_asset)
    raw_tasks = user_input.get("custom_tasks") or []
    previous_tasks = {task.key: task for task in (existing_asset.tasks if existing_asset else [])}
    tasks: list[MaintenanceTask] = []

    for idx, raw_task in enumerate(raw_tasks):
        title = str(raw_task.get(CONF_TASK_TITLE, "")).strip()
        if not title:
            continue
        key = _unique_task_key(raw_task.get("key") or title, existing={task.key for task in tasks})
        previous = previous_tasks.get(key)
        interval = int(raw_task.get(CONF_TASK_INTERVAL_DAYS) or raw_task.get(CONF_BASE_INTERVAL_DAYS) or 90)
        tasks.append(
            MaintenanceTask(
                key=key,
                title=title,
                base_interval_days=interval,
                last_serviced_date=_as_date(raw_task.get(CONF_TASK_LAST_SERVICED_DATE)) or (previous.last_serviced_date if previous else last_serviced_date),
                next_due_override=_as_date(raw_task.get(CONF_TASK_NEXT_DUE_OVERRIDE)) or (previous.next_due_override if previous else None),
                snoozed_until=previous.snoozed_until if previous else None,
                sensor_links=[],
                enabled=True,
            )
        )

    if not tasks:
        primary_title = str(user_input.get(CONF_TASK_TITLE) or "Routine service").strip() or "Routine service"
        tasks.append(
            MaintenanceTask(
                key=_unique_task_key(primary_title, existing=set()),
                title=primary_title,
                base_interval_days=int(user_input.get(CONF_BASE_INTERVAL_DAYS) or 90),
                last_serviced_date=last_serviced_date,
                next_due_override=_as_date(user_input.get(CONF_NEXT_DUE_OVERRIDE)),
                sensor_links=[],
                enabled=True,
            )
        )

    primary_task_key = tasks[0].key
    return Asset(
        asset_id=asset_id,
        name=asset_name,
        area=area,
        area_id=area_id,
        source_entity=source_device,
        equipment_type=EQUIPMENT_TYPE_CUSTOM,
        power_type=str(user_input.get(CONF_POWER_TYPE) or definition.default_power_type),
        battery_service_mode=None,
        category=category,
        catalog_tier=str(user_input.get(CONF_CATALOG_TIER) or CATALOG_TIER_ADVANCED),
        manufacturer=_clean_optional(user_input.get(CONF_MANUFACTURER)) or derived["manufacturer"],
        model=_clean_optional(user_input.get(CONF_MODEL)) or derived["model"],
        install_date=install_date,
        last_serviced_date=last_serviced_date,
        notes=_clean_optional(user_input.get(CONF_NOTES)),
        primary_task_key=primary_task_key,
        tasks=tasks,
        is_custom=True,
        custom_category=category,
        robot_has_mop=False,
        robot_mop_style=None,
        robot_dock_type=None,
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
    equipment_label = asset.name if asset.is_custom else get_equipment_definition(asset.equipment_type).label
    power_label = POWER_TYPE_LABELS.get(asset.power_type, asset.power_type.replace("_", " "))
    battery_suffix = ""
    if asset.battery_service_mode in BATTERY_SERVICE_MODE_LABELS:
        battery_suffix = f", {BATTERY_SERVICE_MODE_LABELS[asset.battery_service_mode].lower()}"
    robot_suffix = ""
    if asset.equipment_type == EQUIPMENT_TYPE_ROBOT_VACUUM:
        robot_bits = [_robot_mop_style_label(asset.robot_mop_style), _robot_dock_type_label(asset.robot_dock_type)]
        robot_suffix = f", {', '.join(bit for bit in robot_bits if bit)}"
    category = asset.custom_category or asset.category or "Uncategorized"
    tier = asset.catalog_tier or CATALOG_TIER_BASIC
    system_type = "Custom system" if asset.is_custom else equipment_label
    return (
        f"{asset.name} ({system_type}, {category}, {tier}, {power_label}{battery_suffix}{robot_suffix}) "
        f"in {area}. Tasks: {task_bits or 'none'}."
    )


def load_profile_from_entry(config_entry) -> HomeProfile:
    return load_home_profile(config_entry.options.get(CONF_HOME_PROFILE, config_entry.data.get(CONF_HOME_PROFILE)))


def _interval_for_task(task_key: str, user_input: dict[str, Any], previous: MaintenanceTask | None) -> int:
    interval_map = {
        TASK_FILTER: CONF_BASE_INTERVAL_DAYS,
        TASK_FLUSH: CONF_BASE_INTERVAL_DAYS,
        TASK_TEST: CONF_BASE_INTERVAL_DAYS,
        TASK_SERVICE: CONF_BASE_INTERVAL_DAYS,
        TASK_INSPECTION: CONF_INSPECTION_INTERVAL_DAYS,
        TASK_ANODE: CONF_ANODE_INTERVAL_DAYS,
        TASK_BATTERY: CONF_BATTERY_INTERVAL_DAYS,
        TASK_REPLACEMENT: CONF_REPLACEMENT_INTERVAL_DAYS,
        TASK_DUST_BIN: CONF_DUST_BIN_INTERVAL_DAYS,
        TASK_MAIN_BRUSH: CONF_MAIN_BRUSH_INTERVAL_DAYS,
        TASK_SIDE_BRUSH: CONF_SIDE_BRUSH_INTERVAL_DAYS,
        TASK_WHEEL_CLEAN: CONF_WHEEL_CLEAN_INTERVAL_DAYS,
        TASK_SENSOR_CLEANING: CONF_SENSOR_CLEANING_INTERVAL_DAYS,
        TASK_CONTACT_CLEANING: CONF_CONTACT_CLEANING_INTERVAL_DAYS,
        TASK_MOP_SERVICE: CONF_MOP_SERVICE_INTERVAL_DAYS,
        TASK_WATER_TANK_CLEANING: CONF_WATER_TANK_INTERVAL_DAYS,
        TASK_DOCK_DUST_BAG: CONF_DOCK_DUST_BAG_INTERVAL_DAYS,
        TASK_DOCK_AIR_PATH: CONF_DOCK_AIR_PATH_INTERVAL_DAYS,
        TASK_DOCK_CLEAN_WATER_TANK: CONF_DOCK_CLEAN_WATER_TANK_INTERVAL_DAYS,
        TASK_DOCK_DIRTY_WATER_TANK: CONF_DOCK_DIRTY_WATER_TANK_INTERVAL_DAYS,
        TASK_DOCK_WASH_TRAY: CONF_DOCK_WASH_TRAY_INTERVAL_DAYS,
        TASK_DOCK_WATER_FILTER: CONF_DOCK_WATER_FILTER_INTERVAL_DAYS,
    }
    defaults = {
        TASK_INSPECTION: 365,
        TASK_ANODE: DEFAULT_WATER_HEATER_ANODE_INTERVAL_DAYS,
        TASK_BATTERY: DEFAULT_FIRE_ALARM_BATTERY_INTERVAL_DAYS,
        TASK_REPLACEMENT: DEFAULT_FIRE_ALARM_REPLACEMENT_INTERVAL_DAYS,
        TASK_SERVICE: int(user_input.get(CONF_BASE_INTERVAL_DAYS, 180)),
        TASK_FILTER: int(user_input.get(CONF_BASE_INTERVAL_DAYS, 90)),
        TASK_DUST_BIN: 3,
        TASK_MAIN_BRUSH: 14,
        TASK_SIDE_BRUSH: 14,
        TASK_WHEEL_CLEAN: 14,
        TASK_SENSOR_CLEANING: 30,
        TASK_CONTACT_CLEANING: 30,
        TASK_MOP_SERVICE: 7,
        TASK_WATER_TANK_CLEANING: 14,
        TASK_DOCK_DUST_BAG: 60,
        TASK_DOCK_AIR_PATH: 30,
        TASK_DOCK_CLEAN_WATER_TANK: 30,
        TASK_DOCK_DIRTY_WATER_TANK: 7,
        TASK_DOCK_WASH_TRAY: 14,
        TASK_DOCK_WATER_FILTER: 30,
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


def _resolve_robot_mop_style(
    user_input: dict[str, Any],
    existing_asset: Asset | None,
    equipment_type: str,
) -> str | None:
    if equipment_type != EQUIPMENT_TYPE_ROBOT_VACUUM:
        return None
    requested = _clean_optional(user_input.get(CONF_ROBOT_MOP_STYLE))
    if requested:
        return requested
    if bool(user_input.get(CONF_ROBOT_HAS_MOP)):
        return ROBOT_MOP_STYLE_SINGLE_PAD_OR_ROLLER
    if existing_asset and existing_asset.robot_mop_style:
        return existing_asset.robot_mop_style
    return ROBOT_MOP_STYLE_NONE


def _resolve_robot_dock_type(
    user_input: dict[str, Any],
    existing_asset: Asset | None,
    equipment_type: str,
) -> str | None:
    if equipment_type != EQUIPMENT_TYPE_ROBOT_VACUUM:
        return None
    requested = _clean_optional(user_input.get(CONF_ROBOT_DOCK_TYPE))
    if requested:
        return requested
    if existing_asset and existing_asset.robot_dock_type:
        return existing_asset.robot_dock_type
    return ROBOT_DOCK_TYPE_CHARGE_ONLY


def _robot_task_enabled(task_key: str, equipment_type: str, mop_style: str | None, dock_type: str | None) -> bool:
    if equipment_type != EQUIPMENT_TYPE_ROBOT_VACUUM:
        return True
    if task_key in {TASK_MOP_SERVICE, TASK_WATER_TANK_CLEANING}:
        return mop_style not in (None, ROBOT_MOP_STYLE_NONE)
    if task_key in {TASK_DOCK_DUST_BAG, TASK_DOCK_AIR_PATH}:
        return dock_type in {ROBOT_DOCK_TYPE_AUTO_EMPTY, ROBOT_DOCK_TYPE_FULL_SERVICE}
    if task_key in {
        TASK_DOCK_CLEAN_WATER_TANK,
        TASK_DOCK_DIRTY_WATER_TANK,
        TASK_DOCK_WASH_TRAY,
        TASK_DOCK_WATER_FILTER,
    }:
        return dock_type == ROBOT_DOCK_TYPE_FULL_SERVICE
    return True


def _robot_mop_style_label(value: str | None) -> str | None:
    labels = {
        ROBOT_MOP_STYLE_NONE: "No mop",
        ROBOT_MOP_STYLE_SINGLE_PAD_OR_ROLLER: "Single pad / roller mop",
        ROBOT_MOP_STYLE_DUAL_PAD: "Dual spinning pads",
    }
    return labels.get(value)


def _robot_dock_type_label(value: str | None) -> str | None:
    labels = {
        ROBOT_DOCK_TYPE_CHARGE_ONLY: "Charging dock",
        ROBOT_DOCK_TYPE_AUTO_EMPTY: "Auto-empty dock",
        ROBOT_DOCK_TYPE_FULL_SERVICE: "Advanced service dock",
    }
    return labels.get(value)


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


def _unique_task_key(seed: str, existing: set[str]) -> str:
    base = slugify(seed) or TASK_SERVICE
    candidate = base
    idx = 2
    while candidate in existing:
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
