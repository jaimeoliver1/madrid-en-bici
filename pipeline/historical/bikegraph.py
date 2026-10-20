"""The OSM bike graph and the 2023 BiciMAD demand as arrays, for fast routing with scipy.sparse.csgraph.

Same graph and weights as 11_all_routes.py and 14_lane_priority.py (see bike_costs.py), but stored as
numpy arrays so that Dijkstra runs in compiled code: every arc u->v has a length, a weight factor and
the id of the undirected street segment it belongs to.
"""
import ast, math, re, unicodedata, numpy as np, pandas as pd, osmium
from pyproj import Transformer
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from bike_costs import factor

BBOX = (40.37, 40.50, -3.76, -3.61)
DAYS = 49  # 1 Jan - 18 Feb 2023
fw = Transformer.from_crs(4326, 25830, always_xy=True)
bw = Transformer.from_crs(25830, 4326, always_xy=True)


LANE_TAGS = ("cycleway", "cycleway:left", "cycleway:right", "cycleway:both")


class Graph:
    def __init__(self, pbf, dem=None, contraflow=False):
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
                cyc = [t.get(k_, "") for k_ in LANE_TAGS]
                lane = t.get("bicycle") == "designated" or any(c.startswith("lane") for c in cyc)
                sep = hw == "cycleway" or any(c.startswith(("track", "separate")) for c in cyc)
                flat = t.get("bridge", "no") != "no" or t.get("tunnel", "no") != "no"
                ways.append((pts, f, ow, hw, t.get("name", ""), lane, sep, flat, t.get("footway", "")))

        H().apply_file(pbf, locations=True)
        ids = {}
        lon, lat = [], []
        for pts, *_ in ways:
            for i, lo, la in pts:
                if i not in ids: ids[i] = len(ids); lon.append(lo); lat.append(la)
        X, Y = fw.transform(np.array(lon), np.array(lat))
        self.osm_id = np.array(list(ids)); self.idx = ids; self.x, self.y = X, Y; self.n = len(ids)
        self.lon, self.lat = np.array(lon), np.array(lat)
        # elevation at every node [DEM]; per way, a profile smoothed over ~50 m so that 30 m DEM noise
        # does not turn into fake slopes; bridges and tunnels take a straight line between their ends
        self.z = sample_dem(dem, self.lon, self.lat) if dem else np.zeros(self.n)
        U, V, F, S, UP, names, hws, lanes, seps, subs = [], [], [], [], [], [], [], [], [], []
        seg = {}
        for wi, (pts, f, ow, hw, name, lane, sep, flat, sub) in enumerate(ways):
            ix = np.array([ids[p[0]] for p in pts])
            d = np.r_[0, np.cumsum(np.hypot(np.diff(X[ix]), np.diff(Y[ix])))]
            z = self.z[ix]
            if flat and d[-1] > 0: zs = z[0] + (z[-1] - z[0]) * d / d[-1]
            elif len(ix) > 2:
                w = np.exp(-0.5 * ((d[:, None] - d[None, :]) / 50.0) ** 2); zs = (w @ z) / w.sum(1)
            else: zs = z
            for j in range(len(ix) - 1):
                ia, ib = ix[j], ix[j + 1]
                if ia == ib: continue
                a, b = pts[j][0], pts[j + 1][0]
                key = (a, b) if a < b else (b, a)
                s = seg.setdefault(key, len(seg))
                if s == len(names): names.append(name); hws.append(hw); lanes.append(lane); seps.append(sep); subs.append(sub)
                L = max(d[j + 1] - d[j], 1e-6); dz = zs[j + 1] - zs[j]
                U.append(ia); V.append(ib); F.append(f); S.append(s); UP.append(max(0.0, dz / L))
                if not ow: U.append(ib); V.append(ia); F.append(f); S.append(s); UP.append(max(0.0, -dz / L))
        self.u, self.v = np.array(U, np.int32), np.array(V, np.int32)
        self.f = np.array(F); self.seg = np.array(S, np.int32); self.upslope = np.array(UP)
        self.seg_lane = np.array(lanes); self.seg_sep = np.array(seps); self.seg_sub = np.array(subs, object)  # OSM footway=* (sidewalk, crossing...)
        # contraflow arcs for one-way segments: absent (infinite cost) unless the segment gets a protected lane,
        # which is then usable in both directions
        self.rev = np.zeros(len(self.u), bool)
        if contraflow:
            have = set(zip(U, V))
            miss = np.array([i for i, (a, b) in enumerate(zip(U, V)) if (b, a) not in have], int)
            ru, rv = self.v[miss], self.u[miss]
            L = np.hypot(X[ru] - X[rv], Y[ru] - Y[rv])
            up = np.maximum(0, (self.z[rv] - self.z[ru]) / np.maximum(L, 1e-6))
            self.u = np.r_[self.u, ru]; self.v = np.r_[self.v, rv]; self.f = np.r_[self.f, self.f[miss]]
            self.seg = np.r_[self.seg, self.seg[miss]]; self.upslope = np.r_[self.upslope, up]
            self.rev = np.r_[self.rev, np.ones(len(miss), bool)]
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
        ok = np.isfinite(f)  # infinite factor = arc not available (e.g. contraflow without a protected lane)
        u, v, w = self.u[ok], self.v[ok], self.length[ok] * f[ok] + 1e-6
        m = csr_matrix((w, (u, v)), shape=(self.n, self.n))
        # csr_matrix sums duplicates; rebuild with the minimum instead when any exist
        if m.nnz < len(w):
            o = np.lexsort((w, v, u)); first = np.r_[True, (np.diff(u[o]) != 0) | (np.diff(v[o]) != 0)]
            o = o[first]; m = csr_matrix((w[o], (u[o], v[o])), shape=(self.n, self.n))
        return m


def sample_dem(path, lon, lat):
    """Elevation (m) at each point from a single-band GeoTIFF in lon/lat [DEM: Copernicus GLO-30]."""
    import rasterio
    with rasterio.open(path) as d:
        a = d.read(1); inv = ~d.transform
        c, r = inv * (np.asarray(lon), np.asarray(lat))
        r = np.clip(np.floor(r).astype(int), 0, a.shape[0] - 1); c = np.clip(np.floor(c).astype(int), 0, a.shape[1] - 1)
        return a[r, c].astype(float)


def street_key(name):
    """Normalised street name so the city's traffic counts ("C. GRAN VIA", "C. MAGDALENA, LA") match OSM ("Gran Vía", "Calle de la Magdalena")."""
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode().lower().strip()
    s = re.sub(r"^lateral\s+", "", s)
    s = re.sub(r",\s*(el|la|los|las)$", "", s)
    for _ in range(2):  # "Paseo. Paseo de la Castellana"
        s = re.sub(r"^(c|calle|av|avda|avenida|paseo|pso|pza|plaza|gta|glorieta|ronda|carretera|ctra|camino|pte|puente|cuesta|carrera|travesia|costanilla|tunel|paso)\.?\s+", "", s)
        s = re.sub(r"^(de|del|de la|de las|de los)\s+", "", s)
    s = re.sub(r"\b(de|del|la|las|los|el|y)\b", " ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def segment_aadt(g, shp, max_snap=80.0, max_spread=1000.0):
    """Motor traffic (AADT, both directions) on every road segment from the city's 2019 counts [MAD].
    Directions counted at the same place are summed. Each count is matched to the nearest OSM segment of the
    same street (normalised name) within 80 m, then spread along that street to the nearest count within 1 km.
    Roads with no count take the median count of their road class (0 for residential streets, which the city
    does not count)."""
    import shapefile
    r = shapefile.Reader(shp, encoding="latin1")
    pts = {}
    for sh, rec in zip(r.shapes(), r.records()):
        try: v = float(str(rec["iMD 0-23H"]).strip())  # average daily vehicles, 0-23 h
        except (ValueError, TypeError): continue
        if v <= 0: continue
        lo, la = sh.points[0]
        k = (street_key(rec["NOMBRE"]), round(lo, 4), round(la, 4)); pts[k] = pts.get(k, 0.0) + v
    road = {"trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified", "residential", "busway"}
    first = np.full(g.nseg, -1); first[g.seg[::-1]] = np.arange(len(g.seg))[::-1]
    a = first; mx = (g.x[g.u[a]] + g.x[g.v[a]]) / 2; my = (g.y[g.u[a]] + g.y[g.v[a]]) / 2
    keys = np.array([street_key(n) if n else "" for n in g.seg_name], object)
    isroad = np.array([h in road for h in g.seg_hw])
    by = {}
    for i in np.where(isroad & (keys != ""))[0]: by.setdefault(keys[i], []).append(i)
    counts = {}  # street key -> [(x, y, value)]
    for (key, lo, la), v in pts.items():
        segs = by.get(key)
        if not segs: continue
        x, y = fw.transform(lo, la); segs = np.array(segs)
        dd = np.hypot(mx[segs] - x, my[segs] - y)
        if dd.min() <= max_snap: counts.setdefault(key, []).append((x, y, v))
    aadt = np.full(g.nseg, np.nan)
    for key, lst in counts.items():
        segs = np.array(by[key]); L = np.array(lst)
        dist, j = cKDTree(L[:, :2]).query(np.c_[mx[segs], my[segs]])
        ok = dist <= max_spread; aadt[segs[ok]] = L[j[ok], 2]
    measured = ~np.isnan(aadt)
    for hw in road:
        m = g.seg_hw == hw
        med = np.nanmedian(aadt[m & measured]) if hw != "residential" and (m & measured).sum() >= 10 else 0.0
        aadt[m & ~measured] = med
    return np.nan_to_num(aadt), measured, len(pts), sum(len(v) for v in counts.values())


def broach_factors(g, aadt, sep_seg):
    """Perceived-distance multiplier per arc [B12, appraisal.py] for today's network plus `sep_seg` separated
    segments; footways, steps and tracks keep bike_costs.py weights; contraflow arcs only where separated."""
    import appraisal as ap_
    from bike_costs import COST
    walk_set = {"footway", "pedestrian", "path", "track", "steps"}
    hw = g.seg_hw[g.seg]; walk = np.array([h in walk_set for h in hw])
    base_walk = np.array([COST[h] if h in walk_set else 0 for h in hw])
    slope_pen = np.zeros(len(g.u)); traffic_pen = np.zeros(len(g.u))
    for lo, v in sorted(ap_.SLOPE): slope_pen[g.upslope >= lo] = v
    for lo, v in sorted(ap_.TRAFFIC): traffic_pen[aadt[g.seg] >= lo] = v
    s = sep_seg[g.seg]; lane = g.seg_lane[g.seg]
    f = 1 + np.where(s, ap_.PATH, np.where(lane, 0.0, traffic_pen)) + slope_pen
    f = np.where(walk & ~s, base_walk + slope_pen, f)
    return np.where(g.rev & ~s, np.inf, f)


def eb_rates(g, flow, nacc, years, sep, days=DAYS):
    """Injury rate per BiciMAD-km on every segment: road-class rate (class = road type x already separated),
    adjusted per segment by empirical Bayes with a negative binomial dispersion fitted by moments [Hauer]."""
    expo = flow * g.seg_len / 1000 * 365 / days
    cls = np.array([f"{h}|{int(s)}" for h, s in zip(g.seg_hw, sep)])
    rate = np.full(g.nseg, nacc.sum() / years / expo.sum())
    for c in np.unique(cls):
        m = (cls == c) & (expo > 0)
        if m.sum() < 20: continue
        R = nacc[m].sum() / years / expo[m].sum(); rate[cls == c] = R
        if R == 0: continue
        mu = R * expo[m]; N = nacc[m] / years
        theta = np.mean(mu) ** 2 / max(np.var(N) - np.mean(N), 1e-12)
        w = 1 / (1 + mu / theta)
        rate[np.where(m)[0]] = (w * mu + (1 - w) * N) / expo[m]
    return rate


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


def assign(g, f, o, d, trips, bad=None, cost=False, batch=24):
    """All-or-nothing assignment: every trip takes its cheapest route under arc factors f.
    Returns trips per street segment, unroutable trips, and (if `bad` marks stressful segments)
    the trips whose whole route avoids them; with cost=True also the trip-weighted total route cost (in metres x f)."""
    M = g.matrix(f)
    flow = np.zeros(g.nseg); lost = 0.0; calm = 0.0; total = 0.0
    origins = np.unique(o)
    for b0 in range(0, len(origins), batch):
        ob = origins[b0:b0 + batch]
        dist, pred = dijkstra(M, indices=ob, return_predecessors=True)
        for r, src in enumerate(ob):
            sel = o == src; dd = d[sel]; tt = trips[sel]
            P = pred[r]
            ok = P[dd] >= 0; lost += tt[~ok].sum(); dd, tt = dd[ok], tt[ok]
            total += (dist[r, dd] * tt).sum()
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
    return (flow, lost, calm, total) if cost else (flow, lost, calm)
