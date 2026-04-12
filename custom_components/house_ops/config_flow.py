"""Config flow for HouseOps."""
from __future__ import annotations

from datetime import date
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    BATTERY_SERVICE_REPLACEABLE,
    CATALOG_TIER_ADVANCED,
    CATALOG_TIER_BASIC,
    CONF_ADD_ANOTHER_TASK,
    CONF_ANODE_INTERVAL_DAYS,
    CONF_AREA_ID,
    CONF_ASSETS,
    CONF_ASSET_ID,
    CONF_ASSET_NAME,
    CONF_BASE_INTERVAL_DAYS,
    CONF_BATTERY_INTERVAL_DAYS,
    CONF_BATTERY_SENSOR,
    CONF_BATTERY_SERVICE_MODE,
    CONF_BATTERY_THRESHOLD,
    CONF_CATALOG_TIER,
    CONF_CATALOG_VIEW,
    CONF_CONTACT_CLEANING_INTERVAL_DAYS,
    CONF_CONFIRM_REMOVE,
    CONF_CUSTOM_AREA,
    CONF_CUSTOM_CATEGORY,
    CONF_DOCK_SOURCE_ENTITY,
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
    CONF_INSTANCE_NAME,
    CONF_INSPECTION_INTERVAL_DAYS,
    CONF_LAST_SERVICED_DATE,
    CONF_MAIN_BRUSH_INTERVAL_DAYS,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_MOP_SERVICE_INTERVAL_DAYS,
    CONF_NEXT_ACTION,
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
    CONF_SEARCH_QUERY,
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
    DEFAULT_INSTANCE_NAME,
    DOMAIN,
    DWELLING_TYPE_APARTMENT,
    DWELLING_TYPE_CONDO,
    DWELLING_TYPE_MOBILE_HOME,
    DWELLING_TYPE_MULTI_FAMILY,
    DWELLING_TYPE_SINGLE_FAMILY,
    DWELLING_TYPE_TOWNHOME,
    EQUIPMENT_TYPE_CUSTOM,
    EQUIPMENT_TYPE_FIRE_ALARMS,
    EQUIPMENT_TYPE_ROBOT_VACUUM,
    OWNERSHIP_TYPE_OWNER,
    OWNERSHIP_TYPE_RENTER,
    POWER_TYPE_WIRED,
    ROBOT_DOCK_TYPE_AUTO_EMPTY,
    ROBOT_DOCK_TYPE_CHARGE_ONLY,
    ROBOT_DOCK_TYPE_FULL_SERVICE,
    ROBOT_MOP_STYLE_DUAL_PAD,
    ROBOT_MOP_STYLE_NONE,
    ROBOT_MOP_STYLE_SINGLE_PAD_OR_ROLLER,
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
    TASK_INSPECTION,
    TASK_MAIN_BRUSH,
    TASK_MOP_SERVICE,
    TASK_REPLACEMENT,
    TASK_SENSOR_CLEANING,
    TASK_SIDE_BRUSH,
    TASK_WATER_TANK_CLEANING,
    TASK_WHEEL_CLEAN,
)
from .equipment_catalog import (
    BATTERY_SERVICE_MODE_LABELS,
    POWER_TYPE_LABELS,
    EquipmentDefinition,
    build_custom_definition,
    get_equipment_definition,
    get_recommended_definitions,
    get_supported_categories,
    get_supported_definitions,
    supports_battery,
)
from .registry import (
    asset_summary,
    build_asset_from_input,
    build_home_profile_from_input,
    default_home_profile,
    dump_assets,
    dump_home_profile,
    find_asset,
    load_assets,
    load_profile_from_entry,
    remove_asset,
    upsert_asset,
)

CREATE_CUSTOM_OPTION = "__create_custom__"


class HouseOpsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HouseOps."""

    VERSION = 1

    def __init__(self) -> None:
        self._instance_name = DEFAULT_INSTANCE_NAME
        self._profile = default_home_profile()
        self._selected_equipment_type: str | None = None
        self._catalog_view = CATALOG_TIER_BASIC
        self._custom_asset_input: dict[str, Any] = {}
        self._custom_tasks: list[dict[str, Any]] = []
        self._robot_defaults: dict[str, Any] = {}
        self._template_search_query = ""
        self._robot_step_complete = False

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
            return await self.async_step_home_profile()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_INSTANCE_NAME, default=DEFAULT_INSTANCE_NAME): selector.TextSelector(),
                }
            ),
        )

    async def async_step_home_profile(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._profile = build_home_profile_from_input(user_input)
            return await self.async_step_add_system()
        return self.async_show_form(step_id="home_profile", data_schema=_home_profile_schema(self._profile))

    async def async_step_add_system(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return await self._async_handle_add_system_action(user_input[CONF_NEXT_ACTION])
        return self.async_show_form(
            step_id="add_system",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NEXT_ACTION): _action_selector(
                        [
                            ("recommended_systems", "Recommended systems"),
                            ("browse_systems", "Browse all templates"),
                            ("search_systems", "Search templates"),
                            ("create_custom_system", "Create custom system"),
                        ]
                    )
                }
            ),
            description_placeholders={"equipment_summary": _definition_summary_text(get_recommended_definitions(self._profile))},
        )

    async def async_step_recommended_systems(self, user_input: dict[str, Any] | None = None):
        definitions = get_recommended_definitions(self._profile)
        if user_input is not None:
            return await self._async_handle_template_selection(user_input[CONF_EQUIPMENT_TYPE])
        return self.async_show_form(
            step_id="recommended_systems",
            data_schema=vol.Schema({vol.Required(CONF_EQUIPMENT_TYPE): _definition_selector(definitions, include_custom_option=True)}),
            description_placeholders={"equipment_summary": _definition_summary_text(definitions)},
        )

    async def async_step_browse_systems(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._catalog_view = str(user_input[CONF_CATALOG_VIEW])
            return await self._async_handle_template_selection(user_input[CONF_EQUIPMENT_TYPE])
        definitions = get_supported_definitions(
            profile=self._profile,
            tier=None if self._catalog_view == "all" else self._catalog_view,
        )
        return self.async_show_form(
            step_id="browse_systems",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CATALOG_VIEW, default=self._catalog_view): _catalog_view_selector(),
                    vol.Required(CONF_EQUIPMENT_TYPE): _definition_selector(definitions, include_custom_option=True),
                }
            ),
            description_placeholders={"equipment_summary": _definition_summary_text(definitions)},
        )

    async def async_step_search_systems(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._catalog_view = str(user_input[CONF_CATALOG_VIEW])
            self._template_search_query = str(user_input.get(CONF_SEARCH_QUERY, "")).strip()
            return await self.async_step_search_system_results()
        return self.async_show_form(
            step_id="search_systems",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CATALOG_VIEW, default=self._catalog_view): _catalog_view_selector(),
                    vol.Optional(CONF_SEARCH_QUERY, default=self._template_search_query): _search_text_selector(),
                }
            ),
        )

    async def async_step_search_system_results(self, user_input: dict[str, Any] | None = None):
        definitions = _filter_definitions(
            get_supported_definitions(profile=self._profile, tier=None if self._catalog_view == "all" else self._catalog_view),
            self._template_search_query,
        )
        if user_input is not None:
            return await self._async_handle_template_selection(user_input[CONF_EQUIPMENT_TYPE], search_query=self._template_search_query)
        return self.async_show_form(
            step_id="search_system_results",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EQUIPMENT_TYPE): _definition_selector(definitions, include_custom_option=True),
                }
            ),
            description_placeholders={
                "equipment_summary": _definition_summary_text(definitions),
                "search_query": self._template_search_query or "all templates",
            },
        )

    async def async_step_create_custom_system(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            cleaned = _sanitize_asset_input(user_input)
            if not cleaned.get(CONF_ASSET_NAME):
                errors[CONF_ASSET_NAME] = "required"
            else:
                self._custom_asset_input = cleaned
                self._custom_tasks = []
                return await self.async_step_custom_system_task()
        defaults = {
            CONF_EQUIPMENT_TYPE: EQUIPMENT_TYPE_CUSTOM,
            CONF_CATALOG_TIER: CATALOG_TIER_ADVANCED,
        }
        defaults.update(self._custom_asset_input)
        return self.async_show_form(
            step_id="create_custom_system",
            data_schema=_build_custom_asset_schema(self._profile, defaults),
            errors=errors,
        )

    async def async_step_custom_system_task(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            cleaned = _sanitize_custom_task_input(user_input)
            if not cleaned.get(CONF_TASK_TITLE):
                errors[CONF_TASK_TITLE] = "required"
            else:
                self._custom_tasks.append(cleaned)
                if cleaned.get(CONF_ADD_ANOTHER_TASK):
                    return await self.async_step_custom_system_task()
                return await self._async_finish_initial_entry()
        return self.async_show_form(
            step_id="custom_system_task",
            data_schema=_custom_task_schema(add_another_default=len(self._custom_tasks) == 0),
            errors=errors,
            description_placeholders={"task_count": str(len(self._custom_tasks))},
        )

    async def async_step_add_equipment_details(self, user_input: dict[str, Any] | None = None):
        definition = get_equipment_definition(self._selected_equipment_type or get_supported_definitions()[0].key)
        errors: dict[str, str] = {}

        if definition.key == EQUIPMENT_TYPE_ROBOT_VACUUM and not self._robot_step_complete and user_input is None:
            return await self.async_step_robot_vacuum_capabilities()

        if user_input is not None:
            cleaned = _sanitize_asset_input(user_input)
            cleaned.update(self._robot_defaults)
            asset = build_asset_from_input(self.hass, cleaned)
            if not asset.name:
                errors[CONF_ASSET_NAME] = "required"
            else:
                return await self._async_finish_initial_entry(asset)

        defaults = _defaults_for_new_asset(definition.key)
        defaults.update(self._robot_defaults)
        return self.async_show_form(
            step_id="add_equipment_details",
            data_schema=_build_asset_schema(definition, defaults),
            errors=errors,
            description_placeholders={
                "equipment_label": definition.label,
                "equipment_description": definition.description,
                "primary_task": _primary_task_label(definition),
            },
        )

    async def async_step_robot_vacuum_capabilities(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._robot_defaults = _sanitize_asset_input(
                {
                    CONF_EQUIPMENT_TYPE: EQUIPMENT_TYPE_ROBOT_VACUUM,
                    **user_input,
                }
            )
            self._robot_step_complete = True
            return await self.async_step_add_equipment_details()
        defaults = {**_defaults_for_new_asset(EQUIPMENT_TYPE_ROBOT_VACUUM), **self._robot_defaults}
        return self.async_show_form(
            step_id="robot_vacuum_capabilities",
            data_schema=_robot_capability_schema(defaults),
        )

    async def _async_handle_add_system_action(self, selected_action: str):
        if selected_action == "recommended_systems":
            return await self.async_step_recommended_systems()
        if selected_action == "browse_systems":
            return await self.async_step_browse_systems()
        if selected_action == "search_systems":
            return await self.async_step_search_systems()
        return await self.async_step_create_custom_system()

    async def _async_handle_template_selection(self, selected_equipment_type: str, *, search_query: str = ""):
        selected = str(selected_equipment_type)
        if selected == CREATE_CUSTOM_OPTION:
            self._custom_asset_input = _prepare_custom_defaults(search_query)
            return await self.async_step_create_custom_system()
        self._selected_equipment_type = selected
        self._robot_step_complete = False
        self._robot_defaults = {}
        return await self.async_step_add_equipment_details()

    async def _async_finish_initial_entry(self, asset=None):
        if asset is None:
            payload = dict(self._custom_asset_input)
            payload["custom_tasks"] = self._custom_tasks
            asset = build_asset_from_input(self.hass, payload)
        return self.async_create_entry(
            title=self._instance_name,
            data={
                CONF_INSTANCE_NAME: self._instance_name,
                CONF_ASSETS: dump_assets([asset]),
                CONF_HOME_PROFILE: dump_home_profile(self._profile),
            },
        )


class HouseOpsOptionsFlow(config_entries.OptionsFlow):
    """Manage equipment inside HouseOps."""

    def __init__(self, config_entry) -> None:
        self._config_entry = config_entry
        self._selected_asset_id: str | None = None
        self._selected_equipment_type: str | None = None
        self._catalog_view = CATALOG_TIER_BASIC
        self._profile = load_profile_from_entry(config_entry)
        self._custom_asset_input: dict[str, Any] = {}
        self._custom_tasks: list[dict[str, Any]] = []
        self._robot_defaults: dict[str, Any] = {}
        self._template_search_query = ""
        self._asset_search_query = ""
        self._asset_search_mode = "review"
        self._robot_step_complete = False

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        if user_input is not None:
            return await self._async_handle_manage_action(user_input[CONF_NEXT_ACTION])
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NEXT_ACTION): _action_selector(
                        [
                            ("review_equipment", "Review systems"),
                            ("add_system", "Add system"),
                            ("edit_equipment", "Edit system"),
                            ("remove_equipment", "Remove system"),
                            ("edit_home_profile", "Edit home profile"),
                        ]
                    )
                }
            ),
            description_placeholders={"equipment_summary": _equipment_summary_text(assets, self._profile)},
        )

    async def async_step_edit_home_profile(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._profile = build_home_profile_from_input(user_input)
            return self.async_create_entry(title="", data=self._options_payload())
        return self.async_show_form(step_id="edit_home_profile", data_schema=_home_profile_schema(self._profile))

    async def async_step_review_equipment(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        if not assets:
            return await self.async_step_init()
        if user_input is not None:
            self._asset_search_query = str(user_input.get(CONF_SEARCH_QUERY, "")).strip()
            self._asset_search_mode = "review"
            return await self.async_step_asset_search_results()
        return self.async_show_form(
            step_id="review_equipment",
            data_schema=_asset_search_schema(self._asset_search_query),
            description_placeholders={"equipment_summary": _equipment_summary_text(assets, self._profile)},
        )

    async def async_step_review_equipment_details(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        asset = find_asset(assets, self._selected_asset_id or "")
        if asset is None:
            return self.async_abort(reason="asset_not_found")
        if user_input is not None:
            selected_action = user_input[CONF_NEXT_ACTION]
            if selected_action == "back_to_manage":
                return await self.async_step_init()
            if selected_action == "edit_selected_equipment":
                self._robot_step_complete = False
                self._robot_defaults = {}
                return await self.async_step_edit_equipment_details()
            return await self.async_step_remove_selected_equipment()
        return self.async_show_form(
            step_id="review_equipment_details",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NEXT_ACTION): _action_selector(
                        [
                            ("edit_selected_equipment", "Edit this system"),
                            ("remove_selected_equipment", "Remove this system"),
                            ("back_to_manage", "Back to system manager"),
                        ]
                    )
                }
            ),
            description_placeholders={"asset_summary": asset_summary(asset)},
        )

    async def async_step_add_system(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            action = str(user_input[CONF_NEXT_ACTION])
            if action == "recommended_systems":
                return await self.async_step_recommended_systems()
            if action == "browse_systems":
                return await self.async_step_browse_systems()
            if action == "search_systems":
                return await self.async_step_search_systems()
            return await self.async_step_create_custom_system()
        return self.async_show_form(
            step_id="add_system",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NEXT_ACTION): _action_selector(
                        [
                            ("recommended_systems", "Recommended systems"),
                            ("browse_systems", "Browse all templates"),
                            ("search_systems", "Search templates"),
                            ("create_custom_system", "Create custom system"),
                        ]
                    )
                }
            ),
            description_placeholders={"equipment_summary": _definition_summary_text(get_recommended_definitions(self._profile))},
        )

    async def async_step_recommended_systems(self, user_input: dict[str, Any] | None = None):
        definitions = get_recommended_definitions(self._profile)
        if user_input is not None:
            return await self._async_handle_template_selection(user_input[CONF_EQUIPMENT_TYPE])
        return self.async_show_form(
            step_id="recommended_systems",
            data_schema=vol.Schema({vol.Required(CONF_EQUIPMENT_TYPE): _definition_selector(definitions, include_custom_option=True)}),
            description_placeholders={"equipment_summary": _definition_summary_text(definitions)},
        )

    async def async_step_browse_systems(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._catalog_view = str(user_input[CONF_CATALOG_VIEW])
            return await self._async_handle_template_selection(user_input[CONF_EQUIPMENT_TYPE])
        definitions = get_supported_definitions(
            profile=self._profile,
            tier=None if self._catalog_view == "all" else self._catalog_view,
        )
        return self.async_show_form(
            step_id="browse_systems",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CATALOG_VIEW, default=self._catalog_view): _catalog_view_selector(),
                    vol.Required(CONF_EQUIPMENT_TYPE): _definition_selector(definitions, include_custom_option=True),
                }
            ),
            description_placeholders={"equipment_summary": _definition_summary_text(definitions)},
        )

    async def async_step_search_systems(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._catalog_view = str(user_input[CONF_CATALOG_VIEW])
            self._template_search_query = str(user_input.get(CONF_SEARCH_QUERY, "")).strip()
            return await self.async_step_search_system_results()
        return self.async_show_form(
            step_id="search_systems",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CATALOG_VIEW, default=self._catalog_view): _catalog_view_selector(),
                    vol.Optional(CONF_SEARCH_QUERY, default=self._template_search_query): _search_text_selector(),
                }
            ),
        )

    async def async_step_search_system_results(self, user_input: dict[str, Any] | None = None):
        definitions = _filter_definitions(
            get_supported_definitions(profile=self._profile, tier=None if self._catalog_view == "all" else self._catalog_view),
            self._template_search_query,
        )
        if user_input is not None:
            return await self._async_handle_template_selection(user_input[CONF_EQUIPMENT_TYPE], search_query=self._template_search_query)
        return self.async_show_form(
            step_id="search_system_results",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EQUIPMENT_TYPE): _definition_selector(definitions, include_custom_option=True),
                }
            ),
            description_placeholders={
                "equipment_summary": _definition_summary_text(definitions),
                "search_query": self._template_search_query or "all templates",
            },
        )

    async def async_step_create_custom_system(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            cleaned = _sanitize_asset_input(user_input)
            if not cleaned.get(CONF_ASSET_NAME):
                errors[CONF_ASSET_NAME] = "required"
            else:
                self._custom_asset_input = cleaned
                self._custom_tasks = []
                return await self.async_step_custom_system_task()
        defaults = {
            CONF_EQUIPMENT_TYPE: EQUIPMENT_TYPE_CUSTOM,
            CONF_CATALOG_TIER: CATALOG_TIER_ADVANCED,
        }
        defaults.update(self._custom_asset_input)
        return self.async_show_form(
            step_id="create_custom_system",
            data_schema=_build_custom_asset_schema(self._profile, defaults),
            errors=errors,
        )

    async def async_step_custom_system_task(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        if user_input is not None:
            cleaned = _sanitize_custom_task_input(user_input)
            if not cleaned.get(CONF_TASK_TITLE):
                errors[CONF_TASK_TITLE] = "required"
            else:
                self._custom_tasks.append(cleaned)
                if cleaned.get(CONF_ADD_ANOTHER_TASK):
                    return await self.async_step_custom_system_task()
                return await self._async_create_or_update_custom_asset()
        return self.async_show_form(
            step_id="custom_system_task",
            data_schema=_custom_task_schema(add_another_default=len(self._custom_tasks) == 0),
            errors=errors,
            description_placeholders={"task_count": str(len(self._custom_tasks))},
        )

    async def async_step_add_equipment_details(self, user_input: dict[str, Any] | None = None):
        definition = get_equipment_definition(self._selected_equipment_type or get_supported_definitions()[0].key)
        assets = _load_entry_assets(self._config_entry)
        errors: dict[str, str] = {}
        if definition.key == EQUIPMENT_TYPE_ROBOT_VACUUM and not self._robot_step_complete and user_input is None:
            return await self.async_step_robot_vacuum_capabilities()
        if user_input is not None:
            cleaned = _sanitize_asset_input(user_input)
            cleaned.update(self._robot_defaults)
            asset = build_asset_from_input(self.hass, cleaned, existing_assets=assets)
            if not asset.name:
                errors[CONF_ASSET_NAME] = "required"
            else:
                updated_assets = upsert_asset(assets, asset)
                return self.async_create_entry(title="", data=self._options_payload(assets=updated_assets))
        return self.async_show_form(
            step_id="add_equipment_details",
            data_schema=_build_asset_schema(definition, {**_defaults_for_new_asset(definition.key), **self._robot_defaults}),
            errors=errors,
            description_placeholders={
                "equipment_label": definition.label,
                "equipment_description": definition.description,
                "primary_task": _primary_task_label(definition),
            },
        )

    async def async_step_edit_equipment(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        if not assets:
            return await self.async_step_init()
        if user_input is not None:
            self._asset_search_query = str(user_input.get(CONF_SEARCH_QUERY, "")).strip()
            self._asset_search_mode = "edit"
            return await self.async_step_asset_search_results()
        return self.async_show_form(
            step_id="edit_equipment",
            data_schema=_asset_search_schema(self._asset_search_query),
            description_placeholders={"equipment_summary": _equipment_summary_text(assets, self._profile)},
        )

    async def async_step_edit_selected_equipment(self, user_input: dict[str, Any] | None = None):
        return await self.async_step_edit_equipment_details()

    async def async_step_edit_equipment_details(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        asset = find_asset(assets, self._selected_asset_id or "")
        if asset is None:
            return self.async_abort(reason="asset_not_found")

        if asset.equipment_type == EQUIPMENT_TYPE_ROBOT_VACUUM and not self._robot_step_complete and user_input is None:
            self._robot_defaults = _defaults_from_asset(asset)
            return await self.async_step_edit_robot_vacuum_capabilities()

        errors: dict[str, str] = {}
        if user_input is not None:
            cleaned = _sanitize_asset_input(user_input)
            cleaned.update(self._robot_defaults)
            if asset.is_custom:
                cleaned["custom_tasks"] = [_task_to_flow_default(task) for task in asset.tasks]
                cleaned[CONF_EQUIPMENT_TYPE] = EQUIPMENT_TYPE_CUSTOM
            updated = build_asset_from_input(
                self.hass,
                cleaned,
                existing_assets=assets,
                existing_asset=asset,
            )
            if not updated.name:
                errors[CONF_ASSET_NAME] = "required"
            else:
                updated_assets = upsert_asset(assets, updated)
                return self.async_create_entry(title="", data=self._options_payload(assets=updated_assets))

        if asset.is_custom:
            return self.async_show_form(
                step_id="edit_equipment_details",
                data_schema=_build_custom_asset_schema(self._profile, _defaults_from_custom_asset(asset)),
                errors=errors,
            )

        definition = get_equipment_definition(asset.equipment_type)
        return self.async_show_form(
            step_id="edit_equipment_details",
            data_schema=_build_asset_schema(definition, {**_defaults_from_asset(asset), **self._robot_defaults}),
            errors=errors,
            description_placeholders={
                "equipment_label": asset.name,
                "equipment_description": asset_summary(asset),
                "primary_task": _primary_task_label(definition),
            },
        )

    async def async_step_remove_equipment(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        if not assets:
            return await self.async_step_init()
        if user_input is not None:
            self._asset_search_query = str(user_input.get(CONF_SEARCH_QUERY, "")).strip()
            self._asset_search_mode = "remove"
            return await self.async_step_asset_search_results()
        return self.async_show_form(
            step_id="remove_equipment",
            data_schema=_asset_search_schema(self._asset_search_query),
            description_placeholders={"equipment_summary": _equipment_summary_text(assets, self._profile)},
        )

    async def async_step_remove_selected_equipment(self, user_input: dict[str, Any] | None = None):
        assets = _load_entry_assets(self._config_entry)
        asset = find_asset(assets, self._selected_asset_id or "")
        if asset is None:
            return self.async_abort(reason="asset_not_found")
        if user_input is not None and user_input.get(CONF_CONFIRM_REMOVE):
            updated_assets = remove_asset(assets, asset.asset_id)
            return self.async_create_entry(title="", data=self._options_payload(assets=updated_assets))
        return self.async_show_form(
            step_id="remove_selected_equipment",
            data_schema=vol.Schema({vol.Required(CONF_CONFIRM_REMOVE, default=False): selector.BooleanSelector()}),
            description_placeholders={"asset_summary": asset_summary(asset)},
        )

    async def _async_handle_manage_action(self, selected_action: str):
        if selected_action == "review_equipment":
            return await self.async_step_review_equipment()
        if selected_action == "add_system":
            return await self.async_step_add_system()
        if selected_action == "edit_equipment":
            return await self.async_step_edit_equipment()
        if selected_action == "edit_home_profile":
            return await self.async_step_edit_home_profile()
        return await self.async_step_remove_equipment()

    async def _async_create_or_update_custom_asset(self):
        assets = _load_entry_assets(self._config_entry)
        payload = dict(self._custom_asset_input)
        payload["custom_tasks"] = self._custom_tasks
        asset = build_asset_from_input(self.hass, payload, existing_assets=assets)
        updated_assets = upsert_asset(assets, asset)
        return self.async_create_entry(title="", data=self._options_payload(assets=updated_assets))

    async def async_step_robot_vacuum_capabilities(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._robot_defaults = _sanitize_asset_input(
                {
                    CONF_EQUIPMENT_TYPE: EQUIPMENT_TYPE_ROBOT_VACUUM,
                    **user_input,
                }
            )
            self._robot_step_complete = True
            return await self.async_step_add_equipment_details()
        defaults = {**_defaults_for_new_asset(EQUIPMENT_TYPE_ROBOT_VACUUM), **self._robot_defaults}
        return self.async_show_form(
            step_id="robot_vacuum_capabilities",
            data_schema=_robot_capability_schema(defaults),
        )

    async def async_step_edit_robot_vacuum_capabilities(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            self._robot_defaults = _sanitize_asset_input(
                {
                    CONF_EQUIPMENT_TYPE: EQUIPMENT_TYPE_ROBOT_VACUUM,
                    **user_input,
                }
            )
            self._robot_step_complete = True
            return await self.async_step_edit_equipment_details()
        return self.async_show_form(
            step_id="edit_robot_vacuum_capabilities",
            data_schema=_robot_capability_schema(self._robot_defaults),
        )

    async def async_step_asset_search_results(self, user_input: dict[str, Any] | None = None):
        assets = _filter_assets(_load_entry_assets(self._config_entry), self._asset_search_query)
        if user_input is not None:
            self._selected_asset_id = str(user_input[CONF_ASSET_ID])
            if self._asset_search_mode == "review":
                return await self.async_step_review_equipment_details()
            if self._asset_search_mode == "edit":
                self._robot_step_complete = False
                self._robot_defaults = {}
                return await self.async_step_edit_equipment_details()
            return await self.async_step_remove_selected_equipment()
        if not assets:
            if self._asset_search_mode == "review":
                return await self.async_step_review_equipment()
            if self._asset_search_mode == "edit":
                return await self.async_step_edit_equipment()
            return await self.async_step_remove_equipment()
        return self.async_show_form(
            step_id="asset_search_results",
            data_schema=_asset_select_schema(assets),
            description_placeholders={"equipment_summary": _equipment_summary_text(assets, self._profile)},
        )

    async def _async_handle_template_selection(self, selected_equipment_type: str, *, search_query: str = ""):
        selected = str(selected_equipment_type)
        if selected == CREATE_CUSTOM_OPTION:
            self._custom_asset_input = _prepare_custom_defaults(search_query)
            return await self.async_step_create_custom_system()
        self._selected_equipment_type = selected
        self._robot_step_complete = False
        self._robot_defaults = {}
        return await self.async_step_add_equipment_details()

    def _options_payload(self, *, assets=None) -> dict[str, Any]:
        current_assets = assets if assets is not None else _load_entry_assets(self._config_entry)
        return {
            CONF_ASSETS: dump_assets(current_assets),
            CONF_HOME_PROFILE: dump_home_profile(self._profile),
        }


def _build_asset_schema(definition: EquipmentDefinition, defaults: dict[str, Any]) -> vol.Schema:
    power_type = str(defaults.get(CONF_POWER_TYPE, definition.default_power_type))
    schema: dict[Any, Any] = {}

    _add_required(schema, CONF_EQUIPMENT_TYPE, _equipment_selector((definition,)), default=definition.key)
    _add_required(schema, CONF_ASSET_NAME, selector.TextSelector(), default=defaults.get(CONF_ASSET_NAME, ""))
    _add_optional(schema, CONF_SOURCE_ENTITY, _device_selector(), default=defaults.get(CONF_SOURCE_ENTITY))
    if definition.key == EQUIPMENT_TYPE_ROBOT_VACUUM:
        _add_optional(schema, CONF_DOCK_SOURCE_ENTITY, _device_selector(), default=defaults.get(CONF_DOCK_SOURCE_ENTITY))
    _add_optional(schema, CONF_AREA_ID, selector.AreaSelector(), default=defaults.get(CONF_AREA_ID))
    _add_optional(schema, CONF_CUSTOM_AREA, selector.TextSelector(), default=defaults.get(CONF_CUSTOM_AREA))

    if len(definition.supported_power_types) > 1:
        _add_required(schema, CONF_POWER_TYPE, _power_selector(definition), default=power_type)

    battery_service_mode = str(defaults.get(CONF_BATTERY_SERVICE_MODE, BATTERY_SERVICE_REPLACEABLE))
    if definition.key == EQUIPMENT_TYPE_FIRE_ALARMS and power_type != POWER_TYPE_WIRED:
        _add_required(schema, CONF_BATTERY_SERVICE_MODE, _battery_service_mode_selector(), default=battery_service_mode)

    _add_optional(schema, CONF_MANUFACTURER, selector.TextSelector(), default=defaults.get(CONF_MANUFACTURER))
    _add_optional(schema, CONF_MODEL, selector.TextSelector(), default=defaults.get(CONF_MODEL))
    _add_optional(schema, CONF_NOTES, selector.TextSelector(selector.TextSelectorConfig(multiline=True)), default=defaults.get(CONF_NOTES))
    _add_optional(schema, CONF_INSTALL_DATE, selector.DateSelector(), default=defaults.get(CONF_INSTALL_DATE))
    _add_optional(schema, CONF_LAST_SERVICED_DATE, selector.DateSelector(), default=defaults.get(CONF_LAST_SERVICED_DATE))
    _add_optional(schema, CONF_NEXT_DUE_OVERRIDE, selector.DateSelector(), default=defaults.get(CONF_NEXT_DUE_OVERRIDE))
    _add_required(schema, CONF_BASE_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults[CONF_BASE_INTERVAL_DAYS])

    if definition.key == EQUIPMENT_TYPE_ROBOT_VACUUM:
        _add_robot_interval_fields(schema, defaults)

    if _task_exists(definition, TASK_INSPECTION):
        _add_optional(schema, CONF_INSPECTION_INTERVAL_DAYS, _number_selector(30, 3650, 1), default=defaults.get(CONF_INSPECTION_INTERVAL_DAYS))

    if _task_exists(definition, TASK_ANODE):
        _add_optional(schema, CONF_ENABLE_ANODE_TASK, selector.BooleanSelector(), default=defaults.get(CONF_ENABLE_ANODE_TASK, False))
        if defaults.get(CONF_ENABLE_ANODE_TASK):
            _add_optional(schema, CONF_ANODE_INTERVAL_DAYS, _number_selector(180, 3650, 1), default=defaults.get(CONF_ANODE_INTERVAL_DAYS))

    if _show_sensor_section(definition):
        _add_optional(schema, CONF_RUNTIME_SENSOR, _entity_selector(["sensor", "number", "input_number"]), default=defaults.get(CONF_RUNTIME_SENSOR))
        _add_optional(schema, CONF_RUNTIME_THRESHOLD, _number_selector(0, 100000, 1), default=defaults.get(CONF_RUNTIME_THRESHOLD))
        _add_optional(schema, CONF_USAGE_SENSOR, _entity_selector(["sensor", "number", "input_number"]), default=defaults.get(CONF_USAGE_SENSOR))
        _add_optional(schema, CONF_USAGE_THRESHOLD, _number_selector(0, 100000, 1), default=defaults.get(CONF_USAGE_THRESHOLD))

    if supports_battery(definition, power_type, battery_service_mode):
        _add_optional(schema, CONF_BATTERY_SENSOR, _entity_selector(["sensor", "number"]), default=defaults.get(CONF_BATTERY_SENSOR))
        _add_optional(schema, CONF_BATTERY_THRESHOLD, _number_selector(1, 100, 1), default=defaults.get(CONF_BATTERY_THRESHOLD, DEFAULT_BATTERY_THRESHOLD))
        _add_optional(schema, CONF_BATTERY_INTERVAL_DAYS, _number_selector(30, 730, 1), default=defaults.get(CONF_BATTERY_INTERVAL_DAYS))

    if _task_exists(definition, TASK_REPLACEMENT):
        _add_optional(schema, CONF_REPLACEMENT_INTERVAL_DAYS, _number_selector(365, 7300, 1), default=defaults.get(CONF_REPLACEMENT_INTERVAL_DAYS))

    return vol.Schema(schema)


def _build_custom_asset_schema(profile, defaults: dict[str, Any]) -> vol.Schema:
    categories = get_supported_categories(profile=profile)
    custom_definition = build_custom_definition("Custom system", defaults.get(CONF_CUSTOM_CATEGORY, "Custom"))
    schema: dict[Any, Any] = {}
    _add_required(schema, CONF_EQUIPMENT_TYPE, _equipment_selector((custom_definition,)), default=EQUIPMENT_TYPE_CUSTOM)
    _add_required(schema, CONF_ASSET_NAME, selector.TextSelector(), default=defaults.get(CONF_ASSET_NAME, ""))
    _add_optional(
        schema,
        CONF_CUSTOM_CATEGORY,
        selector.SelectSelector(
            selector.SelectSelectorConfig(options=list(categories), custom_value=True, mode=selector.SelectSelectorMode.DROPDOWN)
        ),
        default=defaults.get(CONF_CUSTOM_CATEGORY),
    )
    _add_optional(schema, CONF_SOURCE_ENTITY, _device_selector(), default=defaults.get(CONF_SOURCE_ENTITY))
    _add_optional(schema, CONF_AREA_ID, selector.AreaSelector(), default=defaults.get(CONF_AREA_ID))
    _add_optional(schema, CONF_CUSTOM_AREA, selector.TextSelector(), default=defaults.get(CONF_CUSTOM_AREA))
    _add_optional(schema, CONF_MANUFACTURER, selector.TextSelector(), default=defaults.get(CONF_MANUFACTURER))
    _add_optional(schema, CONF_MODEL, selector.TextSelector(), default=defaults.get(CONF_MODEL))
    _add_optional(schema, CONF_NOTES, selector.TextSelector(selector.TextSelectorConfig(multiline=True)), default=defaults.get(CONF_NOTES))
    _add_optional(schema, CONF_INSTALL_DATE, selector.DateSelector(), default=defaults.get(CONF_INSTALL_DATE))
    _add_optional(schema, CONF_LAST_SERVICED_DATE, selector.DateSelector(), default=defaults.get(CONF_LAST_SERVICED_DATE))
    _add_optional(schema, CONF_CATALOG_TIER, _catalog_tier_selector(), default=defaults.get(CONF_CATALOG_TIER, CATALOG_TIER_ADVANCED))
    return vol.Schema(schema)


def _defaults_for_new_asset(equipment_type: str) -> dict[str, Any]:
    definition = get_equipment_definition(equipment_type)
    defaults: dict[str, Any] = {
        CONF_EQUIPMENT_TYPE: equipment_type,
        CONF_BASE_INTERVAL_DAYS: next(task.default_interval_days for task in definition.tasks if task.key == definition.primary_task_key),
        CONF_POWER_TYPE: definition.default_power_type,
        CONF_BATTERY_SERVICE_MODE: BATTERY_SERVICE_REPLACEABLE,
        CONF_BATTERY_THRESHOLD: DEFAULT_BATTERY_THRESHOLD,
    }
    if equipment_type == EQUIPMENT_TYPE_ROBOT_VACUUM:
        defaults.update(
            {
                CONF_ROBOT_HAS_MOP: False,
                CONF_ROBOT_MOP_STYLE: ROBOT_MOP_STYLE_NONE,
                CONF_ROBOT_DOCK_TYPE: ROBOT_DOCK_TYPE_CHARGE_ONLY,
            }
        )
    for task in definition.tasks:
        if task.key == TASK_INSPECTION:
            defaults[CONF_INSPECTION_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_ANODE:
            defaults[CONF_ENABLE_ANODE_TASK] = False
            defaults[CONF_ANODE_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_BATTERY:
            defaults[CONF_BATTERY_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_REPLACEMENT:
            defaults[CONF_REPLACEMENT_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_DUST_BIN:
            defaults[CONF_DUST_BIN_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_MAIN_BRUSH:
            defaults[CONF_MAIN_BRUSH_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_SIDE_BRUSH:
            defaults[CONF_SIDE_BRUSH_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_WHEEL_CLEAN:
            defaults[CONF_WHEEL_CLEAN_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_SENSOR_CLEANING:
            defaults[CONF_SENSOR_CLEANING_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_CONTACT_CLEANING:
            defaults[CONF_CONTACT_CLEANING_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_MOP_SERVICE:
            defaults[CONF_MOP_SERVICE_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_WATER_TANK_CLEANING:
            defaults[CONF_WATER_TANK_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_DOCK_DUST_BAG:
            defaults[CONF_DOCK_DUST_BAG_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_DOCK_AIR_PATH:
            defaults[CONF_DOCK_AIR_PATH_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_DOCK_CLEAN_WATER_TANK:
            defaults[CONF_DOCK_CLEAN_WATER_TANK_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_DOCK_DIRTY_WATER_TANK:
            defaults[CONF_DOCK_DIRTY_WATER_TANK_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_DOCK_WASH_TRAY:
            defaults[CONF_DOCK_WASH_TRAY_INTERVAL_DAYS] = task.default_interval_days
        elif task.key == TASK_DOCK_WATER_FILTER:
            defaults[CONF_DOCK_WATER_FILTER_INTERVAL_DAYS] = task.default_interval_days
    return defaults


def _defaults_from_asset(asset) -> dict[str, Any]:
    defaults = {
        CONF_EQUIPMENT_TYPE: asset.equipment_type,
        CONF_ASSET_NAME: asset.name,
        CONF_SOURCE_ENTITY: asset.source_entity,
        CONF_DOCK_SOURCE_ENTITY: asset.dock_source_entity,
        CONF_AREA_ID: asset.area_id,
        CONF_CUSTOM_AREA: None if asset.area_id else asset.area,
        CONF_POWER_TYPE: asset.power_type,
        CONF_BATTERY_SERVICE_MODE: asset.battery_service_mode or BATTERY_SERVICE_REPLACEABLE,
        CONF_MANUFACTURER: asset.manufacturer,
        CONF_MODEL: asset.model,
        CONF_NOTES: asset.notes,
        CONF_INSTALL_DATE: asset.install_date,
        CONF_LAST_SERVICED_DATE: asset.last_serviced_date,
        CONF_BASE_INTERVAL_DAYS: next(task.base_interval_days for task in asset.tasks if task.key == asset.primary_task_key),
        CONF_NEXT_DUE_OVERRIDE: next((task.next_due_override for task in asset.tasks if task.key == asset.primary_task_key), None),
        CONF_ROBOT_HAS_MOP: asset.robot_has_mop,
        CONF_ROBOT_MOP_STYLE: asset.robot_mop_style or ROBOT_MOP_STYLE_NONE,
        CONF_ROBOT_DOCK_TYPE: asset.robot_dock_type or ROBOT_DOCK_TYPE_CHARGE_ONLY,
    }
    for task in asset.tasks:
        if task.key == TASK_INSPECTION:
            defaults[CONF_INSPECTION_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_ANODE:
            defaults[CONF_ENABLE_ANODE_TASK] = True
            defaults[CONF_ANODE_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_BATTERY:
            defaults[CONF_BATTERY_INTERVAL_DAYS] = task.base_interval_days
            if task.sensor_links:
                defaults[CONF_BATTERY_SENSOR] = task.sensor_links[0].entity_id
                defaults[CONF_BATTERY_THRESHOLD] = task.sensor_links[0].threshold
        elif task.key == TASK_REPLACEMENT:
            defaults[CONF_REPLACEMENT_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_DUST_BIN:
            defaults[CONF_DUST_BIN_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_MAIN_BRUSH:
            defaults[CONF_MAIN_BRUSH_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_SIDE_BRUSH:
            defaults[CONF_SIDE_BRUSH_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_WHEEL_CLEAN:
            defaults[CONF_WHEEL_CLEAN_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_SENSOR_CLEANING:
            defaults[CONF_SENSOR_CLEANING_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_CONTACT_CLEANING:
            defaults[CONF_CONTACT_CLEANING_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_MOP_SERVICE:
            defaults[CONF_MOP_SERVICE_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_WATER_TANK_CLEANING:
            defaults[CONF_WATER_TANK_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_DOCK_DUST_BAG:
            defaults[CONF_DOCK_DUST_BAG_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_DOCK_AIR_PATH:
            defaults[CONF_DOCK_AIR_PATH_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_DOCK_CLEAN_WATER_TANK:
            defaults[CONF_DOCK_CLEAN_WATER_TANK_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_DOCK_DIRTY_WATER_TANK:
            defaults[CONF_DOCK_DIRTY_WATER_TANK_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_DOCK_WASH_TRAY:
            defaults[CONF_DOCK_WASH_TRAY_INTERVAL_DAYS] = task.base_interval_days
        elif task.key == TASK_DOCK_WATER_FILTER:
            defaults[CONF_DOCK_WATER_FILTER_INTERVAL_DAYS] = task.base_interval_days
        for link in task.sensor_links:
            if link.role == "runtime":
                defaults[CONF_RUNTIME_SENSOR] = link.entity_id
                defaults[CONF_RUNTIME_THRESHOLD] = link.threshold
            elif link.role == "usage":
                defaults[CONF_USAGE_SENSOR] = link.entity_id
                defaults[CONF_USAGE_THRESHOLD] = link.threshold
    return defaults


def _defaults_from_custom_asset(asset) -> dict[str, Any]:
    return {
        CONF_EQUIPMENT_TYPE: EQUIPMENT_TYPE_CUSTOM,
        CONF_ASSET_NAME: asset.name,
        CONF_SOURCE_ENTITY: asset.source_entity,
        CONF_DOCK_SOURCE_ENTITY: asset.dock_source_entity,
        CONF_AREA_ID: asset.area_id,
        CONF_CUSTOM_AREA: None if asset.area_id else asset.area,
        CONF_CUSTOM_CATEGORY: asset.custom_category or asset.category,
        CONF_MANUFACTURER: asset.manufacturer,
        CONF_MODEL: asset.model,
        CONF_NOTES: asset.notes,
        CONF_INSTALL_DATE: asset.install_date,
        CONF_LAST_SERVICED_DATE: asset.last_serviced_date,
        CONF_CATALOG_TIER: asset.catalog_tier or CATALOG_TIER_ADVANCED,
    }


def _task_to_flow_default(task) -> dict[str, Any]:
    return {
        "key": task.key,
        CONF_TASK_TITLE: task.title,
        CONF_TASK_INTERVAL_DAYS: task.base_interval_days,
        CONF_TASK_LAST_SERVICED_DATE: task.last_serviced_date,
        CONF_TASK_NEXT_DUE_OVERRIDE: task.next_due_override,
    }


def _sanitize_asset_input(user_input: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(user_input)
    cleaned[CONF_ASSET_NAME] = str(cleaned.get(CONF_ASSET_NAME, "")).strip()
    cleaned[CONF_EQUIPMENT_TYPE] = str(cleaned[CONF_EQUIPMENT_TYPE])

    for key in (
        CONF_MANUFACTURER,
        CONF_MODEL,
        CONF_NOTES,
        CONF_CUSTOM_AREA,
        CONF_AREA_ID,
        CONF_SOURCE_ENTITY,
        CONF_DOCK_SOURCE_ENTITY,
        CONF_RUNTIME_SENSOR,
        CONF_USAGE_SENSOR,
        CONF_BATTERY_SENSOR,
        CONF_BATTERY_SERVICE_MODE,
        CONF_CUSTOM_CATEGORY,
        CONF_CATALOG_TIER,
        CONF_ROBOT_MOP_STYLE,
        CONF_ROBOT_DOCK_TYPE,
        CONF_SEARCH_QUERY,
    ):
        value = cleaned.get(key)
        if value in (None, ""):
            cleaned.pop(key, None)
        else:
            cleaned[key] = str(value).strip()

    for key in (CONF_INSTALL_DATE, CONF_LAST_SERVICED_DATE, CONF_NEXT_DUE_OVERRIDE):
        value = cleaned.get(key)
        if value in (None, ""):
            cleaned.pop(key, None)
        elif not isinstance(value, date):
            cleaned[key] = date.fromisoformat(str(value))

    for key in (
        CONF_BASE_INTERVAL_DAYS,
        CONF_INSPECTION_INTERVAL_DAYS,
        CONF_ANODE_INTERVAL_DAYS,
        CONF_BATTERY_INTERVAL_DAYS,
        CONF_REPLACEMENT_INTERVAL_DAYS,
        CONF_DUST_BIN_INTERVAL_DAYS,
        CONF_FILTER_INTERVAL_DAYS,
        CONF_MAIN_BRUSH_INTERVAL_DAYS,
        CONF_SIDE_BRUSH_INTERVAL_DAYS,
        CONF_WHEEL_CLEAN_INTERVAL_DAYS,
        CONF_SENSOR_CLEANING_INTERVAL_DAYS,
        CONF_CONTACT_CLEANING_INTERVAL_DAYS,
        CONF_MOP_SERVICE_INTERVAL_DAYS,
        CONF_WATER_TANK_INTERVAL_DAYS,
        CONF_DOCK_DUST_BAG_INTERVAL_DAYS,
        CONF_DOCK_AIR_PATH_INTERVAL_DAYS,
        CONF_DOCK_CLEAN_WATER_TANK_INTERVAL_DAYS,
        CONF_DOCK_DIRTY_WATER_TANK_INTERVAL_DAYS,
        CONF_DOCK_WASH_TRAY_INTERVAL_DAYS,
        CONF_DOCK_WATER_FILTER_INTERVAL_DAYS,
        CONF_RUNTIME_THRESHOLD,
        CONF_USAGE_THRESHOLD,
    ):
        value = cleaned.get(key)
        if value in (None, ""):
            cleaned.pop(key, None)
        else:
            cleaned[key] = int(value)

    if cleaned.get(CONF_BATTERY_THRESHOLD) not in (None, ""):
        cleaned[CONF_BATTERY_THRESHOLD] = float(cleaned[CONF_BATTERY_THRESHOLD])
    else:
        cleaned.pop(CONF_BATTERY_THRESHOLD, None)

    if CONF_POWER_TYPE in cleaned and cleaned[CONF_POWER_TYPE] in (None, ""):
        cleaned.pop(CONF_POWER_TYPE, None)

    cleaned[CONF_ENABLE_ANODE_TASK] = bool(cleaned.get(CONF_ENABLE_ANODE_TASK, False))
    cleaned[CONF_ROBOT_HAS_MOP] = bool(cleaned.get(CONF_ROBOT_HAS_MOP, False))
    return cleaned


def _sanitize_custom_task_input(user_input: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(user_input)
    cleaned[CONF_TASK_TITLE] = str(cleaned.get(CONF_TASK_TITLE, "")).strip()
    for key in (CONF_TASK_LAST_SERVICED_DATE, CONF_TASK_NEXT_DUE_OVERRIDE):
        value = cleaned.get(key)
        if value in (None, ""):
            cleaned.pop(key, None)
        elif not isinstance(value, date):
            cleaned[key] = date.fromisoformat(str(value))
    if cleaned.get(CONF_TASK_INTERVAL_DAYS) not in (None, ""):
        cleaned[CONF_TASK_INTERVAL_DAYS] = int(cleaned[CONF_TASK_INTERVAL_DAYS])
    return cleaned


def _add_required(schema: dict[Any, Any], key: str, field_selector: Any, *, default: Any) -> None:
    schema[vol.Required(key, default=default)] = field_selector


def _add_optional(schema: dict[Any, Any], key: str, field_selector: Any, *, default: Any | None = None) -> None:
    if default is None:
        schema[vol.Optional(key)] = field_selector
    else:
        schema[vol.Optional(key, default=default)] = field_selector


def _number_selector(min_value: int | float, max_value: int | float, step: int | float):
    return selector.NumberSelector(
        selector.NumberSelectorConfig(min=min_value, max=max_value, step=step, mode=selector.NumberSelectorMode.BOX)
    )


def _entity_selector(domains: list[str] | None = None):
    if domains is None:
        return selector.EntitySelector(selector.EntitySelectorConfig())
    return selector.EntitySelector(selector.EntitySelectorConfig(domain=domains))


def _device_selector():
    return selector.DeviceSelector()


def _battery_service_mode_selector():
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=value, label=label)
                for value, label in BATTERY_SERVICE_MODE_LABELS.items()
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _definition_selector(definitions: tuple[EquipmentDefinition, ...], *, include_custom_option: bool = False):
    options = [
        selector.SelectOptionDict(value=definition.key, label=f"{definition.label} ({definition.category})")
        for definition in definitions
    ]
    if include_custom_option:
        options.append(selector.SelectOptionDict(value=CREATE_CUSTOM_OPTION, label="Create custom system instead"))
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _equipment_selector(definitions: tuple[EquipmentDefinition, ...]):
    return _definition_selector(definitions)


def _catalog_view_selector():
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=CATALOG_TIER_BASIC, label="Basic"),
                selector.SelectOptionDict(value=CATALOG_TIER_ADVANCED, label="Advanced"),
                selector.SelectOptionDict(value="all", label="All systems"),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _catalog_tier_selector():
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=CATALOG_TIER_BASIC, label="Basic"),
                selector.SelectOptionDict(value=CATALOG_TIER_ADVANCED, label="Advanced"),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _power_selector(definition):
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=power_type, label=POWER_TYPE_LABELS[power_type])
                for power_type in definition.supported_power_types
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _asset_select_schema(assets) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_ASSET_ID): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[selector.SelectOptionDict(value=asset.asset_id, label=asset.name) for asset in assets],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )


def _asset_search_schema(search_query: str) -> vol.Schema:
    return vol.Schema({vol.Optional(CONF_SEARCH_QUERY, default=search_query): _search_text_selector()})


def _home_profile_schema(profile) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_DWELLING_TYPE, default=profile.dwelling_type): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=DWELLING_TYPE_APARTMENT, label="Apartment"),
                        selector.SelectOptionDict(value=DWELLING_TYPE_CONDO, label="Condo"),
                        selector.SelectOptionDict(value=DWELLING_TYPE_TOWNHOME, label="Townhome"),
                        selector.SelectOptionDict(value=DWELLING_TYPE_SINGLE_FAMILY, label="Single-family house"),
                        selector.SelectOptionDict(value=DWELLING_TYPE_MULTI_FAMILY, label="Multi-family home"),
                        selector.SelectOptionDict(value=DWELLING_TYPE_MOBILE_HOME, label="Mobile home"),
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_OWNERSHIP_TYPE, default=profile.ownership_type): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=OWNERSHIP_TYPE_RENTER, label="Renter"),
                        selector.SelectOptionDict(value=OWNERSHIP_TYPE_OWNER, label="Owner"),
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def _custom_task_schema(*, add_another_default: bool) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_TASK_TITLE): selector.TextSelector(),
            vol.Required(CONF_TASK_INTERVAL_DAYS, default=90): _number_selector(1, 3650, 1),
            vol.Optional(CONF_TASK_LAST_SERVICED_DATE): selector.DateSelector(),
            vol.Optional(CONF_TASK_NEXT_DUE_OVERRIDE): selector.DateSelector(),
            vol.Required(CONF_ADD_ANOTHER_TASK, default=add_another_default): selector.BooleanSelector(),
        }
    )


def _robot_capability_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_ROBOT_MOP_STYLE, default=defaults.get(CONF_ROBOT_MOP_STYLE, ROBOT_MOP_STYLE_NONE)): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=ROBOT_MOP_STYLE_NONE, label="No mop"),
                        selector.SelectOptionDict(value=ROBOT_MOP_STYLE_SINGLE_PAD_OR_ROLLER, label="Single pad / roller mop"),
                        selector.SelectOptionDict(value=ROBOT_MOP_STYLE_DUAL_PAD, label="Dual spinning pads"),
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_ROBOT_DOCK_TYPE, default=defaults.get(CONF_ROBOT_DOCK_TYPE, ROBOT_DOCK_TYPE_CHARGE_ONLY)): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=ROBOT_DOCK_TYPE_CHARGE_ONLY, label="Charging dock"),
                        selector.SelectOptionDict(value=ROBOT_DOCK_TYPE_AUTO_EMPTY, label="Auto-empty dock"),
                        selector.SelectOptionDict(value=ROBOT_DOCK_TYPE_FULL_SERVICE, label="Advanced service dock"),
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def _add_robot_interval_fields(schema: dict[Any, Any], defaults: dict[str, Any]) -> None:
    _add_optional(schema, CONF_DUST_BIN_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_DUST_BIN_INTERVAL_DAYS, 3))
    _add_optional(schema, CONF_MAIN_BRUSH_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_MAIN_BRUSH_INTERVAL_DAYS, 14))
    _add_optional(schema, CONF_SIDE_BRUSH_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_SIDE_BRUSH_INTERVAL_DAYS, 14))
    _add_optional(schema, CONF_WHEEL_CLEAN_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_WHEEL_CLEAN_INTERVAL_DAYS, 14))
    _add_optional(schema, CONF_SENSOR_CLEANING_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_SENSOR_CLEANING_INTERVAL_DAYS, 30))
    _add_optional(schema, CONF_CONTACT_CLEANING_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_CONTACT_CLEANING_INTERVAL_DAYS, 30))
    if defaults.get(CONF_ROBOT_MOP_STYLE, ROBOT_MOP_STYLE_NONE) != ROBOT_MOP_STYLE_NONE:
        _add_optional(schema, CONF_MOP_SERVICE_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_MOP_SERVICE_INTERVAL_DAYS, 7))
        _add_optional(schema, CONF_WATER_TANK_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_WATER_TANK_INTERVAL_DAYS, 14))
    dock_type = defaults.get(CONF_ROBOT_DOCK_TYPE, ROBOT_DOCK_TYPE_CHARGE_ONLY)
    if dock_type in {ROBOT_DOCK_TYPE_AUTO_EMPTY, ROBOT_DOCK_TYPE_FULL_SERVICE}:
        _add_optional(schema, CONF_DOCK_DUST_BAG_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_DOCK_DUST_BAG_INTERVAL_DAYS, 60))
        _add_optional(schema, CONF_DOCK_AIR_PATH_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_DOCK_AIR_PATH_INTERVAL_DAYS, 30))
    if dock_type == ROBOT_DOCK_TYPE_FULL_SERVICE:
        _add_optional(schema, CONF_DOCK_CLEAN_WATER_TANK_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_DOCK_CLEAN_WATER_TANK_INTERVAL_DAYS, 30))
        _add_optional(schema, CONF_DOCK_DIRTY_WATER_TANK_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_DOCK_DIRTY_WATER_TANK_INTERVAL_DAYS, 7))
        _add_optional(schema, CONF_DOCK_WASH_TRAY_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_DOCK_WASH_TRAY_INTERVAL_DAYS, 14))
        _add_optional(schema, CONF_DOCK_WATER_FILTER_INTERVAL_DAYS, _number_selector(1, 3650, 1), default=defaults.get(CONF_DOCK_WATER_FILTER_INTERVAL_DAYS, 30))


def _search_text_selector():
    return selector.TextSelector(selector.TextSelectorConfig(type="search"))


def _equipment_summary_text(assets, profile) -> str:
    if not assets:
        recommended = get_recommended_definitions(profile)
        if not recommended:
            return "No systems have been added yet."
        return "No systems have been added yet.\nRecommended:\n" + _definition_summary_text(recommended)
    return "\n".join(f"- {asset_summary(asset)}" for asset in assets)


def _definition_summary_text(definitions: tuple[EquipmentDefinition, ...]) -> str:
    if not definitions:
        return "No matching systems for this home profile."
    return "\n".join(f"- {definition.label} | {definition.category} | {definition.tier}" for definition in definitions[:20])


def _filter_definitions(definitions: tuple[EquipmentDefinition, ...], search_query: str) -> tuple[EquipmentDefinition, ...]:
    query = search_query.strip().lower()
    if not query:
        return definitions
    return tuple(
        definition
        for definition in definitions
        if query in definition.label.lower()
        or query in definition.category.lower()
        or query in definition.key.lower()
        or query in definition.description.lower()
    )


def _filter_assets(assets, search_query: str):
    query = search_query.strip().lower()
    if not query:
        return assets
    filtered = []
    for asset in assets:
        haystack = " ".join(
            bit
            for bit in (
                asset.name,
                asset.equipment_type,
                asset.category,
                asset.custom_category,
                asset.manufacturer,
                asset.model,
                asset.area,
            )
            if bit
        ).lower()
        if query in haystack:
            filtered.append(asset)
    return filtered


def _prepare_custom_defaults(search_query: str) -> dict[str, Any]:
    defaults = {
        CONF_EQUIPMENT_TYPE: EQUIPMENT_TYPE_CUSTOM,
        CONF_CATALOG_TIER: CATALOG_TIER_ADVANCED,
    }
    cleaned_query = search_query.strip()
    if cleaned_query:
        defaults[CONF_ASSET_NAME] = cleaned_query
    return defaults


def _load_entry_assets(config_entry):
    return load_assets(config_entry.options.get(CONF_ASSETS, config_entry.data.get(CONF_ASSETS, [])))


def _primary_task_label(definition: EquipmentDefinition) -> str:
    return next(task.title for task in definition.tasks if task.key == definition.primary_task_key)


def _task_exists(definition: EquipmentDefinition, task_key: str) -> bool:
    return any(task.key == task_key for task in definition.tasks)


def _show_sensor_section(definition: EquipmentDefinition) -> bool:
    return definition.key in {"furnace", "water_heater"}


def _action_selector(options: list[tuple[str, str]]):
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[selector.SelectOptionDict(value=value, label=label) for value, label in options],
            mode=selector.SelectSelectorMode.LIST,
        )
    )
