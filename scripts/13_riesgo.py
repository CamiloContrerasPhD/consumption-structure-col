"""Riesgo de tomar partido (Sitio 2): simulador de exposicion al activismo de marca.
Por marca (>=10 locales):
  - composicion politica de la huella: % locales en territorio Cepeda / 50-50 / De La Espriella
  - exposicion extrema: % locales en municipios con |lean|>30 pts de cada lado
  - share dentro de su dominio (proxy de market share, por conteo de locales)
Logica del simulador (ilustrativa, anclada en evidencia US):
  - Hydock, Paharia & Blair (2020, JMR): el efecto neto del activismo depende del share
    (marcas de share bajo pueden ganar; las de share alto tienden a perder).
  - Hou & Poliquin (2022, SMJ): tras activismo de CEO, visitas -5% en condados mas opuestos,
    ~0 en alineados, disipado en ~10 semanas.
Output: site2/riesgo.js  window.RK = {meta, brands:[...]}
"""
import os, csv, json
from collections import defaultdict

BASE = os.path.join(os.path.dirname(__file__), "..")
P = lambda *a: os.path.join(BASE, *a)

EXT = 0.30   # umbral de territorio "extremo"
MIX = 0.05   # umbral 50/50

br = defaultdict(lambda: {"n":0,"dom":"","leansum":0.0,
                          "cep":0,"mix":0,"dle":0,"cep_ext":0,"dle_ext":0})
dom_tot = defaultdict(int)
for s in csv.DictReader(open(P("data","processed","stores_geo.csv"), encoding="utf-8")):
    lean = float(s["lean"]); b = br[s["brand"]]
    b["n"] += 1; b["dom"] = s["domain"]; b["leansum"] += lean
    dom_tot[s["domain"]] += 1
    if lean < -MIX: b["cep"] += 1
    elif lean > MIX: b["dle"] += 1
    else: b["mix"] += 1
    if lean < -EXT: b["cep_ext"] += 1
    if lean > EXT: b["dle_ext"] += 1

brands = []
for name, b in sorted(br.items()):
    if b["n"] < 10: continue
    n = b["n"]
    brands.append({
        "brand": name, "domain": b["dom"], "n": n,
        "lean": round(b["leansum"]/n, 4),
        "share": round(n/dom_tot[b["dom"]], 4),          # share del dominio (por locales)
        "cep": round(b["cep"]/n, 4), "mix": round(b["mix"]/n, 4), "dle": round(b["dle"]/n, 4),
        "cep_ext": round(b["cep_ext"]/n, 4), "dle_ext": round(b["dle_ext"]/n, 4),
    })
brands.sort(key=lambda x: x["brand"].lower())

meta = {"ext_thr": EXT, "mix_thr": MIX, "n_brands": len(brands),
        "dom_tot": dict(dom_tot),
        "desc": "Composicion politica de la huella por marca + exposicion extrema + share por dominio. "
                "Umbral extremo |lean|>30 pts; 50/50 |lean|<=5 pts."}
with open(P("site2","riesgo.js"), "w", encoding="utf-8") as f:
    f.write("window.RK=" + json.dumps({"meta": meta, "brands": brands}, ensure_ascii=False, separators=(",",":")) + ";\n")

print(f"marcas: {len(brands)}")
ex = [x for x in brands if x["brand"] in ("Exito","D1","Ara","Crepes & Waffles","Juan Valdez")]
for x in ex:
    print(f"  {x['brand']:20s} n={x['n']:4d} share={x['share']:.2f} lean={x['lean']*100:+.0f} "
          f"cep={x['cep']:.2f} mix={x['mix']:.2f} dle={x['dle']:.2f} ext(c/d)={x['cep_ext']:.2f}/{x['dle_ext']:.2f}")
