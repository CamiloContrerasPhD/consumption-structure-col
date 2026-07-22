# -*- coding: utf-8 -*-
"""Centro-periferia: links political lean with a composite ACCESS index per municipio.
Pillars (all by DANE code): chain-retail density (OSM, per 1k votes), fixed-internet (MinTIC 2023Q3,
per 1k votes), upper-secondary net coverage (MEN 2024, cobertura_neta_media, capped 100).
Composite = mean of z-scores of the three pillars. Higher = more central/served.
Outputs: site/cp.js (window.CP) + printed correlations and regional scorecard.
"""
import json, os, csv, math
from collections import defaultdict, Counter

BASE = os.path.join(os.path.dirname(__file__), "..")
P = lambda *a: os.path.join(BASE, *a)

DANE = {"05":"Andina","08":"Caribe","11":"Andina","13":"Caribe","15":"Andina","17":"Andina","18":"Amazonia",
 "19":"Pacifico","20":"Caribe","23":"Caribe","25":"Andina","27":"Pacifico","41":"Andina","44":"Caribe",
 "47":"Caribe","50":"Orinoquia","52":"Pacifico","54":"Andina","63":"Andina","66":"Andina","68":"Andina",
 "70":"Caribe","73":"Andina","76":"Pacifico","81":"Orinoquia","85":"Orinoquia","86":"Amazonia",
 "88":"Caribe","91":"Amazonia","94":"Amazonia","95":"Amazonia","97":"Amazonia","99":"Orinoquia"}

# internet accesses by DANE municipio
inet = {x["cod_municipio"]: float(x["acc"])
        for x in json.load(open(P("data","raw","internet_municipio_2023q3.json"), encoding="utf-8"))}
# education: upper-secondary net coverage (cap 100), by DANE municipio
edu = {}
for x in json.load(open(P("data","raw","educacion_municipio_2024.json"), encoding="utf-8")):
    v = x.get("cobertura_neta_media")
    if v not in (None, ""):
        edu[x["c_digo_municipio"]] = min(100.0, float(v))

# stores per municipio id
stores = Counter()
for r in csv.DictReader(open(P("data","processed","stores_geo.csv"), encoding="utf-8")):
    stores[r["divipola"]] += 1

# join on muni_index
rows = []
for r in csv.DictReader(open(P("data","processed","muni_index.csv"), encoding="utf-8")):
    dv = r["divipola"]; votval = int(r["votval"])
    if votval < 1: continue
    acc = inet.get(dv)
    rows.append({"id":dv,"muni":r["muni"],"region":DANE.get(dv[:2],"?"),"lean":float(r["lean"]),
                 "votval":votval,"stores":stores.get(dv,0),
                 "cons":stores.get(dv,0)/(votval/1000),
                 "inet":(acc/(votval/1000)) if acc is not None else None,
                 "edu":edu.get(dv)})

# ---- composite ACCESS index = mean z-score of (cons, inet, edu) ----
full = [x for x in rows if x["inet"] is not None and x["edu"] is not None]
def zstats(key):
    v=[x[key] for x in full]; m=sum(v)/len(v)
    sd=math.sqrt(sum((t-m)**2 for t in v)/len(v)); return m,(sd or 1)
ms={k:zstats(k) for k in ("cons","inet","edu")}
for x in full:
    z=[(x[k]-ms[k][0])/ms[k][1] for k in ("cons","inet","edu")]
    x["idx"]=round(sum(z)/3,3)
print(f"municipios={len(rows)} con_internet={sum(1 for x in rows if x['inet'] is not None)} "
      f"con_edu={sum(1 for x in rows if x['edu'] is not None)} completos={len(full)}")

# ---- correlations (Spearman, municipios with electoral weight) ----
def spearman(a,b):
    n=len(a)
    def rank(v):
        order=sorted(range(n),key=lambda i:v[i]); rk=[0]*n
        for pos,i in enumerate(order): rk[i]=pos
        return rk
    ra,rb=rank(a),rank(b); ma=sum(ra)/n; mb=sum(rb)/n
    num=sum((ra[i]-ma)*(rb[i]-mb) for i in range(n))
    den=math.sqrt(sum((ra[i]-ma)**2 for i in range(n))*sum((rb[i]-mb)**2 for i in range(n)))
    return num/den if den else 0
big=[x for x in full if x["votval"]>=15000]
L=[x["lean"] for x in big]
corr={
 "lean_cons":round(spearman(L,[x["cons"] for x in big]),3),
 "lean_inet":round(spearman(L,[x["inet"] for x in big]),3),
 "lean_edu": round(spearman(L,[x["edu"]  for x in big]),3),
 "lean_idx": round(spearman(L,[x["idx"]  for x in big]),3),
 "n":len(big)}
print(f"\n=== Correlaciones con el voto (Spearman, {len(big)} municipios >=15k votos) ===")
for k,lbl in [("lean_cons","comercio/1k"),("lean_inet","internet/1k"),("lean_edu","cobertura media"),
              ("lean_idx","INDICE compuesto de acceso")]:
    print(f"  voto vs {lbl:28}: {corr[k]:+.2f}")

# ---- regional scorecard (vote-weighted) ----
agg=defaultdict(lambda:{"vv":0,"nl":0.0,"st":0,"acc":0.0,"avv":0,"edv":0.0,"evv":0,"idv":0.0,"ivv":0})
for x in full:
    a=agg[x["region"]]; a["vv"]+=x["votval"]; a["nl"]+=x["lean"]*x["votval"]; a["st"]+=x["stores"]
    a["acc"]+=inet.get(x["id"],0); a["avv"]+=x["votval"]
    a["edv"]+=x["edu"]*x["votval"]; a["evv"]+=x["votval"]
    a["idv"]+=x["idx"]*x["votval"]; a["ivv"]+=x["votval"]
score=[]
for reg,a in agg.items():
    if reg=="?" or a["vv"]==0: continue
    score.append({"region":reg,"lean":round(a["nl"]/a["vv"],4),
                  "cons":round(a["st"]/(a["vv"]/1000),3),"inet":round(a["acc"]/(a["avv"]/1000),1),
                  "edu":round(a["edv"]/a["evv"],1),"idx":round(a["idv"]/a["ivv"],3),"votval":a["vv"]})
score.sort(key=lambda s:s["lean"])
print("\n=== Scorecard regional (ponderado por votos) ===")
print(f'{"region":10}{"voto":>7}{"comercio":>9}{"internet":>9}{"edu.media":>10}{"INDICE":>8}')
for s in score:
    print(f'  {s["region"]:9}{s["lean"]*100:+6.1f}{s["cons"]:9.2f}{s["inet"]:9.0f}{s["edu"]:10.1f}{s["idx"]:+8.2f}')

# ---- export ----
out={"muni":[{"id":x["id"],"muni":x["muni"],"region":x["region"],"lean":x["lean"],"votval":x["votval"],
              "cons":round(x["cons"],3),"inet":round(x["inet"],2),"edu":round(x["edu"],1),"idx":x["idx"]}
             for x in full],
     "score":score,"corr":corr,
     "meta":{"pilares":"comercio (OSM) + internet fijo (MinTIC 2023T3) + cobertura media (MEN 2024)",
             "indice":"promedio de z-scores; mayor = mas central/servido"}}
with open(P("site","cp.js"),"w",encoding="utf-8") as f:
    f.write("window.CP="+json.dumps(out,ensure_ascii=False,separators=(',',':'))+";")
print(f"\nwrote site/cp.js ({len(full)} municipios completos)")
