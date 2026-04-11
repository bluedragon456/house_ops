"""Constants for HouseOps."""
from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "house_ops"
NAME = "HouseOps"
VERSION = "1.0.1"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]

CONF_ASSETS = "assets"
CONF_HOME_PROFILE = "home_profile"
CONF_INSTANCE_NAME = "instance_name"
CONF_ASSET_ID = "asset_id"
CONF_ASSET_NAME = "name"
CONF_AREA = "area"
CONF_AREA_ID = "area_id"
CONF_CUSTOM_AREA = "custom_area"
CONF_SOURCE_ENTITY = "source_entity"
CONF_EQUIPMENT_TYPE = "equipment_type"
CONF_POWER_TYPE = "power_type"
CONF_BATTERY_SERVICE_MODE = "battery_service_mode"
CONF_MANUFACTURER = "manufacturer"
CONF_MODEL = "model"
CONF_CATEGORY = "category"
CONF_CUSTOM_CATEGORY = "custom_category"
CONF_IS_CUSTOM = "is_custom"
CONF_CATALOG_TIER = "catalog_tier"
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
CONF_ROBOT_HAS_MOP = "robot_has_mop"
CONF_ROBOT_MOP_STYLE = "robot_mop_style"
CONF_ROBOT_DOCK_TYPE = "robot_dock_type"
CONF_FILTER_INTERVAL_DAYS = "filter_interval_days"
CONF_DUST_BIN_INTERVAL_DAYS = "dust_bin_interval_days"
CONF_MAIN_BRUSH_INTERVAL_DAYS = "main_brush_interval_days"
CONF_SIDE_BRUSH_INTERVAL_DAYS = "side_brush_interval_days"
CONF_WHEEL_CLEAN_INTERVAL_DAYS = "wheel_clean_interval_days"
CONF_SENSOR_CLEANING_INTERVAL_DAYS = "sensor_cleaning_interval_days"
CONF_CONTACT_CLEANING_INTERVAL_DAYS = "contact_cleaning_interval_days"
CONF_MOP_SERVICE_INTERVAL_DAYS = "mop_service_interval_days"
CONF_WATER_TANK_INTERVAL_DAYS = "water_tank_interval_days"
CONF_DOCK_DUST_BAG_INTERVAL_DAYS = "dock_dust_bag_interval_days"
CONF_DOCK_AIR_PATH_INTERVAL_DAYS = "dock_air_path_interval_days"
CONF_DOCK_CLEAN_WATER_TANK_INTERVAL_DAYS = "dock_clean_water_tank_interval_days"
CONF_DOCK_DIRTY_WATER_TANK_INTERVAL_DAYS = "dock_dirty_water_tank_interval_days"
CONF_DOCK_WASH_TRAY_INTERVAL_DAYS = "dock_wash_tray_interval_days"
CONF_DOCK_WATER_FILTER_INTERVAL_DAYS = "dock_water_filter_interval_days"
CONF_SEARCH_QUERY = "search_query"
CONF_CONFIRM_REMOVE = "confirm_remove"
CONF_DWELLING_TYPE = "dwelling_type"
CONF_OWNERSHIP_TYPE = "ownership_type"
CONF_CATALOG_VIEW = "catalog_view"
CONF_TEMPLATE_SCOPE = "template_scope"
CONF_NEXT_ACTION = "next_action"
CONF_TASK_TITLE = "task_title"
CONF_TASK_INTERVAL_DAYS = "task_interval_days"
CONF_TASK_LAST_SERVICED_DATE = "task_last_serviced_date"
CONF_TASK_NEXT_DUE_OVERRIDE = "task_next_due_override"
CONF_ADD_ANOTHER_TASK = "add_another_task"

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
EQUIPMENT_TYPE_ROBOT_VACUUM = "robot_vacuum"
EQUIPMENT_TYPE_CUSTOM = "custom"

POWER_TYPE_BATTERY = "battery"
POWER_TYPE_WIRED = "wired"
POWER_TYPE_WIRED_WITH_BATTERY_BACKUP = "wired_with_battery_backup"
POWER_TYPE_GAS = "gas"
POWER_TYPE_ELECTRIC = "electric"
POWER_TYPE_DUAL_FUEL = "dual_fuel"
POWER_TYPE_MANUAL = "manual"
POWER_TYPE_NONE = "none"

BATTERY_SERVICE_NONE = "none"
BATTERY_SERVICE_REPLACEABLE = "replaceable"
BATTERY_SERVICE_SEALED_LIFE = "sealed_life"

ROBOT_MOP_STYLE_NONE = "none"
ROBOT_MOP_STYLE_SINGLE_PAD_OR_ROLLER = "single_pad_or_roller"
ROBOT_MOP_STYLE_DUAL_PAD = "dual_pad"

ROBOT_DOCK_TYPE_CHARGE_ONLY = "charge_only"
ROBOT_DOCK_TYPE_AUTO_EMPTY = "auto_empty"
ROBOT_DOCK_TYPE_FULL_SERVICE = "full_service"

TASK_FILTER = "filter"
TASK_INSPECTION = "inspection"
TASK_FLUSH = "flush"
TASK_ANODE = "anode"
TASK_TEST = "test"
TASK_BATTERY = "battery"
TASK_REPLACEMENT = "replacement"
TASK_SERVICE = "service"
TASK_CLEAN = "clean"
TASK_CHECK = "check"
TASK_LUBRICATE = "lubricate"
TASK_DUST_BIN = "dust_bin"
TASK_MAIN_BRUSH = "main_brush"
TASK_SIDE_BRUSH = "side_brush"
TASK_WHEEL_CLEAN = "wheel_clean"
TASK_SENSOR_CLEANING = "sensor_cleaning"
TASK_CONTACT_CLEANING = "contact_cleaning"
TASK_MOP_SERVICE = "mop_service"
TASK_WATER_TANK_CLEANING = "water_tank_cleaning"
TASK_DOCK_DUST_BAG = "dock_dust_bag"
TASK_DOCK_AIR_PATH = "dock_air_path"
TASK_DOCK_CLEAN_WATER_TANK = "dock_clean_water_tank"
TASK_DOCK_DIRTY_WATER_TANK = "dock_dirty_water_tank"
TASK_DOCK_WASH_TRAY = "dock_wash_tray"
TASK_DOCK_WATER_FILTER = "dock_water_filter"

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

CATALOG_TIER_BASIC = "basic"
CATALOG_TIER_ADVANCED = "advanced"

DWELLING_TYPE_APARTMENT = "apartment"
DWELLING_TYPE_CONDO = "condo"
DWELLING_TYPE_TOWNHOME = "townhome"
DWELLING_TYPE_SINGLE_FAMILY = "single_family"
DWELLING_TYPE_MULTI_FAMILY = "multi_family"
DWELLING_TYPE_MOBILE_HOME = "mobile_home"

OWNERSHIP_TYPE_RENTER = "renter"
OWNERSHIP_TYPE_OWNER = "owner"

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
ATTR_CATEGORY = "category"
ATTR_CATALOG_TIER = "catalog_tier"
ATTR_IS_CUSTOM = "is_custom"
ATTR_ROBOT_MOP_STYLE = "robot_mop_style"
ATTR_ROBOT_DOCK_TYPE = "robot_dock_type"
