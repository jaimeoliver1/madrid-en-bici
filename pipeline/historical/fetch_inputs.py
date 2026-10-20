"""Download the pinned raw inputs of the lane analysis (inputs.json) and check each one against its SHA-256.

Usage: python3 pipeline/historical/fetch_inputs.py <raw_dir> [--allow-unpinned]
A file that is already in <raw_dir> with the right hash is not downloaded again. A file whose hash differs is refused:
the source has changed, and the results would not be the published ones. An input whose hash is not pinned yet is
refused too, unless --allow-unpinned, which prints its hash so it can be added to inputs.json.
Zips are unpacked next to them; the DEM tile is copied to .cache/, where the scripts read it.
Prints the commands that rebuild the lane analysis from these files.
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


ok = True
for name, it in json.load(open(os.path.join(HERE, "inputs.json")))["downloads"].items():
    path = os.path.join(RAW, it["save_as"])
    if not (os.path.exists(path) and sha256(path) == it["sha256"]):
        print(f"{name}: downloading {it['url']}", flush=True)
        req = urllib.request.Request(it["url"], headers={"User-Agent": "madrid-en-bici (reproducing the lane analysis)"})
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
    if it.get("unzip_to"):  # zips inside the zip too (the 2023 trips come as one zip per month); macOS metadata skipped
        out = os.path.join(RAW, it["unzip_to"]); todo = [path]
        while todo:
            z = zipfile.ZipFile(todo.pop())
            for m in z.namelist():
                if m.startswith("__MACOSX/") or m.endswith("/"): continue
                z.extract(m, out)
                if m.lower().endswith(".zip"): todo.append(os.path.join(out, m))
    if it.get("copy_to_cache"):
        os.makedirs(os.path.join(ROOT, ".cache"), exist_ok=True); shutil.copy(path, os.path.join(ROOT, ".cache", it["save_as"]))
if not ok: sys.exit(1)


def find(folder, fname):
    return next(os.path.join(dp, fname) for dp, _, fs in os.walk(os.path.join(RAW, folder)) if fname in fs)


pbf, trips, imd = os.path.join(RAW, "madrid-260101.osm.pbf"), os.path.dirname(find("trips_2023", "trips_23_01_January.csv")), find("imd_2019", "IMD_2019.shp")
print(f"""
Rebuild the lane analysis (from {ROOT}):
  python3 pipeline/historical/14_lane_priority.py {pbf} {trips} data
  python3 pipeline/historical/15_lane_network.py  {pbf} {trips} {imd} data
  python3 pipeline/historical/16_route_graph.py   {pbf} {imd} data site
  python3 pipeline/build_site.py""")
