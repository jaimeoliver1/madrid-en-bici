# Historical scripts

These scripts build the parts of the site that do not change month to month: everything from the 2023 trip-by-trip records (hourly pattern, hills, routes, the 24-hour animation), the district and barrio outlines, the bike counters, the base map, and the lane analysis. They only need to run again if EMT publishes new trip data, or to reproduce the analysis. Each script's docstring gives its usage.

## Reproducing

Every raw input is pinned to the exact file used, with its link, SHA-256 and licence, in `inputs.json`. Files whose publisher keeps serving the same version are downloaded; small files the publisher replaces in place are kept in `vendor/`. The other inputs are in git under `data/`, kept up to date by `pipeline/refresh.py`, so the commit pins them.

```bash
uv pip install -r pipeline/historical/requirements-lock.txt   # Python 3.12, exact package versions
python3 pipeline/historical/fetch_inputs.py raw               # downloads, checks every SHA-256, prints the commands below with paths
```

`fetch_inputs.py` refuses any file whose hash differs from the pinned one, then prints the commands to run, in order. On the pinned inputs every script gives byte-identical outputs on every run (01 and 06 also reproduce the committed files exactly). `lane_network_plans.json` and `route-graph.json` also record the SHA-256 of their inputs and the git commit they were built from.

| Script | Needs | Produces |
|---|---|---|
| `01_trips_2023.py` | 2023 trips | `data/bicimad_2023_summary.csv`, `bicimad_2023_hourly.csv` |
| `05_station_elevation.py` | 2023 trips, `vendor/station_heights_2023_eudem25m.csv` (EU-DEM heights from OpenTopoData, the source `refresh.py` uses for today's stations) | `data/bicimad_2023_station_elevation.csv` (the hills chart) |
| `06_districts_counters.py` | district boundaries, bike counter files 2019–2024 | `data/madrid_districts_shapes.csv`, `data/madrid_bike_counters.csv` |
| `08_barrios.py` | barrio boundaries, population, `data/bicimad_station_context.csv` | `data/madrid_barrios_bicimad.csv` (`refresh.py` then recounts stations and population on these outlines every month) |
| `11_all_routes.py` | OSM snapshot, 2023 trips, `data/madrid_bike_infrastructure.csv` | `data/bicimad_2023_routes_all.csv.gz`, `bicimad_2023_top_routes_routed.csv` |
| `film_01_day_data.py` → `10_film_routes.py` → `12_build_film_data.py` | 2023 trips, barrio boundaries, OSM snapshot | `site/film-data.js` (the 24-hour animation) |
| `13_basemap.py` | OSM snapshot | `site/basemap.js` (main roads, Manzanares, parks, landmarks under every map) |
| `14_lane_priority.py` | OSM snapshot, 2023 trips, `data/madrid_bike_infrastructure.csv`, `data/madrid_bike_accidents.csv` | `data/lane_priority.csv` (first ranking of corridors; `.cache/edges.pkl` for 15 and 16) |
| `15_lane_network.py` | OSM snapshot, 2023 trips, 2019 traffic counts, Copernicus DEM, `data/` accidents, counters and lanes, `.cache/` from 14 | `data/lane_network_plan*.csv`, `lane_network_plans.json` (see `docs/METHOD_LANES.md`; parameters in `appraisal.py`) |
| `16_route_graph.py` | OSM snapshot, 2019 traffic counts, Copernicus DEM, `data/` accidents, counters and lane plan, `.cache/` from 14 and 15 | `site/route-graph.json` (the route planner's network: see `docs/ROUTING.md`) |

Shared code: `bikegraph.py` (street graph and routing), `bike_costs.py` (street-type weights for 10, 11, 14), `appraisal.py` (published parameters), `provenance.py` (input hashes and git commit).

Earlier scripts that built the first versions of the files `refresh.py` now maintains (accidents, bike lanes, stations, weather, racks, district and barrio metrics) were removed; they are in the git history before this README's commit.
