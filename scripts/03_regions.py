# -*- coding: utf-8 -*-
"""Geographic layer: choropleth + region/dept/city rankings (extremos y 50/50) + brand linkage.
Outputs:
  site/geo.js  ->  window.GEO_MUNI (simplified GeoJSON, lean per municipio)
                   window.GEO_AGG  (regions/depts/cities buckets + brand buckets + meta)
"""
import json, pickle, os, csv, unicodedata
from collections import defaultdict, Counter

def nrm(s):
    if not s: return ""
    return unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().upper().strip()
def pid(name, divipola):
    if "BOGOT" in nrm(name): return "11001"
    return divipola or ("X" + nrm(name).replace(" ", ""))
from shapely.geometry import mapping

BASE = os.path.join(os.path.dirname(__file__), "..")
P = lambda *a: os.path.join(BASE, *a)

# DANE 2-digit dept code -> (name, region)
DANE = {
 "05":("Antioquia","Andina"),"08":("Atlantico","Caribe"),"11":("Bogota D.C.","Andina"),
 "13":("Bolivar","Caribe"),"15":("Boyaca","Andina"),"17":("Caldas","Andina"),"18":("Caqueta","Amazonia"),
 "19":("Cauca","Pacifico"),"20":("Cesar","Caribe"),"23":("Cordoba","Caribe"),"25":("Cundinamarca","Andina"),
 "27":("Choco","Pacifico"),"41":("Huila","Andina"),"44":("La Guajira","Caribe"),"47":("Magdalena","Caribe"),
 "50":("Meta","Orinoquia"),"52":("Narino","Pacifico"),"54":("Norte de Santander","Andina"),
 "63":("Quindio","Andina"),"66":("Risaralda","Andina"),"68":("Santander","Andina"),"70":("Sucre","Caribe"),
 "73":("Tolima","Andina"),"76":("Valle del Cauca","Pacifico"),"81":("Arauca","Orinoquia"),
 "85":("Casanare","Orinoquia"),"86":("Putumayo","Amazonia"),"88":("San Andres","Caribe"),
 "91":("Amazonas","Amazonia"),"94":("Guainia","Amazonia"),"95":("Guaviare","Amazonia"),
 "97":("Vaupes","Amazonia"),"99":("Vichada","Orinoquia"),
}

# dept-name (normalized) -> (canonical dept, region), for municipios without DIVIPOLA
NAME2 = {nrm(n):(n,reg) for n,reg in DANE.values()}
NAME2["CUDINAMARCA"] = ("Cundinamarca","Andina")  # OSM typo

MUNI_OVERRIDE = {  # municipios sin DIVIPOLA ni depto resoluble en OSM
    "PASTO":("Narino","Pacifico"),"FACATATIVA":("Cundinamarca","Andina"),
    "SOGAMOSO":("Boyaca","Andina"),
}
def resolve(divipola, osm_dept, name=""):
    dv = (divipola or "")[:2]
    if dv in DANE: return DANE[dv]
    if nrm(name) in MUNI_OVERRIDE: return MUNI_OVERRIDE[nrm(name)]
    if osm_dept and osm_dept.isdigit() and osm_dept.zfill(2) in DANE: return DANE[osm_dept.zfill(2)]
    if nrm(osm_dept) in NAME2: return NAME2[nrm(osm_dept)]
    return (osm_dept or "?", "?")

# ---- municipio index ----
munis = []
with open(P("data","processed","muni_index.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        d, reg = resolve(r["divipola"], r["dept"], r["muni"])
        munis.append({"divipola":r["divipola"],"name":r["muni"],"dept":d,"region":reg,
                      "lean":float(r["lean"]),"votval":int(r["votval"])})
by_dv = {m["divipola"]:m for m in munis if m["divipola"]}

# ---- stores: brands per municipio + per-store lean ----
brands_in = defaultdict(Counter)        # divipola -> Counter(brand)
store_bucket = defaultdict(Counter)     # brand -> Counter(bucket)
def bucket_of(lean):
    a = abs(lean)
    if a < 0.05: return "competido"     # 50/50 (margen < 5 pts)
    if a > 0.20: return "extremo"       # bastion (margen > 20 pts)
    return "medio"
with open(P("data","processed","stores_geo.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        brands_in[r["divipola"]][r["brand"]] += 1
        store_bucket[r["brand"]][bucket_of(float(r["lean"]))] += 1

def topbrands(dv, k=4):
    return [b for b,_ in brands_in.get(dv, Counter()).most_common(k)]

# ---- aggregations (vote-weighted lean) ----
def aggregate(key):
    g = defaultdict(lambda: {"num":0.0,"den":0,"munis":0,"stores":0,"brands":set()})
    for m in munis:
        k = key(m)
        if k is None: continue
        a = g[k]
        a["num"] += m["lean"]*m["votval"]; a["den"] += m["votval"]; a["munis"] += 1
        c = brands_in.get(m["divipola"])
        if c: a["stores"] += sum(c.values()); a["brands"].update(c)
    out = []
    for k,a in g.items():
        if a["den"]==0: continue
        out.append({"name":k,"lean":round(a["num"]/a["den"],4),"votval":a["den"],
                    "munis":a["munis"],"stores":a["stores"],"nbrands":len(a["brands"]),
                    "topbrands":[b for b,_ in Counter({b:1 for b in a["brands"]}).most_common(0)] })
    return out

regions = aggregate(lambda m: m["region"] if m["region"]!="?" else None)
depts   = aggregate(lambda m: m["dept"])
# cities = top municipios by votval (each its own unit)
cities = sorted(munis, key=lambda m:-m["votval"])[:50]
cities = [{"name":f'{m["name"]} ({m["dept"]})',"lean":m["lean"],"votval":m["votval"],
           "munis":1,"stores":sum(brands_in.get(m["divipola"],Counter()).values()),
           "topbrands":topbrands(m["divipola"])} for m in cities]

def buckets(rows, n=8, vmin=0):
    elig = [r for r in rows if r["votval"]>=vmin]
    by_lean = sorted(elig, key=lambda r:r["lean"])
    fifty = sorted(elig, key=lambda r:abs(r["lean"]))
    return {"cepeda":by_lean[:n], "espriella":by_lean[::-1][:n], "competido":fifty[:n]}

# city vote threshold so "50/50" cities are real markets, not tiny towns
CITY_VMIN = 50000
agg = {
 "region": {"rows":regions, "buckets":buckets(regions)},
 "dept":   {"rows":depts,   "buckets":buckets(depts)},
 "city":   {"rows":cities,  "buckets":buckets(cities, n=10, vmin=CITY_VMIN)},
}

# ---- brand buckets: where do brands live (swing vs base) ----
brand_profile = []
for b, c in store_bucket.items():
    tot = sum(c.values())
    if tot < 5: continue
    brand_profile.append({"brand":b,"n":tot,
        "competido":round(c["competido"]/tot,3),
        "extremo":round(c["extremo"]/tot,3)})
most_swing = sorted(brand_profile, key=lambda x:-x["competido"])[:12]
most_base  = sorted(brand_profile, key=lambda x:-x["extremo"])[:12]

# ---- choropleth geometry (simplified) ----
polys = pickle.load(open(P("data","processed","muni_polygons.pkl"), "rb"))
feats = []
for p in polys:
    dv = pid(p["name"], p["divipola"])
    m = by_dv.get(dv)
    if not m: continue
    geom = p["geom"].simplify(0.008, preserve_topology=True)
    if geom.is_empty: continue
    feats.append({"type":"Feature",
        "properties":{"dv":dv,"name":m["name"],"dept":m["dept"],"region":m["region"],
                      "lean":m["lean"],"votval":m["votval"],"top":topbrands(dv)},
        "geometry":mapping(geom)})
geojson = {"type":"FeatureCollection","features":feats}

# ---- store points (dot map) + region x domain summary ----
DOM = ["tiendas","comida","servicios","moda","automotriz"]
DOM_LABEL = {"tiendas":"Tiendas y Compras","comida":"Comida y Bebida","servicios":"Servicios Cotidianos",
             "moda":"Moda y Calzado","automotriz":"Vehiculos"}
SUB = {d: [] for d in DOM}
pts = []
rd = defaultdict(lambda: defaultdict(lambda: {"stores":0,"num":0.0,"den":0}))  # region->domain->stats
region_votval = {r["name"]: r["votval"] for r in regions}
with open(P("data","processed","stores_geo.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        dom = r["domain"]; sub = r["subcat"]
        if dom not in SUB: continue
        if sub not in SUB[dom]: SUB[dom].append(sub)
        di = DOM.index(dom); si = SUB[dom].index(sub)
        pts.append([round(float(r["lon"]),4), round(float(r["lat"]),4), di, si])
        m = by_dv.get(r["divipola"])
        reg = m["region"] if m else "?"
        rd[reg][dom]["stores"] += 1
region_domain = {}
for reg, doms in rd.items():
    if reg == "?": continue
    vv = region_votval.get(reg, 0)
    region_domain[reg] = {DOM_LABEL[d]: {
        "stores": s["stores"],
        "dens": round(s["stores"]/(vv/1000), 3) if vv else 0,
    } for d, s in doms.items()}

meta = {"polo_neg":"Ivan Cepeda","polo_pos":"Abelardo De La Espriella",
        "city_vmin":CITY_VMIN, "n_munis":len(munis),
        "domains":DOM, "domain_label":DOM_LABEL, "subcats":SUB,
        "region_domain":region_domain, "region_votval":region_votval}

with open(P("site","geo.js"),"w",encoding="utf-8") as f:
    f.write("window.GEO_MUNI="+json.dumps(geojson,ensure_ascii=False,separators=(',',':'))+";\n")
    f.write("window.GEO_STORES="+json.dumps(pts,separators=(',',':'))+";\n")
    f.write("window.GEO_AGG="+json.dumps({"agg":agg,"swing":most_swing,"base":most_base,"meta":meta},
            ensure_ascii=False,separators=(',',':'))+";\n")

sz = os.path.getsize(P("site","geo.js"))
print(f"munis={len(munis)} feats={len(feats)} geo.js={sz/1024:.0f}KB")
print("REGIONES (vote-weighted lean):")
for r in sorted(regions, key=lambda r:r["lean"]):
    print(f"  {r['lean']*100:+6.1f} pts  {r['name']:10}  votos={r['votval']:>9,}  marcas={r['nbrands']}")
print("CIUDADES 50/50 (|lean| menor, votos>=%d):"%CITY_VMIN)
for c in agg["city"]["buckets"]["competido"][:8]:
    print(f"  {c['lean']*100:+6.1f} pts  {c['name']:28} votos={c['votval']:>8,}")
print("Marcas mas 'swing' (en municipios competidos):", [b["brand"] for b in most_swing[:6]])
