# District-level cyclability metrics and bike counter trends.
import sys, json, glob, pandas as pd, numpy as np, shapefile
from pyproj import Transformer
from shapely.geometry import shape, Point, LineString
from shapely.prepared import prep
E, D, R = sys.argv[1], sys.argv[2], sys.argv[3]
fw = Transformer.from_crs(4326, 25830, always_xy=True); tr = Transformer.from_crs(25830, 4326, always_xy=True)
r = shapefile.Reader(f"{E}/geo2/DISTRITOS.shp", encoding="utf-8")
dist = [(rec["NOMBRE"], int(rec["COD_DIS"]), shape(sh.__geo_interface__)) for sh, rec in zip(r.shapes(), r.records())]
pob = pd.read_csv(f"{E}/geo2/poblacion.csv", sep=";", encoding="utf-8-sig", dtype=str)
pob["n"] = pob.num_personas.str.replace(".", "", regex=False).astype(int)
year_label = pob.fecha.iloc[0]
pob = pob[pob.fecha == year_label]
pd_ = pob.groupby(pob.cod_distrito.astype(int)).n.sum()
st = pd.read_csv(f"{D}/bicimad_station_context.csv"); st = st[st.status == "IN_SERVICE"]
X, Y = fw.transform(st.lon.values, st.lat.values)
acc = pd.read_csv(f"{D}/madrid_bike_accidents_2019_2026.csv")
AX, AY = fw.transform(acc.lon.values, acc.lat.values)
pk = pd.read_csv(f"{D}/madrid_bike_parking.csv"); PX, PY = fw.transform(pk.lon.values, pk.lat.values)
lanes = pd.read_csv(f"{D}/madrid_bike_infrastructure.csv")
def L(path):
    pts = [tuple(map(float, p.split(","))) for p in path.split(" ")]
    xs, ys = fw.transform([p[0] for p in pts], [p[1] for p in pts]); return LineString(list(zip(xs, ys)))
lanes["geom"] = lanes.path.map(L)
excl_types = ("Exclusive bike lane", "Anillo Verde ring")
rows = []
for name, code, g in dist:
    pg = prep(g)
    inside = lambda xs, ys: sum(pg.contains(Point(x, y)) for x, y in zip(xs, ys))
    ex_km = sum(geom.intersection(g).length for geom, t_ in zip(lanes.geom, lanes.type) if t_ in excl_types) / 1000
    any_km = sum(geom.intersection(g).length for geom in lanes.geom) / 1000
    stn_mask = [pg.contains(Point(x, y)) for x, y in zip(X, Y)]
    rows.append({"district": name, "code": code, "population": int(pd_.get(code, 0)), "area_km2": round(g.area / 1e6, 1),
                 "stations": int(sum(stn_mask)), "docks": int(st.capacity[np.array(stn_mask)].sum()),
                 "exclusive_km": round(ex_km, 1), "all_infra_km": round(any_km, 1),
                 "accidents_2019_2026": inside(AX, AY), "bike_racks": inside(PX, PY)})
df = pd.DataFrame(rows)
df["stations_per_km2"] = (df.stations / df.area_km2).round(2)
df["docks_per_1000"] = (df.docks / df.population * 1000).round(1)
df["exclusive_km_per_100k"] = (df.exclusive_km / df.population * 1e5).round(1)
df["accidents_per_100k_per_year"] = (df.accidents_2019_2026 / df.population * 1e5 / 7.67).round(1)
df = df.sort_values("code"); df.to_csv(f"{D}/madrid_districts_cycling.csv", index=False)
print(year_label); print(df.drop(columns=["code"]).to_string())
tot = df[["population","area_km2","stations","docks","exclusive_km","all_infra_km","accidents_2019_2026","bike_racks"]].sum()
print(tot.to_dict())
# district geometry (simplified, lon/lat) for maps
geo = []
for name, code, g in dist:
    gs = g.simplify(40)
    polys = [gs] if gs.geom_type == "Polygon" else list(gs.geoms)
    rings = []
    for p in polys:
        xs, ys = zip(*p.exterior.coords); lo, la = tr.transform(xs, ys)
        rings.append(" ".join(f"{a:.5f},{b:.5f}" for a, b in zip(lo, la)))
    geo.append({"district": name, "code": code, "rings": "|".join(rings)})
pd.DataFrame(geo).to_csv(f"{D}/madrid_districts_shapes.csv", index=False)
# ---- bike counters: daily bikes per counter, comparable period Jan–Jun by year
fr = []
for f in sorted(glob.glob(f"{E}/counts/bikes_*.csv")):
    d = pd.read_csv(f, sep=";", encoding="utf-8-sig", dtype=str, on_bad_lines="skip")
    d.columns = [c.lower().replace("ãº", "ú") for c in d.columns]
    d = d.rename(columns={"latitud": "latitude", "longitud": "longitude", "nombre_vial": "direccion"})
    d["date"] = pd.to_datetime(d.fecha.str.split(" ").str[0], dayfirst=True, errors="coerce")
    d["bikes"] = pd.to_numeric(d.bicicletas, errors="coerce")
    fr.append(d[["date", "identificador", "bikes", "direccion", "latitude", "longitude"]])
c = pd.concat(fr, ignore_index=True).dropna(subset=["date", "bikes"])
daily = c.groupby(["identificador", "date"]).agg(bikes=("bikes", "sum"), hours=("bikes", "size")).reset_index()
daily = daily[daily.hours >= 23]
daily["year"] = daily.date.dt.year; daily["month"] = daily.date.dt.month
h1 = daily[daily.month <= 6]
yrs = [2020, 2021, 2023, 2024]
common = set.intersection(*[set(h1[h1.year == y].identificador) for y in yrs])
cm = h1[h1.identificador.isin(common)]
trend = cm.groupby("year").bikes.mean().round(0)
print("counters common", len(common)); print(trend.to_dict())
monthly = daily.groupby(daily.date.dt.to_period("M")).agg(avg_bikes_per_counter_day=("bikes", "mean"), counters=("identificador", "nunique")).round(0).reset_index()
monthly["month"] = monthly.date.astype(str); monthly.drop(columns="date").to_csv(f"{D}/madrid_bike_counters_monthly.csv", index=False)
def cnum(v):
    v = str(v).strip()
    if "," in v: return float(v.replace(",", "."))
    p = v.split(".")
    return float(p[0] + "." + "".join(p[1:])) if len(p) > 2 else float(v)
c["latitude"] = c.latitude.map(lambda v: cnum(v) if isinstance(v, str) else np.nan); c["longitude"] = c.longitude.map(lambda v: cnum(v) if isinstance(v, str) else np.nan)
loc = c.dropna(subset=["latitude"]).groupby("identificador").agg(street=("direccion", "first"), lat=("latitude", "first"), lon=("longitude", "first")).reset_index()
best = daily[daily.year == 2023].groupby("identificador").bikes.mean().round(0).rename("avg_daily_bikes_2023").reset_index()
loc = loc.merge(best, on="identificador", how="left").sort_values("avg_daily_bikes_2023", ascending=False)
loc.to_csv(f"{D}/madrid_bike_counters.csv", index=False); print(loc.head(8).to_string())
json.dump({"pop_label": year_label, "counter_trend_janjun": {str(k): int(v) for k, v in trend.items()}, "common_counters": len(common)}, open(f"{R}/districts_meta.json", "w"))
