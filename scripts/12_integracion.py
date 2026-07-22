"""Integracion del mercado (Sitio 2): ¿el consumo esta menos segregado que el electorado?
Replica territorial de Davis et al. (2019, JPE) "How Segregated Is Urban Consumption?" con
el indice de segregacion de razon de varianza (eta^2, Massey & Denton 1988):

  S = sum_u w_u (p_u - P)^2 / (P (1-P))

- Electorado (S_res): unidades = municipios, p_m = proporcion De La Espriella (aprox (1+lean)/2),
  pesos = votos validos. Cuanto revela TU MUNICIPIO sobre tu campo politico.
- Consumo (S_cons): unidades = cadenas, p_b = p promedio de la huella de la marca (ponderada por
  locales), pesos = nro de locales. Cuanto revela TU CADENA sobre tu campo politico.
- ratio = S_cons / S_res: el mercado esta X% tan segregado como el electorado.

Ademas: indice puente por marca (min(share en territorio Cepeda, share en territorio DLE)*2),
segregacion por dominio, y municipios de encuentro (|lean|<5 pts + comercio).
Output: site2/integracion.js  window.IN = {meta, cats, brands, encounter, munis}
"""
import os, csv, json
from collections import defaultdict

BASE = os.path.join(os.path.dirname(__file__), "..")
P = lambda *a: os.path.join(BASE, *a)

# ---- electorate baseline over ALL municipios ----
E = []  # (p_m, votval)
for r in csv.DictReader(open(P("data","processed","muni_index.csv"), encoding="utf-8")):
    lean = float(r["lean"]); vot = int(r["votval"])
    E.append(((1+lean)/2, vot))
TOT = sum(v for _, v in E)
Pn = sum(p*v for p, v in E) / TOT
S_res = sum(v/TOT * (p-Pn)**2 for p, v in E) / (Pn*(1-Pn))

# ---- stores: per-brand footprint ----
stores = list(csv.DictReader(open(P("data","processed","stores_geo.csv"), encoding="utf-8")))
br = defaultdict(lambda: {"n":0, "psum":0.0, "cep":0, "dle":0, "dom":"", "leansum":0.0})
mu = defaultdict(lambda: {"n":0, "lean":0.0, "name":"", "dept":"", "votval":0})
for s in stores:
    lean = float(s["lean"]); p = (1+lean)/2
    b = br[s["brand"]]
    b["n"] += 1; b["psum"] += p; b["dom"] = s["domain"]; b["leansum"] += lean
    if lean > 0: b["dle"] += 1
    else: b["cep"] += 1
    m = mu[s["divipola"]]
    m["n"] += 1; m["lean"] = lean; m["name"] = s["muni"]; m["dept"] = s["dept"]

# votval per muni for encounter ranking
votv = {r["divipola"]: int(r["votval"]) for r in csv.DictReader(open(P("data","processed","muni_index.csv"), encoding="utf-8"))}

NTOT = sum(b["n"] for b in br.values())
Pc = sum(b["psum"] for b in br.values()) / NTOT   # store-encounter national share
S_cons = sum(b["n"]/NTOT * (b["psum"]/b["n"] - Pc)**2 for b in br.values()) / (Pc*(1-Pc))
ratio = S_cons / S_res

# ---- per-domain segregation (across its brands) ----
cats = []
by_dom = defaultdict(list)
for name, b in br.items(): by_dom[b["dom"]].append(b)
for dom, bl in sorted(by_dom.items()):
    nd = sum(b["n"] for b in bl)
    Pd = sum(b["psum"] for b in bl) / nd
    Sd = sum(b["n"]/nd * (b["psum"]/b["n"] - Pd)**2 for b in bl) / max(Pd*(1-Pd), 1e-9)
    cats.append({"domain": dom, "S": round(Sd,4), "n": nd})
cats.sort(key=lambda x: -x["S"])

# ---- bridge index per brand (brands with >= 10 outlets) ----
brands_out = []
for name, b in sorted(br.items()):
    if b["n"] < 10: continue
    sh_c, sh_d = b["cep"]/b["n"], b["dle"]/b["n"]
    brands_out.append({"brand": name, "domain": b["dom"], "n": b["n"],
                       "lean": round(b["leansum"]/b["n"],4),
                       "bridge": round(2*min(sh_c, sh_d),3),
                       "cep": round(sh_c,3), "dle": round(sh_d,3)})
brands_out.sort(key=lambda x: -x["bridge"])

# ---- encounter municipios: |lean| < 0.05 with commerce ----
encounter = []
for mid, m in mu.items():
    if abs(m["lean"]) < 0.05 and m["n"] > 0:
        encounter.append({"id": mid, "name": m["name"], "dept": m["dept"],
                          "lean": round(m["lean"],4), "loc": m["n"], "votval": votv.get(mid,0)})
encounter.sort(key=lambda x: -x["loc"])

# munis for map (all with stores)
munis_out = [{"id": mid, "lean": round(m["lean"],4), "loc": m["n"]} for mid, m in mu.items()]

meta = {"S_res": round(S_res,4), "S_cons": round(S_cons,4), "ratio": round(ratio,4),
        "P_nat": round(Pn,4), "n_stores": NTOT, "n_brands_idx": len(brands_out),
        "n_encounter": len(encounter),
        "desc": "Indice de segregacion (razon de varianza / eta2). S_res sobre municipios "
                "(votos); S_cons sobre cadenas (locales). ratio = S_cons/S_res."}
out = {"meta": meta, "cats": cats, "brands": brands_out, "encounter": encounter[:14], "munis": munis_out}
with open(P("site2","integracion.js"), "w", encoding="utf-8") as f:
    f.write("window.IN=" + json.dumps(out, ensure_ascii=False, separators=(",",":")) + ";\n")

print(f"S_electorado={S_res:.4f}  S_consumo={S_cons:.4f}  ratio={ratio:.3f} "
      f"-> el consumo esta {ratio*100:.0f}% tan segregado como el electorado")
print("dominios mas ordenados politicamente:", [(c['domain'], c['S']) for c in cats])
print("marcas puente top:", [(b['brand'], b['bridge']) for b in brands_out[:6]])
print("marcas burbuja:", [(b['brand'], b['bridge'], round(b['lean']*100)) for b in brands_out[-6:]])
print("municipios de encuentro (top):", [(e['name'], e['loc'], round(e['lean']*100)) for e in encounter[:6]])
