"""Maintenance computation engine for HouseOps."""
from __future__ import annotations

from datetime import date, timedelta

from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_DUE_SOON_DAYS,
    SENSOR_ROLE_BATTERY,
    STATE_DUE,
    STATE_DUE_SOON,
    STATE_OK,
    STATE_OVERDUE,
    STATE_SNOOZED,
    STATE_UNKNOWN,
)
from .models import Asset, ComputedAssetState, ComputedTaskState, RegistrySnapshot, SensorLink


def build_snapshot(hass: HomeAssistant, assets: list[Asset]) -> RegistrySnapshot:
    """Compute a snapshot for every asset."""
    computed: dict[str, ComputedAssetState] = {}
    asset_map = {asset.asset_id: asset for asset in assets}

    for asset in assets:
        task_states: dict[str, ComputedTaskState] = {}
        for task in asset.tasks:
            task_states[task.key] = _compute_task_state(hass, asset, task.key)

        primary = _pick_primary_task(task_states)
        primary_state = task_states[primary] if primary else None
        computed[asset.asset_id] = ComputedAssetState(
            asset=asset,
            state=primary_state.state if primary_state else STATE_UNKNOWN,
            next_service_date=primary_state.next_service_date if primary_state else None,
            days_remaining=primary_state.days_remaining if primary_state else None,
            reason=primary_state.reason if primary_state else "No maintenance tasks configured.",
            primary_task_key=primary,
            tasks=task_states,
        )

    return RegistrySnapshot(assets=asset_map, computed=computed)


def _compute_task_state(hass: HomeAssistant, asset: Asset, task_key: str) -> ComputedTaskState:
    task = next(task for task in asset.tasks if task.key == task_key)
    today = date.today()
    linked_sensors: list[str] = []

    if task.last_serviced is None:
        return ComputedTaskState(
            asset_id=asset.asset_id,
            asset_name=asset.name,
            task_key=task.key,
            task_title=task.title,
            state=STATE_UNKNOWN,
            next_service_date=None,
            days_remaining=None,
            reason="A last serviced or install date is needed before this task can be scheduled.",
            linked_sensors=[],
        )

    next_service_date = task.last_serviced + timedelta(days=task.base_interval_days)
    reasons = [f"Base interval is {task.base_interval_days} days."]

    for link in task.sensor_links:
        linked_sensors.append(link.entity_id)
        adjusted_date, reason = _apply_sensor_link(hass, link, next_service_date)
        if adjusted_date != next_service_date:
            next_service_date = adjusted_date
            reasons.append(reason)

    days_remaining = (next_service_date - today).days

    if task.snoozed_until and task.snoozed_until >= today:
        state = STATE_SNOOZED
        reason = f"Snoozed until {task.snoozed_until.isoformat()}."
    elif days_remaining < 0:
        state = STATE_OVERDUE
        reason = f"Overdue by {abs(days_remaining)} day(s)."
    elif days_remaining == 0:
        state = STATE_DUE
        reason = "Due today."
    elif days_remaining <= DEFAULT_DUE_SOON_DAYS:
        state = STATE_DUE_SOON
        reason = f"Due in {days_remaining} day(s)."
    else:
        state = STATE_OK
        reason = f"Next service in {days_remaining} day(s)."

    detail = " ".join(reasons)
    return ComputedTaskState(
        asset_id=asset.asset_id,
        asset_name=asset.name,
        task_key=task.key,
        task_title=task.title,
        state=state,
        next_service_date=next_service_date,
        days_remaining=days_remaining,
        reason=f"{reason} {detail}".strip(),
        linked_sensors=linked_sensors,
    )


def _apply_sensor_link(
    hass: HomeAssistant,
    link: SensorLink,
    next_service_date: date,
) -> tuple[date, str]:
    state = hass.states.get(link.entity_id)
    if state is None or state.state in {"unknown", "unavailable"}:
        return next_service_date, f"Linked sensor {link.entity_id} was unavailable."

    try:
        value = float(state.state)
    except (TypeError, ValueError):
        return next_service_date, f"Linked sensor {link.entity_id} was non-numeric."

    if link.threshold is None:
        return next_service_date, f"Linked sensor {link.entity_id} has no threshold."

    trigger = value >= link.threshold
    if link.role == SENSOR_ROLE_BATTERY:
        trigger = value <= link.threshold

    if not trigger:
        return next_service_date, f"{link.label or link.role} sensor is within threshold."

    adjusted = next_service_date - timedelta(days=link.accelerate_days)
    if link.role == SENSOR_ROLE_BATTERY:
        adjusted = min(adjusted, date.today())

    return adjusted, (
        f"{link.label or link.role} sensor {link.entity_id} crossed threshold "
        f"({value} vs {link.threshold}), accelerating service."
    )


def _pick_primary_task(task_states: dict[str, ComputedTaskState]) -> str | None:
    if not task_states:
        return None
    ranking = {
        STATE_OVERDUE: 5,
        STATE_DUE: 4,
        STATE_DUE_SOON: 3,
        STATE_SNOOZED: 2,
        STATE_OK: 1,
        STATE_UNKNOWN: 0,
    }
    return max(
        task_states,
        key=lambda key: (
            ranking[task_states[key].state],
            -(
                task_states[key].days_remaining
                if task_states[key].days_remaining is not None
                else 999999
            ),
        ),
    )


def collect_linked_entities(snapshot: RegistrySnapshot) -> set[str]:
    """Collect all linked entity ids from a snapshot."""
    entity_ids: set[str] = set()
    for asset_state in snapshot.computed.values():
        for task in asset_state.tasks.values():
            entity_ids.update(task.linked_sensors)
    return entity_ids
