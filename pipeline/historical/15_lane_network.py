"""Grow a protected bike-lane network (approach B), valuing each addition in euros per year: time and comfort riders
gain once every trip is re-routed, plus injuries avoided on the protected streets, against the yearly cost of
building it. Parameters and sources: appraisal.py. Method: docs/METHOD_LANES.md.

Usage: python3 pipeline/historical/15_lane_network.py <Madrid.osm.pbf> <trips_dir_2023> <IMD_2019.shp> <data_dir>
                                                      [--budget-m 20] [--workers 4] [--pool 150]
Needs 14_lane_priority.py first (street segments with accidents and existing lanes in .cache/edges.pkl) and the
Copernicus DEM tile in .cache/copernicus_dem_N40_W004.tif.
Writes <data_dir>/lane_network_plan.csv (the better of two plans), lane_network_plan_bestfirst.csv,
lane_network_plan_axisfirst.csv and lane_network_plans.json (the comparison).

Model:
  - Candidates are streets, not carriageways: all road segments with the same name within 60 m of each other
    (both sides of a boulevard and its side roads) form one street, cut into pieces of about 1 km. A protected
    piece is usable in both directions and costs its street length once. Candidates are single pieces, whole
    streets, and a few multi-street axes (Atocha-Castellana, Bailen-Princesa, the southern Rondas).
  - Riders take the route with the least perceived distance [B12]; every trip is re-routed for every option.
  - Comfort: perceived km saved x value of time [H06], scaled to all cyclists with the city's bike counters.
  - Safety, protection only: riders on newly protected streets have their injury rate cut to 0.72 [L11]; the
    rate is an empirical-Bayes estimate per segment. Changes in risk from riders changing route are not counted.
  - Cost: [PD] for streets, [CAS] for avenues, annualised at 3% over 25 years [EC14].
  - Two plans: best-first greedy by benefit-cost ratio (lazy re-evaluation; options touching the last addition
    are re-valued at once), and the same greedy starting from the Atocha-Castellana axis. Each stops at the
    budget or when no addition returns more than it costs; the plan with the larger net benefit is the headline.
"""
import os, json, argparse, heapq, pickle, time, numpy as np, pandas as pd
from multiprocessing import Pool
from scipy.spatial import cKDTree
from shapely.geometry import LineString
from shapely.ops import unary_union
import bikegraph as bg
import appraisal as ap_
from bike_costs import COST

ap = argparse.ArgumentParser()
ap.add_argument("pbf"); ap.add_argument("trips"); ap.add_argument("imd"); ap.add_argument("data")
ap.add_argument("--budget-m", type=float, default=20, help="capital budget per plan, million euros")
ap.add_argument("--workers", type=int, default=4); ap.add_argument("--pool", type=int, default=150)
A = ap.parse_args()
ROOT = os.path.dirname(os.path.abspath(A.data)); CACHE = os.path.join(ROOT, ".cache")
t0 = time.time()
log = lambda *a: print(f"[{time.time() - t0:6.0f}s]", *a, flush=True)
YEAR = 365 / bg.DAYS  # the 2023 sample covers 49 days
annual = lambda eur: eur * ap_.ANNUITY

# ---------- graph, traffic, demand ----------
g = bg.Graph(A.pbf, dem=os.path.join(CACHE, "copernicus_dem_N40_W004.tif"), contraflow=True)
aadt, measured, *_ = bg.segment_aadt(g, A.imd)
odc = os.path.join(CACHE, "od2023.pkl")
if os.path.exists(odc): o, d, tr = pickle.load(open(odc, "rb"))
else: o, d, tr = bg.load_od(g, A.trips); pickle.dump((o, d, tr), open(odc, "wb"))
log("graph", g.n, "nodes,", g.nseg, "segments,", int(measured.sum()), "with measured traffic;", int(tr.sum()), "trips")

E = pd.read_pickle(os.path.join(CACHE, "edges.pkl"))
E["seg"] = [g.seg_id.get((a, b) if a < b else (b, a), -1) for a, b in zip(E.a, E.b)]
E = E[E.seg >= 0]
sep0 = g.seg_sep.copy(); sep0[E.seg[E.protected].values] = True
nacc = np.zeros(g.nseg); nacc[E.seg.values] = E.acc.values
accw = np.zeros(g.nseg); accw[E.seg.values] = E.acc_w.values
sbkm = np.zeros(g.nseg); sbkm[E.seg.values] = E.sbkm.values
acc = pd.read_csv(os.path.join(A.data, "madrid_bike_accidents.csv"))
years = (pd.Timestamp(acc.year.max(), 8, 31) - pd.Timestamp(acc.year.min(), 1, 1)).days / 365.25
cost_per_acc = (acc.n_slight * ap_.COST_SLIGHT + acc.n_serious * ap_.COST_SERIOUS + acc.n_killed * ap_.COST_DEATH).sum() / len(acc)
log(f"injury cost per recorded bike accident {cost_per_acc:,.0f} EUR; {len(acc) / years:.0f} accidents a year")

# ---------- perceived distance [B12] ----------
WALK = {"footway", "pedestrian", "path", "track", "steps"}
hw_arc = g.seg_hw[g.seg]
walk = np.array([h in WALK for h in hw_arc])
base_walk = np.array([COST[h] if h in WALK else 0 for h in hw_arc])
slope_pen = np.zeros(len(g.u))
for lo, v in sorted(ap_.SLOPE): slope_pen[g.upslope >= lo] = v
traffic_pen = np.zeros(len(g.u))
for lo, v in sorted(ap_.TRAFFIC): traffic_pen[aadt[g.seg] >= lo] = v

def factors(sep_seg):
    """Perceived-distance multiplier per arc given which segments are separated; contraflow only where protected."""
    s = sep_seg[g.seg]; lane = g.seg_lane[g.seg]
    f = 1 + np.where(s, ap_.PATH, np.where(lane, 0.0, traffic_pen)) + slope_pen
    f = np.where(walk & ~s, base_walk + slope_pen, f)
    return np.where(g.rev & ~s, np.inf, f)

def run(sep_seg):
    flow, lost, _, gc = bg.assign(g, factors(sep_seg), o, d, tr, cost=True)
    return gc / 1000 / bg.DAYS, flow

GC0, flow0 = run(sep0)

# riding speed: median straight-line speed x routed / straight-line length
flow_len = bg.assign(g, np.where(g.rev, np.inf, 1.0), o, d, tr)[0]
crow = np.hypot(g.x[o] - g.x[d], g.y[o] - g.y[d])
SPEED = ap_.SPEED_STRAIGHT_KMH * (flow_len * g.seg_len).sum() / (crow * tr).sum()
# all cyclists / BiciMAD from the city's counters (2023 average daily bikes) [MAD]
cnt = pd.read_csv(os.path.join(A.data, "madrid_bike_counters.csv")).dropna(subset=["lat", "lon", "avg_daily_bikes_2023"])
cx, cy = bg.fw.transform(cnt.lon.values, cnt.lat.values)
first = np.full(g.nseg, -1); first[g.seg[::-1]] = np.arange(len(g.seg))[::-1]
smx = (g.x[g.u[first]] + g.x[g.v[first]]) / 2; smy = (g.y[g.u[first]] + g.y[g.v[first]]) / 2
smlat = (g.lat[g.u[first]] + g.lat[g.v[first]]) / 2
ratios = [cnt.avg_daily_bikes_2023.iat[i] / (flow0[idx].max() / bg.DAYS)
          for i, idx in enumerate(cKDTree(np.c_[smx, smy]).query_ball_point(np.c_[cx, cy], r=40)) if idx and flow0[idx].max() / bg.DAYS >= 5]
SCALE = float(np.median(ratios))
log(f"riding speed {SPEED:.1f} km/h; all cyclists / BiciMAD at {len(ratios)} counters: median {SCALE:.1f}")

# ---------- injury rates per BiciMAD-km, empirical Bayes by road class [Hauer] ----------
expo = flow0 * g.seg_len / 1000 * YEAR
cls = np.array([f"{h}|{int(s)}" for h, s in zip(g.seg_hw, sep0)])
overall = nacc.sum() / years / expo.sum()
rate = np.full(g.nseg, overall)
for c in np.unique(cls):
    m = (cls == c) & (expo > 0)
    if m.sum() < 20: continue
    R = nacc[m].sum() / years / expo[m].sum(); rate[cls == c] = R
    if R == 0: continue
    mu = R * expo[m]; N = nacc[m] / years
    theta = np.mean(mu) ** 2 / max(np.var(N) - np.mean(N), 1e-12)
    w = 1 / (1 + mu / theta)
    rate[np.where(m)[0]] = (w * mu + (1 - w) * N) / expo[m]

def value(segs):
    """Yearly benefit (EUR) of protecting `segs` on top of today's network."""
    s = sep0.copy(); s[segs] = True
    gc, flow = run(s)
    comfort = (GC0 - gc) * 365 * SCALE / SPEED * ap_.VOT
    new = np.unique(segs); new = new[~sep0[new]]
    safety = (flow[new] * g.seg_len[new] / 1000 * YEAR * rate[new]).sum() * (1 - ap_.CMF) * cost_per_acc
    return comfort, safety, flow

# ---------- street pieces: same name, carriageways within 60 m merged, cut into ~1 km ----------
ROAD = {"trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link",
        "residential", "unclassified", "living_street", "busway"}
isroad = np.array([h in ROAD for h in g.seg_hw]) & (g.seg_name != "")
parent = np.arange(g.nseg)
def find(x):
    while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
    return x
for name in np.unique(g.seg_name[isroad]):
    ids = np.where(isroad & (g.seg_name == name))[0]
    if len(ids) < 2: continue
    for a, b in cKDTree(np.c_[smx[ids], smy[ids]]).query_pairs(60):
        ra, rb = find(ids[a]), find(ids[b])
        if ra != rb: parent[ra] = rb
comp = np.array([find(i) for i in range(g.nseg)])
pieces = []  # dicts: name, segs, km, avenue, comp
for cid in np.unique(comp[isroad]):
    ids = np.where(isroad & (comp == cid))[0]
    P = np.c_[smx[ids], smy[ids]]; c0 = P.mean(0)
    ax = np.linalg.svd(P - c0, full_matrices=False)[2][0] if len(ids) > 2 else np.array([1.0, 0.0])
    s = (P - c0) @ ax; span = max(s.max() - s.min(), 1.0)
    k = max(1, round(span / 1000)); cut = np.minimum(((s - s.min()) / span * k).astype(int), k - 1)
    for j in range(k):
        segs = ids[cut == j]
        if not len(segs): continue
        Lall = g.seg_len[segs].sum(); Lprot = g.seg_len[segs][sep0[segs]].sum()
        if Lprot > 0.8 * Lall: continue  # already protected
        ss = s[cut == j]; km = max(ss.max() - ss.min(), g.seg_len[segs].max()) / 1000
        avenue = bool(np.isin(g.seg_hw[segs], ["trunk", "primary", "secondary"]).any())
        pieces.append({"name": g.seg_name[segs[0]], "segs": segs, "km": max(km, 0.2), "avenue": avenue, "comp": cid,
                       "lat": float(smlat[segs].mean()), "sbkm": sbkm[segs].sum(), "accw": accw[segs].sum()})
Pc = pd.DataFrame(pieces)
Pc["build_eur"] = Pc.km * np.where(Pc.avenue, ap_.BUILD_AVENUE, ap_.BUILD_STREET)
tot_s, tot_a = Pc.sbkm.sum(), Pc.accw.sum()
Pc["score"] = 0.5 * Pc.sbkm / tot_s + 0.5 * Pc.accw / tot_a; Pc["score_km"] = Pc.score / Pc.km
log(f"{len(Pc)} street pieces ({Pc.km.sum():.0f} km of street)")

# ---------- candidates: pieces, whole streets, axes ----------
pool = set(Pc.nlargest(A.pool * 2 // 3, "score_km").index) | set(Pc.nlargest(A.pool // 3, "score").index) | set(Pc.nlargest(A.pool // 5, "accw").index)
cands = [{"label": Pc.name[i], "kind": "piece", "pieces": [i]} for i in sorted(pool)]
for cid in Pc.loc[sorted(pool), "comp"].unique():
    ps = Pc.index[Pc.comp == cid].tolist()
    if 2 <= len(ps) and Pc.km[ps].sum() <= 8:
        cands.append({"label": f"{Pc.name[ps[0]]} (whole street)", "kind": "street", "pieces": ps})
AXES = {
    "Atocha - Prado - Recoletos - Castellana": (["Plaza del Emperador Carlos V", "Paseo del Prado", "Plaza de Cibeles", "Plaza de la Cibeles",
                                                  "Paseo de Recoletos", "Plaza de Colón", "Paseo de la Castellana"], 40.405, 40.4485),
    "Bailén - Plaza de España - Princesa": (["Calle de Bailén", "Plaza de España", "Calle de la Princesa"], 40.410, 40.436),
    "Rondas sur (Segovia - Toledo - Valencia - Atocha)": (["Ronda de Segovia", "Ronda de Toledo", "Ronda de Valencia", "Ronda de Atocha", "Glorieta de Embajadores"], 40.39, 40.415),
}
for label, (names, la0, la1) in AXES.items():
    ps = Pc.index[Pc.name.isin(names) & Pc.lat.between(la0, la1)].tolist()
    if ps: cands.append({"label": label, "kind": "axis", "pieces": ps})
for c in cands:
    c["segs"] = np.unique(np.concatenate([Pc.segs[i] for i in c["pieces"]])).astype(np.int32)
    m = np.isin(g.seg, c["segs"]); c["nodes"] = set(np.r_[g.u[m], g.v[m]].tolist())
log(f"{len(cands)} candidates: {sum(c['kind'] == 'piece' for c in cands)} pieces, {sum(c['kind'] == 'street' for c in cands)} whole streets, "
    f"{sum(c['kind'] == 'axis' for c in cands)} axes")
AXIS0 = next(i for i, c in enumerate(cands) if c["kind"] == "axis" and c["label"].startswith("Atocha"))

def evaluate(args):
    i, base = args
    c, s, _ = value(np.unique(np.r_[base, cands[i]["segs"]]).astype(np.int32))
    return i, c, s

def grow(P, start, label, first_vals):
    """Lazy greedy by benefit-cost ratio of each addition (only pieces not yet built are paid for)."""
    built, base, B, spent, rows = set(), np.array([], np.int32), 0.0, 0.0, []
    def add(i, c, s, ratio, step):
        nonlocal base, B, spent
        newp = [p for p in cands[i]["pieces"] if p not in built]
        cost = Pc.build_eur[newp].sum(); gain = c + s - B
        built.update(newp); base = np.unique(np.r_[base, cands[i]["segs"]]).astype(np.int32); B = c + s; spent += cost
        rows.append({"step": step, "option": cands[i]["label"], "kind": cands[i]["kind"], "km_new": round(Pc.km[newp].sum(), 2),
                     "build_eur": round(cost), "benefit_eur_yr": round(gain), "bcr": round(ratio, 2), "cum_build_eur": round(spent),
                     "cum_comfort_eur_yr": round(c), "cum_safety_eur_yr": round(s), "cum_bcr": round(B / annual(spent), 2),
                     "pieces": newp})
        log(f"[{label}] step {step:>2}: {cands[i]['label']} (+{Pc.km[newp].sum():.2f} km, {cost / 1e6:.2f} M EUR) BCR {ratio:.2f} -> "
            f"{spent / 1e6:.1f} M EUR, comfort {c / 1e6:.2f} + safety {s / 1e6:.2f} M EUR/yr")
    newcost = lambda i: Pc.build_eur[[p for p in cands[i]["pieces"] if p not in built]].sum()
    step = 0
    if start is not None:
        _, c, s = evaluate((start, base)); step += 1
        add(start, c, s, (c + s) / annual(newcost(start)), step)
    heap = [(-((c + s - B) / annual(max(newcost(i), 1))), i, 0) for i, (c, s) in first_vals.items() if newcost(i) > 0]
    heapq.heapify(heap)
    while heap:
        step += 1
        while True:
            top = [heapq.heappop(heap) for _ in range(min(A.workers, len(heap)))]
            top = [t for t in top if newcost(t[1]) > 0]  # options already fully built drop out
            if not top:
                if not heap: break
                continue
            stale = [i for _, i, st in top if st != step]
            res = {i: (c, s) for i, c, s in P.imap_unordered(evaluate, [(i, base) for i in stale])}
            for negr, i, st in top:
                if i in res:
                    c, s = res[i]; cands[i]["_v"] = (c, s)
                    heapq.heappush(heap, (-((c + s - B) / annual(newcost(i))), i, step))
                else: heapq.heappush(heap, (negr, i, st))
            if heap[0][2] == step: break
        if not heap: break
        negr, i, _ = heapq.heappop(heap)
        if -negr < 1 or spent + newcost(i) > A.budget_m * 1e6: break
        c, s = cands[i]["_v"]; add(i, c, s, -negr, step)
        touch = [j for _, j, _ in heap if cands[j]["nodes"] & cands[i]["nodes"] and newcost(j) > 0]
        if touch:
            res = {j: (c_, s_) for j, c_, s_ in P.imap_unordered(evaluate, [(j, base) for j in touch])}
            heap = [(n, j, st) for n, j, st in heap if j not in res and newcost(j) > 0]
            for j, (c_, s_) in res.items():
                cands[j]["_v"] = (c_, s_); heap.append((-((c_ + s_ - B) / annual(newcost(j))), j, step + 1))
            heapq.heapify(heap)
    return rows, base, B, spent

with Pool(A.workers) as P:
    first_vals = {i: (c, s) for i, c, s in P.imap_unordered(evaluate, [(i, np.array([], np.int32)) for i in range(len(cands))])}
    log("first pass done")
    for i, (c, s) in sorted(first_vals.items(), key=lambda kv: -(sum(kv[1])) / annual(Pc.build_eur[cands[kv[0]]["pieces"]].sum()))[:12]:
        log(f"   alone: {cands[i]['label'][:50]:50s} {cands[i]['kind']:6s} BCR {(c + s) / annual(Pc.build_eur[cands[i]['pieces']].sum()):.2f}")
    plans = {}
    for label, start in [("bestfirst", None), ("axisfirst", AXIS0)]:
        rows, base, B, spent = grow(P, start, label, dict(first_vals))
        plans[label] = (rows, base, B, spent)

def geom(segs):
    m_ = np.isin(g.seg, segs) & ~g.rev
    ln = unary_union([LineString([(g.x[a], g.y[a]), (g.x[b], g.y[b])]) for a, b in zip(g.u[m_], g.v[m_])]).simplify(4)
    out = []
    for l_ in getattr(ln, "geoms", [ln]):
        lo, la = bg.bw.transform(*l_.xy); out.append(" ".join(f"{x:.5f},{y:.5f}" for x, y in zip(lo, la)))
    return "|".join(out)

summary = {}
for label, (rows, base, B, spent) in plans.items():
    _, _, flow = value(base)
    df = pd.DataFrame(rows)
    def trips(ps, F):
        ss = np.concatenate([Pc.segs[p] for p in ps]); return round((F[ss] * g.seg_len[ss]).sum() / max(g.seg_len[ss].sum(), 1) / bg.DAYS * SCALE)
    df["trips_day_before"] = [trips(ps, flow0) for ps in df.pieces]
    df["trips_day_after"] = [trips(ps, flow) for ps in df.pieces]
    df["geometry"] = [geom(np.concatenate([Pc.segs[p] for p in ps])) for ps in df.pieces]
    df.drop(columns="pieces").to_csv(os.path.join(A.data, f"lane_network_plan_{label}.csv"), index=False)
    km = df.km_new.sum()
    summary[label] = {"options": len(df), "km": round(km, 1), "build_eur": round(spent), "benefit_eur_yr": round(B),
                      "annual_cost_eur_yr": round(annual(spent)), "net_benefit_eur_yr": round(B - annual(spent)), "bcr": round(B / annual(spent), 2)}
    log(f"[{label}] {len(df)} additions, {km:.1f} km, {spent / 1e6:.1f} M EUR -> {B / 1e6:.2f} M EUR/yr vs {annual(spent) / 1e6:.2f} (BCR {B / annual(spent):.2f})")
best = max(summary, key=lambda k: summary[k]["net_benefit_eur_yr"])
summary["headline"] = best
json.dump(summary, open(os.path.join(A.data, "lane_network_plans.json"), "w"), indent=1)
pd.read_csv(os.path.join(A.data, f"lane_network_plan_{best}.csv")).to_csv(os.path.join(A.data, "lane_network_plan.csv"), index=False)
print(json.dumps(summary, indent=1))
