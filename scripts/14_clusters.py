"""Clusters y anomalias (Sitio 2, fase 2): LISA de Anselin (1995) implementado en numpy.
Sobre los municipios con datos de consumo (matriz municipio x marca):
  1. Moran local UNIVARIADO del ECI -> hotspots/coldspots de complejidad del consumo.
  2. Moran local BIVARIADO voto -> lag espacial del ECI -> co-clusters y ANOMALIAS:
     municipios cuyo voto no "cuadra" con el entorno de consumo que los rodea.
Pesos: k vecinos mas cercanos (k=6) sobre centroides (evita islas), fila-estandarizados.
Inferencia: permutacion condicional (199), pseudo p<0.05.
Output: site2/clusters.js  window.CL = {meta, munis:[{id,name,dept,lean,eci,q_eci,q_biv,...}]}
"""
import os, csv, json, math
import numpy as np
from collections import defaultdict

BASE = os.path.join(os.path.dirname(__file__), "..")
P = lambda *a: os.path.join(BASE, *a)

# ---- load CX (munis with eci/lean) + centroids from stores ----
s = open(P("site2","complex.js"), encoding="utf-8").read()
CX = json.loads(s[s.index("=")+1:].rstrip().rstrip(";"))
mu_xy = defaultdict(list)
for r in csv.DictReader(open(P("data","processed","stores_geo.csv"), encoding="utf-8")):
    mu_xy[r["divipola"]].append((float(r["lon"]), float(r["lat"])))

M = [m for m in CX["munis"] if m.get("eci") is not None and m["id"] in mu_xy]
n = len(M)
lon = np.array([np.mean([p[0] for p in mu_xy[m["id"]]]) for m in M])
lat = np.array([np.mean([p[1] for p in mu_xy[m["id"]]]) for m in M])
lean = np.array([m["lean"] for m in M])
eci  = np.array([m["eci"]  for m in M])

# ---- kNN weights (k=6), row-standardized ----
K = 6
la = np.radians(lat); lo = np.radians(lon)
# haversine matrix (n=~520, fine)
dlat = la[:,None]-la[None,:]; dlon = lo[:,None]-lo[None,:]
h = np.sin(dlat/2)**2 + np.cos(la)[:,None]*np.cos(la)[None,:]*np.sin(dlon/2)**2
D = 6371*2*np.arcsin(np.sqrt(np.clip(h,0,1)))
np.fill_diagonal(D, np.inf)
nbr = np.argsort(D, axis=1)[:, :K]            # indices of K nearest
W = np.zeros((n,n))
for i in range(n): W[i, nbr[i]] = 1.0/K

def z(v): return (v - v.mean())/v.std()
zl, ze = z(lean), z(eci)

lagE = W @ ze
lagL = W @ zl

# ---- local Moran: univariate ECI ; bivariate lean -> lag(ECI) ----
Ie  = ze * lagE
Ib  = zl * lagE

# ---- conditional permutation p-values (199 perms) ----
rng = np.random.default_rng(7)
PERM = 199
def pperm(zself, zother):
    """p for I_i = zself_i * mean(zother over neighbors), permuting zother among the rest."""
    p = np.ones(n)
    obs = zself * (W @ zother)
    for i in range(n):
        others = np.delete(np.arange(n), i)
        cnt = 0
        for _ in range(PERM):
            pick = rng.choice(others, size=K, replace=False)
            sim = zself[i] * zother[pick].mean()
            if abs(sim) >= abs(obs[i]): cnt += 1
        p[i] = (cnt+1)/(PERM+1)
    return p
p_e = pperm(ze, ze)
p_b = pperm(zl, ze)

def quad(zself, lag, p):
    q = np.array(['ns']*n, dtype=object)
    sig = p < 0.05
    q[(zself>0)&(lag>0)&sig]='HH'; q[(zself<0)&(lag<0)&sig]='LL'
    q[(zself>0)&(lag<0)&sig]='HL'; q[(zself<0)&(lag>0)&sig]='LH'
    return q
q_eci = quad(ze, lagE, p_e)
q_biv = quad(zl, lagE, p_b)

# ---- global Moran ----
gI_e = float((ze @ (W @ ze))/n)
gI_l = float((zl @ (W @ zl))/n)
gI_b = float((zl @ (W @ ze))/n)

out_m = []
for i, m in enumerate(M):
    out_m.append({"id": m["id"], "name": m["name"], "dept": m["dept"],
                  "lean": m["lean"], "eci": m["eci"], "votval": m["votval"],
                  "qe": q_eci[i], "qb": q_biv[i],
                  "pe": round(float(p_e[i]),3), "pb": round(float(p_b[i]),3)})

meta = {"n": n, "k": K, "perms": PERM,
        "I_eci": round(gI_e,3), "I_lean": round(gI_l,3), "I_biv": round(gI_b,3),
        "desc": "LISA (Anselin 1995) con pesos kNN(6) fila-estandarizados; permutacion condicional. "
                "qe: cluster de ECI; qb: bivariado voto->lag(ECI). HH/LL=co-cluster, HL/LH=anomalia."}
with open(P("site2","clusters.js"), "w", encoding="utf-8") as f:
    f.write("window.CL=" + json.dumps({"meta": meta, "munis": out_m}, ensure_ascii=False, separators=(",",":")) + ";\n")

cnt = lambda q,v: int((q==v).sum())
print(f"n={n} | Moran global: ECI={gI_e:.3f} voto={gI_l:.3f} bivariado={gI_b:.3f}")
print(f"ECI: HH={cnt(q_eci,'HH')} LL={cnt(q_eci,'LL')} HL={cnt(q_eci,'HL')} LH={cnt(q_eci,'LH')} ns={cnt(q_eci,'ns')}")
print(f"BIV: HH={cnt(q_biv,'HH')} LL={cnt(q_biv,'LL')} HL={cnt(q_biv,'HL')} LH={cnt(q_biv,'LH')} ns={cnt(q_biv,'ns')}")
an1=[(M[i]['name'],round(lean[i]*100)) for i in range(n) if q_biv[i]=='LH'][:8]
an2=[(M[i]['name'],round(lean[i]*100)) for i in range(n) if q_biv[i]=='HL'][:8]
print("anomalia LH (vota Cepeda, entorno complejo):", an1)
print("anomalia HL (vota DLE, entorno simple):", an2)
