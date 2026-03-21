"""Registry helpers for HouseOps assets."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

from homeassistant.util import slugify

from .const import (
    CONF_AREA,
    CONF_ASSET_NAME,
    CONF_BASE_INTERVAL_DAYS,
    CONF_BATTERY_INTERVAL_DAYS,
    CONF_BATTERY_SENSOR,
    CONF_BATTERY_THRESHOLD,
    CONF_ENABLE_ANODE_TASK,
    CONF_EQUIPMENT_TYPE,
    CONF_INSTALL_DATE,
    CONF_LAST_SERVICED,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_NOTES,
    CONF_RUNTIME_SENSOR,
    CONF_RUNTIME_THRESHOLD,
    CONF_USAGE_SENSOR,
    CONF_USAGE_THRESHOLD,
    DEFAULT_BATTERY_THRESHOLD,
    EQUIPMENT_TYPE_FIRE_ALARMS,
    EQUIPMENT_TYPE_FURNACE,
    EQUIPMENT_TYPE_WATER_HEATER,
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
from .models import Asset, MaintenanceTask, SensorLink


def load_assets(items: list[dict[str, Any]] | None) -> list[Asset]:
    """Load assets from stored dictionaries."""
    return [Asset.from_dict(item) for item in items or []]


def dump_assets(assets: list[Asset]) -> list[dict[str, Any]]:
    """Dump assets to config entry storage dictionaries."""
    return [asset.as_dict() for asset in assets]


def build_asset_from_input(
    user_input: dict[str, Any],
    *,
    existing_assets: list[Asset] | None = None,
    existing_asset: Asset | None = None,
) -> Asset:
    """Build or update an asset from config input."""
    current_assets = existing_assets or []
    asset_id = existing_asset.asset_id if existing_asset else _generate_asset_id(user_input, current_assets)
    last_serviced = _as_date(user_input.get(CONF_LAST_SERVICED))
    install_date = _as_date(user_input.get(CONF_INSTALL_DATE))
    equipment_type = str(user_input[CONF_EQUIPMENT_TYPE])
    base_interval_days = int(user_input[CONF_BASE_INTERVAL_DAYS])

    tasks = _default_tasks(
        equipment_type=equipment_type,
        base_interval_days=base_interval_days,
        last_serviced=last_serviced,
        install_date=install_date,
        runtime_sensor=user_input.get(CONF_RUNTIME_SENSOR),
        runtime_threshold=_normalize_threshold(user_input.get(CONF_RUNTIME_THRESHOLD)),
        usage_sensor=user_input.get(CONF_USAGE_SENSOR),
        usage_threshold=_normalize_threshold(user_input.get(CONF_USAGE_THRESHOLD)),
        battery_sensor=user_input.get(CONF_BATTERY_SENSOR),
        battery_threshold=user_input.get(CONF_BATTERY_THRESHOLD),
        enable_anode_task=bool(user_input.get(CONF_ENABLE_ANODE_TASK)),
        battery_interval_days=int(user_input.get(CONF_BATTERY_INTERVAL_DAYS, 180)),
        previous_tasks=existing_asset.tasks if existing_asset else None,
    )

    return Asset(
        asset_id=asset_id,
        name=str(user_input[CONF_ASSET_NAME]).strip(),
        area=_clean_optional(user_input.get(CONF_AREA)),
        equipment_type=equipment_type,
        manufacturer=_clean_optional(user_input.get(CONF_MANUFACTURER)),
        model=_clean_optional(user_input.get(CONF_MODEL)),
        install_date=install_date,
        last_serviced=last_serviced,
        base_interval_days=base_interval_days,
        notes=_clean_optional(user_input.get(CONF_NOTES)),
        tasks=tasks,
    )


def upsert_asset(assets: list[Asset], updated_asset: Asset) -> list[Asset]:
    """Insert or update an asset in the asset list."""
    result = deepcopy(assets)
    for idx, asset in enumerate(result):
        if asset.asset_id == updated_asset.asset_id:
            result[idx] = updated_asset
            return result
    result.append(updated_asset)
    return result


def find_asset(assets: list[Asset], asset_id: str) -> Asset | None:
    """Find a single asset."""
    return next((asset for asset in assets if asset.asset_id == asset_id), None)


def mark_task_serviced(
    assets: list[Asset],
    asset_id: str,
    task_key: str,
    serviced_on: date,
) -> list[Asset]:
    """Set a task's last serviced date."""
    updated = deepcopy(assets)
    for asset in updated:
        if asset.asset_id != asset_id:
            continue
        asset.last_serviced = serviced_on
        for task in asset.tasks:
            if task.key == task_key:
                task.last_serviced = serviced_on
                task.snoozed_until = None
                return updated
    raise ValueError(f"Unknown task '{task_key}' for asset '{asset_id}'")


def snooze_task(
    assets: list[Asset],
    asset_id: str,
    task_key: str,
    snoozed_until: date,
) -> list[Asset]:
    """Snooze a task until a date."""
    updated = deepcopy(assets)
    for asset in updated:
        if asset.asset_id != asset_id:
            continue
        for task in asset.tasks:
            if task.key == task_key:
                task.snoozed_until = snoozed_until
                return updated
    raise ValueError(f"Unknown task '{task_key}' for asset '{asset_id}'")


def _default_tasks(
    *,
    equipment_type: str,
    base_interval_days: int,
    last_serviced: date | None,
    install_date: date | None,
    runtime_sensor: str | None,
    runtime_threshold: float | None,
    usage_sensor: str | None,
    usage_threshold: float | None,
    battery_sensor: str | None,
    battery_threshold: float | None,
    enable_anode_task: bool,
    battery_interval_days: int,
    previous_tasks: list[MaintenanceTask] | None,
) -> list[MaintenanceTask]:
    by_key = {task.key: task for task in previous_tasks or []}
    seed_date = last_serviced or install_date
    tasks: list[MaintenanceTask] = []

    if equipment_type == EQUIPMENT_TYPE_FURNACE:
        tasks.extend(
            [
                _task(
                    key=TASK_FILTER,
                    title="Filter replacement",
                    base_interval_days=base_interval_days or 90,
                    seed_date=seed_date,
                    previous=by_key.get(TASK_FILTER),
                    sensor_links=_sensor_links(
                        runtime_sensor=runtime_sensor,
                        runtime_threshold=runtime_threshold,
                        usage_sensor=usage_sensor,
                        usage_threshold=usage_threshold,
                    ),
                ),
                _task(
                    key=TASK_INSPECTION,
                    title="Annual inspection",
                    base_interval_days=365,
                    seed_date=seed_date,
                    previous=by_key.get(TASK_INSPECTION),
                ),
            ]
        )
    elif equipment_type == EQUIPMENT_TYPE_WATER_HEATER:
        tasks.append(
            _task(
                key=TASK_FLUSH,
                title="Annual flush",
                base_interval_days=base_interval_days or 365,
                seed_date=seed_date,
                previous=by_key.get(TASK_FLUSH),
                sensor_links=_sensor_links(usage_sensor=usage_sensor, usage_threshold=usage_threshold),
            )
        )
        if enable_anode_task or TASK_ANODE in by_key:
            tasks.append(
                _task(
                    key=TASK_ANODE,
                    title="Anode rod inspection",
                    base_interval_days=730,
                    seed_date=seed_date,
                    previous=by_key.get(TASK_ANODE),
                )
            )
    elif equipment_type == EQUIPMENT_TYPE_FIRE_ALARMS:
        tasks.extend(
            [
                _task(
                    key=TASK_TEST,
                    title="Monthly alarm test",
                    base_interval_days=base_interval_days or 30,
                    seed_date=seed_date,
                    previous=by_key.get(TASK_TEST),
                ),
                _task(
                    key=TASK_BATTERY,
                    title="Battery replacement",
                    base_interval_days=battery_interval_days or 180,
                    seed_date=seed_date,
                    previous=by_key.get(TASK_BATTERY),
                    sensor_links=_battery_links(battery_sensor, battery_threshold),
                ),
                _task(
                    key=TASK_REPLACEMENT,
                    title="Detector replacement advisory",
                    base_interval_days=3650,
                    seed_date=install_date,
                    previous=by_key.get(TASK_REPLACEMENT),
                ),
            ]
        )
    else:
        raise ValueError(f"Unsupported equipment type: {equipment_type}")

    return tasks


def _task(
    *,
    key: str,
    title: str,
    base_interval_days: int,
    seed_date: date | None,
    previous: MaintenanceTask | None,
    sensor_links: list[SensorLink] | None = None,
) -> MaintenanceTask:
    return MaintenanceTask(
        key=key,
        title=title,
        base_interval_days=base_interval_days,
        last_serviced=previous.last_serviced if previous and previous.last_serviced else seed_date,
        snoozed_until=previous.snoozed_until if previous else None,
        sensor_links=sensor_links or (previous.sensor_links if previous else []),
        usage_threshold=previous.usage_threshold if previous else None,
    )


def _sensor_links(
    *,
    runtime_sensor: str | None = None,
    runtime_threshold: float | None = None,
    usage_sensor: str | None = None,
    usage_threshold: float | None = None,
) -> list[SensorLink]:
    links: list[SensorLink] = []
    if runtime_sensor:
        links.append(
            SensorLink(
                role=SENSOR_ROLE_RUNTIME,
                entity_id=runtime_sensor,
                threshold=float(runtime_threshold) if runtime_threshold is not None else None,
                accelerate_days=30,
                label="Runtime",
            )
        )
    if usage_sensor:
        links.append(
            SensorLink(
                role=SENSOR_ROLE_USAGE,
                entity_id=usage_sensor,
                threshold=float(usage_threshold) if usage_threshold is not None else None,
                accelerate_days=30,
                label="Usage",
            )
        )
    return links


def _battery_links(sensor: str | None, threshold: float | None) -> list[SensorLink]:
    if not sensor:
        return []
    return [
        SensorLink(
            role=SENSOR_ROLE_BATTERY,
            entity_id=sensor,
            threshold=float(threshold if threshold is not None else DEFAULT_BATTERY_THRESHOLD),
            accelerate_days=365,
            label="Battery level",
        )
    ]


def _generate_asset_id(user_input: dict[str, Any], assets: list[Asset]) -> str:
    base = slugify(f"{user_input[CONF_EQUIPMENT_TYPE]}_{user_input[CONF_ASSET_NAME]}")
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
    if value in (None, "", 0, 0.0, "0", "0.0"):
        return None
    return float(value)
