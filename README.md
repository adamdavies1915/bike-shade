# Bike Shade · New Orleans

Live map: https://bikeshade.cargobay.dev · Source: https://github.com/adamdavies1915/bike-shade

A self-hosted recreation of the shaded-bike-map idea using **Leaflet**, **Bike Streets**, and a **NOAA C-CAP canopy analysis**. No ArcGIS account, SDK, service, or subscription is required. The app is static HTML/CSS/JavaScript served by nginx; Python GIS tools prepare the data offline.

## Current status — canopy analysis complete

- Bike Streets public network refreshed **2026-10-08**, from 357 source tiles, with status attributes and source hashes retained.
- NOAA's original **2017, 1-meter classified land-cover GeoTIFF** downloaded locally (1,004,133,100 bytes). Original raster and a lossless tiled spatial subset are in `data/raw/` and excluded from deployment.
- **19,026 of 19,029 route segments** have canopy measurements. Three insufficiently covered segments remain explicitly unknown. The low-stress network snapshot totals approximately **510.8 miles**, including portions of the surrounding urban area inside the bounding box.
- Canopy filter, transparent tree-cover overlay, neighborhood navigation, construction markers, route popups, shareable map positions, mobile layout, and source downloads are implemented.
- Nine unit/integration tests pass, including actual raster pixel counting and out-of-bounds handling. JavaScript syntax, data integrity, and Python compilation pass. Desktop/mobile browser checks and container validation are recorded under `test-results/`.
- Docker image built locally. **Coolify deployment configuration: `bikeshade.cargobay.dev`, internal port 80, `/health`.**

## Preview

With local network listening enabled:

```sh
npm run dev
```

Open http://localhost:8080. No npm installation is necessary to serve the app; Leaflet 1.9.4 is vendored with its BSD license. Browser tests use the development-only Playwright dependency. The only runtime external requests are OpenStreetMap background tiles. All thematic route and canopy data are local. Without background tiles, route geometry still renders. Standard OSM tile usage is for interactive browsing; do not bulk-download or prefetch those tiles.

## Reproduce or refresh the canopy analysis

Python 3.11+ is recommended for current GIS wheels. With outbound networking enabled:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python scripts/fetch_canopy.py
.venv/bin/python scripts/analyze_canopy.py
.venv/bin/python scripts/fetch_city_bikeways.py
.venv/bin/python scripts/rank_routes.py
.venv/bin/python -m unittest discover -s tests
.venv/bin/python scripts/verify.py --require-canopy
npm run check
```

The original download is approximately **957 MB**. The fetcher checks TIFF headers and content length, records a SHA-256, and atomically saves the result. The raw TIFF is excluded from Git and the Docker image. Processing publishes the measured GeoJSON, a generalized transparent canopy PNG, and provenance in `public/data/manifest.json`.

`--require-canopy` rejects any incomplete import. The current build passes. For desktop/mobile interaction tests, run `npm ci`, `npx playwright install chromium`, start the preview server, then `npm run test:browser`. Use `BASE_URL=http://127.0.0.1:8081 npm run test:browser` to test a container instead.

To refresh Bike Streets first, run `.venv/bin/python scripts/fetch_network.py`, then rerun the canopy analysis and `scripts/rank_routes.py`. The refresh uses the public network MVT endpoint and preserves low-stress, conventional infrastructure, and construction categories. It does not use private ride records or accounts. If preparing only a network preview, run `python3 scripts/prepare_network.py`; this resets the public dataset to explicitly unmeasured routes.

## Measurement

1. Project Bike Streets geometry into NAD83 / UTM zone 15N (EPSG:26915), in meters.
2. Remove overlapping linework within each source status class and split each part into segments of at most 100 meters.
3. Buffer each segment by 10 meters on each side, with flat end caps.
4. At native raster resolution, count classified pixel centers inside that corridor. This raster uses canopy classes **11** (upland forest), **13** (palustrine forested wetland), and **16** (estuarine forested wetland). The archived metadata supplied with this exact raster leaves class 4 undefined; it is not treated as canopy. The source XML is retained at `data/raw/NOAA-metadata.xml`. Background, unclassified, masked, and out-of-raster pixels are unknown.
5. Require at least 90% valid buffer coverage. Otherwise publish a null score. For adequately covered buffers, canopy percentage is canopy pixels divided by valid classified pixels.

These are **nearby canopy percentages**, not the percentage of the riding surface shaded or a time-of-day shadow simulation. The overview PNG is generalized for display; measurements use the original pixels. Summary percentages are weighted by segment length and exclude unmeasured segments. Network miles summarize visible layer/filter choices across the snapshot, not just the current viewport or chosen neighborhood.

The source covers a bounding box from `[-90.16, 29.875]` to `[-89.72, 30.18]`, including much of urban New Orleans and New Orleans East. It is not a complete Orleans Parish inventory. Source tile linework may not match surveyed street centerlines; a 10 m buffer cannot establish exact shade on a specific bike lane.

2017 imagery predates Hurricane Ida and later tree changes. This map does **not** recover Laura Harris's hand-selected original shaded corridors or pink connectors, and does not infer new safe connectors. Construction markers reflect the source snapshot, not live conditions.

## Best-covered routes and the city comparison

`public/data/best-routes.geojson` contains ten connected 1 km low-stress candidates. `public/data/best-routes-traffic.geojson` adds ten OSM/city candidates for More traffic. The list follows layer checkboxes, combines enabled sets in descending canopy order, and labels each pick by network. Disabling a layer removes its picks and clears any selected highlight from that layer. Picks compare route-average canopy and are not removed by the individual-segment canopy slider. The highest-ranked result is in Lakeshore–Lake Vista (73.8% nearby canopy); the highest City Park result is 59.0%. These are computed picks from 2017 canopy, not field-verified recommendations.

`rank_routes.py` contracts degree-two network chains, searches connected paths with beam width 8, and ranks the resulting 1 km paths by length-weighted canopy. It rejects construction-marked segments and substantial overlaps with separate construction linework. It also removes candidates sharing more than 25% of their source length with an earlier pick. For More traffic, OSM and city IDs are namespaced; picks overlapping more than 25% within a 5 m geometry tolerance are removed to reduce duplicate streets across the two sources. The search is bounded rather than an exhaustive global optimum. Each pick retains its exact source segment IDs and contribution lengths; tests verify geometry continuity, scores, and overlap. The route source does not encode reliable turn restrictions, so these are exploratory corridors rather than turn-by-turn itineraries.

The city data included in the **More traffic** toggle uses the City of New Orleans [Existing and Proposed Bikeways public view](https://www.arcgis.com/home/item.html?id=dbe68efb96304bd7b43c3424fceab175), downloaded on 2026-10-08. Its reported data edit date is 2025-02-18. Only six explicit existing facility types are included, yielding 2,609 source features and 4,603 measured/unknown parts. Proposed-only facilities are excluded. Street names, facility types, and original IDs remain available in popups/data. Raw snapshot and metadata are retained in `data/raw/`, with public provenance in `public/data/city-bikeways-source.json`.

Low-stress Bike Streets routes are solid; “More traffic” combines OSM-marked bikeways (retrieved via Bike Streets’ designated tile layer) and city bikeways under one toggle with dotted lines; all use the same canopy color scale and filter. City source details remain in popups; grouping city facilities under this control does not infer their traffic-stress classification. The canopy palette runs from a subdued cool gray through mint and emerald to deep green. Low-canopy lines use a cool gray (#91a5ae), 2.75 px stroke, and 85% opacity; high-canopy lines are thicker. The OSM background is partially desaturated so the route colors stand out. Construction stays orange. The canopy image overlay now uses 90% opacity. The pink highlight indicates a selected route pick. Separate summary panels show miles and length-weighted mean canopy for low-stress Bike Streets routes and for the combined OSM-marked/city layer. Each panel follows the layer toggle and canopy filter, across the full dataset rather than only the viewport. The combined layer sums source lengths and can count OSM/city overlaps twice; the interface labels these mapped source totals explicitly. Unknown canopy is excluded from averages.

The running map reads the downloaded city data locally. The City’s ArcGIS service is used only during data refresh; no ArcGIS account or runtime SDK is needed.

## Sources

- [Bike Streets New Orleans map](https://bikestreets.com/la/new-orleans/) — public network snapshot retrieved 2026-10-08. Local provenance and original tile hashes: `data/raw/bikestreets-source.json`. Bike Streets retains its original rights; an open-data redistribution license was not verified. The open-source status of this application's mapping software does not assign a license to third-party route data.
- [NOAA C-CAP metadata](https://www.fisheries.noaa.gov/inport/item/65779) and [download directory](https://chs.coast.noaa.gov/htdata/raster1/landcover/bulkdownload/hires/la/) — New Orleans area parishes, 2017, 1-meter land cover, released December 2021. The source lists a five-year restriction on machine-learning uses; this project performs deterministic raster statistics, not ML.
- [Original GeoTIFF](https://chs.coast.noaa.gov/htdata/raster1/landcover/bulkdownload/hires/la/la_neworleans_2017_ccap_highres_landcover_20211213.tif).
- [City neighborhoods](https://maps.nola.gov/server/rest/services/Reference/Reference_Layers/MapServer/0) — previously downloaded snapshot from 2026-10-01. Used only for local navigation; the running app does not query ArcGIS.
- [Bike Easy shaded routes article](https://bikeeasy.org/tips-guides/maps-trails-guides/shaded-bike-routes/) — project inspiration, Laura Harris, August 2024.
- [Leaflet](https://leafletjs.com/) — version 1.9.4, BSD-2-Clause, license in `public/vendor/LEAFLET-LICENSE.txt`.
- [OpenStreetMap](https://www.openstreetmap.org/copyright) — attributed background map, [tile policy](https://operations.osmfoundation.org/policies/tiles/).

The City's service named `TreeCanopy` was deliberately not used as a measurement: its own description says it is a public-tree inventory and not a true canopy layer, omitting private property.

## Coolify deployment

The current canopy import and checks are complete. To deploy:

1. Add the source repository to Coolify and choose **Dockerfile** build pack, repository root as build context.
2. Set internal application port to **80**, attach your chosen domain, and enable HTTPS.
3. Health check: `GET /health` on port 80.
4. Deploy. No secrets, database, external GIS service, or runtime environment variables are needed.

For a local container check: `docker build -t bike-shade .` then `docker run --rm -p 8080:80 bike-shade`.

The Docker image includes only `public/` and nginx configuration. Refresh data locally and redeploy to publish a new snapshot. For embedding on Bike Easy, use an iframe pointed at the deployed HTTPS URL; the server intentionally does not add a frame-blocking header.
