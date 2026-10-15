# City bikeways / current OpenStreetMap audit

Checked October 13, 2026. This is a review queue, not an OSM import or a list of verified mapping errors. No OSM edits or messages were submitted, and the public Bike Shade map was not changed.

## Findings

There are plausible OSM improvements, but the original comparison cannot establish that OSM is generally out of date. Its comparator was Bike Streets' designated tile layer, not the full OSM database. Bicycle access, shared-lane markings, signed routes, dedicated lanes and separate paths are different concepts.

Current OSM was fetched directly from its primary map API for all 247 city records with at least 20 meters outside a 20-meter buffer of our saved designated layer. The 57 bounding-box requests include surrounding highways, paths and bicycle-route relations. The download completed at 2026-10-13T20:23:59Z. Individual OSM edit timestamps are preserved in the CSV; a recent edit does not imply that bicycle facilities were surveyed.

| Spatial triage | City records |
|---|---:|
| Little or no nearby explicit bicycle-facility/designation tagging; survey needed | 158 |
| Partial nearby bicycle-facility/designation tagging | 76 |
| At least 90% near an explicit bicycle-facility/designation tag | 11 |
| Bicycle access already mapped, without facility/designation tags | 2 |

These are **city records, not distinct streets or confirmed edits**. The city data includes repeated and directional linework. Nearby tags can belong to a crossing street or opposite carriageway. Geometry overlap does not verify facility equivalence, direction, protection or permission to ride.

## Priority review list

| Priority | Corridor and city record | Current OSM evidence | External evidence and decision |
|---|---|---|---|
| 1 | Garden Oaks Dr, 3000–3500 blocks; city 23718, 23727, protected lanes | Relevant road ways include [782764187](https://www.openstreetmap.org/way/782764187), [12698639](https://www.openstreetmap.org/way/12698639), [897084675](https://www.openstreetmap.org/way/897084675). No bicycle/cycleway tags in the checked road histories; no nearby explicit bike facility match for these city records. | Strongest candidate. City's [project status](https://nola.gov/next/sustainability/transportation/bicycling/project-status/) lists Garden Oaks complete as of February 1, 2024. [Coalition documentation](https://nolacompletestreets.org/mnobalgiers/) describes protected lanes; its [historical photo](https://nolacompletestreets.org/wp-content/uploads/2021/05/Garden-Oaks-Bicycle-Rider-1024x765.jpg) visibly shows marked lanes and flexible posts on both sides. Exact capture date is not established; 2021/05 is the upload URL, not a verified capture date. Confirm lanes and separation today, both directions and at intersections, before choosing OSM tags. |
| 2 | Sullen Pl, 4000–4300 blocks; city 22891, shared lane | [12697913](https://www.openstreetmap.org/way/12697913) lacks bicycle/cycleway tags. Its checked history contains no bicycle/cycleway tags. | Candidate for a survey of sharrows/signs, not a proposed dedicated lane. A [2015 city-update republication](https://bizneworleans.com/city-provides-2015-end-of-the-year-update-on-integrated-infrastructure-improvements/) mentions Sullen bikeways, but is too old to verify present markings. |
| 3 | Metairie Rd, 100–700 blocks; city 4908, 4922, shared lanes | Roads including [1098806225](https://www.openstreetmap.org/way/1098806225), [539269026](https://www.openstreetmap.org/way/539269026), [12698021](https://www.openstreetmap.org/way/12698021) lack bicycle/cycleway tags in the fetched records. | Field verification needed on each carriageway. City labels alone do not establish whether there are sharrows, a signed route, or obsolete designation. The two city records are opposite-side source lines; do not describe their summed mileage as new corridor miles. |
| Investigate our filtering | McAlister, city 8023, shared-use path | [12700414](https://www.openstreetmap.org/way/12700414) is `highway=pedestrian`, `bicycle=yes`; this access tag is present in its history since 2010. The city record is 100% within 20 m of bicycle-access-tagged OSM geometry. | Do not treat as a missing OSM bikeway. [Tulane's 2010 dedication report](https://news.tulane.edu/news/make-way-green-space) documents the pedestrian/bicycle conversion. Consider whether Bike Shade should show bicycle-permitted pedestrian paths as their own category. This evidence does not justify changing `bicycle=yes` to `bicycle=designated`. |
| Inspect geometry/filtering first | Basin St / Elk Pl bus-bike records; Crowder Blvd; S Jefferson Davis Pkwy | Eleven records now have at least 90% nearby explicit bike tagging. | Inspect the linked OSM tags in review.csv before proposing any edit; tile filtering, positional offsets or mapping differences can explain these flags. |

The review CSV and GeoJSON contain the remaining corridors, city IDs, facility labels, from/to fields, coordinates, OSM way links, timestamps and complete nearby way tags. Sort by `current_gap_m` to prioritize the largest geometric discrepancies. This field means length outside recognized-tag buffers, **not confirmed missing infrastructure**.

## Imagery and ground truth

A public Panoramax search returned zero images in the four priority bounding boxes (Garden Oaks, Sullen, Metairie, McAlister). The empty responses are saved. This does not establish that Mapillary, KartaView or other imagery providers lack coverage. No recent street-level image or local field observation was obtained that verifies present conditions. Historical photographs and project descriptions support triage only. No claim in this report is a field-verified OSM correction.

For Garden Oaks, start with Old Behrman Highway to General de Gaulle Drive. Record survey date, lane start/end points, direction of travel, pavement markings, vertical separation, intersection transitions and any removed sections. For Sullen and Metairie, distinguish painted sharrows from a dedicated lane and from signs alone. Capture geolocated photographs where practical. Consult current [OSM cycleway tagging](https://wiki.openstreetmap.org/wiki/Key:cycleway) when translating verified observations.

## City data permission

The [exact ArcGIS item](https://www.arcgis.com/home/item.html?id=dbe68efb96304bd7b43c3424fceab175) was checked. Its `licenseInfo` is an informational-use/accuracy/availability disclaimer. It does not expressly grant CC0, ODbL-compatible reuse or permission to incorporate this dataset into OSM. The saved service metadata has empty `copyrightText`. Public download access and empty copyright fields are not affirmative OSM permission.

An older [New Orleans building import](https://wiki.openstreetmap.org/wiki/New_Orleans%2C_Louisiana/Building_Outlines_Import) documents CC0 for specific building/address datasets. That does not establish the license for this bikeway item. **OSM reuse permission remains unverified.** [OSM's import guidelines](https://wiki.openstreetmap.org/wiki/Import/Guidelines) require compatible permission and community review for imports. Independently surveyed observations are a separate evidence path; do not copy city geometry or attributes into OSM based on this report.

A ready-to-send clarification draft is in `permission-request.md`. It has not been sent.

## Files and reproduction

- `review.csv`: 247 machine-triaged city records with current OSM links/tags.
- `review.geojson`: corresponding city geometry for GIS review; city rights remain unresolved for OSM reuse.
- `summary.json`, `provenance.json`: counts, retrieval information and input checksums.
- `city-item.json`: exact license metadata reviewed.
- `panoramax-*.json`: saved no-imagery responses.
- Cached primary OSM API responses and histories are local and ignored by Git. OSM data is © OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright). Third-party data is not covered by this repository's MIT code license.

Re-run from the repository root:

```sh
.venv/bin/python scripts/fetch_osm_audit.py
.venv/bin/python scripts/audit_osm.py
```

The fetcher uses the saved review.geojson candidate set and cached responses. To get a fresh dated snapshot, archive/remove `docs/osm-audit/api-tiles/` first. The analyzer recreates the candidate set from the original city and designated GeoJSONs. It uses EPSG:26915 meters, a common study boundary, geometric unions and 20 m buffers. Bike signals include cycleways, designated bicycle access, bicycle roads and side-specific lane/track/shared-lane/bus-lane tags; general `bicycle=yes` is reported separately. Bicycle relation membership is recorded separately. No directional/angle-based matching is performed; all matches require human review.

An initial whole-area Overpass result reported a July 24, 2026 database timestamp, so it was not used as current evidence. The final classification uses the primary API downloads instead. Review coverage is the 247 candidates, not a citywide current-OSM inventory or a full audit of facility types on already-overlapping routes.
