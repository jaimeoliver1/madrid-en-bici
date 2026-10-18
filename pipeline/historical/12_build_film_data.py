"""Bundle the 24-hour animation's data (film/data) into site/film-data.js for the in-page player.

Usage: python3 pipeline/historical/12_build_film_data.py film/data site/film-data.js
"""
import sys, json, os
D, OUT = sys.argv[1], sys.argv[2]
m = json.load(open(os.path.join(D, "map.json")))
B = {"stations": m["stations"], "districts": m["districts"], "hourly": m["hourly"], "stats": m["stats"],
     "trips": open(os.path.join(D, "trips.txt")).read().strip(), "routes": open(os.path.join(D, "routes.txt")).read().strip()}
with open(OUT, "w") as f:
    f.write("window.FILM = " + json.dumps(B, ensure_ascii=False, separators=(",", ":")) + ";\n")
print(OUT, os.path.getsize(OUT))
