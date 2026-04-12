"""Data models for HouseOps."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(slots=True)
class HomeProfile:
    """User profile used to tailor recommended systems."""

    dwelling_type: str
    ownership_type: str

    def as_dict(self) -> dict[str, str]:
        return {
            "dwelling_type": self.dwelling_type,
            "ownership_type": self.ownership_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "HomeProfile":
        payload = data or {}
        return cls(
            dwelling_type=str(payload.get("dwelling_type", "single_family")),
            ownership_type=str(payload.get("ownership_type", "owner")),
        )


@dataclass(slots=True)
class SensorLink:
    """A Home Assistant sensor that can influence a maintenance task."""

    role: str
    entity_id: str
    threshold: float | None = None
    accelerate_days: int = 0
    label: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "entity_id": self.entity_id,
            "threshold": self.threshold,
            "accelerate_days": self.accelerate_days,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SensorLink":
        return cls(
            role=str(data["role"]),
            entity_id=str(data["entity_id"]),
            threshold=float(data["threshold"]) if data.get("threshold") is not None else None,
            accelerate_days=int(data.get("accelerate_days", 0)),
            label=str(data["label"]) if data.get("label") else None,
        )


@dataclass(slots=True)
class MaintenanceTask:
    """A maintenance task for an equipment asset."""

    key: str
    title: str
    base_interval_days: int
    last_serviced_date: date | None
    next_due_override: date | None = None
    snoozed_until: date | None = None
    sensor_links: list[SensorLink] = field(default_factory=list)
    enabled: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "base_interval_days": self.base_interval_days,
            "last_serviced_date": self.last_serviced_date.isoformat() if self.last_serviced_date else None,
            "next_due_override": self.next_due_override.isoformat() if self.next_due_override else None,
            "snoozed_until": self.snoozed_until.isoformat() if self.snoozed_until else None,
            "sensor_links": [link.as_dict() for link in self.sensor_links],
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MaintenanceTask":
        return cls(
            key=str(data["key"]),
            title=str(data["title"]),
            base_interval_days=int(data["base_interval_days"]),
            last_serviced_date=_parse_date(data.get("last_serviced_date") or data.get("last_serviced")),
            next_due_override=_parse_date(data.get("next_due_override")),
            snoozed_until=_parse_date(data.get("snoozed_until")),
            sensor_links=[SensorLink.from_dict(item) for item in data.get("sensor_links", [])],
            enabled=bool(data.get("enabled", True)),
        )


@dataclass(slots=True)
class Asset:
    """Tracked household equipment."""

    asset_id: str
    name: str
    area: str | None
    area_id: str | None
    source_entity: str | None
    dock_source_entity: str | None
    equipment_type: str
    power_type: str
    battery_service_mode: str | None
    category: str | None
    catalog_tier: str | None
    manufacturer: str | None
    model: str | None
    install_date: date | None
    last_serviced_date: date | None
    notes: str | None
    primary_task_key: str
    tasks: list[MaintenanceTask]
    is_custom: bool = False
    custom_category: str | None = None
    robot_has_mop: bool = False
    robot_mop_style: str | None = None
    robot_dock_type: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "area": self.area,
            "area_id": self.area_id,
            "source_entity": self.source_entity,
            "dock_source_entity": self.dock_source_entity,
            "equipment_type": self.equipment_type,
            "power_type": self.power_type,
            "battery_service_mode": self.battery_service_mode,
            "category": self.category,
            "catalog_tier": self.catalog_tier,
            "is_custom": self.is_custom,
            "custom_category": self.custom_category,
            "robot_has_mop": self.robot_has_mop,
            "robot_mop_style": self.robot_mop_style,
            "robot_dock_type": self.robot_dock_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "install_date": self.install_date.isoformat() if self.install_date else None,
            "last_serviced_date": self.last_serviced_date.isoformat() if self.last_serviced_date else None,
            "notes": self.notes,
            "primary_task_key": self.primary_task_key,
            "tasks": [task.as_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Asset":
        legacy_tasks = data.get("tasks", [])
        return cls(
            asset_id=str(data["asset_id"]),
            name=str(data["name"]),
            area=str(data["area"]) if data.get("area") else None,
            area_id=str(data["area_id"]) if data.get("area_id") else None,
            source_entity=str(data["source_entity"]) if data.get("source_entity") else None,
            dock_source_entity=str(data["dock_source_entity"]) if data.get("dock_source_entity") else None,
            equipment_type=str(data["equipment_type"]),
            power_type=str(data.get("power_type", "wired")),
            battery_service_mode=str(data["battery_service_mode"]) if data.get("battery_service_mode") else None,
            category=str(data["category"]) if data.get("category") else None,
            catalog_tier=str(data["catalog_tier"]) if data.get("catalog_tier") else None,
            is_custom=bool(data.get("is_custom", str(data.get("equipment_type")) == "custom")),
            custom_category=str(data["custom_category"]) if data.get("custom_category") else None,
            robot_has_mop=bool(data.get("robot_has_mop", False)),
            robot_mop_style=str(data["robot_mop_style"]) if data.get("robot_mop_style") else None,
            robot_dock_type=str(data["robot_dock_type"]) if data.get("robot_dock_type") else None,
            manufacturer=str(data["manufacturer"]) if data.get("manufacturer") else None,
            model=str(data["model"]) if data.get("model") else None,
            install_date=_parse_date(data.get("install_date")),
            last_serviced_date=_parse_date(data.get("last_serviced_date") or data.get("last_serviced")),
            notes=str(data["notes"]) if data.get("notes") else None,
            primary_task_key=str(data.get("primary_task_key") or _infer_primary_task_key(legacy_tasks)),
            tasks=[MaintenanceTask.from_dict(item) for item in legacy_tasks],
        )


@dataclass(slots=True)
class ComputedTaskState:
    """Computed state for a single task."""

    asset_id: str
    asset_name: str
    task_key: str
    task_title: str
    state: str
    next_service_date: date | None
    days_remaining: int | None
    reason: str
    due_source: str
    due_details: str
    linked_sensors: list[str]
    override_active: bool


@dataclass(slots=True)
class ComputedAssetState:
    """Computed state for a single asset."""

    asset: Asset
    state: str
    next_service_date: date | None
    days_remaining: int | None
    reason: str
    due_source: str
    due_details: str
    primary_task_key: str | None
    tasks: dict[str, ComputedTaskState]


@dataclass(slots=True)
class RegistrySnapshot:
    """Computed registry snapshot for all assets."""

    assets: dict[str, Asset]
    computed: dict[str, ComputedAssetState]


@dataclass(slots=True)
class HouseOpsRuntimeData:
    """Config entry runtime data."""

    coordinator: Any


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _infer_primary_task_key(tasks: list[dict[str, Any]]) -> str:
    if tasks:
        return str(tasks[0].get("key", "primary"))
    return "primary"
