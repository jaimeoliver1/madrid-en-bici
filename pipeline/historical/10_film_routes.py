"""Route every BiciMAD trip of the animated day along OSM streets.

Builds a bike-weighted street graph from an OSM extract, snaps the 2023 stations to it and
computes the expected route for each station pair used on the film's day. Output is a text
module for the 24-hour animation: one line per pair, "a,b:" + points encoded 2 chars per
coordinate in stage pixels (1920x1080), using the same projection as the film's map.json.

Usage: python3 pipeline/historical/10_film_routes.py <madrid.osm.pbf> <trips_dir_2023> <out_dir>/map.json <out_dir>
Inputs pinned in inputs.json; map.json comes from film_01_day_data.py.
"""
import sys, json, ast, math, heapq, numpy as np, pandas as pd, osmium
from bike_costs import COST, factor
from scipy.spatial import cKDTree

PBF, RAW, MAPJ, OUT = sys.argv[1:5]
BBOX = (40.37, 40.50, -3.76, -3.61)

class H(osmium.SimpleHandler):
    def __init__(s):
        super().__init__(); s.ways = []
    def way(s, w):
        t = w.tags; hw = t.get("highway"); f = factor(t)
        if f is None: return
        try: pts = [(n.ref, n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError: return
        if not any(BBOX[0] <= la <= BBOX[1] and BBOX[2] <= lo <= BBOX[3] for _, lo, la in pts): return
        ow = t.get("oneway") in ("yes", "1", "true") or hw in ("primary_link", "secondary_link") and t.get("oneway") != "no" or t.get("junction") == "roundabout"
        if t.get("oneway:bicycle") == "no" or t.get("cycleway", "").startswith("opposite"): ow = False
        s.ways.append((pts, f, ow, t.get("oneway") == "-1"))

h = H(); h.apply_file(PBF, locations=True)
print("ways", len(h.ways), flush=True)
coord, adj = {}, {}
def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    return 6371000 * 2 * math.asin(math.sqrt(math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2))
for pts, f, ow, rev in h.ways:
    if rev: pts = pts[::-1]
    for (i, lo, la) in pts: coord[i] = (lo, la)
    for (a, *_), (b, *_) in zip(pts, pts[1:]):
        w = hav(coord[a], coord[b]) * f
        adj.setdefault(a, []).append((b, w))
        if not ow: adj.setdefault(b, []).append((a, w))
print("nodes", len(coord), flush=True)

# film selection, identical to the film's data step
t = pd.concat([pd.read_csv(f"{RAW}/trips_23_0{m}.csv", sep=";", low_memory=False) for m in ["1_January", "2_February"]], ignore_index=True).dropna(how="all")
t["unlock"] = pd.to_datetime(t.unlock_date); t["lock"] = pd.to_datetime(t.lock_date)
same = t.station_unlock == t.station_lock
v = t[(t.trip_minutes >= 1) & (t.trip_minutes <= 180) & ~((t.trip_minutes < 2) & same)].dropna(subset=["station_unlock", "station_lock"]).copy()
def co(s):
    try: return ast.literal_eval(s)["coordinates"]
    except Exception: return [np.nan, np.nan]
u = np.array([co(s) for s in v.geolocation_unlock]); v["lon_u"], v["lat_u"] = u[:, 0], u[:, 1]
l = np.array([co(s) for s in v.geolocation_lock]); v["lon_l"], v["lat_l"] = l[:, 0], l[:, 1]
pu = v.groupby("station_unlock")[["lon_u", "lat_u"]].median(); pu.columns = ["lon", "lat"]
pl = v.groupby("station_lock")[["lon_l", "lat_l"]].median(); pl.columns = ["lon", "lat"]
pos = pu.combine_first(pl).dropna()
pos = pos[(pos.lat > 40.3) & (pos.lat < 40.6) & (pos.lon > -3.8) & (pos.lon < -3.6)]
idx = {sid: i for i, sid in enumerate(pos.index)}
DAY = pd.Timestamp("2023-01-12")
w = v[(v.unlock >= DAY - pd.Timedelta(hours=1)) & (v.lock > DAY) & (v.unlock < DAY + pd.Timedelta(days=1))]
w = w[w.station_unlock.isin(pos.index) & w.station_lock.isin(pos.index) & (w.station_unlock != w.station_lock)]
pairs = sorted({(idx[a], idx[b]) for a, b in zip(w.station_unlock, w.station_lock)})
print("pairs", len(pairs), flush=True)

# snap stations to nodes reachable both ways (largest component approximation: nodes with in and out edges)
inn = {b for a in adj for b, _ in adj[a]}
cand = [n for n in adj if n in inn]
kd = cKDTree(np.array([[coord[n][0] * 0.76, coord[n][1]] for n in cand]))
snap = [cand[kd.query([lo * 0.76, la])[1]] for lo, la in zip(pos.lon, pos.lat)]

# same projection as film_01_day_data.py
lat0 = pos.lat.mean(); k = math.cos(math.radians(lat0)); s = 1000 / (pos.lat.max() - pos.lat.min()); cx = (pos.lon.max() + pos.lon.min()) / 2
P = lambda lo, la: (1250 + (lo - cx) * k * s, 40 + (pos.lat.max() - la) * s)
def rdp(p, e):
    if len(p) < 3: return p
    a, b = np.array(p[0]), np.array(p[-1]); ab = b - a; n = math.hypot(*ab); Q = np.array(p) - a
    d = np.abs(ab[0] * Q[:, 1] - ab[1] * Q[:, 0]) / n if n > 0 else np.hypot(Q[:, 0], Q[:, 1])
    i = int(d.argmax())
    return rdp(p[:i + 1], e)[:-1] + rdp(p[i:], e) if d[i] > e else [p[0], p[-1]]
A = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
enc = lambda v: A[int(v) // 64] + A[int(v) % 64]

by_src = {}
for a, b in pairs: by_src.setdefault(a, []).append(b)
lines, fails, lens = [], 0, []
for a, targets in by_src.items():
    src = snap[a]; want = {snap[b] for b in targets}
    dist, prev, seen, left = {src: 0.0}, {}, set(), set(want)
    pq = [(0.0, src)]
    while pq and left:
        d, n = heapq.heappop(pq)
        if n in seen: continue
        seen.add(n); left.discard(n)
        for m, wgt in adj.get(n, ()):
            nd = d + wgt
            if nd < dist.get(m, 1e18): dist[m] = nd; prev[m] = n; heapq.heappush(pq, (nd, m))
    for b in targets:
        tgt = snap[b]
        if tgt not in seen: fails += 1; continue
        path = [tgt]
        while path[-1] != src: path.append(prev[path[-1]])
        path.reverse()
        pts = [P(pos.lon.iloc[a], pos.lat.iloc[a])] + [P(*coord[n]) for n in path] + [P(pos.lon.iloc[b], pos.lat.iloc[b])]
        lens.append(sum(hav(coord[x], coord[y]) for x, y in zip(path, path[1:])))
        pts = rdp([(round(x * 2) / 2, round(y * 2) / 2) for x, y in pts], 1.0)
        lines.append(f"{a},{b}:" + "".join(enc(max(0, min(4095, round(x * 2)))) + enc(max(0, min(4095, round(y * 2)))) for x, y in pts))
txt = "\n".join(lines)
open(f"{OUT}/routes.txt", "w").write(txt)  # read by 12_build_film_data.py
print("routed", len(lines), "failed", fails, "chars", len(txt), "median route m", round(float(np.median(lens))), flush=True)
# split into modules of at most 190 KiB on line boundaries
parts, cur = [], []
for ln in lines:
    if sum(len(x) + 1 for x in cur) + len(ln) > 190 * 1024: parts.append("\n".join(cur)); cur = []
    cur.append(ln)
parts.append("\n".join(cur))
for i, ptxt in enumerate(parts, 1):
    json.dump({"kind": "text", "text": ptxt}, open(f"{OUT}/doc_routes_{i}.json", "w"))
print("modules", len(parts))
