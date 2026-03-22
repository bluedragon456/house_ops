const STRATEGY_ELEMENT = "ll-strategy-dashboard-house-ops";
const LEGACY_ELEMENT = "ll-strategy-house-ops";
const STATUS_SUFFIX = "_maintenance_status";

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
        stateObj.entity_id.endsWith(STATUS_SUFFIX) &&
        stateObj.attributes.tasks !== undefined
    )
    .map((stateObj) => {
      const slug = stripSuffix(
        stateObj.entity_id.replace("sensor.", ""),
        STATUS_SUFFIX
      );
      const name =
        stateObj.attributes.friendly_name?.replace(
          /\s+Maintenance Status$/i,
          ""
        ) || titleize(slug);

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

const buildButtonCard = (entityId, name, icon) => ({
  type: "button",
  entity: entityId,
  name,
  icon,
  tap_action: {
    action: "call-service",
    service: "button.press",
    target: { entity_id: entityId },
  },
});

const buildEmptyDashboard = () => ({
  title: "HouseOps",
  views: [
    {
      title: "Overview",
      path: "overview",
      icon: "mdi:home-wrench-outline",
      cards: [
        {
          type: "markdown",
          content:
            "No HouseOps equipment was discovered yet. Add equipment from Settings > Devices & services > HouseOps > Configure, then reload this dashboard.",
        },
      ],
    },
  ],
});

const buildOverviewView = (assets) => ({
  title: "Overview",
  path: "overview",
  icon: "mdi:home-heart",
  cards: [
    {
      type: "markdown",
      content: `HouseOps is tracking ${assets.length} equipment item(s).`,
    },
    {
      type: "entities",
      title: "Maintenance status",
      entities: assets.map((asset) => ({
        entity: asset.status,
        name: asset.name,
      })),
    },
    {
      type: "entities",
      title: "Upcoming work",
      entities: assets.flatMap((asset) => [
        {
          entity: asset.nextServiceDate,
          name: `${asset.name} next service`,
        },
        {
          entity: asset.daysRemaining,
          name: `${asset.name} days remaining`,
        },
      ]),
    },
    {
      type: "grid",
      columns: 2,
      square: false,
      cards: assets.flatMap((asset) => [
        buildButtonCard(
          asset.markServiced,
          `Mark ${asset.name} serviced`,
          "mdi:check"
        ),
        buildButtonCard(
          asset.snooze,
          `Snooze ${asset.name}`,
          "mdi:clock-outline"
        ),
      ]),
    },
  ],
});

const buildAssetView = (asset) => ({
  title: asset.name,
  path: asset.slug,
  icon: "mdi:tools",
  cards: [
    {
      type: "entities",
      title: asset.name,
      entities: [
        asset.status,
        asset.nextServiceDate,
        asset.daysRemaining,
        asset.reason,
        asset.due,
      ],
    },
    {
      type: "horizontal-stack",
      cards: [
        buildButtonCard(asset.markServiced, "Mark serviced", "mdi:check"),
        buildButtonCard(asset.snooze, "Snooze", "mdi:clock-outline"),
      ],
    },
  ],
});

class HouseOpsDashboardStrategy extends HTMLElement {
  static async generate(config, hass) {
    const assets = discoverAssets(hass);

    if (!assets.length) {
      return buildEmptyDashboard();
    }

    return {
      title: "HouseOps",
      views: [
        buildOverviewView(assets),
        ...assets.map((asset) => buildAssetView(asset)),
      ],
    };
  }
}

if (!customElements.get(STRATEGY_ELEMENT)) {
  customElements.define(STRATEGY_ELEMENT, HouseOpsDashboardStrategy);
  console.debug("[HouseOps] Registered dashboard strategy", STRATEGY_ELEMENT);
}

if (!customElements.get(LEGACY_ELEMENT)) {
  customElements.define(LEGACY_ELEMENT, HouseOpsDashboardStrategy);
}