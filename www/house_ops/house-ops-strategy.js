const HOUSE_OPS_STATUS_SUFFIX = "_maintenance_status";

const titleize = (value) =>
  value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (match) => match.toUpperCase());

const stripSuffix = (value, suffix) =>
  value.endsWith(suffix) ? value.slice(0, -suffix.length) : value;

const buildEntityId = (domain, slug, suffix) => `${domain}.${slug}_${suffix}`;

const discoverAssets = (hass) =>
  Object.values(hass.states)
    .filter(
      (stateObj) =>
        stateObj.entity_id.startsWith("sensor.") &&
        stateObj.entity_id.endsWith(HOUSE_OPS_STATUS_SUFFIX) &&
        stateObj.attributes.tasks !== undefined
    )
    .map((stateObj) => {
      const slug = stripSuffix(stateObj.entity_id.replace("sensor.", ""), HOUSE_OPS_STATUS_SUFFIX);
      const name = stateObj.attributes.friendly_name?.replace(/\s+Maintenance Status$/i, "") || titleize(slug);
      return {
        slug,
        name,
        status: stateObj.entity_id,
        nextServiceDate: buildEntityId("sensor", slug, "next_service_date"),
        daysRemaining: buildEntityId("sensor", slug, "days_remaining"),
        reason: buildEntityId("sensor", slug, "maintenance_reason"),
        due: buildEntityId("binary_sensor", slug, "due"),
        markServiced: buildEntityId("button", slug, "mark_serviced"),
        snooze: buildEntityId("button", slug, "snooze"),
      };
    })
    .sort((left, right) => left.name.localeCompare(right.name));

const buttonCard = (entityId, name, icon) => ({
  type: "button",
  entity: entityId,
  name,
  icon,
  tap_action: {
    action: "perform-action",
    perform_action: "button.press",
    target: { entity_id: entityId },
  },
});

const buildOverviewView = (assets) => ({
  title: "Overview",
  path: "overview",
  icon: "mdi:home-heart",
  type: "sections",
  max_columns: 4,
  sections: [
    {
      type: "grid",
      cards: [
        {
          type: "heading",
          heading: "HouseOps",
          heading_style: "title",
          icon: "mdi:home-wrench-outline",
        },
        {
          type: "markdown",
          content: `Tracking ${assets.length} asset(s) for maintenance and household operations.`,
        },
      ],
    },
    {
      type: "grid",
      cards: [
        {
          type: "heading",
          heading: "Attention Queue",
          icon: "mdi:alert-octagon-outline",
        },
        {
          type: "entity-filter",
          show_empty: false,
          entities: assets.map((asset) => asset.status),
          state_filter: ["due", "overdue", "due_soon"],
          card: {
            type: "entities",
            title: "Assets needing attention",
          },
        },
      ],
    },
    {
      type: "grid",
      cards: [
        {
          type: "heading",
          heading: "Portfolio",
          icon: "mdi:view-grid-outline",
        },
        {
          type: "grid",
          columns: Math.min(Math.max(assets.length, 1), 3),
          square: false,
          cards: assets.flatMap((asset) => [
            {
              type: "tile",
              entity: asset.status,
              name: asset.name,
              vertical: true,
            },
            {
              type: "tile",
              entity: asset.daysRemaining,
              name: `${asset.name} days`,
            },
          ]),
        },
      ],
    },
    {
      type: "grid",
      cards: [
        {
          type: "heading",
          heading: "Quick Actions",
          icon: "mdi:gesture-tap-button",
        },
        {
          type: "grid",
          columns: 2,
          square: false,
          cards: assets.flatMap((asset) => [
            buttonCard(asset.markServiced, `${asset.name} serviced`, "mdi:check-decagram-outline"),
            buttonCard(asset.snooze, `${asset.name} snooze`, "mdi:alarm-snooze"),
          ]),
        },
      ],
    },
  ],
});

const buildAssetView = (asset) => ({
  title: asset.name,
  path: asset.slug,
  icon: "mdi:tools",
  type: "sections",
  max_columns: 4,
  sections: [
    {
      type: "grid",
      cards: [
        {
          type: "heading",
          heading: asset.name,
          heading_style: "title",
          icon: "mdi:home-cog-outline",
        },
        {
          type: "grid",
          columns: 2,
          square: false,
          cards: [
            {
              type: "tile",
              entity: asset.status,
              name: "Maintenance status",
              vertical: true,
            },
            {
              type: "tile",
              entity: asset.due,
              name: "Due now",
            },
            {
              type: "tile",
              entity: asset.nextServiceDate,
              name: "Next service",
            },
            {
              type: "tile",
              entity: asset.daysRemaining,
              name: "Days remaining",
            },
          ],
        },
      ],
    },
    {
      type: "grid",
      cards: [
        {
          type: "heading",
          heading: "Actions",
          icon: "mdi:wrench-clock",
        },
        {
          type: "horizontal-stack",
          cards: [
            buttonCard(asset.markServiced, "Mark serviced", "mdi:check"),
            buttonCard(asset.snooze, "Snooze", "mdi:clock-outline"),
          ],
        },
      ],
    },
    {
      type: "grid",
      cards: [
        {
          type: "heading",
          heading: "Details",
          icon: "mdi:text-box-search-outline",
        },
        {
          type: "entities",
          title: "Asset detail",
          show_header_toggle: false,
          entities: [
            asset.status,
            asset.nextServiceDate,
            asset.daysRemaining,
            asset.reason,
          ],
        },
      ],
    },
  ],
});

const buildEmptyDashboard = () => ({
  title: "HouseOps",
  views: [
    {
      title: "HouseOps",
      path: "house-ops",
      icon: "mdi:home-wrench-outline",
      cards: [
        {
          type: "markdown",
          content: "No HouseOps assets were discovered yet. Add equipment in Settings > Devices & services and reload the dashboard.",
        },
      ],
    },
  ],
});

class HouseOpsStrategy extends HTMLElement {
  static async generateDashboard(info) {
    const assets = discoverAssets(info.hass);
    if (!assets.length) {
      return buildEmptyDashboard();
    }

    return {
      title: "HouseOps",
      views: [buildOverviewView(assets), ...assets.map((asset) => buildAssetView(asset))],
    };
  }
}

if (!customElements.get("ll-strategy-house-ops")) {
  customElements.define("ll-strategy-house-ops", HouseOpsStrategy);
}
