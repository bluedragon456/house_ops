"""Equipment catalog for HouseOps."""
from __future__ import annotations

from dataclasses import dataclass

from .const import (
    BATTERY_SERVICE_REPLACEABLE,
    BATTERY_SERVICE_SEALED_LIFE,
    CATALOG_TIER_ADVANCED,
    CATALOG_TIER_BASIC,
    DEFAULT_FIRE_ALARM_BATTERY_INTERVAL_DAYS,
    DEFAULT_FIRE_ALARM_REPLACEMENT_INTERVAL_DAYS,
    DEFAULT_WATER_HEATER_ANODE_INTERVAL_DAYS,
    DWELLING_TYPE_APARTMENT,
    DWELLING_TYPE_CONDO,
    DWELLING_TYPE_MOBILE_HOME,
    DWELLING_TYPE_MULTI_FAMILY,
    DWELLING_TYPE_SINGLE_FAMILY,
    DWELLING_TYPE_TOWNHOME,
    EQUIPMENT_TYPE_CUSTOM,
    EQUIPMENT_TYPE_FIRE_ALARMS,
    EQUIPMENT_TYPE_FURNACE,
    EQUIPMENT_TYPE_WATER_HEATER,
    OWNERSHIP_TYPE_OWNER,
    OWNERSHIP_TYPE_RENTER,
    POWER_TYPE_BATTERY,
    POWER_TYPE_DUAL_FUEL,
    POWER_TYPE_ELECTRIC,
    POWER_TYPE_GAS,
    POWER_TYPE_MANUAL,
    POWER_TYPE_NONE,
    POWER_TYPE_WIRED,
    POWER_TYPE_WIRED_WITH_BATTERY_BACKUP,
    SENSOR_ROLE_BATTERY,
    SENSOR_ROLE_RUNTIME,
    SENSOR_ROLE_USAGE,
    TASK_ANODE,
    TASK_BATTERY,
    TASK_CHECK,
    TASK_CLEAN,
    TASK_FILTER,
    TASK_FLUSH,
    TASK_INSPECTION,
    TASK_LUBRICATE,
    TASK_REPLACEMENT,
    TASK_SERVICE,
    TASK_TEST,
)
from .models import HomeProfile

ALL_DWELLINGS = (
    DWELLING_TYPE_APARTMENT,
    DWELLING_TYPE_CONDO,
    DWELLING_TYPE_TOWNHOME,
    DWELLING_TYPE_SINGLE_FAMILY,
    DWELLING_TYPE_MULTI_FAMILY,
    DWELLING_TYPE_MOBILE_HOME,
)
OWNER_DWELLINGS = (
    DWELLING_TYPE_CONDO,
    DWELLING_TYPE_TOWNHOME,
    DWELLING_TYPE_SINGLE_FAMILY,
    DWELLING_TYPE_MULTI_FAMILY,
    DWELLING_TYPE_MOBILE_HOME,
)


@dataclass(frozen=True, slots=True)
class TaskDefinition:
    key: str
    title: str
    default_interval_days: int
    sensor_roles: tuple[str, ...] = ()
    allowed_power_types: tuple[str, ...] | None = None
    optional: bool = False


@dataclass(frozen=True, slots=True)
class EquipmentDefinition:
    key: str
    label: str
    description: str
    category: str
    tier: str
    applicable_dwellings: tuple[str, ...]
    applicable_ownership: tuple[str, ...]
    primary_task_key: str
    supported_power_types: tuple[str, ...]
    default_power_type: str
    tasks: tuple[TaskDefinition, ...]
    ui_enabled: bool = True


def _task(key: str, title: str, interval: int, *, sensor_roles: tuple[str, ...] = (), optional: bool = False):
    return TaskDefinition(
        key=key,
        title=title,
        default_interval_days=interval,
        sensor_roles=sensor_roles,
        optional=optional,
    )


def _generic_definition(
    key: str,
    label: str,
    description: str,
    category: str,
    tier: str,
    dwellings: tuple[str, ...],
    ownership: tuple[str, ...],
    *,
    primary_task_key: str = TASK_SERVICE,
    task_title: str = "Routine service",
    interval: int = 180,
    supported_power_types: tuple[str, ...] = (POWER_TYPE_WIRED,),
    default_power_type: str | None = None,
) -> EquipmentDefinition:
    chosen_power = default_power_type or supported_power_types[0]
    return EquipmentDefinition(
        key=key,
        label=label,
        description=description,
        category=category,
        tier=tier,
        applicable_dwellings=dwellings,
        applicable_ownership=ownership,
        primary_task_key=primary_task_key,
        supported_power_types=supported_power_types,
        default_power_type=chosen_power,
        tasks=(
            TaskDefinition(
                key=primary_task_key,
                title=task_title,
                default_interval_days=interval,
            ),
        ),
    )


SUPPORTED_EQUIPMENT: tuple[EquipmentDefinition, ...] = (
    EquipmentDefinition(
        key=EQUIPMENT_TYPE_FURNACE,
        label="Furnace / HVAC",
        description="Track filter changes, annual inspections, and optional runtime-based acceleration.",
        category="HVAC",
        tier=CATALOG_TIER_BASIC,
        applicable_dwellings=ALL_DWELLINGS,
        applicable_ownership=(OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER),
        primary_task_key=TASK_FILTER,
        supported_power_types=(POWER_TYPE_WIRED, POWER_TYPE_GAS, POWER_TYPE_ELECTRIC, POWER_TYPE_DUAL_FUEL),
        default_power_type=POWER_TYPE_WIRED,
        tasks=(
            TaskDefinition(
                key=TASK_FILTER,
                title="Filter replacement",
                default_interval_days=90,
                sensor_roles=(SENSOR_ROLE_RUNTIME, SENSOR_ROLE_USAGE),
            ),
            TaskDefinition(
                key=TASK_INSPECTION,
                title="Annual inspection",
                default_interval_days=365,
            ),
        ),
    ),
    EquipmentDefinition(
        key=EQUIPMENT_TYPE_WATER_HEATER,
        label="Water heater",
        description="Track annual flushes, optional anode rod inspections, and usage-based acceleration.",
        category="Water systems",
        tier=CATALOG_TIER_BASIC,
        applicable_dwellings=ALL_DWELLINGS,
        applicable_ownership=(OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER),
        primary_task_key=TASK_FLUSH,
        supported_power_types=(POWER_TYPE_WIRED, POWER_TYPE_GAS, POWER_TYPE_ELECTRIC),
        default_power_type=POWER_TYPE_WIRED,
        tasks=(
            TaskDefinition(
                key=TASK_FLUSH,
                title="Annual flush",
                default_interval_days=365,
                sensor_roles=(SENSOR_ROLE_USAGE,),
            ),
            TaskDefinition(
                key=TASK_ANODE,
                title="Anode rod inspection",
                default_interval_days=DEFAULT_WATER_HEATER_ANODE_INTERVAL_DAYS,
                optional=True,
            ),
        ),
    ),
    EquipmentDefinition(
        key=EQUIPMENT_TYPE_FIRE_ALARMS,
        label="Fire alarms / smoke detectors",
        description="Track alarm tests, battery service when batteries exist, and long-term replacement advisory.",
        category="Safety",
        tier=CATALOG_TIER_BASIC,
        applicable_dwellings=ALL_DWELLINGS,
        applicable_ownership=(OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER),
        primary_task_key=TASK_TEST,
        supported_power_types=(
            POWER_TYPE_BATTERY,
            POWER_TYPE_WIRED,
            POWER_TYPE_WIRED_WITH_BATTERY_BACKUP,
        ),
        default_power_type=POWER_TYPE_WIRED_WITH_BATTERY_BACKUP,
        tasks=(
            TaskDefinition(
                key=TASK_TEST,
                title="Monthly alarm test",
                default_interval_days=30,
            ),
            TaskDefinition(
                key=TASK_BATTERY,
                title="Battery replacement",
                default_interval_days=DEFAULT_FIRE_ALARM_BATTERY_INTERVAL_DAYS,
                sensor_roles=(SENSOR_ROLE_BATTERY,),
                allowed_power_types=(POWER_TYPE_BATTERY, POWER_TYPE_WIRED_WITH_BATTERY_BACKUP),
            ),
            TaskDefinition(
                key=TASK_REPLACEMENT,
                title="Detector replacement advisory",
                default_interval_days=DEFAULT_FIRE_ALARM_REPLACEMENT_INTERVAL_DAYS,
            ),
        ),
    ),
    _generic_definition("central_ac", "Central AC", "Track seasonal HVAC service for central air conditioning.", "HVAC", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), task_title="Cooling tune-up", interval=180),
    _generic_definition("heat_pump", "Heat pump", "Track regular heat pump service and filter checks.", "HVAC", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), task_title="Heat pump service", interval=180, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("mini_split", "Mini-split", "Track mini-split cleaning and seasonal service.", "HVAC", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), task_title="Mini-split service", interval=180, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("thermostat", "Thermostat", "Track thermostat battery or calibration checks.", "HVAC", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CHECK, task_title="Thermostat check", interval=365, supported_power_types=(POWER_TYPE_BATTERY, POWER_TYPE_WIRED)),
    _generic_definition("whole_home_humidifier", "Whole-home humidifier", "Track humidifier panel changes and service.", "HVAC", CATALOG_TIER_BASIC, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Humidifier service", interval=180),
    _generic_definition("dehumidifier", "Dehumidifier", "Track filter cleaning and seasonal service.", "HVAC", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CLEAN, task_title="Filter cleaning", interval=90, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("air_purifier", "Air purifier", "Track filter replacement and cleaning.", "HVAC", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_FILTER, task_title="Filter replacement", interval=90, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("water_softener", "Water softener", "Track salt refills and resin-system service.", "Water systems", CATALOG_TIER_BASIC, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Water softener service", interval=90),
    _generic_definition("under_sink_filter", "Under-sink filter", "Track filter cartridge replacement.", "Water systems", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_FILTER, task_title="Filter replacement", interval=180, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("whole_home_filter", "Whole-home filter", "Track whole-home water filter replacement.", "Water systems", CATALOG_TIER_BASIC, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_FILTER, task_title="Filter replacement", interval=180, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("sump_pump", "Sump pump", "Track sump pump inspection and test cycles.", "Water systems", CATALOG_TIER_BASIC, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_TEST, task_title="Pump test", interval=90, supported_power_types=(POWER_TYPE_ELECTRIC, POWER_TYPE_BATTERY)),
    _generic_definition("carbon_monoxide_alarm", "CO alarm", "Track testing and replacement on standalone CO alarms.", "Safety", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_TEST, task_title="Alarm test", interval=30, supported_power_types=(POWER_TYPE_BATTERY, POWER_TYPE_WIRED, POWER_TYPE_WIRED_WITH_BATTERY_BACKUP)),
    _generic_definition("combo_smoke_co_alarm", "Combo smoke/CO alarm", "Track testing and replacement for combination alarms.", "Safety", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_TEST, task_title="Alarm test", interval=30, supported_power_types=(POWER_TYPE_BATTERY, POWER_TYPE_WIRED, POWER_TYPE_WIRED_WITH_BATTERY_BACKUP)),
    _generic_definition("fire_extinguisher", "Fire extinguisher", "Track pressure and expiration checks.", "Safety", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_INSPECTION, task_title="Pressure inspection", interval=30, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("refrigerator", "Refrigerator", "Track condenser cleaning and filter replacement.", "Kitchen/laundry", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CLEAN, task_title="Condenser cleaning", interval=180, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("dishwasher", "Dishwasher", "Track filter cleaning and maintenance cycles.", "Kitchen/laundry", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CLEAN, task_title="Filter cleaning", interval=90, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("washer", "Washer", "Track cleaning cycles and hose inspection.", "Kitchen/laundry", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CLEAN, task_title="Tub cleaning", interval=30, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("dryer", "Dryer", "Track lint-path maintenance and vent checks.", "Kitchen/laundry", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CLEAN, task_title="Lint and vent cleaning", interval=30, supported_power_types=(POWER_TYPE_ELECTRIC, POWER_TYPE_GAS)),
    _generic_definition("range_hood", "Range hood", "Track grease filter cleaning and filter replacement.", "Kitchen/laundry", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CLEAN, task_title="Grease filter cleaning", interval=60, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("toilet", "Toilets", "Track leak checks and hardware inspection.", "Plumbing/interior", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CHECK, task_title="Leak check", interval=180, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("faucet_shower", "Faucets / showers", "Track aerator cleaning and leak checks.", "Plumbing/interior", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CHECK, task_title="Leak check", interval=180, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("garbage_disposal", "Garbage disposal", "Track disposal cleaning and inspection.", "Plumbing/interior", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CLEAN, task_title="Disposal cleaning", interval=60, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("garage_door_opener", "Garage door opener", "Track opener safety reversal tests and lubrication.", "Access/common devices", CATALOG_TIER_BASIC, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_TEST, task_title="Safety reversal test", interval=180, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("door_locks", "Door locks", "Track lock lubrication and battery checks.", "Access/common devices", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_LUBRICATE, task_title="Lock lubrication", interval=365, supported_power_types=(POWER_TYPE_BATTERY, POWER_TYPE_MANUAL)),
    _generic_definition("ceiling_fans", "Ceiling fans", "Track balancing, cleaning, and seasonal checks.", "Access/common devices", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CLEAN, task_title="Fan cleaning", interval=180, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("bathroom_exhaust_fans", "Bathroom exhaust fans", "Track cleaning and airflow checks.", "Access/common devices", CATALOG_TIER_BASIC, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CLEAN, task_title="Fan cleaning", interval=180, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("electrical_panel", "Electrical panel", "Track visual inspection and labeling review.", "Electrical", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_INSPECTION, task_title="Panel inspection", interval=365, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("gfci_afci", "GFCI / AFCI circuits", "Track monthly or quarterly test cycles.", "Electrical", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_TEST, task_title="Circuit test", interval=90, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("generator", "Generator", "Track exercise runs and annual service.", "Electrical", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_TEST, task_title="Exercise run", interval=30, supported_power_types=(POWER_TYPE_GAS, POWER_TYPE_DUAL_FUEL)),
    _generic_definition("transfer_switch", "Transfer switch", "Track switch inspection and test runs.", "Electrical", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_TEST, task_title="Transfer test", interval=180, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("surge_protection", "Surge protection", "Track visual inspection and replacement advisory.", "Electrical", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_INSPECTION, task_title="Protection inspection", interval=365, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("ev_charger", "EV charger", "Track charger inspection and cable checks.", "Electrical", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_INSPECTION, task_title="Charger inspection", interval=180, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("roof", "Roof", "Track seasonal roof inspections.", "Exterior/building envelope", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_INSPECTION, task_title="Roof inspection", interval=180, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("gutters", "Gutters", "Track gutter cleaning.", "Exterior/building envelope", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_CLEAN, task_title="Gutter cleaning", interval=180, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("siding", "Siding", "Track siding inspections and wash cycles.", "Exterior/building envelope", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_INSPECTION, task_title="Siding inspection", interval=365, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("windows", "Windows", "Track seal inspection and cleaning.", "Exterior/building envelope", CATALOG_TIER_ADVANCED, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CHECK, task_title="Seal check", interval=365, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("doors", "Exterior doors", "Track weather seal and hardware checks.", "Exterior/building envelope", CATALOG_TIER_ADVANCED, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CHECK, task_title="Seal and hardware check", interval=180, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("caulking_weather_sealing", "Caulking / weather sealing", "Track exterior caulk and weather seal inspection.", "Exterior/building envelope", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_INSPECTION, task_title="Seal inspection", interval=365, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("deck_patio", "Deck / patio", "Track cleaning and seasonal inspection.", "Exterior/building envelope", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_INSPECTION, task_title="Deck inspection", interval=180, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("fence", "Fence", "Track fence inspection and sealing.", "Exterior/building envelope", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_INSPECTION, task_title="Fence inspection", interval=365, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("well_system", "Well system", "Track pressure tank, filter, and water quality maintenance.", "Water/drainage", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Well system service", interval=180),
    _generic_definition("septic_system", "Septic system", "Track inspection and pumping intervals.", "Water/drainage", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Septic inspection", interval=365),
    _generic_definition("sewage_ejector_pump", "Sewage ejector pump", "Track pump testing and inspection.", "Water/drainage", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_TEST, task_title="Pump test", interval=180, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("irrigation_sprinklers", "Irrigation / sprinklers", "Track seasonal startup, shutdown, and inspection.", "Water/drainage", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Irrigation service", interval=180),
    _generic_definition("drainage_grading", "Drainage / grading", "Track drainage inspections around the property.", "Water/drainage", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_INSPECTION, task_title="Drainage inspection", interval=365, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("ductwork", "Ductwork", "Track duct inspection and cleaning reminders.", "Comfort/air distribution", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_INSPECTION, task_title="Duct inspection", interval=365),
    _generic_definition("vents_registers", "Vents / registers", "Track cleaning and airflow checks.", "Comfort/air distribution", CATALOG_TIER_ADVANCED, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CLEAN, task_title="Vent cleaning", interval=180, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("boiler", "Boiler", "Track annual boiler service.", "Comfort/air distribution", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Boiler service", interval=365, supported_power_types=(POWER_TYPE_GAS, POWER_TYPE_ELECTRIC)),
    _generic_definition("radiant_heat", "Radiant heat", "Track seasonal manifold and system checks.", "Comfort/air distribution", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_INSPECTION, task_title="Radiant heat inspection", interval=365),
    _generic_definition("lawn_mower", "Lawn mower", "Track blade sharpening and seasonal tune-ups.", "Lawn and yard equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Lawn mower service", interval=180, supported_power_types=(POWER_TYPE_GAS, POWER_TYPE_ELECTRIC, POWER_TYPE_BATTERY)),
    _generic_definition("riding_mower", "Riding mower", "Track oil changes and blade service.", "Lawn and yard equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Riding mower service", interval=180, supported_power_types=(POWER_TYPE_GAS, POWER_TYPE_ELECTRIC)),
    _generic_definition("string_trimmer", "String trimmer", "Track line replacement and seasonal checks.", "Lawn and yard equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Trimmer service", interval=180, supported_power_types=(POWER_TYPE_GAS, POWER_TYPE_ELECTRIC, POWER_TYPE_BATTERY)),
    _generic_definition("leaf_blower", "Leaf blower", "Track cleaning and seasonal checks.", "Lawn and yard equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Leaf blower service", interval=180, supported_power_types=(POWER_TYPE_GAS, POWER_TYPE_ELECTRIC, POWER_TYPE_BATTERY)),
    _generic_definition("hedge_trimmer", "Hedge trimmer", "Track blade cleaning and sharpening.", "Lawn and yard equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Hedge trimmer service", interval=180, supported_power_types=(POWER_TYPE_GAS, POWER_TYPE_ELECTRIC, POWER_TYPE_BATTERY)),
    _generic_definition("chainsaw", "Chainsaw", "Track chain sharpening and tune-ups.", "Lawn and yard equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Chainsaw service", interval=120, supported_power_types=(POWER_TYPE_GAS, POWER_TYPE_ELECTRIC, POWER_TYPE_BATTERY)),
    _generic_definition("pressure_washer", "Pressure washer", "Track pump maintenance and winterization.", "Lawn and yard equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Pressure washer service", interval=180, supported_power_types=(POWER_TYPE_GAS, POWER_TYPE_ELECTRIC)),
    _generic_definition("snow_blower", "Snow blower", "Track pre-season service and storage prep.", "Lawn and yard equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Snow blower service", interval=365, supported_power_types=(POWER_TYPE_GAS, POWER_TYPE_ELECTRIC, POWER_TYPE_BATTERY)),
    _generic_definition("pool_equipment", "Pool equipment", "Track pumps, filters, and chemistry equipment maintenance.", "Specialty equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Pool equipment service", interval=90),
    _generic_definition("hot_tub_spa", "Hot tub / spa equipment", "Track filter changes and water-care equipment maintenance.", "Specialty equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), task_title="Spa equipment service", interval=90),
    _generic_definition("solar_inverter", "Solar / inverter", "Track inverter inspection and cleaning.", "Specialty equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_INSPECTION, task_title="Inverter inspection", interval=365, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("backup_battery", "Backup battery", "Track battery-system inspection and runtime checks.", "Specialty equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_TEST, task_title="Battery system test", interval=180, supported_power_types=(POWER_TYPE_BATTERY,)),
    _generic_definition("attic_fan", "Attic fan", "Track cleaning and seasonal operation checks.", "Specialty equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_CHECK, task_title="Attic fan check", interval=180, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("crawlspace_dehumidifier", "Crawlspace dehumidifier", "Track filter and drainage maintenance.", "Specialty equipment", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_CLEAN, task_title="Dehumidifier maintenance", interval=90, supported_power_types=(POWER_TYPE_ELECTRIC,)),
    _generic_definition("chimney_fireplace", "Chimney / fireplace", "Track annual inspection and sweeping.", "Pest/seasonal/other owner tasks", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_INSPECTION, task_title="Chimney inspection", interval=365, supported_power_types=(POWER_TYPE_GAS, POWER_TYPE_NONE)),
    _generic_definition("dryer_vent", "Dryer vent", "Track deep dryer vent cleaning.", "Pest/seasonal/other owner tasks", CATALOG_TIER_ADVANCED, ALL_DWELLINGS, (OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER), primary_task_key=TASK_CLEAN, task_title="Dryer vent cleaning", interval=180, supported_power_types=(POWER_TYPE_NONE,)),
    _generic_definition("outdoor_lighting", "Outdoor lighting", "Track seasonal bulb and fixture checks.", "Pest/seasonal/other owner tasks", CATALOG_TIER_ADVANCED, OWNER_DWELLINGS, (OWNERSHIP_TYPE_OWNER,), primary_task_key=TASK_CHECK, task_title="Lighting check", interval=180, supported_power_types=(POWER_TYPE_ELECTRIC,)),
)

_CATALOG = {definition.key: definition for definition in SUPPORTED_EQUIPMENT}

POWER_TYPE_LABELS = {
    POWER_TYPE_BATTERY: "Battery-powered",
    POWER_TYPE_WIRED: "Wired",
    POWER_TYPE_WIRED_WITH_BATTERY_BACKUP: "Wired with battery backup",
    POWER_TYPE_GAS: "Gas",
    POWER_TYPE_ELECTRIC: "Electric",
    POWER_TYPE_DUAL_FUEL: "Dual fuel",
    POWER_TYPE_MANUAL: "Manual",
    POWER_TYPE_NONE: "No power source",
}

BATTERY_SERVICE_MODE_LABELS = {
    BATTERY_SERVICE_REPLACEABLE: "Replaceable battery",
    BATTERY_SERVICE_SEALED_LIFE: "Sealed 10-year battery",
}


def get_equipment_definition(key: str) -> EquipmentDefinition:
    return _CATALOG[key]


def get_supported_definitions(
    *,
    profile: HomeProfile | None = None,
    tier: str | None = None,
    include_unsupported: bool = False,
) -> tuple[EquipmentDefinition, ...]:
    definitions = SUPPORTED_EQUIPMENT
    if tier is not None:
        definitions = tuple(definition for definition in definitions if definition.tier == tier)
    if include_unsupported or profile is None:
        return definitions
    return tuple(definition for definition in definitions if is_definition_applicable(definition, profile))


def get_recommended_definitions(profile: HomeProfile) -> tuple[EquipmentDefinition, ...]:
    return get_supported_definitions(profile=profile, tier=CATALOG_TIER_BASIC)


def is_definition_applicable(definition: EquipmentDefinition, profile: HomeProfile) -> bool:
    return (
        profile.dwelling_type in definition.applicable_dwellings
        and profile.ownership_type in definition.applicable_ownership
    )


def supports_battery(definition: EquipmentDefinition, power_type: str, battery_service_mode: str | None = None) -> bool:
    battery_task = next((task for task in definition.tasks if task.key == TASK_BATTERY), None)
    if battery_task is None:
        return False
    if definition.key == EQUIPMENT_TYPE_FIRE_ALARMS and battery_service_mode == BATTERY_SERVICE_SEALED_LIFE:
        return False
    if battery_task.allowed_power_types is None:
        return True
    return power_type in battery_task.allowed_power_types


def available_task_definitions(
    definition: EquipmentDefinition,
    power_type: str,
    battery_service_mode: str | None = None,
) -> tuple[TaskDefinition, ...]:
    return tuple(
        task
        for task in definition.tasks
        if (task.allowed_power_types is None or power_type in task.allowed_power_types)
        and not (
            definition.key == EQUIPMENT_TYPE_FIRE_ALARMS
            and task.key == TASK_BATTERY
            and battery_service_mode == BATTERY_SERVICE_SEALED_LIFE
        )
    )


def get_supported_categories(*, profile: HomeProfile | None = None, tier: str | None = None) -> tuple[str, ...]:
    categories = []
    for definition in get_supported_definitions(profile=profile, tier=tier):
        if definition.category not in categories:
            categories.append(definition.category)
    return tuple(categories)


def build_custom_definition(label: str, category: str) -> EquipmentDefinition:
    return EquipmentDefinition(
        key=EQUIPMENT_TYPE_CUSTOM,
        label=label,
        description="User-defined custom maintenance system.",
        category=category,
        tier=CATALOG_TIER_ADVANCED,
        applicable_dwellings=ALL_DWELLINGS,
        applicable_ownership=(OWNERSHIP_TYPE_OWNER, OWNERSHIP_TYPE_RENTER),
        primary_task_key=TASK_SERVICE,
        supported_power_types=(POWER_TYPE_NONE,),
        default_power_type=POWER_TYPE_NONE,
        tasks=(),
    )
