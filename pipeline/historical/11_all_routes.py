"""Route every station-to-station BiciMAD trip of Jan-Feb 2023 on the local OSM bike graph and
measure how much of each route runs on Madrid's bike infrastructure.

Usage: python3 pipeline/11_all_routes.py <Madrid.osm.pbf> <trips_dir_2023> <Infraestructura_Ciclista.shp> <out_dir>
Writes <out_dir>/bicimad_2023_routes_all.csv.gz (one row per station pair) and
<out_dir>/bicimad_2023_top_routes_routed.csv (geometry for the most used pairs, for the site map).
"""
import sys, ast, math, heapq, numpy as np, pandas as pd, osmium, shapefile
from pyproj import Transformer
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely.prepared import prep
from scipy.spatial import cKDTree

PBF, RAW, SHP, OUT = sys.argv[1:5]
COST = {"cycleway": 0.6, "living_street": 0.9, "residential": 1.0, "unclassified": 1.0, "service": 1.15, "busway": 1.1,
        "tertiary": 1.15, "tertiary_link": 1.15, "secondary": 1.35, "secondary_link": 1.35, "primary": 1.6, "primary_link": 1.6,
        "pedestrian": 1.3, "path": 1.0, "track": 1.2, "footway": 1.6, "steps": 12.0}
BBOX = (40.37, 40.50, -3.76, -3.61)

class H(osmium.SimpleHandler):
    def __init__(s):
        super().__init__(); s.ways = []
    def way(s, w):
        t = w.tags; hw = t.get("highway")
        if hw not in COST or t.get("access") in ("no", "private") or t.get("bicycle") == "no": return
        try: pts = [(n.ref, n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError: return
        if not any(BBOX[0] <= la <= BBOX[1] and BBOX[2] <= lo <= BBOX[3] for _, lo, la in pts): return
        f = COST[hw]
        if hw != "cycleway" and (t.get("bicycle") == "designated" or any(t.get(k, "").startswith(("track", "lane", "separate"))
                                                                     for k in ("cycleway", "cycleway:left", "cycleway:right", "cycleway:both"))):
            f = min(f, 0.75)
        ow = t.get("oneway") in ("yes", "1", "true") or hw in ("primary_link", "secondary_link") and t.get("oneway") != "no" or t.get("junction") == "roundabout"
        if t.get("oneway:bicycle") == "no" or t.get("cycleway", "").startswith("opposite"): ow = False
        s.ways.append((pts, f, ow, t.get("oneway") == "-1"))

h = H(); h.apply_file(PBF, locations=True)
fw = Transformer.from_crs(4326, 25830, always_xy=True)
coord, adj = {}, {}
for pts, f, ow, rev in h.ways:
    if rev: pts = pts[::-1]
    for (i, lo, la) in pts: coord[i] = (lo, la)
ids = list(coord); X, Y = fw.transform([coord[i][0] for i in ids], [coord[i][1] for i in ids]); xy = dict(zip(ids, zip(X, Y)))
for pts, f, ow, rev in h.ways:
    if rev: pts = pts[::-1]
    for (a, *_), (b, *_) in zip(pts, pts[1:]):
        w = math.dist(xy[a], xy[b]) * f
        adj.setdefault(a, []).append((b, w))
        if not ow: adj.setdefault(b, []).append((a, w))
print("graph", len(coord), flush=True)

t = pd.concat([pd.read_csv(f"{RAW}/trips_23_0{m}.csv", sep=";", low_memory=False) for m in ["1_January", "2_February"]], ignore_index=True).dropna(how="all")
same = t.station_unlock == t.station_lock
v = t[(t.trip_minutes >= 1) & (t.trip_minutes <= 180) & ~same].dropna(subset=["station_unlock", "station_lock"]).copy()
def co(s):
    try: return ast.literal_eval(s)["coordinates"]
    except Exception: return [np.nan, np.nan]
u = np.array([co(s) for s in v.geolocation_unlock]); v["lon_u"], v["lat_u"] = u[:, 0], u[:, 1]
l = np.array([co(s) for s in v.geolocation_lock]); v["lon_l"], v["lat_l"] = l[:, 0], l[:, 1]
pu = v.groupby("station_unlock")[["lon_u", "lat_u"]].median(); pu.columns = ["lon", "lat"]
pl = v.groupby("station_lock")[["lon_l", "lat_l"]].median(); pl.columns = ["lon", "lat"]
pos = pu.combine_first(pl).dropna()
pos = pos[(pos.lat > 40.3) & (pos.lat < 40.6) & (pos.lon > -3.8) & (pos.lon < -3.6)]
names = v.groupby("station_unlock").unlock_station_name.agg(lambda s: s.mode().iat[0])
od = v[v.station_unlock.isin(pos.index) & v.station_lock.isin(pos.index)].groupby(["station_unlock", "station_lock"]).size().rename("trips").reset_index()
print("pairs", len(od), "trips", od.trips.sum(), flush=True)

inn = {b for a in adj for b, _ in adj[a]}
cand = [n for n in adj if n in inn]
kd = cKDTree(np.array([xy[n] for n in cand]))
PX, PY = fw.transform(pos.lon.values, pos.lat.values)
snap = {sid: cand[kd.query([x, y])[1]] for sid, x, y in zip(pos.index, PX, PY)}

r = shapefile.Reader(SHP, encoding="utf-8"); ex, an = [], []
for sh, rec in zip(r.shapes(), r.records()):
    for i0, i1 in zip(list(sh.parts), list(sh.parts[1:]) + [len(sh.points)]):
        p = sh.points[i0:i1]
        if len(p) < 2: continue
        L = LineString(p); an.append(L)
        if rec["d_COD_TIPO"].replace("ESCLUSIVA", "EXCLUSIVA") in ("VÍA EXCLUSIVA BICI", "ANILLO VERDE CICLISTA"): ex.append(L)
EXB = prep(unary_union([l.buffer(15) for l in ex])); ANB = prep(unary_union([l.buffer(15) for l in an]))
# classify each graph edge once (midpoint test), then a route's share is a length-weighted sum
from shapely.geometry import Point
edge_cls = {}
def cls(a, b):
    k = (a, b) if a < b else (b, a)
    c = edge_cls.get(k)
    if c is None:
        m = Point((xy[a][0] + xy[b][0]) / 2, (xy[a][1] + xy[b][1]) / 2)
        c = 2 if EXB.contains(m) else 1 if ANB.contains(m) else 0
        edge_cls[k] = c
    return c

tr = Transformer.from_crs(25830, 4326, always_xy=True)
rows, geo = [], {}
top = set(map(tuple, od.sort_values("trips", ascending=False).head(1500)[["station_unlock", "station_lock"]].values))
for k, (src_id, grp) in enumerate(od.groupby("station_unlock")):
    src = snap[src_id]; want = {snap[b] for b in grp.station_lock}
    dist, prev, seen, left = {src: 0.0}, {}, set(), set(want)
    pq = [(0.0, src)]
    while pq and left:
        d, n = heapq.heappop(pq)
        if n in seen: continue
        seen.add(n); left.discard(n)
        for m, wgt in adj.get(n, ()):
            nd = d + wgt
            if nd < dist.get(m, 1e18): dist[m] = nd; prev[m] = n; heapq.heappush(pq, (nd, m))
    for b, trips in zip(grp.station_lock, grp.trips):
        tgt = snap[b]
        if tgt not in seen: continue
        path = [tgt]
        while path[-1] != src: path.append(prev[path[-1]])
        path.reverse()
        L = [0.0, 0.0, 0.0]
        for a_, b_ in zip(path, path[1:]): L[cls(a_, b_)] += math.dist(xy[a_], xy[b_])
        tot = sum(L) or 1
        rows.append({"from": names.get(src_id, str(src_id)), "to": names.get(b, str(b)), "trips": int(trips), "route_m": round(tot),
                     "share_exclusive": round(L[2] / tot * 100, 1), "share_any": round((L[2] + L[1]) / tot * 100, 1)})
        if (src_id, b) in top:
            lo, la = tr.transform([xy[n][0] for n in path], [xy[n][1] for n in path])
            pts = list(zip(lo, la)); step = max(1, len(pts) // 60)
            keep = pts[::step] + [pts[-1]]
            rows[-1]["path"] = " ".join(f"{a:.5f},{b:.5f}" for a, b in keep)
    if k % 40 == 0: print("sources", k, flush=True)
df = pd.DataFrame(rows)
df.drop(columns="path").to_csv(f"{OUT}/bicimad_2023_routes_all.csv.gz", index=False)
df.dropna(subset=["path"]).sort_values("trips", ascending=False).head(300).to_csv(f"{OUT}/bicimad_2023_top_routes_routed.csv", index=False)
w = df.trips
print("routed pairs", len(df), "trips", int(w.sum()), "share exclusive", round((df.share_exclusive * w).sum() / w.sum(), 1),
      "share any", round((df.share_any * w).sum() / w.sum(), 1), flush=True)
