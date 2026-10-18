"""Load the 2019+ bicycle accident files (datos.madrid.es 300110) into pickles for 04.

Usage: python3 03_accidents_load.py <enrich_raw_dir> <work_dir>
"""
import sys, json, glob, math, collections, pandas as pd, numpy as np, shapefile
from pyproj import Transformer
from shapely.geometry import LineString, Point, shape
from shapely.strtree import STRtree
E = sys.argv[1]; R = sys.argv[2]
tr = Transformer.from_crs(25830, 4326, always_xy=True)
# ---------- accidents 2019+ ----------
fr=[]
for f in glob.glob(f"{E}/acc/a_*.csv"):
    for enc in ["utf-8-sig","latin1"]:
        try: d=pd.read_csv(f,sep=";",encoding=enc,dtype=str); break
        except Exception: pass
    if "num_expediente" not in d.columns: continue
    d.columns=[c.replace("tipo_vehículo","tipo_vehiculo").replace("estado_meteorológico","estado_meteorologico") for c in d.columns]
    fr.append(d)
a=pd.concat(fr,ignore_index=True).drop_duplicates()
a["date"]=pd.to_datetime(a.fecha,dayfirst=True,errors="coerce"); a["year"]=a.date.dt.year
a["hour"]=pd.to_numeric(a.hora.str.split(":").str[0],errors="coerce")
def num(v):
    if not isinstance(v,str) or not v.strip() or v=="NULL": return float("nan")
    v=v.strip()
    if "," in v: return float(v.replace(".","").replace(",","."))
    p=v.split(".")
    return float("".join(p[:-1])+"."+p[-1]) if len(p)>2 else float(v)
for c in ["coordenada_x_utm","coordenada_y_utm"]: a[c]=a[c].map(num)
print(a.shape, a.year.value_counts().sort_index().to_dict())
print(a.tipo_vehiculo.value_counts().head(12).to_dict())
print(a.lesividad.value_counts().head(12).to_dict())
print(a.cod_lesividad.value_counts().to_dict())
print(a.tipo_accidente.value_counts().head(10).to_dict())
print(a.estado_meteorologico.value_counts().head(8).to_dict())
print(a.tipo_persona.value_counts().to_dict())
acc=a.groupby("num_expediente").agg(date=("date","first"),year=("year","first"),hour=("hour","first"),x=("coordenada_x_utm","first"),y=("coordenada_y_utm","first"),
   tipo=("tipo_accidente","first"),meteo=("estado_meteorologico","first"),distrito=("distrito","first"),loc=("localizacion","first"),
   persons=("num_expediente","size"),
   killed=("cod_lesividad",lambda s:(s=="4").sum()), serious=("cod_lesividad",lambda s:(s=="3").sum()))
acc=acc.dropna(subset=["x"]); acc=acc[(acc.x>420000)&(acc.x<460000)]
lon,lat=tr.transform(acc.x.values,acc.y.values); acc["lon"]=lon; acc["lat"]=lat
cyc=a[a.tipo_vehiculo.str.contains("Bicicleta",na=False)&(a.tipo_persona=="Conductor")]
print("cyclist driver records",len(cyc), cyc.lesividad.value_counts().head(6).to_dict())
json.dump({"n":len(acc)},open("/dev/null","w"))
acc.to_pickle(f"{R}/acc.pkl"); a.to_pickle(f"{R}/acc_persons.pkl")
