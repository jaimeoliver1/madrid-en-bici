"""Grow a protected bike-lane network step by step (approach B), valuing each corridor in euros per year:
time and comfort riders gain once every trip is re-routed, plus injury costs avoided, against the yearly cost of
building it. All parameters and their sources are in appraisal.py; the method is written up in docs/METHOD_LANES.md.

Usage: python3 pipeline/historical/15_lane_network.py <Madrid.osm.pbf> <trips_dir_2023> <IMD_2019.shp> <data_dir>
                                                      [--budget-m 30] [--workers 4] [--pool 150]
Needs 14_lane_priority.py first (street segments with accidents and existing lanes, and the corridor pieces, in .cache/)
and the Copernicus DEM tile in .cache/copernicus_dem_N40_W004.tif.
Writes <data_dir>/lane_network_plan.csv: corridors in build order with their euros and cumulative effects.

Model, in short:
  - Riders take the route with the least perceived distance (Broach et al. 2012, non-commute values): extra
    perceived km for motor traffic without a bike lane (by AADT, from the city's 2019 counts), for uphill links
    (by average upslope, Copernicus DEM), and a bonus for separated paths. Footways, steps and tracks keep the
    weights of bike_costs.py.
  - A new protected corridor turns its segments into separated paths; every trip is re-routed (all-or-nothing).
  - Comfort: the drop in perceived km over all trips, at the riding speed, times the value of time (HEATCO).
    BiciMAD trips are scaled to all cyclists with the city's 2023 bike counters.
  - Safety: expected injury cost on every segment = exposure x empirical-Bayes injury rate for its road class
    (2019-2026 police records, valued with HEATCO's Spanish costs per death, serious and slight injury); a newly
    protected segment's rate is multiplied by 0.72 (Lusk et al. 2011).
  - Cost: build cost per km (Plan Director for streets, the Castellana contract for avenues), annualised at 3%
    over 25 years (European Commission 2014).
  - Greedy by benefit-cost ratio of each addition, with lazy re-evaluation; pieces touching the corridor just
    added are re-evaluated straight away. Stops at the budget or when no addition returns more than it costs.
"""
import os, argparse, heapq, pickle, time, numpy as np, pandas as pd
from multiprocessing import Pool
from shapely.geometry import LineString
from shapely.ops import unary_union
import bikegraph as bg
import appraisal as ap_
from bike_costs import COST

ap = argparse.ArgumentParser()
ap.add_argument("pbf"); ap.add_argument("trips"); ap.add_argument("imd"); ap.add_argument("data")
ap.add_argument("--budget-m", type=float, default=30, help="capital budget, million euros")
ap.add_argument("--workers", type=int, default=4); ap.add_argument("--pool", type=int, default=150)
A = ap.parse_args()
ROOT = os.path.dirname(os.path.abspath(A.data)); CACHE = os.path.join(ROOT, ".cache")
t0 = time.time()
log = lambda *a: print(f"[{time.time() - t0:6.0f}s]", *a, flush=True)
YEAR = 365 / bg.DAYS  # the 2023 sample covers 49 days

# ---------- graph, traffic, demand ----------
g = bg.Graph(A.pbf, dem=os.path.join(CACHE, "copernicus_dem_N40_W004.tif"))
aadt, measured, *_ = bg.segment_aadt(g, A.imd)
odc = os.path.join(CACHE, "od2023.pkl")
if os.path.exists(odc): o, d, tr = pickle.load(open(odc, "rb"))
else: o, d, tr = bg.load_od(g, A.trips); pickle.dump((o, d, tr), open(odc, "wb"))
log("graph", g.n, "nodes,", g.nseg, "segments,", int(measured.sum()), "with measured traffic;", int(tr.sum()), "trips")

# existing separated lanes: OSM (cycleway, track) or the city's exclusive-lane layer (via 14_lane_priority.py)
E = pd.read_pickle(os.path.join(CACHE, "edges.pkl"))
E["seg"] = [g.seg_id.get((a, b) if a < b else (b, a), -1) for a, b in zip(E.a, E.b)]
E = E[E.seg >= 0]
sep0 = g.seg_sep.copy(); sep0[E.seg[E.protected].values] = True
acc = pd.read_csv(os.path.join(A.data, "madrid_bike_accidents.csv"))
years = (pd.Timestamp(acc.year.max(), 8, 31) - pd.Timestamp(acc.year.min(), 1, 1)).days / 365.25
cost_per_acc = (acc.n_slight * ap_.COST_SLIGHT + acc.n_serious * ap_.COST_SERIOUS + acc.n_killed * ap_.COST_DEATH).sum() / len(acc)
nacc = np.zeros(g.nseg); nacc[E.seg.values] = E.acc.values  # accidents snapped to each segment, 2019-2026
log(f"injury cost per recorded bike accident {cost_per_acc:,.0f} EUR; {len(acc) / years:.0f} accidents a year")

WALK = {"footway", "pedestrian", "path", "track", "steps"}
hw_arc = g.seg_hw[g.seg]
walk = np.array([h in WALK for h in hw_arc])
base_walk = np.array([COST[h] if h in WALK else 0 for h in hw_arc])
slope_pen = np.zeros(len(g.u))
for lo, v in sorted(ap_.SLOPE):
    slope_pen[g.upslope >= lo] = v
traffic_pen = np.zeros(len(g.u))
for lo, v in sorted(ap_.TRAFFIC):
    traffic_pen[aadt[g.seg] >= lo] = v

def factors(sep_seg):
    """Perceived-distance multiplier per arc [B12] given which segments are separated."""
    s = sep_seg[g.seg]; lane = g.seg_lane[g.seg]
    f = 1 + np.where(s, ap_.PATH, np.where(lane, 0.0, traffic_pen)) + slope_pen
    return np.where(walk & ~s, base_walk + slope_pen, f)

def run(sep_seg):
    """Re-route all trips; return (perceived km per day, flow per segment)."""
    flow, lost, _, gc = bg.assign(g, factors(sep_seg), o, d, tr, cost=True)
    return gc / 1000 / bg.DAYS, flow

GC0, flow0 = run(sep0)
crow = np.hypot(g.x[o] - g.x[d], g.y[o] - g.y[d])  # straight-line length of each station pair, m
# scale BiciMAD to all cyclists with the city's counters (2023 average daily bikes) [MAD]
cnt = pd.read_csv(os.path.join(A.data, "madrid_bike_counters.csv")).dropna(subset=["lat", "lon", "avg_daily_bikes_2023"])
cx, cy = bg.fw.transform(cnt.lon.values, cnt.lat.values)
first = np.full(g.nseg, -1); first[g.seg[::-1]] = np.arange(len(g.seg))[::-1]
mxs = (g.x[g.u[first]] + g.x[g.v[first]]) / 2; mys = (g.y[g.u[first]] + g.y[g.v[first]]) / 2
from scipy.spatial import cKDTree
kd = cKDTree(np.c_[mxs, mys]); near = kd.query_ball_point(np.c_[cx, cy], r=40)
ratios = []
for i, idx in enumerate(near):
    if not idx: continue
    model = flow0[idx].max() / bg.DAYS
    if model >= 5: ratios.append(cnt.avg_daily_bikes_2023.iat[i] / model)
SCALE = float(np.median(ratios)) if ratios else 1.0
log(f"all cyclists / BiciMAD at {len(ratios)} counters: median {SCALE:.1f} (range {np.min(ratios):.1f}-{np.max(ratios):.1f})")

# ---------- injury rates per BiciMAD-km, empirical Bayes by road class [Hauer] ----------
expo = flow0 * g.seg_len / 1000 * YEAR          # BiciMAD km per year on each segment
cls = np.array([f"{h}|{int(s)}" for h, s in zip(g.seg_hw, sep0)])
overall = nacc.sum() / years / expo.sum()
rate = np.full(g.nseg, overall)                 # classes with too little exposure keep the city-wide rate
for c in np.unique(cls):
    m = (cls == c) & (expo > 0)
    if m.sum() < 20: continue
    R = nacc[m].sum() / years / expo[m].sum()   # class rate: accidents per BiciMAD-km
    rate[cls == c] = R
    if R == 0: continue
    mu = R * expo[m]; N = nacc[m] / years
    var_excess = max(np.var(N) - np.mean(N), 1e-12); theta = np.mean(mu) ** 2 / var_excess  # NB dispersion, method of moments
    w = 1 / (1 + mu / theta)                    # weight on the class prediction [Hauer]
    rate[np.where(m)[0]] = (w * mu + (1 - w) * N) / expo[m]

def injury_cost(flow, sep_new):
    """Expected injury cost per year (EUR) for a flow pattern; newly separated segments get the CMF [L11]."""
    e = flow * g.seg_len / 1000 * YEAR
    r = np.where(sep_new & ~sep0, rate * ap_.CMF, rate)
    return (e * r).sum() * cost_per_acc

IC0 = injury_cost(flow0, sep0)
log(f"baseline: {GC0:,.0f} perceived km/day; expected injury cost {IC0 / 1e6:.1f} M EUR/yr (recorded {len(acc) / years * cost_per_acc / 1e6:.1f})")

# ---------- candidates (from 14_lane_priority.py) ----------
C = pd.read_pickle(os.path.join(CACHE, "corridors.pkl")).reset_index(drop=True)
pool = set(C.nlargest(A.pool * 2 // 3, "score_km").index) | set(C.nlargest(A.pool // 3, "score").index) | set(C.nlargest(A.pool // 5, "acc_w").index)
C = C.loc[sorted(pool)].reset_index(drop=True)
C["segs"] = [np.array([g.seg_id[k] for k in ks if k in g.seg_id], np.int32) for ks in C["keys"]]
C["nodes"] = [set(np.r_[g.u[np.isin(g.seg, s)], g.v[np.isin(g.seg, s)]].tolist()) for s in C.segs]
C["build_eur"] = [km * ap_.build_cost_km(h) for km, h in zip(C.km, C.hw)]
log("candidates", len(C), "covering", round(C.km.sum(), 1), "km,", round(C.build_eur.sum() / 1e6, 1), "M EUR to build")

def value(segs):
    """Yearly benefit (EUR) of separating `segs` on top of today's network: comfort + injuries avoided."""
    s = sep0.copy(); s[segs] = True
    gc, flow = run(s)
    VOT = ap_.VOT
    comfort = (GC0 - gc) * 365 * SCALE / SPEED * VOT  # perceived km per day -> hours per year -> EUR
    safety = IC0 - injury_cost(flow, s)
    return comfort, safety, flow

def evaluate(args):
    i, base = args
    segs = np.unique(np.r_[base, C.segs[i]]).astype(np.int32)
    c, s, _ = value(segs)
    return i, c, s

# riding speed from routed distances (needs one pass with plain lengths)
flow_len = bg.assign(g, np.ones(len(g.u)), o, d, tr)[0]
route_km = (flow_len * g.seg_len).sum() / 1000; crow_km = (crow * tr).sum() / 1000
SPEED = ap_.SPEED_STRAIGHT_KMH * route_km / crow_km
log(f"riding speed {SPEED:.1f} km/h (straight-line {ap_.SPEED_STRAIGHT_KMH} x route/straight {route_km / crow_km:.2f})")

annual = lambda eur: eur * ap_.ANNUITY
chosen, base, B_now, spent, rows = [], np.array([], np.int32), 0.0, 0.0, []
with Pool(A.workers) as P:
    heap = []
    for i, c, s in P.imap_unordered(evaluate, [(i, base) for i in C.index]):
        heapq.heappush(heap, (-((c + s) / annual(C.build_eur[i])), i, 0)); C.loc[i, "_c"] = c; C.loc[i, "_s"] = s
    log("first pass done")
    step = 0
    while heap:
        step += 1
        while True:
            top = [heapq.heappop(heap) for _ in range(min(A.workers, len(heap)))]
            stale = [i for _, i, st in top if st != step]
            res = {i: (c, s) for i, c, s in P.imap_unordered(evaluate, [(i, base) for i in stale])}
            for negr, i, st in top:
                if i in res:
                    c, s = res[i]; C.loc[i, "_c"] = c; C.loc[i, "_s"] = s
                    heapq.heappush(heap, (-((c + s - B_now) / annual(C.build_eur[i])), i, step))
                else: heapq.heappush(heap, (negr, i, st))
            if heap[0][2] == step: break
        negr, i, _ = heapq.heappop(heap)
        if -negr < 1 or spent + C.build_eur[i] > A.budget_m * 1e6: break
        base = np.unique(np.r_[base, C.segs[i]]).astype(np.int32); chosen.append(i)
        spent += C.build_eur[i]; c, s = C._c[i], C._s[i]; gain = c + s - B_now; B_now = c + s
        rows.append({"step": step, "street": C.name[i], "road_class": C.hw[i], "km": round(C.km[i], 2),
                     "build_eur": round(C.build_eur[i]), "benefit_eur_yr": round(gain), "bcr": round(-negr, 2),
                     "cum_build_eur": round(spent), "cum_comfort_eur_yr": round(c), "cum_safety_eur_yr": round(s),
                     "cum_bcr": round((c + s) / annual(spent), 2)})
        log(f"step {step:>2}: {C.name[i]} ({C.km[i]:.2f} km, {C.build_eur[i] / 1e6:.2f} M EUR) BCR {-negr:.1f} -> "
            f"{spent / 1e6:.1f} M EUR, comfort {c / 1e6:.2f} + safety {s / 1e6:.2f} M EUR/yr")
        touch = [j for _, j, _ in heap if C.nodes[j] & C.nodes[i]]
        if touch:
            res = {j: (c_, s_) for j, c_, s_ in P.imap_unordered(evaluate, [(j, base) for j in touch])}
            heap = [(n, j, st) for n, j, st in heap if j not in res]
            for j, (c_, s_) in res.items():
                C.loc[j, "_c"] = c_; C.loc[j, "_s"] = s_
                heap.append((-((c_ + s_ - B_now) / annual(C.build_eur[j])), j, step + 1))
            heapq.heapify(heap)

c, s, flow = value(base)
out = pd.DataFrame(rows)
seglen = lambda ss: max(g.seg_len[ss].sum(), 1)
out["trips_day_before"] = [round((flow0[C.segs[i]] * g.seg_len[C.segs[i]]).sum() / seglen(C.segs[i]) / bg.DAYS * SCALE) for i in chosen]
out["trips_day_after"] = [round((flow[C.segs[i]] * g.seg_len[C.segs[i]]).sum() / seglen(C.segs[i]) / bg.DAYS * SCALE) for i in chosen]
def geom(segs):
    m_ = np.isin(g.seg, segs)
    ln = unary_union([LineString([(g.x[a], g.y[a]), (g.x[b], g.y[b])]) for a, b in zip(g.u[m_], g.v[m_])]).simplify(4)
    parts = []
    for l_ in getattr(ln, "geoms", [ln]):
        lo, la = bg.bw.transform(*l_.xy); parts.append(" ".join(f"{x:.5f},{y:.5f}" for x, y in zip(lo, la)))
    return "|".join(parts)
out["geometry"] = [geom(C.segs[i]) for i in chosen]
out.to_csv(os.path.join(A.data, "lane_network_plan.csv"), index=False)
km = C.km[chosen].sum()
log(f"plan: {len(chosen)} corridors, {km:.1f} km, {spent / 1e6:.1f} M EUR -> comfort {c / 1e6:.2f} + safety {s / 1e6:.2f} "
    f"= {(c + s) / 1e6:.2f} M EUR/yr against {annual(spent) / 1e6:.2f} M EUR/yr of build cost (BCR {(c + s) / annual(spent):.1f})")
print(out.drop(columns="geometry").to_string(index=False))
