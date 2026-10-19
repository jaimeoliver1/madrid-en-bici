"""Monthly refresh: re-download every source that updates monthly or faster, rebuild data/ and site/data.js.

Refreshed: BiciMAD daily trips and active users (EMT), live stations and fleet size (GBFS), weather (NOAA
Madrid Retiro), bike accidents, bike infrastructure, bike racks and population (datos.madrid.es), and the
district and barrio metrics that depend on them. Not refreshed (static or no new releases): the 2023
trip-level analysis and routes, elevation, bike counters, benchmarks, the 24-hour animation.

Usage: python3 pipeline/refresh.py [--data data] [--cache .cache] [--site site/data.js]
Needs: pandas numpy pyproj pyshp shapely scipy (same as the rest of the pipeline).
"""
import argparse, datetime, io, json, os, subprocess, sys, time, urllib.parse, urllib.request, zipfile
import numpy as np, pandas as pd, shapefile
from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon
from shapely.prepared import prep
from shapely.strtree import STRtree

UA = {"User-Agent": "Mozilla/5.0 (madrid-cyclability monthly refresh)"}
EMT = "https://datos.emtmadrid.es/api/3/action/package_show?id="
AYTO = "https://datos.madrid.es/api/3/action/package_show?id="
GBFS = "https://madrid.publicbikesystem.net/customer/gbfs/v2/en/"
NOAA = "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/SP000003195.csv"
INFRA = "https://geoportal.madrid.es/fsdescargas/IDEAM_WBGEOPORTAL/OBRAS/BICI/Infraestructura_Ciclista.zip"
TO_UTM = Transformer.from_crs(4326, 25830, always_xy=True)
TO_LL = Transformer.from_crs(25830, 4326, always_xy=True)
EXCLUSIVE = ("VÍA EXCLUSIVA BICI", "ANILLO VERDE CICLISTA")
TYPE_NAME = {"VÍA EXCLUSIVA BICI": "Exclusive bike lane", "VÍA USO COMPARTIDO": "Shared lane (ciclocarril)", "ANILLO VERDE CICLISTA": "Anillo Verde ring",
             "VÍA PREFERENTE BICI": "Bike-priority street", "GIROS Y SENTIDOS": "Turns and contraflow"}


def log(*a):
    print(f"[{datetime.datetime.now():%H:%M:%S}]", *a, flush=True)


def get(url, tries=4):
    """GET with retries; datos.madrid.es sometimes answers an HTML 'Access Denied' page when hit too fast."""
    for k in range(tries):
        try:
            body = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()
            if b"<TITLE>Access Denied</TITLE>" not in body[:400]:
                return body
        except Exception as e:  # network hiccup or rate limit
            log("retry", url[:90], e)
        time.sleep(4 * (k + 1))
    raise RuntimeError(f"could not download {url}")


def cached(cache, key, url):
    """Download url once per key (key carries the source's last-modified stamp)."""
    path = os.path.join(cache, key.replace("/", "_").replace(":", "-"))
    if not os.path.exists(path):
        open(path, "wb").write(get(url)); time.sleep(2)
    return path


def package(base, pid):
    return json.loads(get(base + pid))["result"]


def read_csv(path, **kw):
    for enc in ("utf-8-sig", "latin1"):
        try:
            return pd.read_csv(path, sep=";", encoding=enc, dtype=str, **kw)
        except UnicodeDecodeError:
            continue
    raise ValueError(path)


def utm_num(v):
    """Accident coordinates come as '441236,88' or '446.426.917' depending on the year."""
    if not isinstance(v, str) or not v.strip() or v.strip() == "NULL":
        return float("nan")
    v = v.strip()
    if "," in v:
        return float(v.replace(".", "").replace(",", "."))
    p = v.split(".")
    return float("".join(p[:-1]) + "." + p[-1]) if len(p) > 2 else float(v)


# ---------------------------------------------------------------- sources
def bicimad_daily(cache):
    pkg = package(EMT, "historico-de-viajes-de-bicimad")
    r = next(r for r in pkg["resources"] if r.get("format", "").upper() == "CSV")
    d = pd.read_csv(cached(cache, f"emt_daily_{r.get('last_modified') or r['id']}", r["url"]), sep=";")
    d = d.rename(columns={"FECHA": "date", "VIAJES": "trips"})[["date", "trips"]]
    d["date"] = pd.to_datetime(d.date).dt.strftime("%Y-%m-%d")
    return d.sort_values("date")


def bicimad_users(cache):
    pkg = package(EMT, "usuarios-de-bicimad-activos")
    r = next(r for r in pkg["resources"] if r.get("format", "").upper() == "CSV")
    u = pd.read_csv(cached(cache, f"emt_users_{r.get('last_modified') or r['id']}", r["url"]), sep=";")
    return pd.DataFrame({"month": pd.to_datetime(u["FECHA"]).dt.strftime("%Y-%m"), "active_users": u["USUARIOS ACTIVOS"].astype(int)})


def weather(cache, daily):
    stamp = datetime.date.today().isoformat()
    w = pd.read_csv(cached(cache, f"noaa_retiro_{stamp}.csv", NOAA), dtype=str)
    w["date"] = w.DATE
    for col, src in (("rain_mm", "PRCP"), ("tmax_c", "TMAX"), ("tmin_c", "TMIN")):
        w[col] = pd.to_numeric(w[src], errors="coerce") / 10
    return daily.merge(w[["date", "rain_mm", "tmax_c", "tmin_c"]], on="date", how="left")


def infrastructure(cache):
    stamp = datetime.date.today().strftime("%Y-%m")
    zp = cached(cache, f"infra_{stamp}.zip", INFRA)
    folder = os.path.join(cache, f"infra_{stamp}")
    if not os.path.isdir(folder):
        zipfile.ZipFile(zp).extractall(folder)
    shp = next(os.path.join(dp, f) for dp, _, fs in os.walk(folder) for f in fs if f.lower().endswith(".shp"))
    r = shapefile.Reader(shp, encoding="utf-8")
    rows, lines, excl = [], [], []
    for sh, rec in zip(r.shapes(), r.records()):
        kind = rec["d_COD_TIPO"].replace("ESCLUSIVA", "EXCLUSIVA")
        for i0, i1 in zip(list(sh.parts), list(sh.parts[1:]) + [len(sh.points)]):
            p = sh.points[i0:i1]
            if len(p) < 2:
                continue
            L = LineString(p); lines.append(L)
            if kind in EXCLUSIVE:
                excl.append(L)
            xs, ys = zip(*L.simplify(6).coords); lo, la = TO_LL.transform(xs, ys)
            rows.append({"segment": len(rows) + 1, "type": TYPE_NAME.get(kind, kind.title()), "subtype": rec["d_COD_TI_1"].split(", ")[-1].title(),
                         "length_km": round(L.length / 1000, 3), "path": " ".join(f"{a:.5f},{b:.5f}" for a, b in zip(lo, la))})
    return pd.DataFrame(rows), lines, excl


def nearest_m(tree, geoms, x, y, cap=400):
    p = Point(x, y)
    return min((geoms[i].distance(p) for i in tree.query(p.buffer(cap))), default=cap)


def stations(cache, data, lines, excl):
    info = json.loads(get(GBFS + "station_information"))["data"]["stations"]
    stat = {s["station_id"]: s for s in json.loads(get(GBFS + "station_status"))["data"]["stations"]}
    sysi = json.loads(get(GBFS + "system_information"))
    rows = []
    for s in info:
        t = stat.get(s["station_id"])
        if t:
            rows.append({"station_id": int(s["station_id"]), "name": s["name"], "lat": round(s["lat"], 5), "lon": round(s["lon"], 5), "capacity": s.get("capacity", 0),
                         "bikes_available": t["num_bikes_available"], "docks_available": t["num_docks_available"], "bikes_disabled": t.get("num_bikes_disabled", 0), "status": t["status"]})
    live = pd.DataFrame(rows)
    # elevation: reuse what we have, look up only new stations
    old = pd.read_csv(os.path.join(data, "bicimad_station_context.csv")) if os.path.exists(os.path.join(data, "bicimad_station_context.csv")) else pd.DataFrame(columns=["station_id", "elevation_m"])
    elev = dict(zip(old.station_id, old.elevation_m))
    missing = live[~live.station_id.isin([k for k, v in elev.items() if pd.notna(v)])]
    for i in range(0, len(missing), 100):
        chunk = missing.iloc[i:i + 100]
        q = "|".join(f"{a:.6f},{b:.6f}" for a, b in zip(chunk.lat, chunk.lon))
        res = json.loads(get("https://api.opentopodata.org/v1/eudem25m?locations=" + urllib.parse.quote(q)))["results"]
        elev.update({sid: (round(r["elevation"], 1) if r["elevation"] is not None else None) for sid, r in zip(chunk.station_id, res)})
        time.sleep(1.2)
    live["elevation_m"] = live.station_id.map(elev)
    X, Y = TO_UTM.transform(live.lon.values, live.lat.values)
    te, ta = STRtree(excl), STRtree(lines)
    live["m_to_exclusive_lane"] = [round(nearest_m(te, excl, x, y)) for x, y in zip(X, Y)]
    live["m_to_any_bike_infra"] = [round(nearest_m(ta, lines, x, y)) for x, y in zip(X, Y)]
    snap = datetime.datetime.fromtimestamp(sysi.get("last_updated", time.time()), datetime.timezone(datetime.timedelta(hours=2)))
    fleet = sysi["data"].get("_vehicle_count", {})
    return live, {"fleet": int(fleet.get("_ebike_count", 0)) + int(fleet.get("_mechanical_count", 0)) or None, "snapshot": snap.strftime("%Y-%m-%d %H:%M")}, len(missing)


def accidents(cache, excl):
    pkg = package(AYTO, "300110-0-accidentes-bicicleta")
    frames = []
    for r in pkg["resources"]:
        if r.get("format", "").upper() != "CSV":
            continue
        path = cached(cache, f"acc_{r['id']}_{r.get('last_modified') or r.get('metadata_modified', '')}.csv", r["url"])
        d = read_csv(path)
        if "num_expediente" not in d.columns:  # 2010-2018 files use another layout without coordinates; skipped
            continue
        d.columns = [c.replace("tipo_vehículo", "tipo_vehiculo").replace("estado_meteorológico", "estado_meteorologico") for c in d.columns]
        frames.append(d)
    a = pd.concat(frames, ignore_index=True).drop_duplicates()
    a["date"] = pd.to_datetime(a.fecha, dayfirst=True, errors="coerce"); a["year"] = a.date.dt.year
    a["hour"] = pd.to_numeric(a.hora.str.split(":").str[0], errors="coerce")
    a["x"] = a.coordenada_x_utm.map(utm_num); a["y"] = a.coordenada_y_utm.map(utm_num)
    a["epac"] = a.tipo_vehiculo.str.contains("EPAC", na=False)
    a["serious"] = a.cod_lesividad.isin(["3", "4"]); a["killed"] = a.cod_lesividad.eq("4")
    # people hurt, by the DGT's injury classes (cod_lesividad): 4 died, 3 admitted over 24 h (serious),
    # 1, 2, 5, 6, 7 treated without a stay over 24 h (slight), 14 or blank not hurt
    a["n_killed"] = a.killed.astype(int); a["n_serious"] = a.cod_lesividad.eq("3").astype(int)
    a["n_slight"] = a.cod_lesividad.isin(["1", "2", "5", "6", "7"]).astype(int)
    by = a.groupby("year").agg(accidents=("num_expediente", "nunique"), people=("num_expediente", "size"), seriously_injured_or_killed=("serious", "sum"),
                               killed=("killed", "sum"), ebike_riders=("epac", "sum"), months=("date", lambda s: s.dt.month.nunique())).reset_index()
    acc = a.groupby("num_expediente").agg(year=("year", "first"), hour=("hour", "first"), x=("x", "first"), y=("y", "first"), type=("tipo_accidente", "first"),
                                          weather=("estado_meteorologico", "first"), serious=("serious", "any"), killed=("killed", "any"), place=("localizacion", "first"),
                                          n_slight=("n_slight", "sum"), n_serious=("n_serious", "sum"), n_killed=("n_killed", "sum"))
    acc = acc[(acc.x > 420000) & (acc.x < 460000)].copy()
    lo, la = TO_LL.transform(acc.x.values, acc.y.values); acc["lat"] = np.round(la, 5); acc["lon"] = np.round(lo, 5)
    tree = STRtree(excl)
    acc["on_exclusive_lane"] = [int(nearest_m(tree, excl, x, y, 30) <= 15) for x, y in zip(acc.x, acc.y)]
    acc["serious"] = acc.serious.astype(int); acc["killed"] = acc.killed.astype(int); acc["hour"] = acc.hour.astype("Int64"); acc["place"] = acc.place.str.title()
    acc = acc.reset_index().rename(columns={"num_expediente": "expediente"})
    return acc[["expediente", "year", "hour", "lat", "lon", "type", "weather", "serious", "killed", "n_slight", "n_serious", "n_killed",
                "on_exclusive_lane", "place"]], by, a.date.max()


def parking(cache):
    pkg = package(AYTO, "205099-0-aparca-bicis")
    csvs = [r for r in pkg["resources"] if r.get("format", "").upper() == "CSV" and "205099_" in r["url"]]
    r = max(csvs, key=lambda r: r["url"])  # the daily file is named 205099_YYYYMMDD_hhmmss.csv
    d = read_csv(cached(cache, f"racks_{os.path.basename(r['url'])}", r["url"]))
    d = d[d.ESTADO.eq("OPERATIVO")]
    x = pd.to_numeric(d.COORD_GIS_X, errors="coerce"); y = pd.to_numeric(d.COORD_GIS_Y, errors="coerce"); ok = x.notna() & y.notna()
    lo, la = TO_LL.transform(x[ok].values, y[ok].values)
    return pd.DataFrame({"lat": np.round(la, 5), "lon": np.round(lo, 5), "DISTRITO": d.DISTRITO[ok].values})


def population(cache):
    pkg = package(AYTO, "300557-0-poblacion-distrito-barrio")
    r = next(r for r in pkg["resources"] if r.get("format", "").upper() == "CSV")
    p = read_csv(cached(cache, f"padron_{r.get('last_modified') or r['id']}.csv", r["url"]))
    latest = max(p.fecha.unique(), key=lambda s: int(s.split()[-1]))
    p = p[p.fecha == latest].copy()
    p["n"] = p.num_personas.str.replace(".", "", regex=False).astype(int)
    return p, latest


# ---------------------------------------------------------------- derived metrics
def polygons(rings):
    return [prep(Polygon([tuple(map(float, q.split(","))) for q in r.split(" ")])) for r in rings.split("|")]


def inside(polys, lon, lat):
    pts = [Point(a, b) for a, b in zip(lon, lat)]
    return np.array([any(p.contains(q) for p in polys) for q in pts])


def districts(data, live, acc, racks, pop, lanes):
    dist = pd.read_csv(os.path.join(data, "madrid_districts_cycling.csv")); shp = pd.read_csv(os.path.join(data, "madrid_districts_shapes.csv")).set_index("code")
    on = live[live.status == "IN_SERVICE"]
    popd = pop.groupby(pop.cod_distrito.astype(int)).n.sum()
    ex = lanes[lanes.type.isin(["Exclusive bike lane", "Anillo Verde ring"])]
    lane_pts = lambda df: [(np.mean([float(q.split(",")[0]) for q in p.split(" ")]), np.mean([float(q.split(",")[1]) for q in p.split(" ")]), km) for p, km in zip(df.path, df.length_km)]
    lx, la_ = lane_pts(ex), lane_pts(lanes)
    for i, r in dist.iterrows():
        polys = polygons(shp.loc[r.code, "rings"])
        m = inside(polys, on.lon, on.lat)
        dist.loc[i, "stations"] = int(m.sum()); dist.loc[i, "docks"] = int(on.capacity[m].sum())
        dist.loc[i, "accidents"] = int(inside(polys, acc.lon, acc.lat).sum())
        dist.loc[i, "bike_racks"] = int(inside(polys, racks.lon, racks.lat).sum())
        dist.loc[i, "population"] = int(popd.get(r.code, r.population))
        # lane km by segment midpoint (segments are short; good enough for a monthly refresh)
        dist.loc[i, "exclusive_km"] = round(sum(km for x, y, km in lx if any(p.contains(Point(x, y)) for p in polys)), 1)
        dist.loc[i, "all_infra_km"] = round(sum(km for x, y, km in la_ if any(p.contains(Point(x, y)) for p in polys)), 1)
    years = max(1.0, (acc.year.max() - acc.year.min()) + 1)
    dist["stations_per_km2"] = (dist.stations / dist.area_km2).round(2)
    dist["docks_per_1000"] = (dist.docks / dist.population * 1000).round(1)
    dist["exclusive_km_per_100k"] = (dist.exclusive_km / dist.population * 1e5).round(1)
    dist["accidents_per_100k_per_year"] = (dist.accidents / dist.population * 1e5 / years).round(1)
    return dist


def barrios(data, live, pop):
    b = pd.read_csv(os.path.join(data, "madrid_barrios_bicimad.csv"))
    on = live[live.status == "IN_SERVICE"]
    popb = pop.set_index(pop.cod_barrio.astype(int)).n
    b["stations"] = [int(inside(polygons(r), on.lon, on.lat).sum()) for r in b.rings]
    b["population"] = [int(popb.get(c, p)) for c, p in zip(b.code, b.population)]
    b["stations_per_km2"] = (b.stations / b.area_km2).round(2)
    return b


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--data", default=os.path.join(here, "data")); ap.add_argument("--cache", default=os.path.join(here, ".cache"))
    ap.add_argument("--site", default=os.path.join(here, "site", "data.js"))
    a = ap.parse_args(); os.makedirs(a.cache, exist_ok=True)
    D = lambda f: os.path.join(a.data, f)
    report = {"refreshed_at": datetime.datetime.now().isoformat(timespec="minutes")}

    daily = bicimad_daily(a.cache)
    report["daily_trips"] = f"{daily.date.min()} to {daily.date.max()} ({len(daily)} days)"; log("daily trips", report["daily_trips"])
    users = bicimad_users(a.cache); users.to_csv(D("bicimad_active_users_monthly.csv"), index=False)
    report["active_users"] = f"{users.month.min()} to {users.month.max()}"; log("active users", report["active_users"])
    tw = weather(a.cache, daily); tw.to_csv(D("bicimad_daily_trips_weather.csv"), index=False)
    report["weather_days_missing"] = int(tw.rain_mm.isna().sum()); log("weather joined; days without rain data:", report["weather_days_missing"])

    lanes, lines, excl = infrastructure(a.cache); lanes.to_csv(D("madrid_bike_infrastructure.csv"), index=False)
    report["bike_infrastructure_segments"] = len(lanes); log("bike infrastructure segments", len(lanes))

    live, snap, new_elev = stations(a.cache, a.data, lines, excl)
    live.to_csv(D("bicimad_station_context.csv"), index=False)
    report.update({"stations": len(live), "stations_in_service": int((live.status == "IN_SERVICE").sum()), "new_station_elevations": new_elev, **snap})
    log("live stations", len(live), "fleet", snap["fleet"], "snapshot", snap["snapshot"])

    acc, by, last = accidents(a.cache, excl)
    acc.to_csv(D("madrid_bike_accidents.csv"), index=False); by.to_csv(D("madrid_bike_accidents_by_year.csv"), index=False)
    report["accidents"] = f"{len(acc)} located accidents, latest {last:%Y-%m-%d}"; report["accidents_latest"] = f"{last:%Y-%m-%d}"; log("accidents", report["accidents"])

    racks = parking(a.cache); racks.to_csv(D("madrid_bike_parking.csv"), index=False)
    report["bike_racks"] = len(racks); log("bike racks", len(racks))

    pop, label = population(a.cache); report["population"] = f"{pop.n.sum()} ({label})"; log("population", report["population"])
    districts(a.data, live, acc, racks, pop, lanes).to_csv(D("madrid_districts_cycling.csv"), index=False)
    barrios(a.data, live, pop).to_csv(D("madrid_barrios_bicimad.csv"), index=False)
    log("district and barrio metrics rebuilt")

    json.dump(report, open(D("refresh_meta.json"), "w"), indent=1)
    subprocess.run([sys.executable, os.path.join(here, "pipeline", "build_site.py"), a.data, a.site], check=True)
    log("done:", json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
