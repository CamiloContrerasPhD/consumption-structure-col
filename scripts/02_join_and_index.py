# -*- coding: utf-8 -*-
"""Spatial-join stores to municipios, join 2026 vote margins, build multi-domain site data.
Outputs:
  data/processed/stores_geo.csv   one row per located store
  data/processed/muni_index.csv   one row per municipio
  site/data.js / site/data.json   structured {meta, domains:{...}} for the website
"""
import json, pickle, os, csv, unicodedata
from collections import defaultdict
from shapely.geometry import Point
from shapely import STRtree

BASE = os.path.join(os.path.dirname(__file__), "..")
P = lambda *a: os.path.join(BASE, *a)

def norm(s):
    if not s: return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    for ch in ".,-_": s = s.replace(ch, " ")
    s = " ".join(s.upper().split())
    changed = True
    while changed:
        changed = False
        for suf in (" DISTRITO CAPITAL", " MUNICIPIO", " DE INDIAS", " D C", " DC"):
            if s.endswith(suf):
                s = s[: -len(suf)].strip(); changed = True
    if "(" in s: s = s.split("(")[0].strip()
    return s

# brand -> (canonical name, domain, subcategory)
BRANDS = {
 # ---- TIENDAS Y COMPRAS ----
 "Exito":("Exito","tiendas","Supermercados"),"Olimpica":("Olimpica","tiendas","Supermercados"),
 "Carulla":("Carulla","tiendas","Supermercados"),"Jumbo":("Jumbo","tiendas","Supermercados"),
 "Metro":("Metro","tiendas","Supermercados"),"Makro":("Makro","tiendas","Supermercados"),
 "PriceSmart":("PriceSmart","tiendas","Supermercados"),"Super Inter":("Super Inter","tiendas","Supermercados"),
 "Surtimax":("Surtimax","tiendas","Supermercados"),
 "D1":("D1","tiendas","Descuento"),"Ara":("Ara","tiendas","Descuento"),"Tiendas ARA":("Ara","tiendas","Descuento"),
 "Dollarcity":("Dollarcity","tiendas","Descuento"),"Justo & Bueno":("Justo & Bueno","tiendas","Descuento"),
 "Oxxo":("Oxxo","tiendas","Descuento"),
 "Cruz Verde":("Cruz Verde","tiendas","Farmacias"),"Farmatodo":("Farmatodo","tiendas","Farmacias"),
 "Farmacenter":("Farmacenter","tiendas","Farmacias"),"La Rebaja":("La Rebaja","tiendas","Farmacias"),
 "Locatel":("Locatel","tiendas","Farmacias"),"Cafam":("Cafam","tiendas","Farmacias"),
 "Homecenter":("Homecenter","tiendas","Hogar y Tecnologia"),"Alkosto":("Alkosto","tiendas","Hogar y Tecnologia"),
 "Ktronix":("Ktronix","tiendas","Hogar y Tecnologia"),"Falabella":("Falabella","tiendas","Hogar y Tecnologia"),
 "Easy":("Easy","tiendas","Hogar y Tecnologia"),"Constructor":("Constructor","tiendas","Hogar y Tecnologia"),
 # ---- COMIDA Y BEBIDA ----
 "Juan Valdez Cafe":("Juan Valdez","comida","Cafe"),"Tostao":("Tostao","comida","Cafe"),
 "Cafe OMA":("Cafe OMA","comida","Cafe"),"Starbucks":("Starbucks","comida","Cafe"),"Dunkin'":("Dunkin","comida","Cafe"),
 "McDonald's":("McDonald's","comida","Comida rapida"),"KFC":("KFC","comida","Comida rapida"),
 "Burger King":("Burger King","comida","Comida rapida"),"Frisby":("Frisby","comida","Comida rapida"),
 "El Corral":("El Corral","comida","Comida rapida"),"Presto":("Presto","comida","Comida rapida"),
 "Kokoriko":("Kokoriko","comida","Comida rapida"),"Domino's":("Domino's","comida","Comida rapida"),
 "Subway":("Subway","comida","Comida rapida"),"Buffalo Wings":("Buffalo Wings","comida","Comida rapida"),
 "Sandwich Cubano":("Sandwich Cubano","comida","Comida rapida"),"Pan Pa' Ya!":("Pan Pa' Ya!","comida","Comida rapida"),
 "Crepes & Waffles":("Crepes & Waffles","comida","Restaurante"),
 # ---- SERVICIOS COTIDIANOS ----
 "Bancolombia":("Bancolombia","servicios","Bancos"),"Davivienda":("Davivienda","servicios","Bancos"),
 "Banco de Bogota":("Banco de Bogota","servicios","Bancos"),"Banco Agrario":("Banco Agrario","servicios","Bancos"),
 "BBVA":("BBVA","servicios","Bancos"),"Banco Caja Social":("Banco Caja Social","servicios","Bancos"),
 "Banco de Occidente":("Banco de Occidente","servicios","Bancos"),"Banco AV Villas":("Banco AV Villas","servicios","Bancos"),
 "Banco Popular":("Banco Popular","servicios","Bancos"),"Scotiabank Colpatria":("Scotiabank Colpatria","servicios","Bancos"),
 "Itau":("Itau","servicios","Bancos"),
 "Terpel":("Terpel","servicios","Gasolineras"),"Texaco":("Texaco","servicios","Gasolineras"),
 "Primax":("Primax","servicios","Gasolineras"),"Biomax":("Biomax","servicios","Gasolineras"),
 "Esso":("Esso","servicios","Gasolineras"),"Petromil":("Petromil","servicios","Gasolineras"),
 "Puma":("Puma","servicios","Gasolineras"),"Gazel":("Gazel","servicios","Gasolineras"),"Mobil":("Mobil","servicios","Gasolineras"),
 "Claro":("Claro","servicios","Telecomunicaciones"),"Movistar":("Movistar","servicios","Telecomunicaciones"),
 "Tigo":("Tigo","servicios","Telecomunicaciones"),"WOM":("WOM","servicios","Telecomunicaciones"),
}
BRANDS_N = {norm(k): v for k, v in BRANDS.items()}
DOMAIN_LABEL = {"tiendas":"Tiendas y Compras","comida":"Comida y Bebida","servicios":"Servicios Cotidianos"}
DOMAIN_DESC = {
 "tiendas":"Supermercados, tiendas de descuento, farmacias y almacenes de hogar y tecnologia.",
 "comida":"Cafeterias, comida rapida y restaurantes de cadena.",
 "servicios":"Bancos, estaciones de gasolina y operadores de telecomunicaciones.",
}
DOMAIN_NOUN = {"tiendas":"una cadena","comida":"una marca","servicios":"un servicio"}

# ---- polygons + STRtree ----
polys = pickle.load(open(P("data","processed","muni_polygons.pkl"), "rb"))
geoms = [p["geom"] for p in polys]
tree = STRtree(geoms)

# ---- votes ----
votes_by_name = defaultdict(list)
with open(P("data","raw","voto_2026_municipio.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        votval = float(r["votval"]) or 1.0
        r["lean"] = (float(r["abelardo"]) - float(r["ivan"])) / votval
        votes_by_name[norm(r["muni"])].append(r)

def match_vote(name, dept):
    cands = votes_by_name.get(norm(name), [])
    if not cands: return None
    if len(cands) == 1: return cands[0]
    nd = norm(dept)
    for c in cands:
        cd = norm(c["dep"])
        if nd and (nd.startswith(cd) or cd.startswith(nd) or nd[:8] == cd[:8]):
            return c
    return cands[0]

def disp(name):
    n = name
    for s in (" Distrito Capital - Municipio", " Distrito Capital", " - Municipio"):
        n = n.replace(s, "")
    return n.strip()
def pid(p):
    if "BOGOT" in norm(p["name"]): return "11001"   # Bogota lacks divipola tag in OSM
    return p["divipola"] or ("X" + norm(p["name"]).replace(" ", ""))

muni_rows = []
for p in polys:
    v = match_vote(p["name"], p["dept"]); p["vote"] = v
    p["id"] = pid(p); p["disp"] = disp(p["name"])
    if v:
        muni_rows.append({"divipola":p["id"],"muni":p["disp"],"dept":p["dept"],
                          "lean":round(v["lean"],4),"votval":int(float(v["votval"]))})
matched = sum(1 for p in polys if p["vote"])

# ---- stores ----
draw = json.load(open(P("data","raw","stores_raw.json"), encoding="utf-8"))
store_rows = []
agg = defaultdict(lambda: {"leans":[], "domain":None, "subcat":None})
unloc = 0
for e in draw["elements"]:
    key = BRANDS_N.get(norm(e.get("tags",{}).get("brand","")))
    if not key: continue
    canon, domain, subcat = key
    if "lat" in e: lon,lat = e["lon"],e["lat"]
    elif "center" in e: lon,lat = e["center"]["lon"],e["center"]["lat"]
    else: continue
    pt = Point(lon,lat); hit=None
    for i in tree.query(pt):
        if geoms[i].contains(pt): hit=polys[i]; break
    if hit is None or not hit["vote"]:
        unloc += 1; continue
    lean = hit["vote"]["lean"]
    store_rows.append([canon,domain,subcat,round(lon,5),round(lat,5),hit["id"],hit["disp"],hit["dept"],round(lean,4)])
    a = agg[canon]; a["leans"].append(lean); a["domain"]=domain; a["subcat"]=subcat

# ---- brand index per domain ----
domains = {}
for canon, a in agg.items():
    n = len(a["leans"])
    if n < 5: continue
    d = a["domain"]
    domains.setdefault(d, {"label":DOMAIN_LABEL[d],"desc":DOMAIN_DESC[d],"noun":DOMAIN_NOUN[d],
                           "subcats":set(),"brands":[]})
    domains[d]["subcats"].add(a["subcat"])
    domains[d]["brands"].append({"brand":canon,"subcat":a["subcat"],"n_stores":n,
                                 "index":round(sum(a["leans"])/n,4)})
for d in domains:
    domains[d]["subcats"] = sorted(domains[d]["subcats"])
    domains[d]["brands"].sort(key=lambda x:x["index"])

# ---- write ----
os.makedirs(P("data","processed"), exist_ok=True)
with open(P("data","processed","stores_geo.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["brand","domain","subcat","lon","lat","divipola","muni","dept","lean"]); w.writerows(store_rows)
with open(P("data","processed","muni_index.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["divipola","muni","dept","lean","votval"]); w.writeheader(); w.writerows(muni_rows)

site = {
 "meta":{
   "eje":"Primera vuelta presidencial 2026 (Registraduria, boletin de preconteo)",
   "polo_neg":"Ivan Cepeda","polo_pos":"Abelardo De La Espriella",
   "fuente_voto":"Registraduria Nacional, 2026","fuente_consumo":"OpenStreetMap (tag brand), 2026",
   "n_municipios":matched,"n_locales":len(store_rows),
 },
 "domain_order":["tiendas","comida","servicios"],
 "domains":domains,
}
with open(P("site","data.json"),"w",encoding="utf-8") as f: json.dump(site,f,ensure_ascii=False,indent=1)
with open(P("site","data.js"),"w",encoding="utf-8") as f: f.write("window.SITE = "+json.dumps(site,ensure_ascii=False)+";")

print(f"matched_muni={matched} located={len(store_rows)} unloc={unloc}")
for d in site["domain_order"]:
    if d in domains:
        b=domains[d]["brands"]
        print(f"  {d}: {len(b)} marcas | izq {b[0]['brand']}({b[0]['index']:+.3f}) der {b[-1]['brand']}({b[-1]['index']:+.3f})")
