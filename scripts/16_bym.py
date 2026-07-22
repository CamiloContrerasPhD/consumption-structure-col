"""Incertidumbre (Sitio 2, fase 2): modelo BYM (Besag-York-Mollie 1991) con PyMC.
  y_m ~ Binomial(n_m, p_m)          y = votos De La Espriella (aprox. dos-partidos), n = votos validos
  logit(p_m) = b0 + theta_m + phi_m
  theta ~ Normal(0, s_t)            heterogeneidad no espacial
  phi   ~ ICAR(s_s)                 suavizado espacial (vecindario kNN simetrizado)
Posterior por municipio: media de p, IC 95%, y el "shrinkage" (correccion vs dato crudo).
Output: site2/bym.js  window.BY = {meta, munis:[{id,name,dept,n,raw,p,lo,hi,w}]}
"""
import os, csv, json, pickle, math
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..")
P = lambda *a: os.path.join(BASE, *a)

# ---- munis: raw share + counts ----
rows = []
for r in csv.DictReader(open(P("data","processed","muni_index.csv"), encoding="utf-8")):
    lean = float(r["lean"]); n = int(r["votval"])
    if n < 50: continue
    p_raw = min(max((1+lean)/2, 1e-4), 1-1e-4)
    rows.append({"id": r["divipola"], "name": r["muni"], "dept": r["dept"],
                 "n": n, "y": int(round(n*p_raw)), "raw": p_raw})

# ---- centroids: polygons for real DIVIPOLA ids; stores-mean fallback ----
from collections import defaultdict
cent = {}
try:
    polys = pickle.load(open(P("data","processed","muni_polygons.pkl"), "rb"))
    for p_ in polys:
        dv = p_.get("divipola")
        if dv:
            c = p_["geom"].representative_point()
            cent[dv] = (c.x, c.y)
except Exception as e:
    print("polygons no disponibles:", e)
mu_xy = defaultdict(list)
for s in csv.DictReader(open(P("data","processed","stores_geo.csv"), encoding="utf-8")):
    mu_xy[s["divipola"]].append((float(s["lon"]), float(s["lat"])))
for k, v in mu_xy.items():
    if k not in cent:
        cent[k] = (float(np.mean([q[0] for q in v])), float(np.mean([q[1] for q in v])))

rows = [r for r in rows if r["id"] in cent]
N = len(rows)
lon = np.array([cent[r["id"]][0] for r in rows]); lat = np.array([cent[r["id"]][1] for r in rows])
y = np.array([r["y"] for r in rows]); n = np.array([r["n"] for r in rows])

# ---- kNN(6) symmetrized adjacency; force single component ----
la = np.radians(lat); lo = np.radians(lon)
dlat = la[:,None]-la[None,:]; dlon = lo[:,None]-lo[None,:]
h = np.sin(dlat/2)**2 + np.cos(la)[:,None]*np.cos(la)[None,:]*np.sin(dlon/2)**2
D = 6371*2*np.arcsin(np.sqrt(np.clip(h,0,1)))
np.fill_diagonal(D, np.inf)
K = 6
W = np.zeros((N,N), dtype=int)
for i in range(N):
    for j in np.argsort(D[i])[:K]: W[i,j] = 1
W = np.maximum(W, W.T)

# union-find to connect components
parent = list(range(N))
def find(a):
    while parent[a]!=a: parent[a]=parent[parent[a]]; a=parent[a]
    return a
def union(a,b): parent[find(a)]=find(b)
for i in range(N):
    for j in range(i+1,N):
        if W[i,j]: union(i,j)
comps = defaultdict(list)
for i in range(N): comps[find(i)].append(i)
comp_list = list(comps.values())
while len(comp_list) > 1:
    a = comp_list[0]; best = (np.inf, None, None)
    for c in comp_list[1:]:
        sub = D[np.ix_(a, c)]
        k = np.unravel_index(np.argmin(sub), sub.shape)
        if sub[k] < best[0]: best = (sub[k], a[k[0]], c[k[1]])
    W[best[1], best[2]] = W[best[2], best[1]] = 1
    union(best[1], best[2])
    comps = defaultdict(list)
    for i in range(N): comps[find(i)].append(i)
    comp_list = list(comps.values())
print(f"n={N} municipios; aristas={W.sum()//2}; componente unica")

# ---- BYM in PyMC ----
import pymc as pm
with pm.Model() as model:
    b0 = pm.Normal("b0", 0, 2)
    s_t = pm.HalfNormal("s_t", 1.0)
    s_s = pm.HalfNormal("s_s", 1.0)
    theta = pm.Normal("theta", 0, 1, shape=N)
    phi = pm.ICAR("phi", W=W)
    phi_c = phi - phi.mean()          # centrado: identifica b0 (ICAR es impropio)
    eta = b0 + s_t*theta + s_s*phi_c
    p = pm.Deterministic("p", pm.math.sigmoid(eta))
    pm.Binomial("y", n=n, p=p, observed=y)
    idata = pm.sample(draws=800, tune=1200, chains=4, cores=1, target_accept=0.93,
                      random_seed=11, progressbar=False)

post = idata.posterior["p"].stack(s=("chain","draw")).values  # N x S
p_mean = post.mean(1); p_lo = np.percentile(post, 2.5, axis=1); p_hi = np.percentile(post, 97.5, axis=1)

# ---- propagacion a marcas y categorias: lean de huella con intervalo creible ----
# lean_b^(s) = promedio sobre los locales de la marca de (2 p_m^(s) - 1)
id2idx = {r["id"]: i for i, r in enumerate(rows)}
br_munis = defaultdict(list); br_dom = {}
dom_munis = defaultdict(list)
for s_ in __import__("csv").DictReader(open(P("data","processed","stores_geo.csv"), encoding="utf-8")):
    i = id2idx.get(s_["divipola"])
    if i is None: continue
    br_munis[s_["brand"]].append(i); br_dom[s_["brand"]] = s_["domain"]
    dom_munis[s_["domain"]].append(i)

def lean_ci(idx_list):
    draws = (2*post[idx_list, :] - 1).mean(axis=0)   # S draws del lean promedio de la huella
    return (float(draws.mean()), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)))

brands_out2 = []
for b, idxs in sorted(br_munis.items()):
    if len(idxs) < 10: continue
    m_, lo_, hi_ = lean_ci(idxs)
    brands_out2.append({"brand": b, "domain": br_dom[b], "n": len(idxs),
                        "lean": round(m_,4), "lo": round(lo_,4), "hi": round(hi_,4),
                        "w": round(hi_-lo_,4), "cross0": bool(lo_ < 0 < hi_)})
cats_out = []
for d, idxs in sorted(dom_munis.items()):
    m_, lo_, hi_ = lean_ci(idxs)
    cats_out.append({"domain": d, "n": len(idxs), "lean": round(m_,4),
                     "lo": round(lo_,4), "hi": round(hi_,4), "cross0": bool(lo_ < 0 < hi_)})

out_m = []
for i, r in enumerate(rows):
    out_m.append({"id": r["id"], "name": r["name"], "dept": r["dept"], "n": r["n"],
                  "raw": round(r["raw"],4), "p": round(float(p_mean[i]),4),
                  "lo": round(float(p_lo[i]),4), "hi": round(float(p_hi[i]),4),
                  "w": round(float(p_hi[i]-p_lo[i]),4)})

import arviz as az
# convergencia sobre la cantidad de interes (p), no sobre componentes con trade-offs
rhat_p = az.rhat(idata, var_names=["p"])["p"].values
rhat_max = float(np.nanmax(rhat_p))
meta = {"n": N, "k": K, "draws": 800, "chains": 4, "rhat_max": round(rhat_max,3),
        "median_width": round(float(np.median(p_hi-p_lo)),4),
        "desc": "BYM (Besag-York-Mollie 1991): Binomial + logit(p)=b0+theta+ICAR; kNN(6) simetrizado. "
                "p = proporcion De La Espriella (aprox. dos-partidos)."}
meta["n_brands"] = len(brands_out2)
meta["n_afirmable"] = sum(1 for b in brands_out2 if not b["cross0"])
with open(P("site2","bym.js"), "w", encoding="utf-8") as f:
    f.write("window.BY=" + json.dumps({"meta": meta, "munis": out_m, "brands": brands_out2, "cats": cats_out},
                                      ensure_ascii=False, separators=(",",":")) + ";\n")

print(f"rhat_max={rhat_max:.3f} | ancho mediano IC95={np.median(p_hi-p_lo):.4f}")
print(f"marcas con IC: {len(brands_out2)} | con color politico afirmable (IC no cruza 0): {meta['n_afirmable']}")
wide_b = sorted(brands_out2, key=lambda x: -x["w"])[:5]
print("marcas mas fragiles:", [(b['brand'], b['n'], round(b['w']*100,1)) for b in wide_b])
print("categorias:", [(c['domain'], round(c['lean']*100,1), 'cruza0' if c['cross0'] else 'afirmable') for c in cats_out])
shr = sorted(out_m, key=lambda x: -abs(x["p"]-x["raw"]))[:6]
print("mayores correcciones (shrinkage):", [(x["name"], x["raw"], "->", x["p"]) for x in shr])
wid = sorted(out_m, key=lambda x: -x["w"])[:6]
print("mayor incertidumbre:", [(x["name"], x["n"], x["w"]) for x in wid])
