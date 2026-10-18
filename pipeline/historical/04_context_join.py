"""Join accidents, bike lanes, station elevation, racks, shops and weather to BiciMAD stations; prints the headline findings.

Usage: python3 04_context_join.py <enrich_raw_dir> <work_dir> <raw_dir>
"""
import sys, json, math, collections, pandas as pd, numpy as np, shapefile
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
E, R, RAW = sys.argv[1], sys.argv[2], sys.argv[3]
tr = Transformer.from_crs(25830, 4326, always_xy=True); fw = Transformer.from_crs(4326, 25830, always_xy=True)
acc = pd.read_pickle(f"{R}/acc.pkl"); ap = pd.read_pickle(f"{R}/acc_persons.pkl")
out = {}
# --- accidents by year
ap["epac"] = ap.tipo_vehiculo.str.contains("EPAC", na=False)
ap["serious"] = ap.cod_lesividad.isin(["3","4"]); ap["killed"] = ap.cod_lesividad.eq("4")
by = ap.groupby("year").agg(people=("num_expediente","size"), accidents=("num_expediente","nunique"), serious=("serious","sum"), killed=("killed","sum"), epac=("epac","sum"),
                           months=("date", lambda s: s.dt.month.nunique()))
by["epac_share"] = (by.epac/by.people*100).round(1)
out["acc_year"] = by.reset_index().to_dict("records"); print(by)
ap["hour"]=pd.to_numeric(ap.hour,errors="coerce")
h = acc.groupby("hour").size().reindex(range(24), fill_value=0); out["acc_hour"]=h.tolist()
out["acc_type"] = acc.tipo.value_counts().head(8).to_dict()
out["acc_meteo"] = acc.meteo.value_counts().to_dict()
# --- bike infrastructure
r = shapefile.Reader(f"{E}/infra/Infraestructura_Ciclista.shp", encoding="utf-8")
lines=[]; kinds=[]
for sh, rec in zip(r.shapes(), r.records()):
    for i0, i1 in zip(list(sh.parts), list(sh.parts[1:])+[len(sh.points)]):
        pts = sh.points[i0:i1]
        if len(pts)>1: lines.append(LineString(pts)); kinds.append((rec["d_COD_TIPO"].replace("ESCLUSIVA","EXCLUSIVA"), rec["d_COD_TI_1"].split(", ")[-1]))
km = collections.defaultdict(float); km2 = collections.defaultdict(float)
for L,k in zip(lines,kinds): km[k[0]] += L.length/1000; km2[k[1]] += L.length/1000
out["infra_km"] = {k: round(v,1) for k,v in sorted(km.items(), key=lambda x:-x[1])}
out["infra_km_detail"] = {k: round(v,1) for k,v in sorted(km2.items(), key=lambda x:-x[1])}
print(out["infra_km"], out["infra_km_detail"])
excl = [L for L,k in zip(lines,kinds) if k[0] in ("VÍA EXCLUSIVA BICI","ANILLO VERDE CICLISTA")]
anyl = lines
T_ex = STRtree(excl); T_any = STRtree(anyl)
def near(tree, geoms, x, y, d):
    p = Point(x, y); idx = tree.query(p.buffer(d))
    return any(geoms[i].distance(p) <= d for i in idx)
# accidents on/near infrastructure (within 15 m)
acc["on_excl"] = [near(T_ex, excl, x, y, 15) for x,y in zip(acc.x, acc.y)]
acc["on_any"] = [near(T_any, anyl, x, y, 15) for x,y in zip(acc.x, acc.y)]
out["acc_on_infra"] = {"accidents": int(len(acc)), "within15m_exclusive": int(acc.on_excl.sum()), "within15m_any": int(acc.on_any.sum())}
print(out["acc_on_infra"])
# hotspots: 150 m grid
acc["gx"] = (acc.x//150).astype(int); acc["gy"] = (acc.y//150).astype(int)
hs = acc.groupby(["gx","gy"]).agg(n=("loc","size"), loc=("loc", lambda s: s.mode().iat[0]), lon=("lon","mean"), lat=("lat","mean")).sort_values("n", ascending=False)
out["hotspots"] = [{"place": r_["loc"].title(), "accidents": int(r_.n), "lat": round(r_.lat,5), "lon": round(r_.lon,5)} for _, r_ in hs.head(12).iterrows()]
print(out["hotspots"][:6])
# --- stations: elevation, lanes, parking, net flow
el = json.load(open(f"{E}/misc/station_elevation.json"))
st23 = pd.read_csv(f"{RAW}/../data/bicimad_2023_stations.csv")
live = pd.read_csv(f"{RAW}/../data/bicimad_live_stations.csv")
st = pd.DataFrame([{"station_id":int(k), **v} for k,v in el.items()])
st = st.merge(live[["station_id","capacity","bikes_available","docks_available","status"]], on="station_id", how="left")
X, Y = fw.transform(st.lon.values, st.lat.values); st["x"]=X; st["y"]=Y
st["lane_exclusive_50m"] = [near(T_ex, excl, x, y, 50) for x,y in zip(X,Y)]
st["lane_any_50m"] = [near(T_any, anyl, x, y, 50) for x,y in zip(X,Y)]
# nearest-name match 2023 station flows by coordinate (within 60 m)
s23 = st23.copy(); X2, Y2 = fw.transform(s23.lon.values, s23.lat.values); s23["x"]=X2; s23["y"]=Y2
from scipy.spatial import cKDTree
kd = cKDTree(np.c_[X,Y]); dist, ix = kd.query(np.c_[X2,Y2])
s23["elev"] = np.where(dist<80, st.elev.values[ix], np.nan)
s23 = s23.dropna(subset=["elev"])
corr = float(np.corrcoef(s23.elev, s23.net_per_day)[0,1])
s23["elev_band"] = pd.cut(s23.elev, [0,600,620,640,660,680,800], labels=["<600","600–620","620–640","640–660","660–680","680+"])
band = s23.groupby("elev_band", observed=True).agg(stations=("name","size"), net_per_day=("net_per_day","mean")).round(2)
out["elev_flow"] = {"stations_matched": int(len(s23)), "corr": round(corr,2), "bands": [[str(i), int(r_.stations), float(r_.net_per_day)] for i,r_ in band.iterrows()]}
print(out["elev_flow"])
s23[["station_id","name","elev","net_per_day","departures","arrivals"]].to_csv(f"{R}/stations_2023_elev.csv", index=False)
# live occupancy vs elevation
lv = st[st.status=="IN_SERVICE"].copy(); lv["occ"] = lv.bikes_available/(lv.bikes_available+lv.docks_available).replace(0,np.nan)
lv["elev_band"] = pd.cut(lv.elev, [0,600,620,640,660,680,800], labels=["<600","600–620","620–640","640–660","660–680","680+"])
out["elev_live"] = [[str(i), int(g_.shape[0]), round(float(g_.occ.mean()*100),1), int((g_.bikes_available==0).sum())] for i,g_ in lv.groupby("elev_band", observed=True)]
print(out["elev_live"])
out["stations_lanes"] = {"stations": int(len(st)), "exclusive_50m": int(st.lane_exclusive_50m.sum()), "any_50m": int(st.lane_any_50m.sum())}
print(out["stations_lanes"])
# parking racks
pk = pd.read_csv(f"{E}/misc/aparcabicis.csv", sep=";", encoding="utf-8-sig", dtype=str)
pk = pk[pk.ESTADO.eq("OPERATIVO")] if "ESTADO" in pk else pk
pk["x"]=pd.to_numeric(pk.COORD_GIS_X,errors="coerce"); pk["y"]=pd.to_numeric(pk.COORD_GIS_Y,errors="coerce"); pk=pk.dropna(subset=["x"])
pk_d = pk.DISTRITO.value_counts()
out["parking"] = {"racks": int(len(pk)), "by_district": pk_d.head(21).to_dict()}
pl, pa = tr.transform(pk.x.values, pk.y.values); pk["lon"]=pl; pk["lat"]=pa
pk[["lat","lon","DISTRITO"]].round(5).to_csv(f"{R}/parking.csv", index=False)
# bike shops
pois = json.load(open(f"{E}/misc/osm_bike_pois.json"))["elements"]
shops = [{"name": e["tags"].get("name",""), "kind": e["tags"].get("shop") or e["tags"].get("amenity"),
          "lat": round(e.get("lat", e.get("center",{}).get("lat",0)),5), "lon": round(e.get("lon", e.get("center",{}).get("lon",0)),5)} for e in pois]
out["shops"] = {"total": len(shops), "repair_stations": sum(s["kind"]=="bicycle_repair_station" for s in shops)}
pd.DataFrame(shops).to_csv(f"{R}/bike_shops.csv", index=False)
# accidents per district vs lanes km per district? (district polygons not available) -> accidents per district
out["acc_district"] = acc.distrito.value_counts().to_dict()
# --- weather vs trips
w = pd.read_csv(f"{E}/misc/ghcn_retiro.csv", dtype=str)
w["date"]=pd.to_datetime(w.DATE); w["prcp"]=pd.to_numeric(w.PRCP,errors="coerce")/10; w["tmax"]=pd.to_numeric(w.TMAX,errors="coerce")/10; w["tmin"]=pd.to_numeric(w.TMIN,errors="coerce")/10
w = w[w.date>="2024-02-01"][["date","prcp","tmax","tmin"]]
dd = pd.read_csv(f"{RAW}/viajes_dia.csv", sep=";", parse_dates=["FECHA"]).rename(columns={"FECHA":"date","VIAJES":"trips"})
m = dd.merge(w, on="date", how="left")
m["dow"]=m.date.dt.dayofweek; m["wk"]=m.dow<5
m["base"] = m.trips.rolling(29, center=True, min_periods=10).median()
m["rel"] = m.trips/m.base*100
m["rain_band"] = pd.cut(m.prcp, [-0.1,0.0,1,5,10,200], labels=["Dry","Under 1 mm","1–5 mm","5–10 mm","10 mm+"])
rb = m.dropna(subset=["prcp"]).groupby("rain_band", observed=True).agg(days=("trips","size"), rel=("rel","median")).round(1)
out["rain"] = [[str(i), int(r_.days), float(r_.rel)] for i,r_ in rb.iterrows()]
m["t_band"] = pd.cut(m.tmax, [-10,10,15,20,25,30,35,50], labels=["<10°","10–15°","15–20°","20–25°","25–30°","30–35°","35°+"])
tb = m.dropna(subset=["tmax"]).query("prcp==0").groupby("t_band", observed=True).agg(days=("trips","size"), rel=("rel","median")).round(1)
out["temp"] = [[str(i), int(r_.days), float(r_.rel)] for i,r_ in tb.iterrows()]
out["weather_coverage"] = {"days": int(m.prcp.notna().sum()), "of": int(len(m))}
print(out["rain"], out["temp"], out["weather_coverage"])
m[["date","trips","prcp","tmax","tmin"]].assign(date=m.date.dt.strftime("%Y-%m-%d")).to_csv(f"{R}/daily_trips_weather.csv", index=False)
# --- outputs for maps
acc_out = acc[["lat","lon","year","hour","tipo","meteo","serious","killed","on_excl"]].copy()
acc_out["lat"]=acc_out.lat.round(5); acc_out["lon"]=acc_out.lon.round(5)
acc_out.to_csv(f"{R}/accidents_points.csv", index_label="expediente")
# lanes simplified in lon/lat
feat=[]
for L,k in zip(lines,kinds):
    Ls = L.simplify(8)
    xs, ys = zip(*Ls.coords); lo, la = tr.transform(xs, ys)
    feat.append({"kind": k[0], "sub": k[1], "path": ";".join(f"{a:.5f},{b:.5f}" for a,b in zip(lo,la))})
pd.DataFrame(feat).to_csv(f"{R}/bike_lanes.csv", index=False)
json.dump(out, open(f"{R}/enrich.json","w"), ensure_ascii=False, indent=1, default=str)
