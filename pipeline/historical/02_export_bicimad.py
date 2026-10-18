"""Export the aggregates from 01 as the bicimad_2023_* CSVs in data/.

Usage: python3 02_export_bicimad.py <eda.json> <data_dir> <gbfs_station_information.json> <gbfs_station_status.json>
"""
import sys, json, csv, os
R = json.load(open(sys.argv[1])); O = sys.argv[2]; os.makedirs(O, exist_ok=True)
def w(name, header, rows):
    with open(f"{O}/{name}", "w", newline="") as f:
        c = csv.writer(f); c.writerow(header); c.writerows(rows)
w("bicimad_daily_trips_2024_2026.csv", ["date","trips"], R["daily"])
w("bicimad_active_users_monthly.csv", ["month","active_users"], [[m,u] for m,u,*_ in R["users"]])
w("bicimad_2023_hourly.csv", ["hour","weekday_avg_trips","weekend_avg_trips"],
  [[h, R["hourly"]["weekday"][h], R["hourly"]["weekend"][h]] for h in range(24)])
rows = [["duration_min", i*2, i*2+2, n] for i,n in enumerate(R["dur_hist"])] + \
       [["distance_km", round(i*.25,2), round(i*.25+.25,2), n] for i,n in enumerate(R["km_hist"])]
w("bicimad_2023_distributions.csv", ["measure","bin_start","bin_end","trips"], rows)
w("bicimad_2023_stations.csv", ["station_id","name","lat","lon","departures","arrivals","net_per_day"],
  [[s["id"],s["name"],s["lat"],s["lon"],s["dep"],s["arr"],s["net"]] for s in R["stations23"]])
w("bicimad_2023_top_routes.csv", ["route","from_station","to_station","trips"], [[f"{a} → {b}",a,b,n] for a,b,n in R["top_od"]])
q, s = R["quality"], R["trip_stats"]
summ = [
 ["records","Trip records (non-blank rows)",q["raw_rows"]],
 ["bounces","Same-station returns under 2 min (failed starts)",q["raw_rows"]-q["valid"]-q["over_3h"]-q["negative_or_zero_duration"]],
 ["over_3h","Trips over 3 hours",q["over_3h"]],
 ["nonpositive","Zero or negative duration",q["negative_or_zero_duration"]],
 ["dur_mismatch","trip_minutes disagrees with timestamps by >2 min",q["dur_mismatch_gt2min"]],
 ["dockless","Trips ending outside a station (fleet 2)",q["free_lock"]],
 ["valid","Trips kept for analysis",q["valid"]],
 ["days","Days covered",len(R["trips23_daily"])],
 ["avg_daily","Average trips per day",s["avg_daily"]],
 ["weekday_avg","Average trips per weekday",s["weekday_avg"]],
 ["weekend_avg","Average trips per weekend day",s["weekend_avg"]],
 ["dur_median","Median duration (min)",s["dur_median"]],
 ["dur_p90","90th percentile duration (min)",s["dur_p90"]],
 ["km_median","Median straight-line distance (km)",s["km_median"]],
 ["speed_median","Median straight-line speed (km/h)",s["speed_median"]],
 ["same_station_share","Round trips to the same station (%)",s["same_station_share"]],
 ["bikes","Distinct bikes used",s["bikes"]],
 ["stations","Stations with trips",s["stations"]],
 ["trips_per_bike_day","Median trips per bike per day",s["trips_per_bike_day_median"]],
]
w("bicimad_2023_summary.csv", ["metric","label","value"], summ)
st = {x["n"]:x for x in R["live_stations"]}
gi = json.load(open(sys.argv[3]))["data"]["stations"]; gs = {x["station_id"]:x for x in json.load(open(sys.argv[4]))["data"]["stations"]}
lr = []
for x in gi:
    y = gs.get(x["station_id"]); 
    if not y: continue
    lr.append([x["station_id"], x["name"], round(x["lat"],5), round(x["lon"],5), x["capacity"], y["num_bikes_available"], y["num_docks_available"], y["num_bikes_disabled"], y["status"]])
w("bicimad_live_stations.csv", ["station_id","name","lat","lon","capacity","bikes_available","docks_available","bikes_disabled","status"], lr)
print(R["live"]["ts"])
