"""Select the trips of Thursday 12 Jan 2023 and project stations and district outlines onto the 1920x1080 film frame.

Usage: python3 film_01_day_data.py <raw_dir> <out_dir>
"""
import sys, json, ast, math, pandas as pd, numpy as np
D, OUT = sys.argv[1], sys.argv[2]
t = pd.concat([pd.read_csv(f"{D}/y2023/bicimad_2023/trips_23_0{m}.csv", sep=";", low_memory=False) for m in ["1_January","2_February"]], ignore_index=True).dropna(how="all")
t["unlock"]=pd.to_datetime(t.unlock_date); t["lock"]=pd.to_datetime(t.lock_date)
same=t.station_unlock==t.station_lock
v=t[(t.trip_minutes>=1)&(t.trip_minutes<=180)&~((t.trip_minutes<2)&same)].dropna(subset=["station_unlock","station_lock"]).copy()
def co(s):
    try: return ast.literal_eval(s)["coordinates"]
    except Exception: return [np.nan,np.nan]
# station positions from all valid trips (median)
u=np.array([co(s) for s in v.geolocation_unlock]); v["lon_u"],v["lat_u"]=u[:,0],u[:,1]
l=np.array([co(s) for s in v.geolocation_lock]); v["lon_l"],v["lat_l"]=l[:,0],l[:,1]
pu=v.groupby("station_unlock")[["lon_u","lat_u"]].median(); pu.columns=["lon","lat"]
pl=v.groupby("station_lock")[["lon_l","lat_l"]].median(); pl.columns=["lon","lat"]
pos=pu.combine_first(pl).dropna()
pos=pos[(pos.lat>40.3)&(pos.lat<40.6)&(pos.lon>-3.8)&(pos.lon<-3.6)]
print("stations",len(pos), pos.lat.min(),pos.lat.max(),pos.lon.min(),pos.lon.max())
DAY=pd.Timestamp("2023-01-12")
day_all=v[(v.unlock>=DAY)&(v.unlock<DAY+pd.Timedelta(days=1))]
w=v[(v.unlock>=DAY-pd.Timedelta(hours=1))&(v.lock>DAY)&(v.unlock<DAY+pd.Timedelta(days=1))]
w=w[w.station_unlock.isin(pos.index)&w.station_lock.isin(pos.index)]
# projection: fit station bbox to height 1000 px, centred at x=1250
lat0=pos.lat.mean(); k=math.cos(math.radians(lat0))
H=1000; top=40
dy=pos.lat.max()-pos.lat.min(); s=H/dy
cx_lon=(pos.lon.max()+pos.lon.min())/2
def P(lon,lat): return (1250+(lon-cx_lon)*k*s, top+(pos.lat.max()-lat)*s)
idx={sid:i for i,sid in enumerate(pos.index)}
stations=[[round(c,1) for c in P(r.lon,r.lat)] for _,r in pos.iterrows()]
print("x range", min(p[0] for p in stations), max(p[0] for p in stations))
def b36(n,w):
    d="0123456789abcdefghijklmnopqrstuvwxyz"; o=""
    for _ in range(w): o=d[n%36]+o; n//=36
    assert n==0; return o
rec=[]
for _,r in w.sort_values("unlock").iterrows():
    st=int((r.unlock-DAY).total_seconds())+3600; du=max(30,int((r.lock-r.unlock).total_seconds()))
    if du>10800: continue
    rec.append(b36(st,4)+b36(du,3)+b36(idx[r.station_unlock],2)+b36(idx[r.station_lock],2))
txt="".join(rec); open(f"{OUT}/trips.txt","w").write(txt)
print("trips encoded",len(rec),"bytes",len(txt))
# moving-bike curve for stats
secs=np.arange(0,86400,60)
st=((w.unlock-DAY).dt.total_seconds()).values; en=((w.lock-DAY).dt.total_seconds()).values
moving=np.array([((st<=x)&(en>x)).sum() for x in secs])
pk=int(moving.argmax())
hourly=day_all.groupby(day_all.unlock.dt.hour).size().reindex(range(24),fill_value=0)
stats={"date":"Thursday 12 January 2023","trips":int(len(day_all)),"bikes":int(day_all.idBike.nunique()),
 "stations":int(pd.concat([day_all.station_unlock,day_all.station_lock]).nunique()),
 "peakMoving":int(moving.max()),"peakAt":f"{pk//60:02d}:{pk%60:02d}","busiestHour":int(hourly.idxmax()),"busiestHourTrips":int(hourly.max()),
 "medianMin":round(float(day_all.trip_minutes.median()),1)}
print(stats)
# basemap: barrios, projected, clipped by frame later with SVG
g=json.load(open(f"{D}/geo/madrid_barrios.geojson"))
def rdp(pts,eps):
    if len(pts)<3: return pts
    a,b=np.array(pts[0]),np.array(pts[-1]); ab=b-a; n=np.hypot(*ab)
    P_=np.array(pts)
    Q=P_-a; d=np.abs(ab[0]*Q[:,1]-ab[1]*Q[:,0])/n if n>0 else np.hypot(Q[:,0],Q[:,1])
    i=int(d.argmax())
    if d[i]>eps: return rdp(pts[:i+1],eps)[:-1]+rdp(pts[i:],eps)
    return [pts[0],pts[-1]]
paths=[]
for f in g["features"]:
    geom=f["geometry"]; polys=geom["coordinates"] if geom["type"]=="MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        for ring in poly[:1]:
            pts=[P(x,y) for x,y in ring]
            xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
            if max(xs)<-50 or min(xs)>1970 or max(ys)<-50 or min(ys)>1130: continue
            pts=rdp(pts,1.2)
            paths.append("M"+"L".join(f"{p[0]:.0f} {p[1]:.0f}" for p in pts)+"Z")
path="".join(paths)
json.dump({"stations":stations,"stats":stats,"hourly":[int(x) for x in hourly],"moving":[int(x) for x in moving[::10]],"districts":path},open(f"{OUT}/map.json","w"),separators=(",",":"))
print("barrio paths",len(paths),"map.json bytes",len(open(f"{OUT}/map.json").read()))
