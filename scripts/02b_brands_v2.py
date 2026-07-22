# -*- coding: utf-8 -*-
"""Universo de marcas AMPLIADO (v2): combina multiples fuentes OSM (brand-tagged + por tipo de tienda),
normaliza variantes de nombre y mapea ~110 marcas en 6 dominios (incluye Moda, Automotriz, Variedades).
Sustituye a 02_join_and_index.py para los sitios.
Salidas: data/processed/stores_geo.csv, site/data.json, site/data.js
"""
import csv, json, os, unicodedata
from collections import defaultdict, Counter
from shapely.geometry import Point
from shapely import STRtree

BASE = os.path.join(os.path.dirname(__file__), "..")
P = lambda *a: os.path.join(BASE, *a)

def norm(s):
    if not s: return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    for ch in ".,-_'&": s = s.replace(ch, " ")
    s = " ".join(s.upper().split())
    changed = True
    while changed:
        changed = False
        for suf in (" DISTRITO CAPITAL", " MUNICIPIO", " DE INDIAS", " D C", " DC"):
            if s.endswith(suf): s = s[:-len(suf)].strip(); changed = True
    if "(" in s: s = s.split("(")[0].strip()
    return s

# ---- brand groups: (canonical, domain, subcat, [variantes]) ----
GROUPS = [
 # DESCUENTO
 ("D1","tiendas","Descuento",["D1","Tiendas D1","Tienda D1","Supermercado D1"]),
 ("Ara","tiendas","Descuento",["Ara","Tiendas Ara","Tienda Ara"]),
 ("Dollarcity","tiendas","Descuento",["Dollarcity","Dollar City"]),
 ("Justo & Bueno","tiendas","Descuento",["Justo & Bueno","Justo y Bueno","Mercaderia Justo & Bueno"]),
 ("Isimo","tiendas","Descuento",["Isimo","Tiendas Isimo"]),
 ("Oxxo","tiendas","Descuento",["Oxxo"]),
 # SUPERMERCADOS
 ("Exito","tiendas","Supermercados",["Exito","Exito Express","Almacenes Exito","Exito Vecino"]),
 ("Carulla","tiendas","Supermercados",["Carulla","Carulla Express","Carulla Fresh Market"]),
 ("Olimpica","tiendas","Supermercados",["Olimpica","Supertiendas Olimpica","SAO","Super Almacenes Olimpica"]),
 ("Jumbo","tiendas","Supermercados",["Jumbo","Jumbo Cencosud"]),
 ("Metro","tiendas","Supermercados",["Metro"]),
 ("Makro","tiendas","Supermercados",["Makro"]),
 ("PriceSmart","tiendas","Supermercados",["PriceSmart","Price Smart"]),
 ("Surtimax","tiendas","Supermercados",["Surtimax","Surti Max"]),
 ("Super Inter","tiendas","Supermercados",["Super Inter","Superinter","Supermercados Super Inter"]),
 ("Surtimayorista","tiendas","Supermercados",["Surtimayorista","Surti Mayorista"]),
 ("Colsubsidio","tiendas","Supermercados",["Colsubsidio","Mercado Colsubsidio","Supermercado Colsubsidio"]),
 ("Cooratiendas","tiendas","Supermercados",["Cooratiendas","Coratiendas"]),
 ("Mercaldas","tiendas","Supermercados",["Mercaldas"]),
 ("Mercacentro","tiendas","Supermercados",["Mercacentro"]),
 ("Mercamas","tiendas","Supermercados",["Mercamas","Mercamos"]),
 ("Zapatoca","tiendas","Supermercados",["Zapatoca","Supermercados Zapatoca"]),
 ("Comfandi","tiendas","Supermercados",["Comfandi"]),
 ("Euro","tiendas","Supermercados",["Euro","Euro Supermercados"]),
 ("Megatiendas","tiendas","Supermercados",["Megatiendas","Mega Tiendas"]),
 ("La Canasta","tiendas","Supermercados",["La Canasta"]),
 ("Pomona","tiendas","Supermercados",["Pomona"]),
 ("Surtifruver","tiendas","Supermercados",["Surtifruver","Surtifruver de la Sabana"]),
 ("Consumo","tiendas","Supermercados",["Consumo","Almacenes Consumo"]),
 ("Mercamio","tiendas","Supermercados",["Mercamio"]),
 # FARMACIAS
 ("Cruz Verde","tiendas","Farmacias",["Cruz Verde"]),
 ("Farmatodo","tiendas","Farmacias",["Farmatodo"]),
 ("Farmacenter","tiendas","Farmacias",["Farmacenter"]),
 ("La Rebaja","tiendas","Farmacias",["La Rebaja","Drogas La Rebaja","La Rebaja Plus","Drogueria La Rebaja","Droguerias La Rebaja"]),
 ("Locatel","tiendas","Farmacias",["Locatel"]),
 ("Audifarma","tiendas","Farmacias",["Audifarma"]),
 ("Drogueria Alemana","tiendas","Farmacias",["Drogueria Alemana"]),
 ("Drogueria Inglesa","tiendas","Farmacias",["Drogueria Inglesa"]),
 ("Drogas La Economia","tiendas","Farmacias",["Drogas La Economia","La Economia"]),
 ("Pasteur","tiendas","Farmacias",["Pasteur","Farmacia Pasteur","Drogueria Pasteur"]),
 ("Multidrogas","tiendas","Farmacias",["Multidrogas"]),
 ("Cafam","tiendas","Farmacias",["Cafam","Drogueria Cafam"]),
 # HOGAR Y TECNOLOGIA
 ("Homecenter","tiendas","Hogar y Tecnologia",["Homecenter","Home Center"]),
 ("Alkosto","tiendas","Hogar y Tecnologia",["Alkosto"]),
 ("Ktronix","tiendas","Hogar y Tecnologia",["Ktronix"]),
 ("Falabella","tiendas","Hogar y Tecnologia",["Falabella"]),
 ("Easy","tiendas","Hogar y Tecnologia",["Easy"]),
 ("Constructor","tiendas","Hogar y Tecnologia",["Constructor"]),
 # VARIEDADES
 ("Miniso","tiendas","Variedades",["Miniso"]),
 ("Office Depot","tiendas","Variedades",["Office Depot"]),
 ("Pepe Ganga","tiendas","Variedades",["Pepe Ganga"]),
 # MODA
 ("Arturo Calle","moda","Ropa",["Arturo Calle"]),
 ("Studio F","moda","Ropa",["Studio F","Studio F Man"]),
 ("Koaj","moda","Ropa",["Koaj","Koaj Basic"]),
 ("Lili Pink","moda","Ropa",["Lili Pink"]),
 ("Diane & Geordi","moda","Ropa",["Diane & Geordi"]),
 ("Pat Primo","moda","Ropa",["Pat Primo","Patprimo"]),
 ("Americanino","moda","Ropa",["Americanino"]),
 ("Gef","moda","Ropa",["Gef"]),
 ("Levi's","moda","Ropa",["Levi's","Levis"]),
 ("H&M","moda","Ropa",["H&M"]),
 ("Zara","moda","Ropa",["Zara"]),
 ("Totto","moda","Accesorios",["Totto"]),
 ("Velez","moda","Accesorios",["Velez"]),
 ("Bata","moda","Calzado",["Bata"]),
 ("Spring Step","moda","Calzado",["Spring Step"]),
 ("Aquiles","moda","Calzado",["Aquiles"]),
 ("Bosi","moda","Calzado",["Bosi"]),
 ("Facol","moda","Calzado",["Facol"]),
 ("Adidas","moda","Deportiva",["Adidas"]),
 ("Nike","moda","Deportiva",["Nike"]),
 ("Decathlon","moda","Deportiva",["Decathlon"]),
 # AUTOMOTRIZ
 ("Renault","automotriz","Carros",["Renault"]),
 ("Chevrolet","automotriz","Carros",["Chevrolet"]),
 ("Toyota","automotriz","Carros",["Toyota"]),
 ("Mazda","automotriz","Carros",["Mazda"]),
 ("Kia","automotriz","Carros",["Kia"]),
 ("Nissan","automotriz","Carros",["Nissan"]),
 ("Hyundai","automotriz","Carros",["Hyundai"]),
 ("Ford","automotriz","Carros",["Ford"]),
 ("Volkswagen","automotriz","Carros",["Volkswagen"]),
 ("Mercedes-Benz","automotriz","Carros",["Mercedes-Benz","Mercedes Benz"]),
 ("BMW","automotriz","Carros",["BMW"]),
 ("Yamaha","automotriz","Motos",["Yamaha"]),
 ("Honda","automotriz","Motos",["Honda"]),
 ("Suzuki","automotriz","Motos",["Suzuki"]),
 ("Bajaj","automotriz","Motos",["Bajaj"]),
 ("AKT","automotriz","Motos",["AKT"]),
 ("Auteco","automotriz","Motos",["Auteco"]),
 # COMIDA
 ("Juan Valdez","comida","Cafe",["Juan Valdez","Juan Valdez Cafe"]),
 ("Tostao","comida","Cafe",["Tostao","Tostao Cafe & Pan"]),
 ("Cafe OMA","comida","Cafe",["Cafe OMA","OMA"]),
 ("Starbucks","comida","Cafe",["Starbucks"]),
 ("Dunkin","comida","Cafe",["Dunkin","Dunkin Donuts"]),
 ("McDonald's","comida","Comida rapida",["McDonald's","McDonalds"]),
 ("KFC","comida","Comida rapida",["KFC"]),
 ("Burger King","comida","Comida rapida",["Burger King"]),
 ("Frisby","comida","Comida rapida",["Frisby"]),
 ("El Corral","comida","Comida rapida",["El Corral","Hamburguesas El Corral"]),
 ("Presto","comida","Comida rapida",["Presto"]),
 ("Kokoriko","comida","Comida rapida",["Kokoriko"]),
 ("Domino's","comida","Comida rapida",["Domino's","Dominos","Domino's Pizza"]),
 ("Subway","comida","Comida rapida",["Subway"]),
 ("Sandwich Qbano","comida","Comida rapida",["Sandwich Qbano","Sandwichqbano","Qbano"]),
 ("Jeno's Pizza","comida","Comida rapida",["Jeno's Pizza","Jenos Pizza"]),
 ("Pizza Hut","comida","Comida rapida",["Pizza Hut"]),
 ("Papa John's","comida","Comida rapida",["Papa John's","Papa Johns"]),
 ("Little Caesars","comida","Comida rapida",["Little Caesars"]),
 ("Home Burgers","comida","Comida rapida",["Home Burgers"]),
 ("La Brasa Roja","comida","Comida rapida",["La Brasa Roja","Brasa Roja"]),
 ("Buffalo Wings","comida","Comida rapida",["Buffalo Wings","Buffalo Grill"]),
 ("Pan Pa' Ya!","comida","Comida rapida",["Pan Pa' Ya!","Pan Pa Ya"]),
 ("Crepes & Waffles","comida","Restaurante",["Crepes & Waffles","Crepes y Waffles"]),
 ("Popsy","comida","Heladeria",["Popsy"]),
 ("Mimos","comida","Heladeria",["Mimos","Heladeria Mimos","Helados Mimos"]),
 ("Cosechas","comida","Bebidas",["Cosechas"]),
 # BANCOS
 ("Bancolombia","servicios","Bancos",["Bancolombia"]),
 ("Davivienda","servicios","Bancos",["Davivienda","DAVIbank"]),
 ("Banco de Bogota","servicios","Bancos",["Banco de Bogota"]),
 ("Banco Agrario","servicios","Bancos",["Banco Agrario","Banco Agrario de Colombia"]),
 ("BBVA","servicios","Bancos",["BBVA"]),
 ("Banco Caja Social","servicios","Bancos",["Banco Caja Social"]),
 ("Banco de Occidente","servicios","Bancos",["Banco de Occidente"]),
 ("Banco AV Villas","servicios","Bancos",["Banco AV Villas","AV Villas"]),
 ("Banco Popular","servicios","Bancos",["Banco Popular"]),
 ("Scotiabank Colpatria","servicios","Bancos",["Scotiabank Colpatria","Scotiabank","Colpatria"]),
 ("Itau","servicios","Bancos",["Itau","Itau Corpbanca"]),
 ("Banco Pichincha","servicios","Bancos",["Banco Pichincha"]),
 ("Banco Falabella","servicios","Bancos",["Banco Falabella"]),
 ("GNB Sudameris","servicios","Bancos",["GNB Sudameris"]),
 ("Bancoomeva","servicios","Bancos",["Bancoomeva","Bancomeeva"]),
 # GASOLINERAS
 ("Terpel","servicios","Gasolineras",["Terpel"]),
 ("Texaco","servicios","Gasolineras",["Texaco"]),
 ("Primax","servicios","Gasolineras",["Primax"]),
 ("Biomax","servicios","Gasolineras",["Biomax"]),
 ("Esso","servicios","Gasolineras",["Esso"]),
 ("Petromil","servicios","Gasolineras",["Petromil"]),
 ("Puma","servicios","Gasolineras",["Puma"]),
 ("Gazel","servicios","Gasolineras",["Gazel"]),
 ("Mobil","servicios","Gasolineras",["Mobil"]),
 ("Zeuss","servicios","Gasolineras",["Zeuss","Zeus"]),
 ("Petrobras","servicios","Gasolineras",["Petrobras"]),
 ("Brio","servicios","Gasolineras",["Brio"]),
 ("Shell","servicios","Gasolineras",["Shell"]),
 ("Octano","servicios","Gasolineras",["Octano"]),
 # TELECOM
 ("Claro","servicios","Telecomunicaciones",["Claro"]),
 ("Movistar","servicios","Telecomunicaciones",["Movistar"]),
 ("Tigo","servicios","Telecomunicaciones",["Tigo"]),
 ("WOM","servicios","Telecomunicaciones",["WOM"]),
]
ALIAS = {}
for canon, dom, sub, variants in GROUPS:
    for v in [canon] + variants:
        ALIAS[norm(v)] = (canon, dom, sub)
# fallback contains-rules para grafias sueltas (substring del nombre normalizado)
CONTAINS = [("LA REBAJA","La Rebaja","tiendas","Farmacias"),
            ("JUSTO Y BUENO","Justo & Bueno","tiendas","Descuento"),
            ("JUSTO BUENO","Justo & Bueno","tiendas","Descuento"),
            ("SANDWICH QBANO","Sandwich Qbano","comida","Comida rapida"),
            ("SANDWICHQBANO","Sandwich Qbano","comida","Comida rapida"),
            ("MEGA TIENDAS","Megatiendas","tiendas","Supermercados"),
            ("SURTI MAX","Surtimax","tiendas","Supermercados"),
            ("DROGUERIA COLSUBSIDIO","Colsubsidio","tiendas","Farmacias"),
            ("COSECHAS","Cosechas","comida","Bebidas")]

DOMAIN_LABEL={"tiendas":"Tiendas y Compras","comida":"Comida y Bebida","servicios":"Servicios Cotidianos",
              "moda":"Moda y Calzado","automotriz":"Vehiculos","variedades":"Variedades"}
DOMAIN_DESC={"tiendas":"Supermercados, descuento, farmacias y hogar y tecnologia.",
             "comida":"Cafe, comida rapida, restaurante y heladeria.",
             "servicios":"Bancos, gasolineras y telecomunicaciones.",
             "moda":"Ropa, calzado y deportiva.","automotriz":"Concesionarios de carros y motos.",
             "variedades":"Tiendas de variedades y miscelanea."}
DOMAIN_NOUN={"tiendas":"una cadena","comida":"una marca","servicios":"un servicio",
             "moda":"una marca","automotriz":"una marca","variedades":"una tienda"}
DOMAIN_ORDER=["tiendas","comida","servicios","moda","automotriz","variedades"]

def classify(tags):
    for key in (tags.get("brand"), tags.get("name")):
        if not key: continue
        n = norm(key)
        if n in ALIAS: return ALIAS[n]
    nm_name = norm(tags.get("name") or tags.get("brand") or "")
    for sub_s, canon, dom, sub in CONTAINS:
        if sub_s in nm_name: return (canon, dom, sub)
    return None

# ---- load polygons + STRtree + votes (same as 02) ----
import pickle
polys = pickle.load(open(P("data","processed","muni_polygons.pkl"), "rb"))
geoms=[p["geom"] for p in polys]; tree=STRtree(geoms)
votes_by_name=defaultdict(list)
for r in csv.DictReader(open(P("data","raw","voto_2026_municipio.csv"), encoding="utf-8")):
    votval=float(r["votval"]) or 1.0
    r["lean"]=(float(r["abelardo"])-float(r["ivan"]))/votval
    votes_by_name[norm(r["muni"])].append(r)
def match_vote(name, dept):
    cands=votes_by_name.get(norm(name),[])
    if not cands: return None
    if len(cands)==1: return cands[0]
    nd=norm(dept)
    for c in cands:
        cd=norm(c["dep"])
        if nd and (nd.startswith(cd) or cd.startswith(nd) or nd[:8]==cd[:8]): return c
    return cands[0]
def disp(name):
    n=name
    for s in (" Distrito Capital - Municipio"," Distrito Capital"," - Municipio"): n=n.replace(s,"")
    return n.strip()
def pid(p):
    if "BOGOT" in norm(p["name"]): return "11001"
    return p["divipola"] or ("X"+norm(p["name"]).replace(" ",""))
for p in polys:
    v=match_vote(p["name"],p["dept"]); p["vote"]=v; p["id"]=pid(p); p["disp"]=disp(p["name"])

# ---- load + dedup all OSM sources ----
SOURCES=["stores_raw.json","shops_super.json","shops_pharma.json","shops_ropa.json","shops_food.json"]
seen=set(); store_rows=[]; agg=defaultdict(lambda:{"leans":[],"domain":None,"subcat":None})
unloc=0; nomatch=0
for src in SOURCES:
    path=P("data","raw",src)
    if not os.path.exists(path): continue
    for e in json.load(open(path,encoding="utf-8"))["elements"]:
        key=(e["type"],e["id"])
        if key in seen: continue
        seen.add(key)
        cl=classify(e.get("tags",{}))
        if not cl: nomatch+=1; continue
        canon,dom,sub=cl
        if "lat" in e: lon,lat=e["lon"],e["lat"]
        elif "center" in e: lon,lat=e["center"]["lon"],e["center"]["lat"]
        else: continue
        pt=Point(lon,lat); hit=None
        for i in tree.query(pt):
            if geoms[i].contains(pt): hit=polys[i]; break
        if hit is None or not hit["vote"]: unloc+=1; continue
        lean=hit["vote"]["lean"]
        store_rows.append([canon,dom,sub,round(lon,5),round(lat,5),hit["id"],hit["disp"],hit["dept"],round(lean,4)])
        a=agg[canon]; a["leans"].append(lean); a["domain"]=dom; a["subcat"]=sub

# ---- brand index per domain ----
domains={}
for canon,a in agg.items():
    n=len(a["leans"])
    if n<5: continue
    d=a["domain"]
    domains.setdefault(d,{"label":DOMAIN_LABEL[d],"desc":DOMAIN_DESC[d],"noun":DOMAIN_NOUN[d],"subcats":set(),"brands":[]})
    domains[d]["subcats"].add(a["subcat"])
    domains[d]["brands"].append({"brand":canon,"subcat":a["subcat"],"n_stores":n,"index":round(sum(a["leans"])/n,4)})
for d in domains:
    domains[d]["subcats"]=sorted(domains[d]["subcats"]); domains[d]["brands"].sort(key=lambda x:x["index"])

os.makedirs(P("data","processed"),exist_ok=True)
with open(P("data","processed","stores_geo.csv"),"w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["brand","domain","subcat","lon","lat","divipola","muni","dept","lean"]); w.writerows(store_rows)
matched=sum(1 for p in polys if p["vote"])
site={"meta":{"eje":"Primera vuelta presidencial 2026 (Registraduria)","polo_neg":"Ivan Cepeda","polo_pos":"Abelardo De La Espriella",
              "fuente_voto":"Registraduria 2026","fuente_consumo":"OpenStreetMap 2026 (multi-fuente)","n_municipios":matched,"n_locales":len(store_rows)},
      "domain_order":[d for d in DOMAIN_ORDER if d in domains],"domains":domains}
with open(P("site","data.json"),"w",encoding="utf-8") as f: json.dump(site,f,ensure_ascii=False,indent=1)
with open(P("site","data.js"),"w",encoding="utf-8") as f: f.write("window.SITE = "+json.dumps(site,ensure_ascii=False)+";")

print(f"localizados={len(store_rows)} sin_match_marca={nomatch} fuera/sin_voto={unloc} | municipios_voto={matched}")
print(f"marcas en sitio={sum(len(domains[d]['brands']) for d in domains)} | dominios={list(domains.keys())}")
for d in site["domain_order"]:
    b=domains[d]["brands"]
    print(f"  {d}: {len(b)} marcas | izq {b[0]['brand']}({b[0]['index']:+.3f}) der {b[-1]['brand']}({b[-1]['index']:+.3f})")
