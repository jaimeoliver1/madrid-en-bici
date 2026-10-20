"""Build the compact bike network for the website's route planner (site/route-graph.json).

Usage: python3 pipeline/historical/16_route_graph.py <madrid.osm.pbf> <IMD_2019.shp> <data_dir> <site_dir>
Needs 14_lane_priority.py first (.cache/edges.pkl: accidents and existing separated lanes per segment),
.cache/od2023.pkl (written by 15_lane_network.py, for exposure) and the Copernicus DEM tile in .cache/.

The planner runs Dijkstra in the browser with the same perceived-distance model as 15_lane_network.py
(appraisal.py: Broach et al. 2012 for traffic, separated paths and slopes) plus an optional accident term, and can
switch on the protected lanes proposed in data/lane_network_plan.csv (its exact segments, column osm_segments). To keep
the file small:
  - sidewalks, crossings, service roads, steps and tracks are left out;
  - segments between junctions are merged into links that carry length-weighted sums of every cost component, so
    any weighting chosen in the browser gives exactly the same cost as on the full segment graph;
  - coordinates are rounded to 1e-5 degrees (about 1 m) and stored as differences.
"""
import os, sys, json, pickle, numpy as np, pandas as pd
from scipy.spatial import cKDTree
import bikegraph as bg
import appraisal as ap_
import provenance as pv
from bike_costs import COST

PBF, IMD, DATA, SITE = sys.argv[1:5]
CACHE = os.path.join(os.path.dirname(os.path.abspath(DATA)), ".cache")
DEM = os.path.join(CACHE, "copernicus_dem_N40_W004.tif")
PROV = pv.record(osm=PBF, traffic=[IMD, IMD[:-4] + ".dbf"], dem=DEM, accidents=os.path.join(DATA, "madrid_bike_accidents.csv"),
                 counters=os.path.join(DATA, "madrid_bike_counters.csv"), plan=os.path.join(DATA, "lane_network_plan.csv"))
g = bg.Graph(PBF, dem=DEM)
aadt, measured, *_ = bg.segment_aadt(g, IMD)
cached = pickle.load(open(os.path.join(CACHE, "od2023.pkl"), "rb"))
pv.check({"inputs": {"osm": {"sha256": cached[3]["osm"]}}} if len(cached) == 4 else {}, osm=PROV["inputs"]["osm"]["sha256"])
o, d, tr = cached[:3]
E = pd.read_pickle(os.path.join(CACHE, "edges.pkl"))
pv.check(E.attrs, **{k: PROV["inputs"][k]["sha256"] for k in ("osm", "accidents")})
E["seg"] = [g.seg_id.get((a, b) if a < b else (b, a), -1) for a, b in zip(E.a, E.b)]
E = E[E.seg >= 0]
sep0 = g.seg_sep.copy(); sep0[E.seg[E.protected].values] = True
nacc = np.zeros(g.nseg); nacc[E.seg.values] = E.acc.values
acc = pd.read_csv(os.path.join(DATA, "madrid_bike_accidents.csv"))
years = pv.accident_years(DATA)
cost_per_acc = (acc.n_slight * ap_.COST_SLIGHT + acc.n_serious * ap_.COST_SERIOUS + acc.n_killed * ap_.COST_DEATH).sum() / len(acc)

# ---------- today's flows and injury rates (same model as 15_lane_network.py) ----------
WALK = {"footway", "pedestrian", "path", "track", "steps"}
f = bg.broach_factors(g, aadt, sep0)
flow0 = bg.assign(g, f, o, d, tr)[0]
rate = bg.eb_rates(g, flow0, nacc, years, sep0)          # injuries per BiciMAD-km
first = np.full(g.nseg, -1); first[g.seg[::-1]] = np.arange(len(g.seg))[::-1]
smx = (g.x[g.u[first]] + g.x[g.v[first]]) / 2; smy = (g.y[g.u[first]] + g.y[g.v[first]]) / 2
cnt = pd.read_csv(os.path.join(DATA, "madrid_bike_counters.csv")).dropna(subset=["lat", "lon", "avg_daily_bikes_2023"])
cx, cy = bg.fw.transform(cnt.lon.values, cnt.lat.values)
SCALE = float(np.median([cnt.avg_daily_bikes_2023.iat[i] / (flow0[idx].max() / bg.DAYS)
                         for i, idx in enumerate(cKDTree(np.c_[smx, smy]).query_ball_point(np.c_[cx, cy], r=40)) if idx and flow0[idx].max() / bg.DAYS >= 5]))
inj_eur_km = rate / SCALE * cost_per_acc                  # expected injury cost per km ridden by one cyclist, EUR
print(f"all cyclists / BiciMAD {SCALE:.1f}; median injury cost per km on roads {np.median(inj_eur_km[np.isin(g.seg_hw, ['residential', 'tertiary'])]):.2f} EUR", flush=True)

# ---------- which segments the proposed plan protects ----------
plan = pd.read_csv(os.path.join(DATA, "lane_network_plan.csv"))
ROAD = {"trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link",
        "residential", "unclassified", "living_street", "busway"}
inplan = np.zeros(g.nseg, bool); plan_step = np.zeros(g.nseg, int)
# the exact street segments each step protects (OSM node pairs written by 15_lane_network.py)
for _, r in plan.iterrows():
    for pair in str(r.osm_segments).split():
        a_, b_ = map(int, pair.split("-")); s_ = g.seg_id.get((a_, b_) if a_ < b_ else (b_, a_))
        if s_ is not None and not inplan[s_]: inplan[s_] = True; plan_step[s_] = r.step
inplan &= ~sep0
print("plan segments", inplan.sum(), "km", round(g.seg_len[inplan].sum() / 1000, 1), flush=True)

# ---------- keep what a rider would use ----------
KEEP = ROAD | {"cycleway", "pedestrian", "path"}
keep = np.array([h in KEEP or (h == "footway" and s not in ("sidewalk", "crossing", "traffic_island")) for h, s in zip(g.seg_hw, g.seg_sub)])
# segment endpoints and allowed directions (from the arcs of the graph)
a_n = np.array([g.idx[a] for a, b in g.seg_key]); b_n = np.array([g.idx[b] for a, b in g.seg_key])
fwd = np.zeros(g.nseg, bool); bwd = np.zeros(g.nseg, bool); upf = np.zeros(g.nseg); upb = np.zeros(g.nseg)
real = ~g.rev
isf = g.u[real] == a_n[g.seg[real]]
fwd[g.seg[real][isf]] = True; bwd[g.seg[real][~isf]] = True
# keep only the largest connected component of the kept network
segs = np.where(keep)[0]
parent = np.arange(g.n)
def find(x):
    while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
    return x
for s in segs:
    ra, rb = find(a_n[s]), find(b_n[s])
    if ra != rb: parent[ra] = rb
root = np.array([find(a_n[s]) for s in segs]); big = np.bincount(root).argmax()
segs = segs[root == big]
print("segments kept", len(segs), "of", g.nseg, flush=True)

# per-segment cost components, in metres (see the JS: cost = L + walk + traffic + path bonus + slope + accidents)
L = g.seg_len
walkx = np.array([COST[h] - 1 if h in WALK else 0.0 for h in g.seg_hw]) * L
band = np.zeros(g.nseg, int)
for i, (lo, _) in enumerate(sorted(ap_.TRAFFIC)): band[aadt >= lo] = i + 1   # 1: 10-20k, 2: 20-30k, 3: 30k+
busy = ~g.seg_lane & ~sep0 & (band > 0)
SLO = [lo for lo, _ in sorted(ap_.SLOPE)]
def slope_band(grade):
    return sum(grade >= lo for lo in SLO)   # 0: under 2%, 1: 2-4%, 2: 4-6%, 3: 6% or more

# ---------- merge segments between junctions into links ----------
deg = np.bincount(np.r_[a_n[segs], b_n[segs]], minlength=g.n)
inc = {}
for s in segs:
    inc.setdefault(a_n[s], []).append(s); inc.setdefault(b_n[s], []).append(s)
def dir_from(s, n):  # (can go from n along s, can come back to n along s)
    return (fwd[s], bwd[s]) if a_n[s] == n else (bwd[s], fwd[s])
def through(n):
    if deg[n] != 2: return False
    s1, s2 = inc[n]
    if g.seg_name[s1] != g.seg_name[s2] or inplan[s1] != inplan[s2]: return False
    o1, i1 = dir_from(s1, n); o2, i2 = dir_from(s2, n)
    return (i1 == o2) and (o1 == i2)   # same direction rules on both sides
used = np.zeros(g.nseg, bool); links = []
def walk(n0, s0):
    path = [n0]; ss = []; n, s = n0, s0
    while True:
        used[s] = True; ss.append(s)
        n = b_n[s] if a_n[s] == n else a_n[s]; path.append(n)
        if not through(n): break
        s = inc[n][1] if inc[n][0] == s else inc[n][0]
        if used[s]: break
    return path, ss
for n0 in np.unique(np.r_[a_n[segs], b_n[segs]]):
    if through(n0): continue
    for s0 in inc[n0]:
        if not used[s0]: links.append(walk(n0, s0))
for s in segs:  # closed loops with no junction
    if not used[s]: links.append(walk(a_n[s], s))
print("links", len(links), flush=True)

nodes = {}; E_out = []; GEO = []; names = {"": 0}
q = lambda v: int(round(v * 1e5))
for path, ss in links:
    na, nb = path[0], path[-1]
    for n in (na, nb):
        if n not in nodes: nodes[n] = len(nodes)
    # directions for the whole link: allowed from na towards nb, and back
    okf = all(dir_from(s, n)[0] for s, n in zip(ss, path[:-1])); okb = all(dir_from(s, n)[1] for s, n in zip(ss, path[:-1]))
    if not (okf or okb): continue
    c = dict(L=0.0, W=0.0, T1=0.0, T2=0.0, T3=0.0, S=0.0, P=0.0, PT1=0.0, PT2=0.0, PT3=0.0, PW=0.0,
             U1f=0.0, U2f=0.0, U3f=0.0, U1b=0.0, U2b=0.0, U3b=0.0, Gf=0.0, Gb=0.0, A=0.0, I=0.0, IP=0.0, step=0)
    # elevation profile along the link from the DEM, smoothed over ~50 m (as in bikegraph.py) so noise is not read as hills
    dd = np.r_[0, np.cumsum([L[s] for s in ss])]; zz = g.z[path]
    if len(zz) > 2:
        wk = np.exp(-0.5 * ((dd[:, None] - dd[None, :]) / 50.0) ** 2); zz = (wk @ zz) / wk.sum(1)
    for j, (s, n) in enumerate(zip(ss, path[:-1])):
        l = L[s]; c["L"] += l
        if sep0[s]: c["S"] += l
        else:
            c["W"] += walkx[s]
            if busy[s]: c[f"T{band[s]}"] += l
        if inplan[s]:
            c["P"] += l; c["PW"] += walkx[s]; c["step"] = max(c["step"], plan_step[s])
            if busy[s]: c[f"PT{band[s]}"] += l
        up = zz[j + 1] - zz[j]                  # climb when riding na -> nb
        sb = slope_band(abs(up) / max(l, 1e-6))
        if sb: c[f"U{sb}{'f' if up > 0 else 'b'}"] += l
        c["Gf"] += max(up, 0); c["Gb"] += max(-up, 0)
        c["A"] += nacc[s]
        ie = inj_eur_km[s] * l / 1000
        c["I"] += ie
        if inplan[s]: c["IP"] += ie
    nm = g.seg_name[ss[0]]
    if nm not in names: names[nm] = len(names)
    two_way_plan = 1 if (c["P"] >= 0.9 * c["L"] and not (okf and okb)) else 0
    E_out.append([nodes[na], nodes[nb], int(okf) + 2 * int(okb) + 4 * two_way_plan, round(c["L"]), round(c["W"]),
                  round(c["T1"]), round(c["T2"]), round(c["T3"]), round(c["S"]), round(c["P"]), round(c["PT1"]), round(c["PT2"]), round(c["PT3"]),
                  round(c["PW"]), round(c["U1f"]), round(c["U2f"]), round(c["U3f"]), round(c["U1b"]), round(c["U2b"]), round(c["U3b"]),
                  round(c["Gf"], 1), round(c["Gb"], 1), int(c["A"]), round(c["I"] * 1000), round(c["IP"] * 1000), names[nm], int(c["step"])])
    # geometry: node coordinates along the link, simplified to ~3 m, as rounded lon/lat differences
    xs, ys = g.x[path], g.y[path]
    from shapely.geometry import LineString
    ln = LineString(np.c_[xs, ys]).simplify(3)
    lo, la = bg.bw.transform(*ln.xy)
    qq = [(q(a_), q(b_)) for a_, b_ in zip(lo, la)]
    flat = [qq[0][0], qq[0][1]]
    for (x0, y0), (x1, y1) in zip(qq, qq[1:]): flat += [x1 - x0, y1 - y0]
    GEO.append(flat)
node_ll = np.zeros((len(nodes), 2), int)
for n, i in nodes.items(): node_ll[i] = (q(g.lon[n]), q(g.lat[n]))
FIELDS = ["a", "b", "dir", "L", "W", "T1", "T2", "T3", "S", "P", "PT1", "PT2", "PT3", "PW", "U1f", "U2f", "U3f", "U1b", "U2b", "U3b",
          "Gf", "Gb", "A", "I", "IP", "name", "step"]
out = {
    "about": "Compact bike network for the route planner. Built by pipeline/historical/16_route_graph.py; method in docs/ROUTING.md.",
    "provenance": PROV,
    "fields": FIELDS,
    "params": {"traffic": [round(v, 4) for _, v in sorted(ap_.TRAFFIC)], "path": round(ap_.PATH, 4), "slope": [round(v, 4) for _, v in sorted(ap_.SLOPE)],
               "speed_kmh": 12.8, "injury_unit": "I and IP are expected injury cost per traversal, in thousandths of a euro", "vot_eur_h": round(ap_.VOT, 2), "cmf": ap_.CMF, "walk": {k: COST[k] for k in sorted(WALK)}},
    "nodes": node_ll.ravel().tolist(),
    "edges": [v for e in E_out for v in e],
    "geom": GEO,
    "names": [n for n, _ in sorted(names.items(), key=lambda kv: kv[1])],
}
path_out = os.path.join(SITE, "route-graph.json")
json.dump(out, open(path_out, "w"), separators=(",", ":"), ensure_ascii=False)
print(path_out, round(os.path.getsize(path_out) / 1e6, 2), "MB;", len(nodes), "nodes,", len(E_out), "links", flush=True)
