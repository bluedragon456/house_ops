# HouseOps

HouseOps is a Home Assistant custom integration for tracking recurring maintenance on household equipment. It creates Home Assistant devices and entities for each equipment item, keeps maintenance schedules visible, and includes a dashboard strategy for a dedicated operations view.

## Included in this version

- Furnace / HVAC tracking
- Water heater tracking
- Fire alarms / smoke detectors tracking
- Catalog-driven maintenance defaults by equipment type
- Manual install date, last serviced date, and next due override support
- Power-type-aware fire alarm battery handling
- Equipment review, add, edit, and remove flows under `Configure`
- Asset-level and task-level entities for dashboards and automations
- Lovelace dashboard strategy at `www/house_ops/house-ops-strategy.js`

## Equipment management

HouseOps uses a single integration entry and treats each piece of equipment as a managed asset inside that entry.

To manage equipment later:

1. Go to `Settings > Devices & services`
2. Open `HouseOps`
3. Click `Configure`
4. Use the built-in menu to:
   - Review equipment
   - Add equipment
   - Edit equipment
   - Remove equipment

The options flow is the primary equipment workflow. You do not need to add another integration entry just to add another piece of equipment.

## Supported equipment defaults

### Furnace / HVAC

- Filter replacement: `90` days
- Annual inspection: `365` days

### Water heater

- Flush: `365` days
- Anode rod inspection: `1825` days by default when enabled

### Fire alarms / smoke detectors

- Alarm test: `30` days
- Battery replacement: `180` days by default when batteries exist
- Detector replacement advisory: `3650` days

## Dates and overrides

Each equipment item can store:

- `Install date`
- `Last serviced date`
- `Next due date override`

If a next due override is set, HouseOps uses it as the active due date until that task is marked serviced. After the task is marked serviced, the override is cleared and the normal schedule resumes from the new completed date.

If no install or service date is set, HouseOps will still create the item and surface that it is temporarily using today as a baseline until you provide a real date.

## Areas

HouseOps prefers Home Assistant areas using the built-in area selector. If you need a custom location that is not in Home Assistant yet, you can also enter a custom area name.

## Fire alarm power types

Fire alarms support these power configurations:

- `Battery-powered`
- `Wired`
- `Wired with battery backup`

Battery maintenance fields only appear when the selected power type actually has a battery.

## Dashboard setup

Copy the strategy file into your Home Assistant `www` directory so it is available at:

```text
/local/house_ops/house-ops-strategy.js
```

Then register it in Home Assistant:

1. Go to `Settings > Dashboards`
2. Open `Resources`
3. Add a resource:
   - URL: `/local/house_ops/house-ops-strategy.js`
   - Type: `JavaScript Module`
4. Hard refresh the browser after adding the resource

### Dashboard YAML

Use this exact dashboard config:

```yaml
title: HouseOps
strategy:
  type: custom:house-ops
```

If no HouseOps equipment exists yet, the strategy returns a safe empty dashboard instead of failing.

## Installation

### HACS

1. Add this repository as a custom integration repository if needed
2. Install `HouseOps`
3. Restart Home Assistant

### Manual

1. Copy `custom_components/house_ops` into your Home Assistant `custom_components` folder
2. Copy `www/house_ops` into your Home Assistant `www` folder
3. Restart Home Assistant

## Notes

- HouseOps currently supports one integration entry with many equipment items inside it
- Existing stored assets from the earlier HouseOps schema are read with backward-compatible field fallbacks where possible
- The equipment catalog is structured for future expansion to more household maintenance categories
