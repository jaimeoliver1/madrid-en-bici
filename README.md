# Madrid en bici

**¿Es fácil moverse en bici por Madrid?** A public website that explains, with open data and plenty of maps, how BiciMAD (Madrid's public bike share) and the city's bike lanes are doing, and what would make Madrid easier to cycle in. It's in Spanish, with an English toggle.

- **Live site:** _add the Vercel URL here once deployed_
- **What's on it:** a 24-hour animation of every BiciMAD bike, a report card against planning benchmarks, and sections on coverage, hills, bike lanes, safety and weather. It ends with six recommendations.
- **Live data:** station availability comes straight from BiciMAD's public feed in the visitor's browser. Everything else is refreshed monthly by a GitHub Action.

## Repository layout

```
site/        the website: plain HTML + JS (d3), no build step
  index.html   page and styles
  app.js       charts, maps, texts (ES/EN), live station updates
  player.js    the 24-hour animation player
  data.js      generated data bundle (pipeline/build_site.py)
  film-data.js generated animation data (pipeline/historical/)
data/        processed open data, small CSVs, the single source for data.js
pipeline/
  refresh.py      monthly refresh: download sources -> data/ -> site/data.js
  build_site.py   data/ -> site/data.js
  historical/     one-off scripts behind the static 2023 analysis, routes and animation
film/        source of the 24-hour animation as a standalone video (Claude Motion scenes)
docs/        data sources and gaps, and the data request sent to EMT
```

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

Ideas, fixes and new analyses are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## Licence and attribution

The code is under the MIT licence (see [LICENSE](LICENSE)). The data belongs to its publishers and is reused under their open-data terms, which require attribution:

- **EMT Madrid:** BiciMAD data, ODC Attribution licence.
- **Ayuntamiento de Madrid:** datos.madrid.es.
- **OpenStreetMap contributors:** ODbL.
- **NOAA:** GHCN-Daily weather.
- **Copernicus:** EU-DEM elevation.

Keep the sources list on the site if you reuse it.
