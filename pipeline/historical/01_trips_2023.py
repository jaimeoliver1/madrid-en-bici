"""Profile the Jan-Feb 2023 BiciMAD trip records: data quality, trip facts and the hourly pattern.

Usage: python3 pipeline/historical/01_trips_2023.py <trips_dir_2023> <data_dir>
Writes <data_dir>/bicimad_2023_summary.csv and bicimad_2023_hourly.csv. Inputs pinned in inputs.json.
A valid trip lasts 1 min to 3 h and is not a return to the same station within 2 min (a failed start).
"""
import sys, ast, csv, os, numpy as np, pandas as pd
import provenance as pv

T, D = sys.argv[1], sys.argv[2]
t = pd.concat([pd.read_csv(f, sep=";", low_memory=False) for f in pv.trips_files(T)], ignore_index=True).dropna(how="all").reset_index(drop=True)
t["unlock"] = pd.to_datetime(t.unlock_date); t["lock"] = pd.to_datetime(t.lock_date)
def coords(s):
    try: return ast.literal_eval(s)["coordinates"]
    except Exception: return [np.nan, np.nan]
for side in ["unlock", "lock"]:
    c = np.array([coords(s) for s in t[f"geolocation_{side}"]], dtype=float)
    t[f"lon_{side}"], t[f"lat_{side}"] = c[:, 0], c[:, 1]
lat1, lon1, lat2, lon2 = map(np.radians, [t.lat_unlock, t.lon_unlock, t.lat_lock, t.lon_lock])
a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
t["km"] = 6371 * 2 * np.arcsin(np.sqrt(a))
t["same_station"] = t.station_unlock == t.station_lock

valid = (t.trip_minutes >= 1) & (t.trip_minutes <= 180) & ~((t.trip_minutes < 2) & t.same_station)
v = t[valid].copy()
v["date"] = v.unlock.dt.date; v["hour"] = v.unlock.dt.hour; v["dow"] = v.unlock.dt.dayofweek
daily = v.groupby("date").size()
weekday = np.array([pd.Timestamp(d).dayofweek < 5 for d in daily.index])
vk = v[~v.same_station & v.km.notna()]
spd = vk.km / (vk.trip_minutes / 60)
nonpos, over3h = int((t.trip_minutes <= 0).sum()), int((t.trip_minutes > 180).sum())
summary = [
    ["records", "Trip records (non-blank rows)", len(t)],
    ["bounces", "Excluded: under 1 min, or back at the same station within 2 min", len(t) - int(valid.sum()) - over3h - nonpos],
    ["over_3h", "Trips over 3 hours", over3h],
    ["nonpositive", "Zero or negative duration", nonpos],
    ["dur_mismatch", "trip_minutes disagrees with timestamps by >2 min", int(((t.lock - t.unlock).dt.total_seconds() / 60 - t.trip_minutes).abs().gt(2).sum())],
    ["dockless", "Trips ending outside a station (fleet 2)", int((t.locktype == "FREE").sum())],
    ["valid", "Trips kept for analysis", int(valid.sum())],
    ["days", "Days covered", int(daily.size)],
    ["avg_daily", "Average trips per day", int(daily.mean())],
    ["weekday_avg", "Average trips per weekday", int(daily[weekday].mean())],
    ["weekend_avg", "Average trips per weekend day", int(daily[~weekday].mean())],
    ["dur_median", "Median duration (min)", round(float(v.trip_minutes.median()), 1)],
    ["dur_p90", "90th percentile duration (min)", round(float(v.trip_minutes.quantile(.9)), 1)],
    ["km_median", "Median straight-line distance (km)", round(float(vk.km.median()), 2)],
    ["speed_median", "Median straight-line speed (km/h)", round(float(spd[(spd > 0) & (spd < 40)].median()), 1)],
    ["same_station_share", "Round trips to the same station (%)", round(float(v.same_station.mean() * 100), 1)],
    ["bikes", "Distinct bikes used", int(v.idBike.nunique())],
    ["stations", "Stations with trips", int(pd.concat([v.station_unlock, v.station_lock]).nunique())],
    ["trips_per_bike_day", "Median trips per bike per day", round(float((v.groupby("idBike").size() / daily.size).median()), 2)],
]
with open(os.path.join(D, "bicimad_2023_summary.csv"), "w", newline="") as f:
    csv.writer(f).writerows([["metric", "label", "value"]] + summary)

nd_wd, nd_we = v[v.dow < 5].date.nunique(), v[v.dow >= 5].date.nunique()
wd = (v[v.dow < 5].groupby("hour").size().reindex(range(24), fill_value=0) / nd_wd).round(1)
we = (v[v.dow >= 5].groupby("hour").size().reindex(range(24), fill_value=0) / nd_we).round(1)
with open(os.path.join(D, "bicimad_2023_hourly.csv"), "w", newline="") as f:
    csv.writer(f).writerows([["hour", "weekday_avg_trips", "weekend_avg_trips"]] + [[h, wd[h], we[h]] for h in range(24)])
print("\n".join(f"{k}: {x}" for k, _, x in summary))
