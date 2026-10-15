# Project notes

## OSM bikeway audit — resume here

Saved October 14, 2026. [Full audit](osm-audit/README.md) · [Review CSV](osm-audit/review.csv) · [GIS review layer](osm-audit/review.geojson) · [Unsent permission request](osm-audit/permission-request.md).

We compared the city bikeways with current OSM for 247 flagged city records. Garden Oaks Drive is the strongest candidate for missing bicycle-facility tags. Sullen Place and Metairie Road need a survey of shared-lane markings. McAlister already has bicycle access mapped; its absence from our designated layer is a filtering difference.

### Latest user observation

On October 14, Adam stated that **Garden Oaks is a protected bike lane**. This supports the city record and historical photograph. The date of his observation, precise extent, both-direction coverage, and present separation details have not yet been established. Do not present this as a completed dated field survey.

### Next steps

1. Confirm current Garden Oaks lane extent and protection in both directions, particularly Old Behrman Highway to General de Gaulle Drive. Record the observation date and preferably geolocated photos.
2. Recheck current OSM ways and any separately mapped bicycle paths before choosing tags. Start with way IDs 782764187, 12698639 and 897084675; links and evidence are in the audit.
3. If using city geometry or attributes, resolve the dataset's reuse permission. The saved draft has not been sent. Independently surveyed observations offer a separate evidence path.
4. Prepare a small, evidence-backed OSM correction for review. No OSM edits, notes, or external messages have been made.
5. Separately consider whether Bike Shade should include bicycle-permitted pedestrian paths such as McAlister in its display.

The live map has not been changed by this audit. CSV categories are automated review flags, not confirmed errors; records can duplicate streets or carriageways. Raw OSM API downloads are kept locally and excluded from Git. The report, review files, provenance, and read-only reproduction scripts are versioned.
