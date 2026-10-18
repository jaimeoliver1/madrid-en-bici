"""Profile the Jan-Feb 2023 BiciMAD trip records and the 2024+ daily series; writes an aggregate JSON for 02.

Usage: python3 01_bicimad_eda.py <raw_dir> <eda.json>
(raw_dir holds y2023/bicimad_2023/trips_23_0*.csv, viajes_dia.csv, activos_mes.csv, stations.csv and the gbfs_*.json snapshot)
"""
import sys, json, ast, pandas as pd, numpy as np
D = sys.argv[1]; OUT = sys.argv[2]
R = {}

# ---------- Trip-level Jan-Feb 2023 ----------
t = pd.concat([pd.read_csv(f"{D}/y2023/bicimad_2023/trips_23_0{m}.csv", sep=";", low_memory=False)
               for m in ["1_January","2_February"]], ignore_index=True).dropna(how="all").reset_index(drop=True)
raw_n = len(t)
t["unlock"] = pd.to_datetime(t.unlock_date); t["lock"] = pd.to_datetime(t.lock_date)
def coords(s):
    try: return ast.literal_eval(s)["coordinates"]
    except Exception: return [np.nan, np.nan]
for side in ["unlock","lock"]:
    c = np.array([coords(s) for s in t[f"geolocation_{side}"]], dtype=float)
    t[f"lon_{side}"], t[f"lat_{side}"] = c[:,0], c[:,1]
lat1,lon1,lat2,lon2 = map(np.radians,[t.lat_unlock,t.lon_unlock,t.lat_lock,t.lon_lock])
a = np.sin((lat2-lat1)/2)**2+np.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2
t["km"] = 6371*2*np.arcsin(np.sqrt(a))
t["same_station"] = t.station_unlock == t.station_lock

print(pd.crosstab(t.fleet, t.locktype))
q = {
 "raw_rows": int(raw_n),
 "negative_or_zero_duration": int((t.trip_minutes<=0).sum()),
 "under_1min": int(((t.trip_minutes>0)&(t.trip_minutes<1)).sum()),
 "under_1min_same_station": int(((t.trip_minutes<1)&t.same_station).sum()),
 "over_3h": int((t.trip_minutes>180).sum()),
 "missing_station_unlock": int(t.station_unlock.isna().sum()),
 "missing_station_lock": int(t.station_lock.isna().sum()),
 "free_lock": int((t.locktype=="FREE").sum()),
 "fleet2": int((t.fleet==2).sum()),
 "dur_mismatch_gt2min": int(((t.lock-t.unlock).dt.total_seconds()/60 - t.trip_minutes).abs().gt(2).sum()),
}
# A "valid" trip: 1 min..3 h, OR not a <2min same-station bounce
valid = (t.trip_minutes>=1)&(t.trip_minutes<=180)&~((t.trip_minutes<2)&t.same_station)
q["valid"] = int(valid.sum()); R["quality"] = q
v = t[valid].copy()
print(q)

v["date"]=v.unlock.dt.date; v["hour"]=v.unlock.dt.hour; v["dow"]=v.unlock.dt.dayofweek
daily = v.groupby("date").size()
R["trips23_daily"] = [[str(k), int(x)] for k,x in daily.items()]
ndays_wd = v[v.dow<5].date.nunique(); ndays_we = v[v.dow>=5].date.nunique()
R["hourly"] = {"weekday": (v[v.dow<5].groupby("hour").size().reindex(range(24),fill_value=0)/ndays_wd).round(1).tolist(),
               "weekend": (v[v.dow>=5].groupby("hour").size().reindex(range(24),fill_value=0)/ndays_we).round(1).tolist()}
# heatmap dow x hour avg trips
hm = v.groupby(["dow","hour"]).size().unstack(fill_value=0).reindex(columns=range(24),fill_value=0)
nd = v.groupby("dow").date.nunique()
R["heatmap"] = (hm.div(nd,axis=0)).round(0).astype(int).values.tolist()
# duration hist (1-min bins to 60) & distance hist
R["dur_hist"] = np.histogram(v.trip_minutes.clip(upper=60), bins=np.arange(0,61,2))[0].tolist()
vk = v[~v.same_station & v.km.notna()]
R["km_hist"] = np.histogram(vk.km.clip(upper=8), bins=np.arange(0,8.01,0.25))[0].tolist()
spd = vk.km/(vk.trip_minutes/60)
R["trip_stats"] = {
  "dur_median": round(float(v.trip_minutes.median()),1), "dur_mean": round(float(v.trip_minutes.mean()),1),
  "dur_p90": round(float(v.trip_minutes.quantile(.9)),1),
  "km_median": round(float(vk.km.median()),2), "km_p90": round(float(vk.km.quantile(.9)),2),
  "speed_median": round(float(spd[(spd>0)&(spd<40)].median()),1),
  "same_station_share": round(float(v.same_station.mean()*100),1),
  "bikes": int(v.idBike.nunique()), "stations": int(pd.concat([v.station_unlock,v.station_lock]).nunique()),
  "trips_per_bike_day_median": round(float((v.groupby("idBike").size()/daily.size).median()),2),
  "avg_daily": int(daily.mean()), "weekday_avg": int(daily[[pd.Timestamp(d).dayofweek<5 for d in daily.index]].mean()),
  "weekend_avg": int(daily[[pd.Timestamp(d).dayofweek>=5 for d in daily.index]].mean()),
  "first": str(daily.index.min()), "last": str(daily.index.max()),
}
# stations
name_u = v.groupby("station_unlock").unlock_station_name.agg(lambda s:s.mode().iat[0])
name_l = v.groupby("station_lock").lock_station_name.agg(lambda s:s.mode().iat[0])
names = name_u.combine_first(name_l)
pos_u = v.groupby("station_unlock")[["lat_unlock","lon_unlock"]].median(); pos_u.columns=["lat","lon"]
pos_l = v.groupby("station_lock")[["lat_lock","lon_lock"]].median(); pos_l.columns=["lat","lon"]
pos = pos_u.combine_first(pos_l)
dep = v.groupby("station_unlock").size(); arr = v.groupby("station_lock").size()
st = pd.DataFrame({"name":names,"dep":dep,"arr":arr}).join(pos).fillna({"dep":0,"arr":0})
st["net_per_day"] = ((st.arr-st.dep)/daily.size).round(1)
st["total"]=st.dep+st.arr
st = st.dropna(subset=["lat"])
R["stations23"] = [{"id":int(i),"name":r["name"],"lat":round(r.lat,5),"lon":round(r.lon,5),"dep":int(r.dep),"arr":int(r.arr),"net":float(r.net_per_day)} for i,r in st.iterrows()]
R["top_stations"] = [[r["name"], int(r.dep), int(r.arr)] for _,r in st.sort_values("total",ascending=False).head(12).iterrows()]
R["imbalance_gain"] = [[r["name"], float(r.net_per_day)] for _,r in st.sort_values("net_per_day",ascending=False).head(8).iterrows()]
R["imbalance_loss"] = [[r["name"], float(r.net_per_day)] for _,r in st.sort_values("net_per_day").head(8).iterrows()]
# concentration: share of departures from top 10% stations
dsort = st.dep.sort_values(ascending=False)
R["trip_stats"]["top10pct_station_share"] = round(float(dsort.head(int(len(dsort)*.1)).sum()/dsort.sum()*100),1)
od = vk.groupby(["unlock_station_name","lock_station_name"]).size().sort_values(ascending=False).head(10)
R["top_od"] = [[a,b,int(n)] for (a,b),n in od.items()]
# elevation proxy: lat-based? skip. Hour-of-day net flow for top imbalance stations
# ---------- Daily totals 2024-2026 ----------
dd = pd.read_csv(f"{D}/viajes_dia.csv", sep=";", parse_dates=["FECHA"]).set_index("FECHA").VIAJES
R["daily"] = [[d.strftime("%Y-%m-%d"), int(x)] for d,x in dd.items()]
m = dd.resample("ME").agg(["sum","mean","count"])
R["monthly"] = [[d.strftime("%Y-%m"), int(r["sum"]), int(r["mean"])] for d,r in m.iterrows()]
yoy = []
for d,r in m.iterrows():
    p = d - pd.DateOffset(years=1); p = p + pd.offsets.MonthEnd(0)
    if p in m.index: yoy.append([d.strftime("%Y-%m"), round((r["mean"]/m.loc[p,"mean"]-1)*100,1)])
R["yoy"] = yoy
dow = dd.groupby(dd.index.dayofweek).mean()
R["dow_avg"] = [int(x) for x in dow]
R["records"] = {"max":[dd.idxmax().strftime("%Y-%m-%d"), int(dd.max())], "min":[dd.idxmin().strftime("%Y-%m-%d"), int(dd.min())],
  "total": int(dd.sum()), "days": int(dd.size), "first": dd.index.min().strftime("%Y-%m-%d"), "last": dd.index.max().strftime("%Y-%m-%d"),
  "missing_days": int(pd.date_range(dd.index.min(), dd.index.max()).difference(dd.index).size)}
R["lowest_days"] = [[d.strftime("%Y-%m-%d"), int(x)] for d,x in dd.nsmallest(8).items()]
R["highest_days"] = [[d.strftime("%Y-%m-%d"), int(x)] for d,x in dd.nlargest(8).items()]
# anomalies vs 28-day rolling median
roll = dd.rolling(29, center=True, min_periods=10).median()
# compare against same-weekday median for robustness
z = dd/roll
R["anomalies_low"] = [[d.strftime("%Y-%m-%d"), int(dd[d]), round(float(z[d])*100)] for d in z.nsmallest(10).index]
ann = dd.groupby(dd.index.year).agg(["mean","count"])
R["annual"] = [[int(y), int(r["mean"]), int(r["count"])] for y,r in ann.iterrows()]
# ---------- Active users ----------
u = pd.read_csv(f"{D}/activos_mes.csv", sep=";", parse_dates=["FECHA"]).set_index("FECHA")["USUARIOS ACTIVOS"]
uu = pd.DataFrame({"users":u}); uu["trips"]=m["sum"].reindex(uu.index); uu["days"]=m["count"].reindex(uu.index)
uu["tpu"]=(uu.trips/uu.users).round(2)
R["users"] = [[d.strftime("%Y-%m"), int(r.users), (None if pd.isna(r.trips) else int(r.trips)), (None if pd.isna(r.tpu) else float(r.tpu)), int(r.days) if not pd.isna(r.days) else None] for d,r in uu.iterrows()]
# ---------- Stations: open data CSV + live GBFS ----------
sc = pd.read_csv(f"{D}/stations.csv", sep=";", encoding="utf-8-sig")
R["stations_csv"] = {"n": int(len(sc)), "bases_total": int(sc.TotalBases.sum()), "bases_median": float(sc.TotalBases.median()),
   "state": sc.State.value_counts().to_dict(), "bases_hist": sc.TotalBases.value_counts().sort_index().to_dict()}
gi = pd.DataFrame(json.load(open(f"{D}/gbfs_station_information.json"))["data"]["stations"])
gs_j = json.load(open(f"{D}/gbfs_station_status.json")); gs = pd.DataFrame(gs_j["data"]["stations"])
sysi = json.load(open(f"{D}/gbfs_system_information.json"))["data"]
g = gi[["station_id","name","lat","lon","capacity"]].merge(gs[["station_id","num_bikes_available","num_bikes_disabled","num_docks_available","num_docks_disabled","status","is_renting"]], on="station_id")
g["occ"] = g.num_bikes_available/(g.num_bikes_available+g.num_docks_available).replace(0,np.nan)
ts = pd.Timestamp(gs_j["last_updated"], unit="s", tz="UTC").tz_convert("Europe/Madrid")
active = g[g.status=="IN_SERVICE"]
R["live"] = {"ts": ts.strftime("%Y-%m-%d %H:%M"), "stations": int(len(g)), "in_service": int((g.status=="IN_SERVICE").sum()),
  "status": g.status.value_counts().to_dict(),
  "bikes_available": int(g.num_bikes_available.sum()), "bikes_disabled": int(g.num_bikes_disabled.sum()),
  "docks_available": int(g.num_docks_available.sum()), "docks_disabled": int(g.num_docks_disabled.sum()),
  "capacity": int(g.capacity.sum()), "fleet_ebikes": sysi.get("_vehicle_count",{}).get("_ebike_count"),
  "fleet_mech": sysi.get("_vehicle_count",{}).get("_mechanical_count"),
  "empty": int((active.num_bikes_available==0).sum()), "full": int((active.num_docks_available==0).sum()),
  "low": int((active.occ<0.15).sum()), "high": int((active.occ>0.85).sum()),
  "occ_hist": np.histogram(active.occ.dropna(), bins=np.linspace(0,1,11))[0].tolist(),
  "cap_median": float(g.capacity.median())}
R["live_stations"] = [{"n":r["name"],"lat":round(r.lat,5),"lon":round(r.lon,5),"b":int(r.num_bikes_available),"d":int(r.num_docks_available),"s":r.status} for _,r in g.iterrows()]
json.dump(R, open(OUT,"w"), ensure_ascii=False, default=str)
for k in ["quality","trip_stats","records","annual","live","stations_csv"]: print(k, R[k])
print("top", R["top_stations"][:5]); print("gain", R["imbalance_gain"][:5]); print("loss", R["imbalance_loss"][:5])
print("od", R["top_od"][:5]); print("dow", R["dow_avg"]); print("yoy", R["yoy"]); print("anom", R["anomalies_low"]); print("users", R["users"][-6:])
print("hourly wd", R["hourly"]["weekday"]); print("monthly", R["monthly"])
