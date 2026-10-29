# Contributing

Thanks for helping make Madrid easier to cycle in. Keep the site simple, visual and readable by anyone.

## Where to start

- Pick an issue labelled [good first issue](https://github.com/jaimeoliver1/madrid-en-bici/labels/good%20first%20issue). Comment that you're taking it so two people don't do the same work.
- Spotted a wrong number? Use the ["una cifra parece incorrecta" form](https://github.com/jaimeoliver1/madrid-en-bici/issues/new?template=dato-incorrecto.yml); every figure and how to check it is in [`docs/CIFRAS.md`](docs/CIFRAS.md).
- Not sure it's worth a pull request? Open an issue first and ask. Small is fine.
- Spanish or English, whichever you prefer, in issues and pull requests.

## Ground rules

- **Plain language.** The audience is residents and policy makers, not specialists. One idea per chart, one sentence per note. All text lives in the `T` dictionary in `site/app.js`, in both `es` and `en`.
- **Every number comes from data.** No hard-coded figures in the page. Add the value to `pipeline/build_site.py` (which writes `site/data.js`) and read it from `window.MC` in `app.js`.
- **Quoted figures live in the register.** A number that appears in a headline, a post or the press kit goes in `pipeline/figures.py`, with its formula, file and source. It then shows up in `docs/CIFRAS.md` and on the site, and is recomputed every month.
- **Cite sources.** A new dataset goes in `docs/DATA_SOURCES.md`, with its update frequency and gaps, and in the sources list at the bottom of the page.
- **Keep it small.** No frameworks and no build step for the site. Raw downloads stay out of git; they go in `.cache/`. Commit only processed CSVs under about 1 MB each.
- **Accessible.** Charts need a text alternative (tooltip or note). Respect `prefers-reduced-motion`. Check light and dark mode, and a 400 px wide screen.

## Typical changes

| You want to… | Edit |
|---|---|
| fix or translate text | `site/app.js` (the `T` dictionary) |
| change a chart | the matching function in `site/app.js` (`bicimad`, `coverage`, `hills`, `lanes`, `safety`, `weather`, `fixes`) |
| add a data source | `pipeline/refresh.py` (download and clean) → `pipeline/build_site.py` (bundle) → `site/app.js` (draw) |
| change the look | the tokens at the top of the `<style>` in `site/index.html` |

## Before opening a pull request

```bash
pip install -r requirements.txt
python3 pipeline/build_site.py            # regenerate site/data.js if data/ or build_site.py changed
python3 pipeline/figures.py               # regenerate docs/CIFRAS.md and data/figures.json if you touched a figure
python3 -m http.server -d site 8000       # check the page: no console errors, no sideways scroll on mobile
```

Describe what changed and why in the pull request. For data changes, say which source and date range you used.
