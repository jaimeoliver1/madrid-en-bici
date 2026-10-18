"""Export the context datasets (accidents, lanes, station context, weather, racks) as CSVs in data/.

Usage: python3 05_context_export.py <enrich_raw_dir> <work_dir> <data_dir>
"""
import sys, json, pandas as pd, numpy as np, shapefile
from pyproj import Transformer
from shapely.geometry import LineString
E, R, D = sys.argv[1], sys.argv[2], sys.argv[3]
tr = Transformer.from_crs(25830, 4326, always_xy=True)
acc = pd.read_pickle(f"{R}/acc.pkl"); ap = pd.read_pickle(f"{R}/acc_persons.pkl")
# accidents points
import importlib.util
pts = pd.read_csv(f"{R}/accidents_points.csv")
pts = pts.merge(acc[["loc"]].rename(columns={"loc":"place"}), left_on="expediente", right_index=True, how="left")
pts["place"] = pts.place.str.title()
pts["serious"] = (pts.serious > 0).astype(int); pts["killed"] = (pts.killed > 0).astype(int); pts["on_exclusive_lane"] = pts.on_excl.astype(int)
pts["hour"] = pts.hour.astype("Int64")
pts[["expediente","year","hour","lat","lon","tipo","meteo","serious","killed","on_exclusive_lane","place"]].rename(columns={"tipo":"type","meteo":"weather"}).to_csv(f"{D}/madrid_bike_accidents_2019_2026.csv", index=False)
# accidents by year (people-level stats)
ap["epac"]=ap.tipo_vehiculo.str.contains("EPAC",na=False); ap["serious"]=ap.cod_lesividad.isin(["3","4"]); ap["killed"]=ap.cod_lesividad.eq("4")
by=ap.groupby("year").agg(accidents=("num_expediente","nunique"),people=("num_expediente","size"),seriously_injured_or_killed=("serious","sum"),killed=("killed","sum"),ebike_riders=("epac","sum"),months=("date",lambda s:s.dt.month.nunique())).reset_index()
by.to_csv(f"{D}/madrid_bike_accidents_by_year.csv", index=False); print(by)
# lanes with length
r = shapefile.Reader(f"{E}/infra/Infraestructura_Ciclista.shp", encoding="utf-8"); rows=[]
for sh, rec in zip(r.shapes(), r.records()):
    for i0, i1 in zip(list(sh.parts), list(sh.parts[1:])+[len(sh.points)]):
        p = sh.points[i0:i1]
        if len(p)<2: continue
        L = LineString(p); Ls = L.simplify(6); xs, ys = zip(*Ls.coords); lo, la = tr.transform(xs, ys)
        kind = rec["d_COD_TIPO"].replace("ESCLUSIVA","EXCLUSIVA")
        group = {"VÍA EXCLUSIVA BICI":"Exclusive bike lane","VÍA USO COMPARTIDO":"Shared lane (ciclocarril)","ANILLO VERDE CICLISTA":"Anillo Verde ring","VÍA PREFERENTE BICI":"Bike-priority street","GIROS Y SENTIDOS":"Turns and contraflow"}[kind]
        rows.append({"segment": len(rows)+1, "type": group, "subtype": rec["d_COD_TI_1"].split(", ")[-1].title(), "length_km": round(L.length/1000,3), "path": " ".join(f"{a:.5f},{b:.5f}" for a,b in zip(lo,la))})
pd.DataFrame(rows).to_csv(f"{D}/madrid_bike_infrastructure.csv", index=False)
# station context (live stations + elevation + lane proximity)
st = pd.read_csv(f"{R}/stations_2023_elev.csv")
st.rename(columns={"elev":"elevation_m"}).round({"elevation_m":1}).to_csv(f"{D}/bicimad_2023_station_elevation.csv", index=False)
# rebuild live context
el = json.load(open(f"{E}/misc/station_elevation.json"))
live = pd.read_csv(f"{D}/bicimad_live_stations.csv")
from shapely.strtree import STRtree
from shapely.geometry import Point
fw = Transformer.from_crs(4326, 25830, always_xy=True)
lines=[]; ex=[]
for sh, rec in zip(r.shapes(), r.records()):
    for i0, i1 in zip(list(sh.parts), list(sh.parts[1:])+[len(sh.points)]):
        p = sh.points[i0:i1]
        if len(p)>1:
            lines.append(LineString(p)); ex.append(rec["d_COD_TIPO"].replace("ESCLUSIVA","EXCLUSIVA") in ("VÍA EXCLUSIVA BICI","ANILLO VERDE CICLISTA"))
excl=[l for l,e in zip(lines,ex) if e]; Te=STRtree(excl); Ta=STRtree(lines)
def dmin(tree, geoms, x, y):
    p=Point(x,y); idx=tree.query(p.buffer(400)); return min([geoms[i].distance(p) for i in idx], default=400)
live["elevation_m"] = live.station_id.astype(str).map(lambda k: round(el.get(k,{}).get("elev") or float("nan"),1))
X,Y = fw.transform(live.lon.values, live.lat.values)
live["m_to_exclusive_lane"] = [round(dmin(Te,excl,x,y)) for x,y in zip(X,Y)]
live["m_to_any_bike_infra"] = [round(dmin(Ta,lines,x,y)) for x,y in zip(X,Y)]
live.to_csv(f"{D}/bicimad_station_context.csv", index=False)
# weather
w = pd.read_csv(f"{R}/daily_trips_weather.csv"); w.rename(columns={"prcp":"rain_mm","tmax":"tmax_c","tmin":"tmin_c"}).to_csv(f"{D}/bicimad_daily_trips_weather.csv", index=False)
pd.read_csv(f"{R}/parking.csv").to_csv(f"{D}/madrid_bike_parking.csv", index=False)
pd.read_csv(f"{R}/bike_shops.csv").to_csv(f"{D}/madrid_bike_shops_osm.csv", index=False)
import os
for f in sorted(os.listdir(D)): print(f, os.path.getsize(f"{D}/{f}"))
