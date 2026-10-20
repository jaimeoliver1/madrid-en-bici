"""District outlines for the maps, and the city's bike counters with their 2023 average daily bikes.

Usage: python3 pipeline/historical/06_districts_counters.py <DISTRITOS.shp> <counters_dir> <data_dir>
Writes <data_dir>/madrid_districts_shapes.csv (read by refresh.py and build_site.py) and madrid_bike_counters.csv
(read by 15_lane_network.py and build_site.py). counters_dir holds the yearly bike files bikes_2019.csv ...
bikes_2024.csv of datos.madrid.es 300321. Inputs pinned in inputs.json. The district metrics themselves
(madrid_districts_cycling.csv) are kept up to date by refresh.py.
"""
import sys, glob, pandas as pd, numpy as np, shapefile
from pyproj import Transformer
from shapely.geometry import shape

SHP, C, D = sys.argv[1], sys.argv[2], sys.argv[3]
tr = Transformer.from_crs(25830, 4326, always_xy=True)
r = shapefile.Reader(SHP, encoding="utf-8")
dist = [(rec["NOMBRE"], int(rec["COD_DIS"]), shape(sh.__geo_interface__)) for sh, rec in zip(r.shapes(), r.records())]

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

# bike counters: hourly counts -> full days (23+ hours) -> 2023 average per counter
fr = []
for f in sorted(glob.glob(f"{C}/bikes_*.csv")):
    d = pd.read_csv(f, sep=";", encoding="utf-8-sig", dtype=str, on_bad_lines="skip")
    d.columns = [c.lower().replace("ãº", "ú") for c in d.columns]
    d = d.rename(columns={"latitud": "latitude", "longitud": "longitude", "nombre_vial": "direccion"})
    d["date"] = pd.to_datetime(d.fecha.str.split(" ").str[0], dayfirst=True, errors="coerce")
    d["bikes"] = pd.to_numeric(d.bicicletas, errors="coerce")
    fr.append(d[["date", "identificador", "bikes", "direccion", "latitude", "longitude"]])
c = pd.concat(fr, ignore_index=True).dropna(subset=["date", "bikes"])
daily = c.groupby(["identificador", "date"]).agg(bikes=("bikes", "sum"), hours=("bikes", "size")).reset_index()
daily = daily[daily.hours >= 23]
def cnum(v):
    v = str(v).strip()
    if "," in v: return float(v.replace(",", "."))
    p = v.split(".")
    return float(p[0] + "." + "".join(p[1:])) if len(p) > 2 else float(v)
c["latitude"] = c.latitude.map(lambda v: cnum(v) if isinstance(v, str) else np.nan); c["longitude"] = c.longitude.map(lambda v: cnum(v) if isinstance(v, str) else np.nan)
loc = c.dropna(subset=["latitude"]).groupby("identificador").agg(street=("direccion", "first"), lat=("latitude", "first"), lon=("longitude", "first")).reset_index()
best = daily[daily.date.dt.year == 2023].groupby("identificador").bikes.mean().round(0).rename("avg_daily_bikes_2023").reset_index()
loc = loc.merge(best, on="identificador", how="left").sort_values("avg_daily_bikes_2023", ascending=False)
loc.to_csv(f"{D}/madrid_bike_counters.csv", index=False); print(len(geo), "districts;", len(loc), "counters"); print(loc.head(8).to_string())
