"""Barrio outlines, areas and residents, with BiciMAD stations per km2.

Usage: python3 pipeline/historical/08_barrios.py <BARRIOS.shp> <poblacion.csv> data
Writes data/madrid_barrios_bicimad.csv. Inputs pinned in inputs.json (the outlines and the population file are kept in
pipeline/historical/vendor/). refresh.py recounts stations and updates the population every month on these outlines,
so after a refresh only those columns differ from what this script writes.
"""
import sys, pandas as pd, numpy as np, shapefile
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.prepared import prep

SHP, POB, D = sys.argv[1], sys.argv[2], sys.argv[3]
fw = Transformer.from_crs(4326, 25830, always_xy=True); tr = Transformer.from_crs(25830, 4326, always_xy=True)
r = shapefile.Reader(SHP, encoding="utf-8")
pob = pd.read_csv(POB, sep=";", encoding="utf-8-sig", dtype=str)
pob = pob[pob.fecha == pob.fecha.iloc[0]]
pob["n"] = pob.num_personas.str.replace(".", "", regex=False).astype(int)
pob["code"] = pob.cod_barrio.astype(int)
popb = pob.set_index("code").n
st = pd.read_csv(f"{D}/bicimad_station_context.csv"); st = st[st.status == "IN_SERVICE"]
X, Y = fw.transform(st.lon.values, st.lat.values); pts = [Point(x, y) for x, y in zip(X, Y)]
lanes = pd.read_csv(f"{D}/madrid_bike_infrastructure.csv")
rows = []
for sh, rec in zip(r.shapes(), r.records()):
    g = shape(sh.__geo_interface__); pg = prep(g)
    n = sum(pg.contains(p) for p in pts)
    code = int(rec["COD_BAR"])
    gs = g.simplify(30); polys = [gs] if gs.geom_type == "Polygon" else list(gs.geoms)
    rings = []
    for p in polys:
        xs, ys = zip(*p.exterior.coords); lo, la = tr.transform(xs, ys)
        rings.append(" ".join(f"{a:.4f},{b:.4f}" for a, b in zip(lo, la)))
    rows.append({"barrio": rec["NOMBRE"], "district": rec["NOMDIS"], "code": code, "population": int(popb.get(code, 0)),
                 "area_km2": round(g.area / 1e6, 2), "stations": n, "rings": "|".join(rings)})
b = pd.DataFrame(rows)
b["stations_per_km2"] = (b.stations / b.area_km2).round(2)
b.to_csv(f"{D}/madrid_barrios_bicimad.csv", index=False)
P = b.population.sum()
for lo in (0, 1, 4, 10):
    print(f"residents in barrios with > {lo} stations/km2:", round(b[b.stations_per_km2 > lo].population.sum() / P * 100, 1), "%")
print("no station:", round(b[b.stations == 0].population.sum() / P * 100, 1), "%", (b.stations == 0).sum(), "barrios")
