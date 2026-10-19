"""Grow a protected bike-lane network step by step (approach B): at each step add the corridor that most
reduces stressful riding once every trip is re-routed, plus the accidents it covers, per km built.

Usage: python3 pipeline/historical/15_lane_network.py <Madrid.osm.pbf> <trips_dir_2023> <data_dir> [--budget 50] [--w-bikes 0.5] [--workers 4]
Needs 14_lane_priority.py to have run first (it leaves the street segments and corridors in .cache/).
Writes <data_dir>/lane_network_plan.csv: the corridors in build order with cumulative effects and geometry.

Method:
  - Routing: all-or-nothing on the OSM bike graph (bike_costs.py) with scipy's Dijkstra; a protected corridor
    gets the weight of a cycleway (0.6), so riders detour onto it when it pays.
  - Stress exposure X = bike-km per day on unprotected segments x their traffic stress (from 14_lane_priority.py).
  - Gain of a network S = w * (X0 - X(S)) / X0 + (1 - w) * (weighted accidents on S's new lanes) / (all weighted accidents).
  - Greedy by gain per km, with lazy re-evaluation (CELF): a candidate's last gain is an upper bound unless it
    touches the corridor just added (connections can make a piece worth more), so those are always re-evaluated.
  - Calm trips: trips whose whole route avoids unprotected segments of stress >= 0.5.
"""
import os, sys, argparse, heapq, pickle, time, numpy as np, pandas as pd
from multiprocessing import Pool
from shapely.geometry import LineString
from shapely.ops import unary_union
import bikegraph as bg
from bike_costs import COST

ap = argparse.ArgumentParser()
ap.add_argument("pbf"); ap.add_argument("trips"); ap.add_argument("data")
ap.add_argument("--budget", type=float, default=50); ap.add_argument("--w-bikes", type=float, default=0.5)
ap.add_argument("--workers", type=int, default=4); ap.add_argument("--pool", type=int, default=150)
A = ap.parse_args()
CACHE = os.path.join(os.path.dirname(os.path.abspath(A.data)), ".cache")
t0 = time.time()
log = lambda *a: print(f"[{time.time() - t0:6.0f}s]", *a, flush=True)

g = bg.Graph(A.pbf)
odc = os.path.join(CACHE, "od2023.pkl")
if os.path.exists(odc): o, d, tr = pickle.load(open(odc, "rb"))
else: o, d, tr = bg.load_od(g, A.trips); pickle.dump((o, d, tr), open(odc, "wb"))
log("graph", g.n, "nodes,", g.nseg, "segments;", len(o), "station pairs,", int(tr.sum()), "trips")

# per-segment stress, existing protection and accidents, from 14_lane_priority.py
E = pd.read_pickle(os.path.join(CACHE, "edges.pkl"))
E["seg"] = [g.seg_id.get((a, b) if a < b else (b, a), -1) for a, b in zip(E.a, E.b)]
E = E[E.seg >= 0]
LINK = {"trunk_link": 1.0, "primary_link": 1.0, "secondary_link": 0.85, "tertiary_link": 0.5, "busway": 0.5, "service": 0.2, "living_street": 0.1}
stress = np.zeros(g.nseg); prot = np.zeros(g.nseg, bool); accw = np.zeros(g.nseg)
stress[E.seg] = E.stress.fillna(E.hw.map(LINK)).fillna(0).values
prot[E.seg] = E.protected.values; accw[E.seg] = E.acc_w.values
acc_tot = accw.sum()

# candidate corridors: the most promising pieces of 14's ranking, by score per km, total score and accidents
C = pd.read_pickle(os.path.join(CACHE, "corridors.pkl")).reset_index(drop=True)
pool = set(C.nlargest(A.pool * 2 // 3, "score_km").index) | set(C.nlargest(A.pool // 3, "score").index) | set(C.nlargest(A.pool // 5, "acc_w").index)
C = C.loc[sorted(pool)].reset_index(drop=True)
C["segs"] = [np.array([g.seg_id[k] for k in ks if k in g.seg_id], np.int32) for ks in C["keys"]]
C["nodes"] = [set(np.r_[g.u[np.isin(g.seg, s)], g.v[np.isin(g.seg, s)]].tolist()) for s in C.segs]
log("candidates", len(C), "covering", round(C.km.sum(), 1), "km")

arc_of = lambda segs: np.isin(g.seg, segs)
BAD = lambda p: (stress >= 0.5) & ~p

def state(segs):
    """Re-route everything with `segs` protected; return (stress exposure, calm trips, flow)."""
    f = g.f.copy(); p = prot.copy()
    if len(segs):
        m = arc_of(segs); f[m] = np.minimum(f[m], COST["cycleway"]); p[segs] = True
    flow, lost, calm = bg.assign(g, f, o, d, tr, bad=BAD(p))
    X = (flow * g.seg_len * stress * ~p).sum() / 1000 / bg.DAYS
    return X, calm, flow

def acc_new(segs):
    s = np.unique(segs); return accw[s[~prot[s]]].sum()

X0, calm0, flow0 = state(np.array([], np.int32))
log(f"today: stress exposure {X0:.0f} weighted bike-km/day, calm trips {calm0 / tr.sum() * 100:.1f}%")
w = A.w_bikes
def gain(X, segs): return w * (X0 - X) / X0 + (1 - w) * acc_new(segs) / acc_tot

def evaluate(args):
    i, base = args
    segs = np.unique(np.r_[base, C.segs[i]]).astype(np.int32)
    X, calm, _ = state(segs)
    return i, X, calm

chosen, base, J = [], np.array([], np.int32), 0.0
with Pool(A.workers) as P:
    heap = []
    for i, X, calm in P.imap_unordered(evaluate, [(i, base) for i in C.index]):
        heapq.heappush(heap, (-(gain(X, np.r_[base, C.segs[i]]) - J) / C.km[i], i, 0))
    log("first pass done")
    km, step, rows = 0.0, 0, []
    while heap and km < A.budget:
        step += 1
        # lazy greedy: re-evaluate the top few against the current network until the best one is fresh
        while True:
            top = [heapq.heappop(heap) for _ in range(min(A.workers, len(heap)))]
            stale = [i for _, i, s in top if s != step]
            res = {}
            for i, X, calm in P.imap_unordered(evaluate, [(i, base) for i in stale]): res[i] = (X, calm)
            for negr, i, s in top:
                if i in res:
                    X, calm = res[i]; r = (gain(X, np.r_[base, C.segs[i]]) - J) / C.km[i]
                    heapq.heappush(heap, (-r, i, step)); C.loc[i, "_X"] = X; C.loc[i, "_calm"] = calm
                else: heapq.heappush(heap, (negr, i, s))
            if heap[0][2] == step: break
        negr, i, _ = heapq.heappop(heap)
        if -negr <= 0: break
        base = np.unique(np.r_[base, C.segs[i]]).astype(np.int32)
        X, calm = C._X[i], C._calm[i]; J = gain(X, base); km += C.km[i]; chosen.append(i)
        rows.append({"step": step, "street": C.name[i], "road_class": C.hw[i], "km": round(C.km[i], 2), "cum_km": round(km, 1),
                     "gain_per_km": round(-negr * 1000, 3), "stress_exposure_cut_pct": round((X0 - X) / X0 * 100, 1),
                     "acc_covered_pct": round(acc_new(base) / acc_tot * 100, 1), "calm_trips_pct": round(calm / tr.sum() * 100, 1)})
        log(f"step {step:>2}: {C.name[i]} ({C.km[i]:.2f} km) -> {km:.1f} km, exposure -{rows[-1]['stress_exposure_cut_pct']}%, "
            f"accidents {rows[-1]['acc_covered_pct']}%, calm trips {rows[-1]['calm_trips_pct']}%")
        # pieces that touch the new corridor may be worth more now (connections): re-evaluate them right away
        touch = [j for _, j, _ in heap if C.nodes[j] & C.nodes[i]]
        if touch:
            res = {j: (X_, c_) for j, X_, c_ in P.imap_unordered(evaluate, [(j, base) for j in touch])}
            heap = [(n, j, s) for n, j, s in heap if j not in res]
            for j, (X_, c_) in res.items():
                heap.append((-(gain(X_, np.r_[base, C.segs[j]]) - J) / C.km[j], j, step + 1)); C.loc[j, "_X"] = X_; C.loc[j, "_calm"] = c_
            heapq.heapify(heap)

# final state for flows on each chosen corridor
X, calm, flow = state(base)
out = pd.DataFrame(rows)
out["trips_day_after"] = [round((flow[C.segs[i]] * g.seg_len[C.segs[i]]).sum() / max(g.seg_len[C.segs[i]].sum(), 1) / bg.DAYS) for i in chosen]
out["trips_day_before"] = [round((flow0[C.segs[i]] * g.seg_len[C.segs[i]]).sum() / max(g.seg_len[C.segs[i]].sum(), 1) / bg.DAYS) for i in chosen]
def geom(segs):
    ia = g.u[np.isin(g.seg, segs)]; ib = g.v[np.isin(g.seg, segs)]
    m = unary_union([LineString([(g.x[a], g.y[a]), (g.x[b], g.y[b])]) for a, b in zip(ia, ib)]).simplify(4)
    parts = []
    for ln in getattr(m, "geoms", [m]):
        lo, la = bg.bw.transform(*ln.xy); parts.append(" ".join(f"{x:.5f},{y:.5f}" for x, y in zip(lo, la)))
    return "|".join(parts)
out["geometry"] = [geom(C.segs[i]) for i in chosen]
out.to_csv(os.path.join(A.data, "lane_network_plan.csv"), index=False)
log(f"today: exposure {X0:.0f}, calm trips {calm0 / tr.sum() * 100:.1f}%  ->  after {km:.1f} km: exposure {X:.0f} "
    f"(-{(X0 - X) / X0 * 100:.1f}%), calm trips {calm / tr.sum() * 100:.1f}%, accidents covered {acc_new(base) / acc_tot * 100:.1f}%")
print(out.drop(columns="geometry").to_string(index=False))
