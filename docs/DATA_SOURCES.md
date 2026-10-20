# Data sources, update frequency and gaps

| Data | Publisher | Used | Source updates | Refreshed by |
|---|---|---|---|---|
| BiciMAD daily trips | EMT Madrid (datos.emtmadrid.es) | Feb 2024 onwards | Monthly | `refresh.py` |
| BiciMAD monthly active users | EMT Madrid | Feb 2024 onwards | Monthly | `refresh.py` |
| BiciMAD trip-by-trip records | EMT Madrid, [Históricos de BiciMAD](https://datos.madrid.es/dataset/900034-0-bicimad-viajes-estaciones) (yearly archives 2017–2023; 2023 file [`bicimad_2023.zip`](https://media.emtmadrid.es/-9Nii5DXo4x)) | 1 Jan – 18 Feb 2023 | No release since Feb 2023 | manual (`pipeline/historical/`) |
| BiciMAD live stations (GBFS) | EMT (madrid.publicbikesystem.net) | Live in the browser (polled every minute); one snapshot per refresh as fallback | Real time | `site/app.js`, `refresh.py` |
| Bicycle accidents | Policía Municipal (datos.madrid.es 300110) | 2019 onwards | About monthly, 1–2 month lag | `refresh.py` |
| Cycling infrastructure | Ayuntamiento geoportal (205107) | Latest layer | A few times a year | `refresh.py` |
| Bike racks | datos.madrid.es (205099) | Latest | Daily | `refresh.py` |
| Population by barrio | Padrón (300557) | Latest 1 January | Yearly | `refresh.py` |
| Bike counters | Ayuntamiento de Madrid, [Aforos de bicicletas (300321)](https://datos.madrid.es/dataset/300321-0-aforos-peatones-bicicletas), yearly files | 2019 – Jun 2024 | Yearly files | manual (`pipeline/historical/inputs.json`) |
| District and barrio boundaries | Ayuntamiento de Madrid, [Límites administrativos](https://datos.madrid.es/dataset/900012-0-limites-administrativos-mapas) | Sep 2026 version, kept in `pipeline/historical/vendor/` | Rarely | manual (`pipeline/historical/inputs.json`) |
| Street network for routing and the lane analysis | OpenStreetMap, [Geofabrik snapshot](https://download.geofabrik.de/europe/spain/madrid-260101.osm.pbf) | 1 Jan 2026 | Yearly snapshot kept online | manual (`pipeline/historical/inputs.json`) |
| Bike shops, map background | OpenStreetMap (BBBike extract, Overpass) | Oct 2026 | Continuous | manual (`13_basemap.py`) |
| Motor traffic per road section | Ayuntamiento de Madrid, [IMD (203962)](https://datos.madrid.es/dataset/203962-0-trafico-imd) | 2019 | Yearly | manual (`pipeline/historical/inputs.json`) |
| Elevation for routing | [Copernicus DEM GLO-30](https://registry.opendata.aws/copernicus-dem/), tile N40 W004 | Static | Static | manual (`pipeline/historical/inputs.json`) |
| Weather | NOAA GHCN-Daily, Madrid Retiro | Feb 2024 onwards | Daily | `refresh.py` |
| Elevation of stations | [EU-DEM v1.1](https://www.opentopodata.org/datasets/eudem/) 25 m (OpenTopoData API) | Today's stations; 2023 stations (kept in `pipeline/historical/vendor/`) | Static | new stations only, in `refresh.py`; `05_station_elevation.py` |
| Benchmarks | ITDP, CRTM EDM 2018, Barcelona, Paris, Copenhagenize | — | Irregular | manual |

## Data gaps

### BiciMAD
- **No trip-level data since February 2023.** Hourly patterns, station flows, the hill effect, routes and the animation rest on seven winter weeks, when the network had about 260 stations instead of today's 676.
- **No history of station availability.** We use one live snapshot. Dataset 216343 on datos.madrid.es holds historical availability and has not been explored yet. Recording the live feed every few minutes would build our own history.
- **Fleet size disagrees between sources.** The live feed and the city's reports give different numbers: 9,421 versus about 8,000 in May 2026.
- **2023 trip records have quality problems.** Blank rows, failed undocks (about 25%) and durations that don't match the timestamps.
- **The station list file is stale.** The CSV has 631 stations; the live feed has 678. 30 stations are in Pozuelo de Alarcón.

### Bike lanes
- **No construction dates**, so growth over time can't be shown.
- **No detail on width, physical separation or surface.**
- **Definitions are broad.** The city counts about 426 km as segregated; the press counts about 292 km.

### Counters
- **The series has holes:** July 2021 to August 2022, and everything after June 2024.
- **The set of counters changes over time.** Only 29 counters run continuously.

### Accidents
- **All bikes are included,** with no flag for BiciMAD.
- **No exposure measure** (kilometres ridden), so risk per trip can't be calculated.
- **Only crashes attended by police are recorded.**
- **2010–2018 records use another layout** and are left out.

### Routes
- **Modelled on OpenStreetMap, not GPS tracks.** Real riders may take other streets.

### Context
- **Madrid's cycling modal share is out of date.** The last comparable figure is 0.5% from the 2018 regional travel survey (CRTM EDM 2018). Newer city figures use mobile-phone data and aren't comparable with other cities.
- **Weather comes from one station** (El Retiro).
- **Google Maps is not used.** Its API is paid and its terms restrict storing results.

See `docs/solicitud-datos-bicimad.md` for a draft request to EMT for the missing trip data.
