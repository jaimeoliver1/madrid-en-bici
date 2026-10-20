# Routing: how the project finds bike routes

This note covers the routing behind the analysis and the route planner on the website ("¿Por dónde voy en bici?"). The lane-network analysis that uses it is described in [METHOD_LANES.md](METHOD_LANES.md).

## The street network

The network is built from OpenStreetMap (Geofabrik's Madrid snapshot of 1 January 2026, pinned in `pipeline/historical/inputs.json`) by `pipeline/historical/bikegraph.py`:

- **Nodes** are OSM nodes; **arcs** are the stretches between consecutive nodes of a way, in each direction riders may use them (one-way streets only one way unless bikes are exempt).
- Each segment carries its road type, street name, whether it has a painted bike lane (`cycleway=lane`, `bicycle=designated`) or a separated one (`highway=cycleway`, `cycleway=track/separate`, or Madrid's exclusive-lane layer), motor traffic (the city's 2019 average daily traffic per section, matched to OSM streets by name) and uphill grade in each direction (Copernicus DEM GLO-30, profiles smoothed over about 50 m).
- Madrid's big boulevards (Castellana, Recoletos, Prado) are tagged `trunk` in OSM. They are in the network, open to bikes.

## How a rider weighs a street

A rider chooses the route with the least **perceived distance**: the length of each stretch times a multiplier. The multipliers come from Broach, Dill & Gliebe (2012), who estimated them from 1,449 GPS-tracked bike trips in Portland, Oregon (non-commute values of their Table 3, converted for single links: see METHOD_LANES.md section 1).

| Feature | Extra perceived km per km |
|---|---|
| Motor traffic 10,000–20,000 / 20,000–30,000 / 30,000+ vehicles a day, no bike lane | +0.20 / +0.86 / +1.97 |
| Painted bike lane | cancels the traffic penalty |
| Separated bike path or protected lane | −0.30 |
| Uphill 2–4% / 4–6% / 6%+ | +0.54 / +1.36 / +2.49 |
| Footways, pedestrian streets, paths (not in Broach et al.) | weights in `bike_costs.py`, for walking the bike or riding slowly |

## Dijkstra's algorithm

Routes are found with Dijkstra's algorithm: starting from the origin, it repeatedly settles the closest unsettled corner and relaxes its outgoing arcs, so every corner gets the cheapest perceived distance from the origin; the route is read back from each corner's predecessor.

- **In the analysis** (`bikegraph.assign`), one run of `scipy.sparse.csgraph.dijkstra` per origin station gives the routes to every destination at once. All 324,000 BiciMAD trips of January–February 2023 (about 47,000 station pairs from 260 origins) are routed in about 22 seconds. Trips per street segment are added up by walking each route back from its destination.
- **On the website** (`site/routing.js`), the same algorithm runs in the visitor's browser with a binary heap, on a compact copy of the network. A route takes a few tens of milliseconds, so it is recomputed every time a slider moves.

Routing is all-or-nothing: everyone takes the single best route. Real riders spread over several similar routes.

## The planner's compact network

`pipeline/historical/16_route_graph.py` writes `site/route-graph.json` (about 9 MB, 2 MB compressed; loaded only when the visitor reaches the planner):

- Sidewalks, crossings, service roads, steps and tracks are left out, and only the largest connected part of the network is kept: about 248,000 of 459,000 segments.
- Segments between junctions are merged into about 83,500 links. Each link stores length-weighted sums of every cost component: length, traffic bands, separated length, walking extra, uphill length by grade band in each direction, climb, recorded accidents and expected injury cost, and the same for the part covered by the proposed lanes. Because the cost is a weighted sum of these components, any weighting chosen in the browser gives exactly the cost the full segment graph would give.
- Coordinates are rounded to 1e-5 degrees (about 1 m) and stored as differences.

## Using the planner

- Two buttons, **A · Salida** and **B · Llegada**, say which point the next tap on the map sets; after the start is set, the next tap sets the finish. Each shows the street the point snapped to.
- The **A and B markers can be dragged**; they snap to the nearest street of the network when dropped.
- The map **zooms to the route** when A or B change. Every map on the site has a **full-screen button** (under +, − and ⟲); in the planner it takes the controls along, so the weights can still be changed.

## What the visitor can change

| Slider | What it multiplies | ×1 means |
|---|---|---|
| Evitar calles con muchos coches | the traffic penalties | Broach et al. (published) |
| Preferir carriles protegidos | the separated-path bonus | Broach et al. (published) |
| Evitar cuestas | the uphill penalties | Broach et al. (published) |
| Evitar sitios con accidentes | an extra cost for recorded injury risk | the expected injury cost of riding the stretch (empirical-Bayes rate × HEATCO cost per accident, per cyclist-km) turned into perceived km at the value of time (€11.94 an hour at 12.8 km/h). Default ×0: Broach's weights already reflect how riders perceive danger. |

The switch **"Con los carriles protegidos propuestos"** turns the lanes of the headline plan (`data/lane_network_plan.csv`) into separated, two-way lanes: their traffic and walking penalties are removed, the separated-path bonus applies, one-way streets can be ridden both ways, and their injury cost is multiplied by 0.72 (Lusk et al. 2011).

For each route the planner shows length, time at 12.8 km/h (the BiciMAD median, from the 2023 trips), the share on protected lanes, the share on streets with 10,000+ vehicles a day and no bike lane, metres of climb, recorded accidents on the route (2019–2026), and the main streets used. It also shows the plain shortest route for comparison.

## Limits

- The weights come from Portland riders; they could be refitted to Madrid with the 2017–2018 BiciMAD GPS tracks.
- Turns, traffic lights and junction design are not in the network.
- Traffic counts are from 2019; streets the city does not count use the median of their road type, and residential streets count as quiet.
- Accidents are those recorded by the police; the accident slider uses rates per BiciMAD-km scaled to all cyclists with the bike counters, which is rough on streets BiciMAD riders rarely use.
- The planner is for exploring the model, not for navigation: it does not know about works, closures or temporary restrictions.

## Rebuilding

Every raw input is pinned to the exact file used (download link, dataset page, SHA-256, licence) in `pipeline/historical/inputs.json`; the rest are in git under `data/`. Package versions are in `pipeline/historical/requirements-lock.txt`. The lane analysis is below; `fetch_inputs.py` prints the commands for every historical script (see `pipeline/historical/README.md`).

```bash
uv pip install -r pipeline/historical/requirements-lock.txt          # Python 3.12
python3 pipeline/historical/fetch_inputs.py raw                      # downloads, checks every SHA-256, prints the paths
python3 pipeline/historical/14_lane_priority.py raw/madrid-260101.osm.pbf <trips_2023_dir> data
python3 pipeline/historical/15_lane_network.py  raw/madrid-260101.osm.pbf <trips_2023_dir> <IMD_2019.shp> data   # about an hour
python3 pipeline/historical/16_route_graph.py   raw/madrid-260101.osm.pbf <IMD_2019.shp> data site                # about a minute
python3 pipeline/build_site.py
```

| Input | Source | Pinned file |
|---|---|---|
| Street network | OpenStreetMap via [Geofabrik](https://download.geofabrik.de/europe/spain/madrid.html), ODbL | [`madrid-260101.osm.pbf`](https://download.geofabrik.de/europe/spain/madrid-260101.osm.pbf) (1 January 2026) |
| BiciMAD trips, 1 Jan – 18 Feb 2023 | EMT Madrid, [Históricos de BiciMAD (datos.madrid.es)](https://datos.madrid.es/dataset/900034-0-bicimad-viajes-estaciones) | [`bicimad_2023.zip`](https://media.emtmadrid.es/-9Nii5DXo4x): `trips_23_01_January.csv`, `trips_23_02_February.csv` |
| Motor traffic 2019 | Ayuntamiento de Madrid, [Intensidad media diaria por tramos](https://datos.madrid.es/dataset/203962-0-trafico-imd), CC BY 4.0 | [`IMD_2019.shp`](https://datos.madrid.es/dataset/203962-0-trafico-imd/resource/203962-5-trafico-imd-zip/download/203962-5-trafico-imd-zip) |
| Elevation | ESA [Copernicus DEM GLO-30](https://registry.opendata.aws/copernicus-dem/) | [tile N40 W004](https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N40_00_W004_00_DEM/Copernicus_DSM_COG_10_N40_00_W004_00_DEM.tif), saved as `.cache/copernicus_dem_N40_W004.tif` |
| Bike accidents, existing bike lanes, bike counters | datos.madrid.es ([300110](https://datos.madrid.es/dataset/300110-0-accidentes-bicicleta), [geoportal layer](https://geoportal.madrid.es/fsdescargas/IDEAM_WBGEOPORTAL/OBRAS/BICI/Infraestructura_Ciclista.zip), [300321](https://datos.madrid.es/dataset/300321-0-aforos-peatones-bicicletas)) | `data/madrid_bike_accidents.csv`, `data/madrid_bike_infrastructure.csv`, `data/madrid_bike_counters.csv` in git |

The OSM extract is Geofabrik's yearly snapshot because it stays online; BBBike's extract and Geofabrik's daily files are replaced, so they cannot be fetched again. The city's bike-lane layer is only served in its latest version, so the analysis reads the copy `refresh.py` keeps in git.

Each run records what it was built from: `data/lane_network_plans.json` and `site/route-graph.json` carry a `provenance` block with the SHA-256 of every input and the git commit. Caches in `.cache/` are tagged with the inputs they came from, and a script stops if a cache was built from other inputs.
