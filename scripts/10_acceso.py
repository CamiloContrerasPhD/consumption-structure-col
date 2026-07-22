"""Acceso y desiertos de consumo (Sitio 2).
Une la huella de locales (OSM) con la poblacion municipal 2025 (DANE CNPV) y el voto 2026.
- acceso = locales de cadena por cada 10.000 habitantes (oferta formal per capita)
- desierto = poblacion alta con acceso bajo (locales faltantes vs mediana nacional)
- bivariado acceso x voto + correlaciones (Spearman)
Output: site2/acceso.js  window.ACC = {meta, munis:[...], corr:{...}, terciles:{...}}
"""
import os, csv, json, unicodedata
from collections import Counter

BASE = os.path.join(os.path.dirname(__file__), "..")
P = lambda *a: os.path.join(BASE, *a)

DANE_DEPT = {
 "05":"Antioquia","08":"Atlantico","11":"Bogota D.C.","13":"Bolivar","15":"Boyaca",
 "17":"Caldas","18":"Caqueta","19":"Cauca","20":"Cesar","23":"Cordoba","25":"Cundinamarca",
 "27":"Choco","41":"Huila","44":"La Guajira","47":"Magdalena","50":"Meta","52":"Narino",
 "54":"Norte de Santander","63":"Quindio","66":"Risaralda","68":"Santander","70":"Sucre",
 "73":"Tolima","76":"Valle del Cauca","81":"Arauca","85":"Casanare","86":"Putumayo",
 "88":"San Andres","91":"Amazonas","94":"Guainia","95":"Guaviare","97":"Vaupes","99":"Vichada",
}
NAME2CODE = {}
for c, n in DANE_DEPT.items():
    NAME2CODE["".join(ch for ch in unicodedata.normalize("NFKD",n).encode("ascii","ignore").decode().upper() if ch.isalnum())] = c

def asc(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode()
    return "".join(ch for ch in s.upper() if ch.isalnum())

NAME2 = {asc(n): n for n in DANE_DEPT.values()}; NAME2["CUDINAMARCA"]="Cundinamarca"
MUNI_DEPT = {"PAIME":"Cundinamarca","COVENAS":"Sucre","TURBANA":"Bolivar","NOROSI":"Bolivar","BECERRIL":"Cesar",
 "CAUCASIA":"Antioquia","SEVILLA":"Valle del Cauca","QUIMBAYA":"Quindio","COLOMBIA":"Huila","SANTACATALINA":"Bolivar",
 "FLORENCIA":"Caqueta","SOGAMOSO":"Boyaca","PASTO":"Narino","NUQUI":"Choco","LAJAGUADEIBIRICO":"Cesar"}
def resolve_dept(divipola, raw, name):
    by = DANE_DEPT.get((divipola or "")[:2])
    if by: return by
    if asc(raw) in NAME2: return NAME2[asc(raw)]
    if asc(name) in MUNI_DEPT: return MUNI_DEPT[asc(name)]
    return raw or "?"

# ---- poblacion 2025 (DANE) ----
pop_by_dv = {}; by_dept_name = {}; by_name = {}
for r in csv.DictReader(open(P("data","processed","poblacion_municipio.csv"), encoding="utf-8")):
    dv = r["divipola"]; pop = int(r["poblacion"])
    urb = float(r["urb_share"]) if r["urb_share"] else None
    pop_by_dv[dv] = {"pop": pop, "urb": urb}
    by_dept_name[(dv[:2], asc(r["nombre"]))] = dv
    by_name.setdefault(asc(r["nombre"]), []).append(dv)

def real_dv(mid, name, dept_name):
    if mid in pop_by_dv: return mid
    dc = NAME2CODE.get(asc(dept_name))
    if dc and (dc, asc(name)) in by_dept_name: return by_dept_name[(dc, asc(name))]
    cand = by_name.get(asc(name), [])
    return cand[0] if len(cand) == 1 else None

# ---- locales por municipio (id de muni_index) ----
loc = Counter()
for r in csv.DictReader(open(P("data","processed","stores_geo.csv"), encoding="utf-8")):
    loc[r["divipola"]] += 1

# ---- municipios: lean, votval, name, dept ----
rows = []; nojoin = 0
for r in csv.DictReader(open(P("data","processed","muni_index.csv"), encoding="utf-8")):
    mid = r["divipola"]; name = r["muni"]; dept = resolve_dept(mid, r["dept"], name)
    dv = real_dv(mid, name, dept)
    if dv is None or dv not in pop_by_dv: nojoin += 1; continue
    pr = pop_by_dv[dv]
    n = loc.get(mid, 0)
    acc = round(n / pr["pop"] * 10000, 3)
    rows.append({"id": mid, "name": name, "dept": dept, "pop": pr["pop"], "urb": pr["urb"],
                 "loc": n, "acc": acc, "lean": float(r["lean"]), "votval": int(r["votval"])})

# ---- mediana de acceso SOBRE MUNICIPIOS CON COBERTURA (OSM solo cubre parte) ----
covered = [x for x in rows if x["loc"] > 0]
accs = sorted(x["acc"] for x in covered)
med = round(accs[len(accs)//2], 3)
for x in rows:
    # deficit = locales faltantes vs la mediana de los municipios cubiertos
    x["deficit"] = round(max(0.0, med - x["acc"]) * x["pop"] / 10000, 0)
# cobertura: % municipios y % poblacion con al menos un local de cadena
cov_pop = sum(x["pop"] for x in covered)
coverage = {"munis_cubiertos": len(covered), "munis_total": len(rows),
            "pob_cubierta": cov_pop, "pob_total": sum(x["pop"] for x in rows)}

# ---- terciles para bivariado acceso x voto ----
def terciles(vals):
    s = sorted(vals); n = len(s); return (s[n//3], s[2*n//3])
at = terciles([x["acc"] for x in rows])
def acc_t(v): return 0 if v <= at[0] else (1 if v <= at[1] else 2)
def vote_t(l): return 0 if l < -0.05 else (2 if l > 0.05 else 1)  # Cepeda / 50-50 / De La Espriella
for x in rows: x["bi"] = acc_t(x["acc"]) * 3 + vote_t(x["lean"])

# ---- correlaciones de Spearman ----
def spearman(a, b):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i]); rk = [0]*len(v)
        for r2, i in enumerate(order): rk[i] = r2
        return rk
    ra, rb = rank(a), rank(b); n = len(a)
    d2 = sum((ra[i]-rb[i])**2 for i in range(n))
    return round(1 - 6*d2/(n*(n*n-1)), 3)
A = [x["acc"] for x in rows]; L = [x["lean"] for x in rows]; U = [x["urb"] for x in rows if x["urb"] is not None]
Lu = [x["lean"] for x in rows if x["urb"] is not None]
corr = {"acc_lean": spearman(A, L), "acc_urb": spearman([x["acc"] for x in rows if x["urb"] is not None], U),
        "urb_lean": spearman(U, Lu), "n": len(rows)}

meta = {"year": 2025, "median_acc": med, "acc_terciles": at, "coverage": coverage,
        "pop_total": sum(x["pop"] for x in rows), "loc_total": sum(x["loc"] for x in rows),
        "desc": "Acceso = locales de cadena por 10.000 hab (OSM / DANE 2025). Desierto = poblacion alta y acceso bajo."}
out = {"meta": meta, "corr": corr, "munis": rows}
with open(P("site2","acceso.js"), "w", encoding="utf-8") as f:
    f.write("window.ACC=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")

print(f"municipios con poblacion: {len(rows)} | sin empalme: {nojoin}")
print(f"cobertura: {coverage['munis_cubiertos']}/{coverage['munis_total']} munis "
      f"({100*coverage['pob_cubierta']/coverage['pob_total']:.0f}% de la poblacion)")
print(f"mediana acceso (cubiertos): {med} locales/10k | nacional: {meta['loc_total']} locales, {meta['pop_total']:,} hab")
print("correlaciones:", corr)
top_des = sorted([x for x in rows if x["loc"] > 0], key=lambda x: -x["deficit"])[:8]
print("mayores desiertos (cubiertos, pob alta + acceso bajo):", [(x["name"], int(x["pop"]), x["loc"], x["acc"], int(x["deficit"])) for x in top_des])
top_acc = sorted(rows, key=lambda x: -x["acc"])[:6]
print("mayor acceso:", [(x["name"], x["acc"], x["loc"]) for x in top_acc])
