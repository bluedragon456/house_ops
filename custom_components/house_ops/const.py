"""Constants for HouseOps."""
from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "house_ops"
NAME = "HouseOps"
VERSION = "0.2.0"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]

CONF_ASSETS = "assets"
CONF_INSTANCE_NAME = "instance_name"
CONF_ASSET_ID = "asset_id"
CONF_ASSET_NAME = "name"
CONF_AREA = "area"
CONF_AREA_ID = "area_id"
CONF_CUSTOM_AREA = "custom_area"
CONF_EQUIPMENT_TYPE = "equipment_type"
CONF_POWER_TYPE = "power_type"
CONF_MANUFACTURER = "manufacturer"
CONF_MODEL = "model"
CONF_INSTALL_DATE = "install_date"
CONF_LAST_SERVICED_DATE = "last_serviced_date"
CONF_LAST_SERVICED = "last_serviced"
CONF_NEXT_DUE_OVERRIDE = "next_due_override"
CONF_BASE_INTERVAL_DAYS = "base_interval_days"
CONF_INSPECTION_INTERVAL_DAYS = "inspection_interval_days"
CONF_ANODE_INTERVAL_DAYS = "anode_interval_days"
CONF_BATTERY_INTERVAL_DAYS = "battery_interval_days"
CONF_REPLACEMENT_INTERVAL_DAYS = "replacement_interval_days"
CONF_NOTES = "notes"
CONF_RUNTIME_SENSOR = "runtime_sensor"
CONF_RUNTIME_THRESHOLD = "runtime_threshold"
CONF_USAGE_SENSOR = "usage_sensor"
CONF_USAGE_THRESHOLD = "usage_threshold"
CONF_BATTERY_SENSOR = "battery_sensor"
CONF_BATTERY_THRESHOLD = "battery_threshold"
CONF_ENABLE_ANODE_TASK = "enable_anode_task"
CONF_CONFIRM_REMOVE = "confirm_remove"

DEFAULT_INSTANCE_NAME = "HouseOps"
DEFAULT_DUE_SOON_DAYS = 14
DEFAULT_SNOOZE_DAYS = 7
DEFAULT_BATTERY_THRESHOLD = 30.0
DEFAULT_FIRE_ALARM_BATTERY_INTERVAL_DAYS = 180
DEFAULT_FIRE_ALARM_REPLACEMENT_INTERVAL_DAYS = 3650
DEFAULT_WATER_HEATER_ANODE_INTERVAL_DAYS = 1825

EQUIPMENT_TYPE_FURNACE = "furnace"
EQUIPMENT_TYPE_WATER_HEATER = "water_heater"
EQUIPMENT_TYPE_FIRE_ALARMS = "fire_alarms"

POWER_TYPE_BATTERY = "battery"
POWER_TYPE_WIRED = "wired"
POWER_TYPE_WIRED_WITH_BATTERY_BACKUP = "wired_with_battery_backup"

TASK_FILTER = "filter"
TASK_INSPECTION = "inspection"
TASK_FLUSH = "flush"
TASK_ANODE = "anode"
TASK_TEST = "test"
TASK_BATTERY = "battery"
TASK_REPLACEMENT = "replacement"

STATE_OK = "ok"
STATE_DUE_SOON = "due_soon"
STATE_DUE = "due"
STATE_OVERDUE = "overdue"
STATE_SNOOZED = "snoozed"
STATE_UNKNOWN = "unknown"

MAINTENANCE_STATES = [
    STATE_OK,
    STATE_DUE_SOON,
    STATE_DUE,
    STATE_OVERDUE,
    STATE_SNOOZED,
    STATE_UNKNOWN,
]

DUE_SOURCE_CALCULATED = "calculated"
DUE_SOURCE_OVERRIDDEN = "overridden"
DUE_SOURCE_SENSOR = "sensor_adjusted"
DUE_SOURCE_DEFAULTED = "defaulted"

SENSOR_ROLE_RUNTIME = "runtime"
SENSOR_ROLE_USAGE = "usage"
SENSOR_ROLE_BATTERY = "battery"

SERVICE_MARK_SERVICED = "mark_serviced"
SERVICE_SNOOZE_TASK = "snooze_task"
SERVICE_RECALCULATE = "recalculate"
SERVICE_ADD_ASSET = "add_asset"

ATTR_TASK_KEY = "task_key"
ATTR_OCCURRED_ON = "occurred_on"
ATTR_DAYS = "days"
ATTR_REASON = "reason"
ATTR_DUE_SOURCE = "due_source"
ATTR_DUE_DETAILS = "due_details"
ATTR_ASSET_NAME = "asset_name"
ATTR_TASK_TITLE = "task_title"
ATTR_TASKS = "tasks"
ATTR_LINKED_SENSORS = "linked_sensors"
ATTR_EQUIPMENT_TYPE = "equipment_type"
ATTR_POWER_TYPE = "power_type"
ATTR_OVERRIDE_ACTIVE = "override_active"
