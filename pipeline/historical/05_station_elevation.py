"""Height of every 2023 BiciMAD station and the bikes it gained or lost per day (the hills chart).

Usage: python3 pipeline/historical/05_station_elevation.py <trips_dir_2023> <data_dir>
Writes <data_dir>/bicimad_2023_station_elevation.csv. Station positions are the median of the trips' recorded
coordinates. Heights are EU-DEM v1.1 (25 m) from the OpenTopoData API, the same source refresh.py uses for today's
stations, so both hills charts share one height scale. The answers are kept in
vendor/station_heights_2023_eudem25m.csv, and the API is only asked about a station that is not in that file.
"""
import sys, os, ast, json, time, urllib.parse, urllib.request, numpy as np, pandas as pd
import provenance as pv

T, D = sys.argv[1], sys.argv[2]
HEIGHTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor", "station_heights_2023_eudem25m.csv")
t = pd.concat([pd.read_csv(f, sep=";", low_memory=False) for f in pv.trips_files(T)], ignore_index=True).dropna(how="all")
same = t.station_unlock == t.station_lock
v = t[(t.trip_minutes >= 1) & (t.trip_minutes <= 180) & ~((t.trip_minutes < 2) & same)].copy()
v["date"] = pd.to_datetime(v.unlock_date).dt.date
def co(s):
    try: return ast.literal_eval(s)["coordinates"]
    except Exception: return [np.nan, np.nan]
for side in ("unlock", "lock"):
    c = np.array([co(s) for s in v[f"geolocation_{side}"]], dtype=float); v[f"lon_{side}"], v[f"lat_{side}"] = c[:, 0], c[:, 1]
names = v.groupby("station_unlock").unlock_station_name.agg(lambda s: s.mode().iat[0]).combine_first(
    v.groupby("station_lock").lock_station_name.agg(lambda s: s.mode().iat[0]))
pu = v.groupby("station_unlock")[["lat_unlock", "lon_unlock"]].median(); pu.columns = ["lat", "lon"]
pl = v.groupby("station_lock")[["lat_lock", "lon_lock"]].median(); pl.columns = ["lat", "lon"]
st = pd.DataFrame({"name": names, "departures": v.groupby("station_unlock").size(), "arrivals": v.groupby("station_lock").size()})
st = st.join(pu.combine_first(pl)).fillna({"departures": 0, "arrivals": 0}).dropna(subset=["lat"])
st = st[st.lat.between(40.3, 40.6) & st.lon.between(-3.8, -3.6)]  # a few records carry no or bogus coordinates
st["net_per_day"] = ((st.arrivals - st.departures) / v.date.nunique()).round(1)
st.index = st.index.astype(int); st.index.name = "station_id"
st["lat"], st["lon"] = st.lat.round(5), st.lon.round(5)

# heights: from the kept file; ask the API only for stations (or positions) it does not have
h = pd.read_csv(HEIGHTS) if os.path.exists(HEIGHTS) else pd.DataFrame(columns=["station_id", "lat", "lon", "elevation_m"])
known = {(int(r.station_id), r.lat, r.lon): r.elevation_m for r in h.itertuples()}
todo = [(i, r.lat, r.lon) for i, r in st.iterrows() if (i, r.lat, r.lon) not in known]
for k in range(0, len(todo), 100):
    chunk = todo[k:k + 100]
    q = "|".join(f"{la:.5f},{lo:.5f}" for _, la, lo in chunk)
    req = urllib.request.Request("https://api.opentopodata.org/v1/eudem25m?locations=" + urllib.parse.quote(q), headers={"User-Agent": "madrid-en-bici"})
    res = json.load(urllib.request.urlopen(req, timeout=60))["results"]
    known.update({key: round(r["elevation"], 1) for key, r in zip(chunk, res)})
    time.sleep(1.2)  # the public API allows one request per second
if todo:
    pd.DataFrame([(i, la, lo, e) for (i, la, lo), e in known.items()], columns=["station_id", "lat", "lon", "elevation_m"]) \
        .sort_values("station_id").to_csv(HEIGHTS, index=False)
    print("asked OpenTopoData for", len(todo), "stations; kept in", HEIGHTS)
st["elevation_m"] = [known[(i, r.lat, r.lon)] for i, r in st.iterrows()]

out = st.reset_index()[["station_id", "name", "elevation_m", "net_per_day", "departures", "arrivals"]].astype({"departures": int, "arrivals": int})
out.sort_values("station_id").to_csv(os.path.join(D, "bicimad_2023_station_elevation.csv"), index=False)
print(len(out), "stations; height", out.elevation_m.min(), "-", out.elevation_m.max(), "m; correlation with net bikes per day",
      round(float(np.corrcoef(out.elevation_m, out.net_per_day)[0, 1]), 2))
