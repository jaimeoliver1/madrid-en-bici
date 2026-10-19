"""The OSM bike graph and the 2023 BiciMAD demand as arrays, for fast routing with scipy.sparse.csgraph.

Same graph and weights as 11_all_routes.py and 14_lane_priority.py (see bike_costs.py), but stored as
numpy arrays so that Dijkstra runs in compiled code: every arc u->v has a length, a weight factor and
the id of the undirected street segment it belongs to.
"""
import ast, math, numpy as np, pandas as pd, osmium
from pyproj import Transformer
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from bike_costs import factor

BBOX = (40.37, 40.50, -3.76, -3.61)
DAYS = 49  # 1 Jan - 18 Feb 2023
fw = Transformer.from_crs(4326, 25830, always_xy=True)
bw = Transformer.from_crs(25830, 4326, always_xy=True)


class Graph:
    def __init__(self, pbf):
        ways = []

        class H(osmium.SimpleHandler):
            def way(s, w):
                t = w.tags; f = factor(t)
                if f is None: return
                try: pts = [(n.ref, n.lon, n.lat) for n in w.nodes]
                except osmium.InvalidLocationError: return
                if not any(BBOX[0] <= la <= BBOX[1] and BBOX[2] <= lo <= BBOX[3] for _, lo, la in pts): return
                hw = t.get("highway")
                ow = t.get("oneway") in ("yes", "1", "true") or hw in ("primary_link", "secondary_link") and t.get("oneway") != "no" or t.get("junction") == "roundabout"
                if t.get("oneway:bicycle") == "no" or t.get("cycleway", "").startswith("opposite"): ow = False
                if t.get("oneway") == "-1": pts = pts[::-1]
                ways.append((pts, f, ow, hw, t.get("name", "")))

        H().apply_file(pbf, locations=True)
        ids = {}
        lon, lat = [], []
        for pts, *_ in ways:
            for i, lo, la in pts:
                if i not in ids: ids[i] = len(ids); lon.append(lo); lat.append(la)
        X, Y = fw.transform(np.array(lon), np.array(lat))
        self.osm_id = np.array(list(ids)); self.idx = ids; self.x, self.y = X, Y; self.n = len(ids)
        U, V, F, S, names, hws = [], [], [], [], [], []
        seg = {}
        for wi, (pts, f, ow, hw, name) in enumerate(ways):
            for (a, *_), (b, *_) in zip(pts, pts[1:]):
                ia, ib = ids[a], ids[b]
                if ia == ib: continue
                key = (a, b) if a < b else (b, a)
                s = seg.setdefault(key, len(seg))
                if s == len(names): names.append(name); hws.append(hw)
                U.append(ia); V.append(ib); F.append(f); S.append(s)
                if not ow: U.append(ib); V.append(ia); F.append(f); S.append(s)
        self.u, self.v = np.array(U, np.int32), np.array(V, np.int32)
        self.f = np.array(F); self.seg = np.array(S, np.int32)
        self.length = np.hypot(X[self.u] - X[self.v], Y[self.u] - Y[self.v])
        self.seg_key = list(seg); self.seg_name = np.array(names, object); self.seg_hw = np.array(hws, object)
        self.nseg = len(seg)
        self.seg_len = np.zeros(self.nseg); np.maximum.at(self.seg_len, self.seg, self.length)
        self.seg_id = seg
        # arc lookup: (u, v) -> arc index, via sorted integer keys
        k = self.u.astype(np.int64) * self.n + self.v
        self._order = np.argsort(k, kind="stable"); self._keys = k[self._order]

    def arcs(self, pu, pv):
        k = np.asarray(pu, np.int64) * self.n + np.asarray(pv)
        return self._order[np.searchsorted(self._keys, k)]

    def matrix(self, f):
        """Sparse cost matrix for per-arc weight factors f (keeps the cheapest arc between two nodes)."""
        w = self.length * f + 1e-6
        m = csr_matrix((w, (self.u, self.v)), shape=(self.n, self.n))
        # csr_matrix sums duplicates; rebuild with the minimum instead when any exist
        if m.nnz < len(w):
            o = np.lexsort((w, self.v, self.u)); first = np.r_[True, (np.diff(self.u[o]) != 0) | (np.diff(self.v[o]) != 0)]
            o = o[first]; m = csr_matrix((w[o], (self.u[o], self.v[o])), shape=(self.n, self.n))
        return m


def load_od(g, trips_dir):
    """Station-to-station trips of Jan-Feb 2023, snapped to graph nodes: arrays (origin node, destination node, trips)."""
    t = pd.concat([pd.read_csv(f"{trips_dir}/trips_23_0{m}.csv", sep=";", low_memory=False) for m in ["1_January", "2_February"]], ignore_index=True).dropna(how="all")
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
    both = np.intersect1d(g.u, g.v)  # nodes you can both reach and leave
    kd = cKDTree(np.c_[g.x[both], g.y[both]])
    PX, PY = fw.transform(pos.lon.values, pos.lat.values)
    snap = dict(zip(pos.index, both[kd.query(np.c_[PX, PY])[1]]))
    o = od.station_unlock.map(snap).values; d = od.station_lock.map(snap).values
    keep = o != d
    return o[keep].astype(np.int32), d[keep].astype(np.int32), od.trips.values[keep].astype(float)


def assign(g, f, o, d, trips, bad=None, batch=24):
    """All-or-nothing assignment: every trip takes its cheapest route under arc factors f.
    Returns trips per street segment, unroutable trips, and (if `bad` marks stressful segments)
    the trips whose whole route avoids them."""
    M = g.matrix(f)
    flow = np.zeros(g.nseg); lost = 0.0; calm = 0.0
    origins = np.unique(o)
    for b0 in range(0, len(origins), batch):
        ob = origins[b0:b0 + batch]
        _, pred = dijkstra(M, indices=ob, return_predecessors=True)
        for r, src in enumerate(ob):
            sel = o == src; dd = d[sel]; tt = trips[sel]
            P = pred[r]
            ok = P[dd] >= 0; lost += tt[~ok].sum(); dd, tt = dd[ok], tt[ok]
            # walk all destinations back to the origin together, one step per loop
            cur, w = dd.copy(), tt.copy()
            hit = np.zeros(len(cur), bool); ix = np.arange(len(cur))
            while len(cur):
                p = P[cur]
                a = g.arcs(p, cur)
                np.add.at(flow, g.seg[a], w)
                if bad is not None: hit[ix] |= bad[g.seg[a]]
                keep = p != src
                cur, w, ix = p[keep], w[keep], ix[keep]
            if bad is not None: calm += tt[~hit].sum()
    return flow, lost, calm
