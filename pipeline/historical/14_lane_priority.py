"""Where would a new protected bike lane help most? Rank street corridors by the bikes that ride them
unprotected (weighted by how stressful the street is) and by the bike accidents that happen on them.

Usage: python3 pipeline/historical/14_lane_priority.py <Madrid.osm.pbf> <trips_dir_2023> <Infraestructura_Ciclista.shp> <data_dir> [--w-bikes 0.5]
Writes <data_dir>/lane_priority.csv (ranked corridors with geometry) and prints the 10/25/50 km plans.

Method (approach A, a static ranking):
  1. Route every Jan-Feb 2023 station-to-station trip on the same bike-weighted OSM graph as 11_all_routes.py
     and count trips on every street segment (cached in <data_dir>/../.cache/edge_trips.npz).
  2. Mark segments that already have a separated lane (within 15 m of Madrid's exclusive infrastructure).
  3. Snap each located bike accident (2019 onwards) to the nearest street segment within 25 m;
     serious injuries and deaths count 5 times.
  4. Group unprotected segments into corridors: same street name, connected, cut into pieces of about 1 km.
  5. Score = w * (share of the city's stress-weighted unprotected bike-km) + (1 - w) * (share of weighted accidents),
     and rank corridors by score per km of street.
Stress is a proxy for the level of traffic stress (Mekuria et al. 2012) from road class and lane count:
residential 0.2, tertiary 0.5, secondary 0.85, primary and trunk 1; the side roads of a big boulevard (same name
as a trunk or primary carriageway) count 0.5.
"""
import sys, os, ast, math, heapq, argparse, zlib, numpy as np, pandas as pd, osmium, shapefile
from bike_costs import COST, factor
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely import STRtree
from scipy.spatial import cKDTree

ap = argparse.ArgumentParser()
ap.add_argument("pbf"); ap.add_argument("trips"); ap.add_argument("shp"); ap.add_argument("data")
ap.add_argument("--w-bikes", type=float, default=0.5)
ap.add_argument("--what-if", default="", help="';'-separated street names to treat as already protected when routing (latent demand test)")
A = ap.parse_args()
WHATIF = set(filter(None, A.what_if.split(";")))
CACHE = os.path.join(os.path.dirname(os.path.abspath(A.data)), ".cache"); os.makedirs(CACHE, exist_ok=True)

CANDIDATE = {"trunk": 1.0, "primary": 1.0, "secondary": 0.85, "tertiary": 0.5, "residential": 0.2, "unclassified": 0.2}
BBOX = (40.37, 40.50, -3.76, -3.61)
DAYS = 49  # 1 Jan - 18 Feb 2023

# ---------- graph (identical weights to 11_all_routes.py), keeping the way of every edge ----------
class H(osmium.SimpleHandler):
    def __init__(s):
        super().__init__(); s.ways = []
    def way(s, w):
        t = w.tags; hw = t.get("highway"); f = factor(t)
        if f is None: return
        try: pts = [(n.ref, n.lon, n.lat) for n in w.nodes]
        except osmium.InvalidLocationError: return
        if not any(BBOX[0] <= la <= BBOX[1] and BBOX[2] <= lo <= BBOX[3] for _, lo, la in pts): return
        if t.get("name") in WHATIF: f = COST["cycleway"]
        ow = t.get("oneway") in ("yes", "1", "true") or hw in ("primary_link", "secondary_link") and t.get("oneway") != "no" or t.get("junction") == "roundabout"
        if t.get("oneway:bicycle") == "no" or t.get("cycleway", "").startswith("opposite"): ow = False
        try: lanes = int(t.get("lanes", "0").split(";")[0])
        except ValueError: lanes = 0
        s.ways.append((pts, f, ow, t.get("oneway") == "-1", hw, t.get("name", ""), lanes))

h = H(); h.apply_file(A.pbf, locations=True)
fw = Transformer.from_crs(4326, 25830, always_xy=True); bw = Transformer.from_crs(25830, 4326, always_xy=True)
coord = {}
for pts, *_ in h.ways:
    for (i, lo, la) in pts: coord[i] = (lo, la)
ids = list(coord); X, Y = fw.transform([coord[i][0] for i in ids], [coord[i][1] for i in ids]); xy = dict(zip(ids, zip(X, Y)))
adj, edge_way = {}, {}
for wi, (pts, f, ow, rev, *_r) in enumerate(h.ways):
    if rev: pts = pts[::-1]
    for (a, *_), (b, *_) in zip(pts, pts[1:]):
        w = math.dist(xy[a], xy[b]) * f
        adj.setdefault(a, []).append((b, w))
        if not ow: adj.setdefault(b, []).append((a, w))
        edge_way[(a, b) if a < b else (b, a)] = wi
EK = list(edge_way); EIDX = {k: i for i, k in enumerate(EK)}
print("graph", len(coord), "edges", len(EK), flush=True)

# ---------- trips per edge (cached: routing takes a few minutes) ----------
cache = os.path.join(CACHE, "edge_trips.npz" if not WHATIF else "edge_trips_whatif_%08x.npz" % zlib.crc32(A.what_if.encode()))
if os.path.exists(cache) and np.load(cache)["n"] == len(EK):
    etrips = np.load(cache)["t"]; print("edge trips from cache", flush=True)
else:
    t = pd.concat([pd.read_csv(f"{A.trips}/trips_23_0{m}.csv", sep=";", low_memory=False) for m in ["1_January", "2_February"]], ignore_index=True).dropna(how="all")
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
    od = v[v.station_unlock.isin(pos.index) & v.station_lock.isin(pos.index)].groupby(["station_unlock", "station_lock"]).size().rename("trips").reset_index()
    inn = {b for a in adj for b, _ in adj[a]}
    cand = [n for n in adj if n in inn]
    kd = cKDTree(np.array([xy[n] for n in cand]))
    PX, PY = fw.transform(pos.lon.values, pos.lat.values)
    snap = {sid: cand[kd.query([x, y])[1]] for sid, x, y in zip(pos.index, PX, PY)}
    etrips = np.zeros(len(EK))
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
            if tgt not in seen or tgt == src: continue
            n = tgt
            while n != src:
                p = prev[n]; etrips[EIDX[(p, n) if p < n else (n, p)]] += trips; n = p
        if k % 40 == 0: print("sources", k, flush=True)
    np.savez_compressed(cache, t=etrips, n=len(EK))
print("trips on edges: total bike-km/day", round(sum(etrips[i] * math.dist(xy[a], xy[b]) for i, (a, b) in enumerate(EK)) / 1000 / DAYS), flush=True)

# ---------- existing separated lanes ----------
r = shapefile.Reader(A.shp, encoding="utf-8"); ex = []
for sh, rec in zip(r.shapes(), r.records()):
    if rec["d_COD_TIPO"].replace("ESCLUSIVA", "EXCLUSIVA") not in ("VÍA EXCLUSIVA BICI", "ANILLO VERDE CICLISTA"): continue
    for i0, i1 in zip(list(sh.parts), list(sh.parts[1:]) + [len(sh.points)]):
        if i1 - i0 >= 2: ex.append(LineString(sh.points[i0:i1]))
EXB = prep(unary_union([g.buffer(15) for g in ex]))

# ---------- per-edge table ----------
rows = []
for i, (a, b) in enumerate(EK):
    pts, f, ow, rev, hw, name, lanes = h.ways[edge_way[(a, b)]]
    L = math.dist(xy[a], xy[b]); mx, my = (xy[a][0] + xy[b][0]) / 2, (xy[a][1] + xy[b][1]) / 2
    stress = CANDIDATE.get(hw)
    if stress is not None and hw in ("residential", "unclassified") and lanes >= 3: stress = 0.5
    if stress is not None and hw == "tertiary" and lanes >= 3: stress = 0.85
    rows.append((i, a, b, hw, name, L, mx, my, etrips[i], stress))
E = pd.DataFrame(rows, columns=["i", "a", "b", "hw", "name", "len", "mx", "my", "trips", "stress"])
# side roads of a boulevard: tagged residential but they run beside 3-6 lanes of traffic
big = set(E.loc[E.hw.isin(["trunk", "primary"]), "name"]) - {""}
E.loc[E.hw.isin(["residential", "unclassified"]) & E.name.isin(big), "stress"] = 0.5
E["protected"] = [EXB.contains(Point(x, y)) for x, y in zip(E.mx, E.my)]
E["cand"] = E.stress.notna() & ~E.protected & (E.name != "")
E["bkm"] = E.trips * E.len / 1000 / DAYS                     # bike-km per day
E["sbkm"] = E.bkm * E.stress.fillna(0)                        # stress-weighted
print("candidate edges", int(E.cand.sum()), "of", len(E), flush=True)

# ---------- accidents -> nearest road edge within 25 m ----------
acc = pd.read_csv(os.path.join(A.data, "madrid_bike_accidents.csv"))
acc = acc.dropna(subset=["lat", "lon"])
acc["w"] = 1 + 4 * ((acc.serious > 0) | (acc.killed > 0))
road = E[E.hw.isin(list(CANDIDATE) + ["living_street", "service", "busway", "tertiary_link", "secondary_link", "primary_link", "trunk_link", "cycleway"])]
lines = [LineString([xy[a], xy[b]]) for a, b in zip(road.a, road.b)]
tree = STRtree(lines)
AX, AY = fw.transform(acc.lon.values, acc.lat.values)
pts = [Point(x, y) for x, y in zip(AX, AY)]
qi, ti = tree.query_nearest(pts, max_distance=25, return_distance=False, all_matches=False)
E["acc"] = 0.0; E["acc_w"] = 0.0; E["acc_sev"] = 0.0
ridx = road.index.values
for q, t_ in zip(qi, ti):
    j = ridx[t_]; E.at[j, "acc"] += 1; E.at[j, "acc_w"] += acc.w.iat[q]; E.at[j, "acc_sev"] += acc.w.iat[q] > 1
years = (pd.Timestamp(acc.year.max(), 8, 31) - pd.Timestamp(acc.year.min(), 1, 1)).days / 365.25
E.to_pickle(os.path.join(CACHE, "edges.pkl"))  # for diagnostics
print("accidents", len(acc), "snapped", len(qi), "years", round(years, 2), flush=True)

# ---------- corridors: same name + connected, cut into ~1 km pieces along the street's main axis ----------
C = E[E.cand].copy()
parent = {}
def find(x):
    while parent.get(x, x) != x:
        parent[x] = parent.get(parent[x], parent[x]); x = parent[x]
    return x
def union(x, y):
    rx, ry = find(x), find(y)
    if rx != ry: parent[rx] = ry
for name, g in C.groupby("name"):
    for a, b in zip(g.a, g.b): union(("n", name, a), ("n", name, b))
C["comp"] = [find(("n", n, a)) for n, a in zip(C.name, C.a)]
pieces = []
for comp, g in C.groupby("comp"):
    P = np.c_[g.mx, g.my]; c0 = P.mean(0)
    if len(g) > 1:
        _, _, vt = np.linalg.svd(P - c0, full_matrices=False); ax = vt[0]
    else: ax = np.array([1.0, 0.0])
    s = (P - c0) @ ax; span = s.max() - s.min() if len(g) > 1 else g.len.iat[0]
    k = max(1, round(span / 1000))
    cut = np.minimum(((s - s.min()) / (span + 1e-9) * k).astype(int), k - 1)
    for j in range(k):
        gg = g[cut == j]
        if gg.empty: continue
        # street length, not lane length: parallel carriageways (a boulevard can have 4) count once, a winding street keeps its length
        ss = s[cut == j]; tot = gg.len.sum(); span = ss.max() - ss.min()
        km = (span if tot > 1.6 * span else tot) / 1000
        pieces.append({"name": gg.name.iat[0], "hw": gg.hw.mode().iat[0], "km": km, "edges": gg.i.tolist(),
                       "bkm": gg.bkm.sum(), "sbkm": gg.sbkm.sum(), "acc": gg.acc.sum(), "acc_w": gg.acc_w.sum(), "acc_sev": gg.acc_sev.sum(),
                       "trips_day": (gg.trips * gg.len).sum() / max(gg.len.sum(), 1) / DAYS})
Pc = pd.DataFrame(pieces)
Pc["km"] = Pc.km.clip(lower=0.25)  # roundabouts and short blocks compete as if 250 m long
tot_s, tot_a = E.loc[~E.protected, "sbkm"].sum(), E.acc_w.sum()
w = A.w_bikes
Pc["score"] = w * Pc.sbkm / tot_s + (1 - w) * Pc.acc_w / tot_a
Pc["score_km"] = Pc.score / Pc.km
# every corridor piece, with its street segments, for 15_lane_network.py
Pc.assign(keys=[[EK[i] for i in e] for e in Pc.edges]).drop(columns="edges").to_pickle(os.path.join(CACHE, "corridors.pkl"))
Pc = Pc.sort_values("score_km", ascending=False).reset_index(drop=True)
Pc["cum_km"] = Pc.km.cumsum()
Pc["cum_sbkm_pct"] = Pc.sbkm.cumsum() / tot_s * 100
Pc["cum_bkm_pct"] = Pc.bkm.cumsum() / E.loc[~E.protected, "bkm"].sum() * 100
Pc["cum_acc_pct"] = Pc.acc_w.cumsum() / tot_a * 100

def geom(edges):
    segs = [LineString([xy[EK[i][0]], xy[EK[i][1]]]) for i in edges]
    m = unary_union(segs).simplify(4)
    out = []
    for ln in getattr(m, "geoms", [m]):
        lo, la = bw.transform(*ln.xy); out.append(" ".join(f"{x:.5f},{y:.5f}" for x, y in zip(lo, la)))
    return "|".join(out)
top = Pc[Pc.cum_km <= 60].copy()
top["geometry"] = [geom(e) for e in top.edges]
out = top.assign(rank=range(1, len(top) + 1), acc_per_year=(top.acc / years).round(1), serious_per_year=(top.acc_sev / years).round(2),
                 bike_km_day=top.bkm.round(0), trips_day=top.trips_day.round(0), km=top.km.round(2),
                 cum_km=top.cum_km.round(1), cum_bike_km_pct=top.cum_bkm_pct.round(1), cum_stress_bike_km_pct=top.cum_sbkm_pct.round(1), cum_acc_pct=top.cum_acc_pct.round(1))
cols = ["rank", "name", "hw", "km", "trips_day", "bike_km_day", "acc_per_year", "serious_per_year", "cum_km", "cum_bike_km_pct", "cum_stress_bike_km_pct", "cum_acc_pct", "geometry"]
out[cols].rename(columns={"name": "street", "hw": "road_class"}).to_csv(os.path.join(A.data, "lane_priority.csv"), index=False)

print(f"\nweights: bikes {w:.2f} / accidents {1 - w:.2f}; unprotected bike-km/day {E.loc[~E.protected, 'bkm'].sum():.0f}; accidents {int(E.acc.sum())}")
for budget in (10, 25, 50):
    s = Pc[Pc.cum_km <= budget]
    print(f"{budget:>3} km: {len(s):>3} corridors, {s.cum_bkm_pct.iat[-1]:.1f}% of unprotected bike-km, "
          f"{s.cum_sbkm_pct.iat[-1]:.1f}% of stress-weighted bike-km, {s.cum_acc_pct.iat[-1]:.1f}% of weighted accidents")
print(out[["rank", "name", "km", "trips_day", "acc_per_year", "cum_km"]].head(25).to_string(index=False))
