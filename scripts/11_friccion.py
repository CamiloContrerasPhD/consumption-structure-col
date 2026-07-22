"""Friccion politica en la expansion (Sitio 2, pagina Oportunidad).
Test: entre pares (marca, municipio) donde la marca esta AUSENTE, ¿la presencia observada
(dado lo que la densidad de relatedness predice) cae con la DISTANCIA POLITICA entre el
municipio y la base de la marca?

Modelo (LPM): presencia ~ densidad + dist_politica + dist_geografica + log(votval)
  - dist_politica = |lean_municipio - lean_marca|  (en puntos, 0-200 teorico)
  - dist_geografica = haversine(municipio, centroide de la huella de la marca)
IC por bootstrap (remuestreo de municipios). Correlacional, no causal.

Output: site2/friccion.js  window.FR = {meta, coef, curve, brands}
"""
import os, csv, json, math
import numpy as np
from collections import defaultdict

BASE = os.path.join(os.path.dirname(__file__), "..")
P = lambda *a: os.path.join(BASE, *a)

# ---- load CX from complex.js ----
s = open(P("site2","complex.js"), encoding="utf-8").read()
CX = json.loads(s[s.index("=")+1:].rstrip().rstrip(";"))
muniOrder = CX["muniOrder"]
munis = {m["id"]: m for m in CX["munis"]}
brands = CX["brands"]
nM, nB = len(muniOrder), len(brands)

# ---- coordinates: muni = mean of store coords; brand centroid = mean of its stores ----
mu_xy = defaultdict(list); br_xy = defaultdict(list)
for r in csv.DictReader(open(P("data","processed","stores_geo.csv"), encoding="utf-8")):
    lon, lat = float(r["lon"]), float(r["lat"])
    mu_xy[r["divipola"]].append((lon, lat))
    br_xy[r["brand"]].append((lon, lat))
mu_c = {k: (np.mean([p[0] for p in v]), np.mean([p[1] for p in v])) for k, v in mu_xy.items()}
br_c = {k: (np.mean([p[0] for p in v]), np.mean([p[1] for p in v])) for k, v in br_xy.items()}

def hav_km(a, b):
    lo1, la1, lo2, la2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    x = math.sin((la2-la1)/2)**2 + math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
    return 6371*2*math.asin(math.sqrt(x))

# ---- build pair-level dataset ----
rows = []  # y, density, poldist(pts), geodist(100km), logvot, mi, brand
for j, b in enumerate(brands):
    bl = b["lean"]; bc = br_c.get(b["brand"])
    dens = CX["brandDensity"][b["brand"]]; pres = CX["brandPresent"][b["brand"]]
    for i, mid in enumerate(muniOrder):
        m = munis[mid]; mc = mu_c.get(mid)
        if bc is None or mc is None: continue
        rows.append((float(pres[i]), dens[i], abs(m["lean"]-bl)*100,
                     hav_km(mc, bc)/100.0, math.log10(max(m["votval"],1)), i, j))
rows = np.array(rows)
y, X = rows[:,0], np.column_stack([np.ones(len(rows)), rows[:,1], rows[:,2], rows[:,3], rows[:,4]])
names = ["const","densidad","dist_politica","dist_geo_100km","log_votval"]

def ols(Xm, ym):
    beta, *_ = np.linalg.lstsq(Xm, ym, rcond=None)
    return beta
beta = ols(X, y)

# ---- bootstrap CI (resample municipios, 200 reps) ----
rng = np.random.default_rng(42)
mi = rows[:,5].astype(int)
by_mi = defaultdict(list)
for k, i in enumerate(mi): by_mi[i].append(k)
mids = list(by_mi.keys())
bs = []
for _ in range(200):
    take = rng.choice(mids, size=len(mids), replace=True)
    idx = np.concatenate([by_mi[t] for t in take])
    bs.append(ols(X[idx], y[idx])[2])
lo, hi = np.percentile(bs, [2.5, 97.5])

# ---- descriptive curve: within density deciles, presence rate by political-distance bin ----
dens_v, pol_v = rows[:,1], rows[:,2]
dec = np.quantile(dens_v, np.linspace(0,1,11))
POLBINS = [0,5,10,20,30,45,200]
curve = []
for pb in range(len(POLBINS)-1):
    sel_p = (pol_v>=POLBINS[pb]) & (pol_v<POLBINS[pb+1])
    gaps, wts = [], []
    for d in range(10):
        sel_d = (dens_v>=dec[d]) & (dens_v<=dec[d+1])
        base = y[sel_d].mean() if sel_d.sum() else 0
        sel = sel_d & sel_p
        if sel.sum() >= 50:
            gaps.append(y[sel].mean()-base); wts.append(sel.sum())
    if gaps:
        g = float(np.average(gaps, weights=wts))
        curve.append({"bin": f"{POLBINS[pb]}-{POLBINS[pb+1] if POLBINS[pb+1]<200 else '+'}",
                      "gap": round(g*100,2), "n": int(sum(wts))})

# ---- per-brand friction coefficient ----
bj = rows[:,6].astype(int)
br_out = []
for j, b in enumerate(brands):
    sel = bj==j
    if sel.sum() < 200: continue
    bt = ols(X[sel], y[sel])
    br_out.append({"brand": b["brand"], "domain": b["domain"], "n": b["n"],
                   "lean": b["lean"], "fric": round(float(bt[2])*1000,2)})  # pp per 10 pts? scale below
# fric = coef *1000 -> puntos porcentuales de presencia por cada 10 pts de distancia politica? coef is per 1 pt in probability
# clearer: coef*100 = pp per pt; *10 -> pp per 10pts. Use pp_per10 = coef*100*10 = coef*1000. OK as stored.
br_out.sort(key=lambda x: x["fric"])

meta = {"n_pairs": int(len(rows)), "n_munis": nM, "n_brands": nB,
        "coef_pp_per10pts": round(float(beta[2])*1000,2),
        "ci_lo": round(float(lo)*1000,2), "ci_hi": round(float(hi)*1000,2),
        "coefs": {names[k]: round(float(beta[k]),5) for k in range(len(names))},
        "desc": "LPM presencia ~ densidad + dist politica + dist geografica + log votos. "
                "coef en puntos porcentuales de presencia por +10 pts de distancia politica."}
out = {"meta": meta, "curve": curve, "brands": br_out}
with open(P("site2","friccion.js"), "w", encoding="utf-8") as f:
    f.write("window.FR=" + json.dumps(out, ensure_ascii=False, separators=(",",":")) + ";\n")

print(f"pares: {len(rows):,} | coef dist_politica: {meta['coef_pp_per10pts']} pp/10pts "
      f"[{meta['ci_lo']}, {meta['ci_hi']}]")
print("coefs:", meta["coefs"])
print("curva:", [(c['bin'], c['gap']) for c in curve])
print("mas friccion (presencia cae mas con distancia politica):", [(b['brand'], b['fric']) for b in br_out[:6]])
print("menos friccion / 'ciegas':", [(b['brand'], b['fric']) for b in br_out[-6:]])
