# Contributing

Thanks for helping make Madrid easier to cycle in. Keep the site simple, visual and readable by anyone.

## Ground rules

- **Plain language.** The audience is residents and policy makers, not specialists. One idea per chart, one sentence per note. All text lives in the `T` dictionary in `site/app.js`, in both `es` and `en`.
- **Every number comes from data.** No hard-coded figures in the page. Add the value to `pipeline/build_site.py` (which writes `site/data.js`) and read it from `window.MC` in `app.js`.
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
python3 -m http.server -d site 8000       # check the page: no console errors, no sideways scroll on mobile
```

Describe what changed and why in the pull request. For data changes, say which source and date range you used.
