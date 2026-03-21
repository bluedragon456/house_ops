"""Data models for HouseOps."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


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
    last_serviced: date | None
    snoozed_until: date | None = None
    sensor_links: list[SensorLink] = field(default_factory=list)
    usage_threshold: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "title": self.title,
            "base_interval_days": self.base_interval_days,
            "last_serviced": self.last_serviced.isoformat() if self.last_serviced else None,
            "snoozed_until": self.snoozed_until.isoformat() if self.snoozed_until else None,
            "sensor_links": [link.as_dict() for link in self.sensor_links],
            "usage_threshold": self.usage_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MaintenanceTask":
        return cls(
            key=str(data["key"]),
            title=str(data["title"]),
            base_interval_days=int(data["base_interval_days"]),
            last_serviced=_parse_date(data.get("last_serviced")),
            snoozed_until=_parse_date(data.get("snoozed_until")),
            sensor_links=[SensorLink.from_dict(item) for item in data.get("sensor_links", [])],
            usage_threshold=float(data["usage_threshold"]) if data.get("usage_threshold") is not None else None,
        )


@dataclass(slots=True)
class Asset:
    """Tracked household equipment."""

    asset_id: str
    name: str
    area: str | None
    equipment_type: str
    manufacturer: str | None
    model: str | None
    install_date: date | None
    last_serviced: date | None
    base_interval_days: int
    notes: str | None
    tasks: list[MaintenanceTask]

    def as_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "area": self.area,
            "equipment_type": self.equipment_type,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "install_date": self.install_date.isoformat() if self.install_date else None,
            "last_serviced": self.last_serviced.isoformat() if self.last_serviced else None,
            "base_interval_days": self.base_interval_days,
            "notes": self.notes,
            "tasks": [task.as_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Asset":
        return cls(
            asset_id=str(data["asset_id"]),
            name=str(data["name"]),
            area=str(data["area"]) if data.get("area") else None,
            equipment_type=str(data["equipment_type"]),
            manufacturer=str(data["manufacturer"]) if data.get("manufacturer") else None,
            model=str(data["model"]) if data.get("model") else None,
            install_date=_parse_date(data.get("install_date")),
            last_serviced=_parse_date(data.get("last_serviced")),
            base_interval_days=int(data["base_interval_days"]),
            notes=str(data["notes"]) if data.get("notes") else None,
            tasks=[MaintenanceTask.from_dict(item) for item in data.get("tasks", [])],
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
    linked_sensors: list[str]


@dataclass(slots=True)
class ComputedAssetState:
    """Computed state for a single asset."""

    asset: Asset
    state: str
    next_service_date: date | None
    days_remaining: int | None
    reason: str
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
