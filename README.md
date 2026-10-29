# Madrid en bici

🇪🇸 [Léeme en español](README.es.md)

**¿Es fácil moverse en bici por Madrid?** A public website that explains, with open data and plenty of maps, how BiciMAD (Madrid's public bike share) and the city's bike lanes are doing, and what would make Madrid easier to cycle in. It's in Spanish, with an English toggle.

- **Live site:** https://madrid-en-bici.vercel.app
- **What's on it:** two tabs. **Ir en bici**, for people who ride: live BiciMAD numbers, a 24-hour animation of every bike, a **route planner** that runs Dijkstra's algorithm in the browser with weights you can change, your barrio's coverage, and four short tip cards (hills, rush hours, dangerous junctions, rain) whose charts open on demand. **Mejorar Madrid**, for the City Council: a report card, the bike network today, a **costed plan for the next protected lanes**, six recommendations, accidents, station coverage and demand.
- **Live data:** station availability comes straight from BiciMAD's public feed in the visitor's browser. Everything else is refreshed monthly by a GitHub Action.

## Repository layout

```
site/        the website: plain HTML + JS (d3), no build step
  index.html   page and styles
  app.js       charts, maps, texts (ES/EN), live strip (polls BiciMAD every minute)
  player.js    the 24-hour animation player
  routing.js   route planner (Dijkstra in the browser) and the proposed lane plan
  route-graph.json  generated compact bike network for the planner (pipeline/historical/16_route_graph.py)
  share.js     draws the shareable "nota de mi barrio" image in the browser
  data.js      generated data bundle (pipeline/build_site.py)
  film-data.js generated animation data (pipeline/historical/)
  basemap.js   generated map context: main roads, river, parks, landmarks (pipeline/historical/13_basemap.py)
data/        processed open data, small CSVs, the single source for data.js
pipeline/
  refresh.py      monthly refresh: download sources -> data/ -> site/data.js
  build_site.py   data/ -> site/data.js
  figures.py      the register of every quoted figure -> data/figures.json, docs/CIFRAS.md
  historical/     one-off scripts behind the static 2023 analysis, routes and animation
film/        source of the 24-hour animation as a standalone video (Claude Motion scenes)
docs/        data sources and gaps, the data request sent to EMT, and the methods:
  CIFRAS.md        every figure we quote: formula, data file, code, original source
  ROUTING.md       how routes are found (Dijkstra, rider weights, the planner)
  METHOD_LANES.md  where to build protected lanes: euros, sources, results
```

## Check a number

Every figure the site, the social posts and the press quote is listed in [`docs/CIFRAS.md`](docs/CIFRAS.md) (also at the bottom of the site, under *Cada cifra, con su fuente*). Each row gives a formula you can repeat in a spreadsheet, the file in `data/`, the script that built it and the publisher's original page. Found a mistake? [Open an issue](https://github.com/jaimeoliver1/madrid-en-bici/issues/new?template=dato-incorrecto.yml).

## Run it locally

```bash
python3 -m http.server -d site 8000      # open http://localhost:8000
```

## Update the data

```bash
pip install -r requirements.txt
python3 pipeline/refresh.py              # about 2 minutes; downloads are cached in .cache/
```

`.github/workflows/refresh.yml` runs the same command on the 10th of every month and commits the result. Vercel redeploys on every push. The refresh covers:

- BiciMAD daily trips and active users
- the live station feed and fleet size
- weather
- accidents, bike lanes, bike racks and population

The 2023 trip-level parts don't change until EMT publishes new trip data. See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) for each source, how often it updates, and the known gaps.

## Deploy

The site is static: Vercel serves `site/` as is (see `vercel.json`). Any static host works too, such as Cloudflare Pages or GitHub Pages.

## Contributing

Ideas, fixes and new analyses are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first, then pick an issue labelled [good first issue](https://github.com/jaimeoliver1/madrid-en-bici/labels/good%20first%20issue).

## Licence and attribution

The code is under the MIT licence (see [LICENSE](LICENSE)). The data belongs to its publishers and is reused under their open-data terms, which require attribution:

- **EMT Madrid:** BiciMAD data, ODC Attribution licence.
- **Ayuntamiento de Madrid:** datos.madrid.es.
- **OpenStreetMap contributors:** ODbL.
- **NOAA:** GHCN-Daily weather.
- **Copernicus:** EU-DEM elevation.

Keep the sources list on the site if you reuse it.
