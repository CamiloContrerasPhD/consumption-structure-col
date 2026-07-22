# -*- coding: utf-8 -*-
"""Economic complexity of consumption (Sitio 2 MVP).
Builds the municipality x brand presence matrix from stores_geo.csv and computes:
  - RCA (Balassa) and binary specialization matrix M
  - Diversity (per municipio), Ubiquity (per brand)
  - ECI / PCI via the eigenvector method (Hidalgo-Hausmann)
  - Brand proximity (phi) and relatedness density per (municipio, brand)
  - Opportunity = high relatedness density where the brand is absent
Outputs: site2/complex.js  (window.CX = {meta, munis, brands, muniOrder, brandDensity, brandPresent})
"""
import csv, json, os
from collections import defaultdict, Counter
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..")
P = lambda *a: os.path.join(BASE, *a)

# DANE 2-digit dept code -> clean name (resolve numeric/raw OSM dept to a name)
DANE_DEPT = {
 "05":"Antioquia","08":"Atlantico","11":"Bogota D.C.","13":"Bolivar","15":"Boyaca",
 "17":"Caldas","18":"Caqueta","19":"Cauca","20":"Cesar","23":"Cordoba","25":"Cundinamarca",
 "27":"Choco","41":"Huila","44":"La Guajira","47":"Magdalena","50":"Meta","52":"Narino",
 "54":"Norte de Santander","63":"Quindio","66":"Risaralda","68":"Santander","70":"Sucre",
 "73":"Tolima","76":"Valle del Cauca","81":"Arauca","85":"Casanare","86":"Putumayo",
 "88":"San Andres","91":"Amazonas","94":"Guainia","95":"Guaviare","97":"Vaupes","99":"Vichada",
}

# normalized DANE name -> canonical (for munis matched by name, dept from OSM)
import unicodedata
def _asc(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode()
    return "".join(ch for ch in s.upper() if ch.isalnum())
NAME2 = {_asc(n): n for n in DANE_DEPT.values()}
NAME2["CUDINAMARCA"] = "Cundinamarca"  # OSM typo
# muni-name -> dept, for munis whose OSM dept was empty or mojibake (no real DIVIPOLA)
MUNI_DEPT = {
 "PAIME":"Cundinamarca","COVENAS":"Sucre","TURBANA":"Bolivar","NOROSI":"Bolivar",
 "BECERRIL":"Cesar","CAUCASIA":"Antioquia","SEVILLA":"Valle del Cauca","QUIMBAYA":"Quindio",
 "COLOMBIA":"Huila","SANTACATALINA":"Bolivar","FLORENCIA":"Caqueta","SOGAMOSO":"Boyaca",
 "COTA":"Cundinamarca","ELROSAL":"Cundinamarca","LAVEGA":"Cundinamarca","SUPATA":"Cundinamarca",
 "SASAIMA":"Cundinamarca","FACATATIVA":"Cundinamarca","GACHETA":"Cundinamarca","UBATE":"Cundinamarca",
 "GUASCA":"Cundinamarca","SOPO":"Cundinamarca","LENGUAZAQUE":"Cundinamarca","MACHETA":"Cundinamarca",
 "PASTO":"Narino","PACHO":"Cundinamarca","SUBACHOQUE":"Cundinamarca","CAJICA":"Cundinamarca",
 "LAJAGUADEIBIRICO":"Cesar","VILLAGOMEZ":"Cundinamarca","NUQUI":"Choco","COLOMBIA HUILA":"Huila",
}

def resolve_dept(divipola, raw, name):
    by_code = DANE_DEPT.get((divipola or "")[:2])
    if by_code: return by_code                       # real DIVIPOLA -> code -> name
    if _asc(raw) in NAME2: return NAME2[_asc(raw)]    # clean OSM dept name
    if _asc(name) in MUNI_DEPT: return MUNI_DEPT[_asc(name)]  # name-matched fallback
    return raw or "?"

# ---- load municipio info (lean, votval, name, dept) ----
muni_info = {}
for r in csv.DictReader(open(P("data","processed","muni_index.csv"), encoding="utf-8")):
    dept = resolve_dept(r["divipola"], r["dept"], r["muni"])
    muni_info[r["divipola"]] = {"name": r["muni"], "dept": dept,
                                "lean": float(r["lean"]), "votval": int(r["votval"])}

# ---- load stores -> counts[municipio][brand], brand domain, brand lean ----
counts = defaultdict(Counter)
brand_domain = {}
brand_lean_sum = defaultdict(float); brand_lean_n = defaultdict(int)
for r in csv.DictReader(open(P("data","processed","stores_geo.csv"), encoding="utf-8")):
    dv, b = r["divipola"], r["brand"]
    if dv not in muni_info:
        continue
    counts[dv][b] += 1
    brand_domain[b] = r["domain"]
    brand_lean_sum[b] += float(r["lean"]); brand_lean_n[b] += 1

munis = sorted(counts.keys())
brands = sorted(brand_domain.keys())
mi = {m: i for i, m in enumerate(munis)}
bi = {b: i for i, b in enumerate(brands)}
nM, nB = len(munis), len(brands)

C = np.zeros((nM, nB))
for m in munis:
    for b, c in counts[m].items():
        C[mi[m], bi[b]] = c
print(f"matriz: {nM} municipios x {nB} marcas; locales={int(C.sum())}")

# ---- RCA (Balassa) and binary specialization M ----
row = C.sum(1, keepdims=True); col = C.sum(0, keepdims=True); tot = C.sum()
with np.errstate(divide="ignore", invalid="ignore"):
    RCA = (C / np.where(row==0,1,row)) / np.where(col==0,1,col/tot) * 1.0
    RCA = (C / np.where(row==0,1,row)) / (col / tot)
RCA = np.nan_to_num(RCA, nan=0.0, posinf=0.0)
M = (RCA >= 1).astype(float)

diversity = M.sum(1)   # kc0 per municipio
ubiquity  = M.sum(0)   # kp0 per brand

# keep only municipios/brands that are specialized somewhere (for the eigenvector step)
okM = diversity > 0
okB = ubiquity > 0
Mr = M[np.ix_(okM, okB)]
kc0 = Mr.sum(1); kp0 = Mr.sum(0)

# ---- ECI / PCI via eigenvector method ----
def eci_pci(Mr, kc0, kp0):
    # ~Mcc' = sum_p (M_cp M_c'p)/(kc0_c kp0_p)
    A = (Mr / kc0[:, None]) @ (Mr / kp0[None, :]).T          # nMr x nMr
    B = (Mr / kp0[None, :]).T @ (Mr / kc0[:, None])          # nBr x nBr
    def second_eig(X):
        w, v = np.linalg.eig(X)
        order = np.argsort(-w.real)
        vec = v[:, order[1]].real                            # 2nd largest eigenvalue
        return vec
    eci = second_eig(A); pci = second_eig(B)
    # standardize
    eci = (eci - eci.mean()) / eci.std()
    pci = (pci - pci.mean()) / pci.std()
    return eci, pci

eci_r, pci_r = eci_pci(Mr, kc0, kp0)
# sign convention: ECI should correlate positively with diversity
if np.corrcoef(eci_r, kc0)[0,1] < 0: eci_r = -eci_r
# PCI sign aligned to ECI via brand-municipio link (rarer/sophisticated brands high)
if np.corrcoef(pci_r, -kp0)[0,1] < 0: pci_r = -pci_r

eci = np.full(nM, np.nan); eci[okM] = eci_r
pci = np.full(nB, np.nan); pci[okB] = pci_r

# ---- brand proximity (phi) and relatedness density ----
cooc = M.T @ M                                   # nB x nB co-occurrence
ubiq_safe = np.where(ubiquity==0, 1, ubiquity)
phi = cooc / np.maximum(ubiq_safe[:,None], ubiq_safe[None,:])   # min-conditional => divide by max ubiquity
np.fill_diagonal(phi, 0.0)
denom = phi.sum(0)                               # per brand
denom = np.where(denom==0, 1, denom)
density = (M @ phi) / denom[None, :]             # nM x nB in [0,1]: relatedness density of brand b in municipio m

# opportunity score: density where brand absent (M==0)
opp = density * (1 - M)

# ---- assemble outputs ----
def f(x): return round(float(x), 4)
munis_out = []
for m in munis:
    i = mi[m]; info = muni_info[m]
    # top missing brands by opportunity
    order = np.argsort(-opp[i])
    top = [{"brand": brands[j], "dens": f(opp[i, j])} for j in order[:6] if opp[i, j] > 0]
    munis_out.append({"id": m, "name": info["name"], "dept": info["dept"],
                      "lean": f(info["lean"]), "votval": info["votval"],
                      "div": int(diversity[i]),
                      "eci": (None if np.isnan(eci[i]) else f(eci[i])),
                      "opp": top})

brands_out = []
for b in brands:
    j = bi[b]
    brands_out.append({"brand": b, "domain": brand_domain[b],
                       "ubiq": int(ubiquity[j]),
                       "pci": (None if np.isnan(pci[j]) else f(pci[j])),
                       "lean": f(brand_lean_sum[b]/max(1,brand_lean_n[b])),
                       "n": brand_lean_n[b]})

# per-brand density + presence aligned to muniOrder (for the opportunity choropleth selector)
brandDensity = {b: [f(density[mi[m], bi[b]]) for m in munis] for b in brands}
brandPresent = {b: [int(M[mi[m], bi[b]]) for m in munis] for b in brands}

CX = {
    "meta": {"n_munis": nM, "n_brands": nB,
             "desc": "Complejidad economica del consumo. ECI/PCI por metodo de eigenvector; "
                     "densidad de relatedness; oportunidad = densidad alta donde la marca esta ausente.",
             "polo_neg": "Ivan Cepeda", "polo_pos": "Abelardo De La Espriella"},
    "muniOrder": munis,
    "munis": munis_out,
    "brands": sorted(brands_out, key=lambda x: (x["pci"] is None, x["pci"] if x["pci"] is not None else 0)),
    "brandDensity": brandDensity,
    "brandPresent": brandPresent,
}
os.makedirs(P("site2"), exist_ok=True)
with open(P("site2","complex.js"), "w", encoding="utf-8") as fh:
    fh.write("window.CX=" + json.dumps(CX, ensure_ascii=False, separators=(",",":")) + ";")

sz = os.path.getsize(P("site2","complex.js"))/1024
print(f"site2/complex.js = {sz:.0f} KB")
# sanity
top_eci = sorted([x for x in munis_out if x["eci"] is not None], key=lambda x:-x["eci"])[:6]
print("ECI alto (canasta mas compleja):", [(x["name"], x["eci"], 'lean', round(x['lean']*100)) for x in top_eci])
top_pci = sorted([x for x in brands_out if x["pci"] is not None], key=lambda x:-x["pci"])[:6]
print("PCI alto (marcas mas sofisticadas/raras):", [(x["brand"], x["pci"]) for x in top_pci])
low_pci = sorted([x for x in brands_out if x["pci"] is not None], key=lambda x:x["pci"])[:6]
print("PCI bajo (mas ubicuas):", [(x["brand"], x["pci"]) for x in low_pci])
