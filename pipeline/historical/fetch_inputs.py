"""Get the pinned raw inputs of pipeline/historical/ (inputs.json), check each against its SHA-256, and print the
commands that rebuild every output from them.

Usage: python3 pipeline/historical/fetch_inputs.py <raw_dir> [--allow-unpinned]
Downloads go to <raw_dir>; a file already there with the right hash is not downloaded again. Vendored files are read
from vendor/. A file whose hash differs is refused: the source has changed, and the results would not be the
published ones. An input whose hash is not pinned yet is refused too, unless --allow-unpinned, which prints its hash
so it can be added to inputs.json. Zips are unpacked into <raw_dir>; the DEM tile is copied to .cache/, where the
scripts read it.
"""
import hashlib, json, os, shutil, sys, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.path.abspath(sys.argv[1]); UNPINNED = "--allow-unpinned" in sys.argv
os.makedirs(RAW, exist_ok=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""): h.update(block)
    return h.hexdigest()


def unzip(path, out):
    """Unpack a zip, and the zips inside it (the 2023 trips come as one zip per month); macOS metadata skipped."""
    todo = [path]
    while todo:
        z = zipfile.ZipFile(todo.pop())
        for m in z.namelist():
            if m.startswith("__MACOSX/") or m.endswith("/"): continue
            z.extract(m, out)
            if m.lower().endswith(".zip"): todo.append(os.path.join(out, m))


M = json.load(open(os.path.join(HERE, "inputs.json")))
items = [(n, it, os.path.join(RAW, it["save_as"])) for n, it in M["downloads"].items()] + \
        [(n, it, os.path.join(HERE, it["file"])) for n, it in M["vendored"].items()]
ok = True
for name, it, path in items:
    if "save_as" in it and not (os.path.exists(path) and sha256(path) == it["sha256"]):
        print(f"{name}: downloading {it['url']}", flush=True)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        req = urllib.request.Request(it["url"], headers={"User-Agent": "madrid-en-bici (reproducing the analysis)"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r, open(path + ".part", "wb") as f: shutil.copyfileobj(r, f)
        except OSError as e:
            print(f"{name}: DOWNLOAD FAILED: {e}; dataset page {it['page']}"); ok = False; continue
        os.replace(path + ".part", path)
    got = sha256(path)
    if it["sha256"] is None:
        print(f"{name}: NOT PINNED: sha256 {got}, {os.path.getsize(path)} bytes; add it to inputs.json")
        if not UNPINNED: ok = False; continue
    elif got != it["sha256"]:
        print(f"{name}: REFUSED: sha256 {got} but inputs.json pins {it['sha256']} ({it['page']})"); ok = False; continue
    else:
        print(f"{name}: ok {got[:12]}")
    if it.get("unzip_to"): unzip(path, os.path.join(RAW, it["unzip_to"]))
    if it.get("copy_to_cache"):
        os.makedirs(os.path.join(ROOT, ".cache"), exist_ok=True); shutil.copy(path, os.path.join(ROOT, ".cache", it["save_as"]))
if not ok: sys.exit(1)


def find(folder, fname):
    return next(os.path.join(dp, fname) for dp, _, fs in os.walk(os.path.join(RAW, folder)) if fname in fs)


pbf = os.path.join(RAW, M["downloads"]["osm"]["save_as"])
trips = os.path.dirname(find("trips_2023", "trips_23_01_January.csv"))
imd, film = find("imd_2019", "IMD_2019.shp"), os.path.join(RAW, "film")
pop = os.path.join(HERE, M["vendored"]["population"]["file"])
H = "pipeline/historical"
print(f"""
Rebuild everything (from {ROOT}), in this order:
  python3 {H}/01_trips_2023.py        {trips} data
  python3 {H}/05_station_elevation.py {trips} data
  python3 {H}/06_districts_counters.py {find("distritos", "DISTRITOS.shp")} {os.path.join(RAW, "counters")} data
  python3 {H}/08_barrios.py           {find("barrios", "BARRIOS.shp")} {pop} data
  python3 {H}/11_all_routes.py        {pbf} {trips} data
  python3 {H}/film_01_day_data.py     {trips} {find("barrios", "BARRIOS.shp")} {film}
  python3 {H}/10_film_routes.py       {pbf} {trips} {film}/map.json {film}
  python3 {H}/12_build_film_data.py   {film} site/film-data.js
  python3 {H}/13_basemap.py           {pbf} site/basemap.js
  python3 {H}/14_lane_priority.py     {pbf} {trips} data
  python3 {H}/15_lane_network.py      {pbf} {trips} {imd} data
  python3 {H}/16_route_graph.py       {pbf} {imd} data site
  python3 pipeline/build_site.py
08 rewrites data/madrid_barrios_bicimad.csv; refresh.py then recounts its stations and population every month.""")
