"""Bundle the processed CSVs in data/ into site/data.js, the single data file the website loads.

Usage: python3 pipeline/build_site.py [data] [site/data.js]
"""
import sys, json, os
import numpy as np, pandas as pd

D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "data")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "site", "data.js")
R = lambda f: pd.read_csv(os.path.join(D, f))
fix = lambda s: s.encode("latin1").decode("utf-8") if isinstance(s, str) and "Ã" in s else s
B = {}

# BiciMAD demand
daily = R("bicimad_daily_trips_weather.csv")
daily["date"] = pd.to_datetime(daily.date)
m = daily.groupby(daily.date.dt.to_period("M")).trips.agg(["sum", "mean"]).reset_index()
B["monthly"] = [[str(r.date), int(r["sum"]), int(r["mean"])] for _, r in m.iterrows()]
users = R("bicimad_active_users_monthly.csv")
B["users"] = [[r.month, int(r.active_users)] for _, r in users.iterrows()]
h = R("bicimad_2023_hourly.csv")
B["hourly"] = {"weekday": h.weekday_avg_trips.round().astype(int).tolist(), "weekend": h.weekend_avg_trips.round().astype(int).tolist()}
feb_sep = {int(y): int(daily[(daily.date.dt.year == y) & daily.date.dt.month.between(2, 9)].trips.sum()) for y in sorted(daily.date.dt.year.unique())}
last12 = daily[daily.date > daily.date.max() - pd.Timedelta(days=365)]

# Weather effect (trips vs 29-day centred median)
daily = daily.sort_values("date")
daily["rel"] = daily.trips / daily.trips.rolling(29, center=True, min_periods=10).median() * 100
bands = [(-1, 0, "dry"), (0, 1, "lt1"), (1, 5, "1to5"), (5, 10, "5to10"), (10, 999, "gt10")]
B["rain"] = [[k, int(((daily.rain_mm > lo) & (daily.rain_mm <= hi)).sum()), round(float(daily[(daily.rain_mm > lo) & (daily.rain_mm <= hi)].rel.median()), 1)] for lo, hi, k in bands]
tb = [(-20, 10), (10, 15), (15, 20), (20, 25), (25, 30), (30, 35), (35, 60)]
dry = daily[daily.rain_mm == 0]
B["heat"] = [[lo, hi, int(((dry.tmax_c >= lo) & (dry.tmax_c < hi)).sum()), round(float(dry[(dry.tmax_c >= lo) & (dry.tmax_c < hi)].rel.median()), 1)] for lo, hi in tb]

# Stations now (live snapshot) with elevation and lane distance
st = R("bicimad_station_context.csv")
on = st[st.status == "IN_SERVICE"].copy()
on["occ"] = on.bikes_available / (on.bikes_available + on.docks_available).replace(0, np.nan)
B["stations"] = [[round(r.lat, 5), round(r.lon, 5), int(r.bikes_available), int(r.docks_available), None if pd.isna(r.elevation_m) else round(r.elevation_m), int(r.m_to_exclusive_lane), int(r.station_id)] for _, r in on.iterrows()]
eb = [(0, 600), (600, 620), (620, 640), (640, 660), (660, 680), (680, 900)]
B["elev_live"] = [[lo, hi, int(((on.elevation_m >= lo) & (on.elevation_m < hi)).sum()),
                   round(float(on[(on.elevation_m >= lo) & (on.elevation_m < hi)].occ.mean() * 100), 1),
                   int(((on.elevation_m >= lo) & (on.elevation_m < hi) & (on.bikes_available == 0)).sum())] for lo, hi in eb]
se = R("bicimad_2023_station_elevation.csv")
B["elev_flow"] = [[round(r.elevation_m), r.net_per_day, r["name"]] for _, r in se.iterrows()]
B["elev_corr"] = round(float(np.corrcoef(se.elevation_m, se.net_per_day)[0, 1]), 2)
B["elev_bands_2023"] = [[lo, hi, round(float(se[(se.elevation_m >= lo) & (se.elevation_m < hi)].net_per_day.mean()), 2)] for lo, hi in eb]

# 2023 trip-level facts
summ = R("bicimad_2023_summary.csv").set_index("metric").value
B["trip"] = {k: float(summ[k]) for k in ["dur_median", "km_median", "speed_median", "trips_per_bike_day", "weekday_avg", "weekend_avg"]}

# Districts
dist = R("madrid_districts_cycling.csv")
shp = R("madrid_districts_shapes.csv").set_index("code")
B["districts"] = [{"name": r.district, "code": int(r.code), "pop": int(r.population), "area": r.area_km2, "stations": int(r.stations), "docks": int(r.docks),
                   "excl_km": r.exclusive_km, "infra_km": r.all_infra_km, "acc": int(r.accidents), "racks": int(r.bike_racks),
                   "rings": shp.loc[r.code, "rings"]} for _, r in dist.iterrows()]

# Barrios: BiciMAD station density
bar = R("madrid_barrios_bicimad.csv")
B["barrios"] = [[r.barrio, r.district, int(r.population), r.area_km2, int(r.stations), r.rings] for _, r in bar.iterrows()]
P = bar.population.sum()
B["barrio_cov"] = {str(t): round(float(bar[bar.stations_per_km2 >= t].population.sum() / P * 100), 1) for t in (1, 4, 10)}
B["barrio_cov"]["none"] = round(float(bar[bar.stations == 0].population.sum() / P * 100), 1)

# Lanes, simplified to every other vertex
lanes = R("madrid_bike_infrastructure.csv")
code = {"Exclusive bike lane": "x", "Anillo Verde ring": "v", "Bike-priority street": "p", "Shared lane (ciclocarril)": "s", "Turns and contraflow": "s"}
def thin(p):
    pts = p.split(" ")
    keep = pts[::2] + ([pts[-1]] if len(pts) % 2 == 0 else [])
    return " ".join(",".join(f"{float(v):.4f}" for v in q.split(",")) for q in keep)
B["lanes"] = [[code[r.type], thin(r.path)] for _, r in lanes.iterrows()]
km = lanes.groupby("type").length_km.sum()
B["lane_km"] = {code[k]: round(float(v)) for k, v in km.items() if code[k] != "s" or k.startswith("Shared")}

# Accidents
acc = R("madrid_bike_accidents.csv")
B["acc_points"] = [[round(r.lat, 4), round(r.lon, 4), int(r.serious or r.killed)] for _, r in acc.iterrows()]
ay = R("madrid_bike_accidents_by_year.csv")
B["acc_year"] = [[int(r.year), int(r.accidents), round(r.ebike_riders / r.people * 100, 1), int(r.months), int(r.seriously_injured_or_killed), int(r.killed)] for _, r in ay.iterrows()]
B["acc_hour"] = acc.hour.dropna().astype(int).value_counts().reindex(range(24), fill_value=0).tolist()
B["acc_on_excl"] = round(float(acc.on_exclusive_lane.mean() * 100))
acc["gx"] = (acc.lat / 0.00135).astype(int); acc["gy"] = (acc.lon / 0.00177).astype(int)
hs = acc.groupby(["gx", "gy"]).agg(n=("lat", "size"), place=("place", lambda s: s.mode().iat[0]), lat=("lat", "mean"), lon=("lon", "mean")).sort_values("n", ascending=False).head(8)
B["hotspots"] = [[r.place, int(r.n), round(r.lat, 5), round(r.lon, 5)] for _, r in hs.iterrows()]

# Counters
cn = R("madrid_bike_counters.csv").dropna(subset=["avg_daily_bikes_2023"])
cn["street"] = cn.street.map(fix)
cn = cn.drop_duplicates("street")
B["counters"] = [[r.street, int(r.avg_daily_bikes_2023), round(r.lat, 5), round(r.lon, 5)] for _, r in cn.head(10).iterrows()]

# Routes along streets for the most common trips (optional until routing has run)
# Routes: shares over every routed 2023 trip (11_all_routes.py); map shows the most used pairs
rp = os.path.join(D, "bicimad_2023_top_routes_routed.csv")
if os.path.exists(rp):
    rt = R("bicimad_2023_top_routes_routed.csv").head(300)
    ra = R("bicimad_2023_routes_all.csv.gz") if os.path.exists(os.path.join(D, "bicimad_2023_routes_all.csv.gz")) else rt
    w = ra.trips
    B["routes"] = {"pairs": int(len(ra)), "trips": int(w.sum()), "all_trips": int(w.sum()) if len(ra) > len(rt) else 323872,
                   "share_excl": round(float((ra.share_exclusive * w).sum() / w.sum()), 1),
                   "share_any": round(float((ra.share_any * w).sum() / w.sum()), 1),
                   "hist": np.histogram(ra.share_exclusive, bins=[0, 10, 25, 50, 75, 101], weights=w)[0].astype(int).tolist(),
                   "paths": [[int(r.trips), r.share_exclusive, " ".join(",".join(f"{float(v):.4f}" for v in q.split(",")) for q in r.path.split(" "))] for _, r in rt.iterrows()]}

# Headline numbers
pop = int(dist.population.sum()); area = float(dist.area_km2.sum())
meta = json.load(open(os.path.join(D, "refresh_meta.json"))) if os.path.exists(os.path.join(D, "refresh_meta.json")) else {}
st_city = int(dist.stations.sum()); docks = int(dist.docks.sum()); fleet = int(meta.get("fleet") or 9421)
B["k"] = {
    "population": pop, "area_km2": round(area), "stations": st_city, "stations_outside": int(len(on)) - st_city, "docks": docks, "fleet": fleet,
    "feb_sep": feb_sep, "trips_last12": int(last12.trips.sum()), "avg_day_last12": int(last12.trips.mean()),
    "record_day": [daily.loc[daily.trips.idxmax(), "date"].strftime("%Y-%m-%d"), int(daily.trips.max())],
    "trips_per_bike_day": round(float(last12.trips.mean() / fleet), 1),
    "bikes_per_1000": round(fleet / pop * 1000, 1), "docks_per_1000": round(docks / pop * 1000, 1),
    "stations_per_km2_city": round(st_city / area, 2),
    "excl_km": round(float(dist.exclusive_km.sum())), "all_infra_km": round(float(dist.all_infra_km.sum())),
    "excl_km_per_100k": round(float(dist.exclusive_km.sum()) / pop * 1e5, 1),
    "stations_near_excl_pct": round(float((on.m_to_exclusive_lane <= 50).mean() * 100)),
    "empty_now": int((on.bikes_available == 0).sum()), "snapshot": meta.get("snapshot", "2026-10-17 15:49"), "refreshed": meta.get("refreshed_at", "")[:10], "acc_last": meta.get("accidents_latest", "2026-08-31"),
    "daily_first": daily.date.min().strftime("%Y-%m-%d"), "daily_last": daily.date.max().strftime("%Y-%m-%d"),
    "racks": int(len(R("madrid_bike_parking.csv"))), "users_last": int(users.active_users.iloc[-1]), "users_last_month": users.month.iloc[-1],
}
with open(OUT, "w") as f:
    f.write("window.MC = " + json.dumps(B, ensure_ascii=False, separators=(",", ":")) + ";\n")
print(OUT, os.path.getsize(OUT), json.dumps(B["k"], ensure_ascii=False))
