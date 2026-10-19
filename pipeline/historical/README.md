# Historical scripts

These one-off scripts produced the parts of the site built from the 2023 trip-by-trip records and other static inputs:

- hourly patterns
- station flows against elevation
- modelled routes
- the 24-hour animation

They only need to run again if EMT publishes new trip data, or to reproduce the analysis. Each script's docstring gives its usage. They expect raw downloads (not in git) in a working folder.

| Script | Needs | Produces |
|---|---|---|
| `01_bicimad_eda.py` → `02_export_bicimad.py` | EMT 2023 trip zips, daily trips, GBFS snapshot | `data/bicimad_2023_hourly.csv`, `bicimad_2023_summary.csv` |
| `03_accidents_load.py` → `04_context_join.py` → `05_context_export.py` | accident CSVs, cycling infrastructure shapefile, OpenTopoData elevation, NOAA weather | `data/bicimad_2023_station_elevation.csv`, first versions of the files `refresh.py` now maintains |
| `06_districts_counters.py` | district shapefile, padrón, bike counter CSVs (dataset 300321) | `data/madrid_districts_*.csv`, `data/madrid_bike_counters.csv` |
| `08_barrios.py` | barrio shapefile, padrón | `data/madrid_barrios_bicimad.csv` |
| `11_all_routes.py` | BBBike `Madrid.osm.pbf`, 2023 trips, infrastructure shapefile | `data/bicimad_2023_routes_all.csv.gz`, `bicimad_2023_top_routes_routed.csv` |
| `film_01_day_data.py` → `10_film_routes.py` → `12_build_film_data.py` | 2023 trips, OSM extract | `site/film-data.js` (animation data) |
| `14_lane_priority.py` | OSM extract, 2023 trips, infrastructure shapefile, `data/madrid_bike_accidents.csv` | `data/lane_priority.csv` (street corridors ranked for a new protected lane: bikes riding unprotected × traffic stress, plus accidents; `--w-bikes` sets the balance) |
| `13_basemap.py` | OSM extract (BBBike Madrid `.osm.pbf`) | `site/basemap.js` (main roads, Manzanares, parks, landmarks under every map) |

Where the raw files come from is listed in `docs/DATA_SOURCES.md`.
