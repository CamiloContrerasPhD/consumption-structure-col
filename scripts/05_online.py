# -*- coding: utf-8 -*-
"""'Que se busca online' pillar from Google Trends interest-by-department (subregion).
Each entity positioned by audience-lean (vote-weighted by its regional search interest) on the political
axis, sized by national interest (rescaled across batches via the shared anchor 'Karol G').
Source: Google Trends comparedgeo (today 12-m), 6 anchored batches. Output: site/online.js (window.ONLINE).
"""
import json, os, csv, unicodedata, re, math
BASE=os.path.join(os.path.dirname(__file__),"..")
P=lambda *a:os.path.join(BASE,*a)

raw=json.load(open(P("data","raw","trends_online.json"),encoding="utf-8"))
# category per entity name (anchor 'Karol G' is deduped after the first batch)
NAME2CAT={
 "Karol G":"Urbano","Feid":"Urbano","Blessd":"Urbano","Maluma":"Urbano","J Balvin":"Urbano",
 "Diomedes Diaz":"Vallenato","Silvestre Dangond":"Vallenato","Carlos Vives":"Vallenato",
 "Peter Manjarres":"Vallenato","Adriana Lucia":"Vallenato",
 "Jessi Uribe":"Popular","Pipe Bueno":"Popular","Paola Jara":"Popular","Yeison Jimenez":"Popular",
 "Grupo Niche":"Salsa","Guayacan Orquesta":"Salsa","Joe Arroyo":"Salsa","Hansel Camacho":"Salsa",
 "Juanes":"Pop/Rock","Morat":"Pop/Rock","Aterciopelados":"Pop/Rock","Doctor Krapula":"Pop/Rock","Systema Solar":"Pop/Rock",
 "ChocQuibTown":"Pacifico","Herencia de Timbiqui":"Pacifico","Grupo Bahia":"Pacifico",
 "Kevin Florez":"Champeta","Mr Black":"Champeta","Petrona Martinez":"Champeta",
 "Netflix":"Plataformas","Disney Plus":"Plataformas","Spotify":"Plataformas","HBO Max":"Plataformas",
 "ChatGPT":"IA","Gemini":"IA","Copilot":"IA","Inteligencia artificial":"IA",
}

def nm(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().upper()
    return re.sub("[^A-Z]","",s)
txt=open(P("site","geo.js"),encoding="utf-8").read()
agg=json.loads(txt.split("window.GEO_AGG=")[1].rstrip().rstrip(";"))
dept={nm(r["name"]):(r["lean"],r["votval"]) for r in agg["agg"]["dept"]["rows"]}
def dept_of(d):
    k=nm(d)
    if k in dept: return dept[k]
    for dk,dv in dept.items():
        if dk.startswith(k) or k.startswith(dk): return dv
    return None

# per batch: nat interest of anchor (col 1) for rescaling
def nat_anchor(b): return sum(r[1] for r in b["rows"])
ref=nat_anchor(raw[0])

entities=[]; seen=set()
for bi,b in enumerate(raw):
    kws=b["kws"]; rows=b["rows"]
    na=nat_anchor(b) or 1
    scale=ref/na
    for j,kw in enumerate(kws):
        if j==0 and bi>0: continue           # skip repeated anchor
        col=j+1
        num=den=0; nat=0; ndept=0
        for r in rows:
            v=r[col]
            if v<=0: continue
            nat+=v; ndept+=1
            dv=dept_of(r[0])
            if dv is None: continue
            L,vv=dv; w=v*vv          # interest (per-capita rate) x electoral size = audience weight
            num+=w*L; den+=w
        if den==0 or ndept<6: continue        # insufficient coverage
        entities.append({"name":kw,"cat":NAME2CAT.get(kw,"Otro"),"lean":round(num/den,4),
                         "pts":round(num/den*100,2),"size":round(nat*scale,1),"ndept":ndept})
        seen.add(kw)
entities.sort(key=lambda e:e["lean"])

print(f"entidades={len(entities)}  (ref_anchor_nat={ref})")
print(f'{"entidad":24}{"cat":12}{"lean(pts)":>10}{"size":>10}{"deptos":>8}')
for e in entities:
    print(f'  {e["name"]:22}{e["cat"]:12}{e["pts"]:+10.1f}{e["size"]:10.0f}{e["ndept"]:8}')

out={"meta":{"fuente":"Google Trends, interes por subregion (12 meses), 6 lotes anclados en 'Karol G'",
             "eje":"lean de audiencia = voto departamental ponderado por interes de busqueda",
             "polo_neg":"Ivan Cepeda","polo_pos":"Abelardo De La Espriella"},
     "cats":sorted(set(e["cat"] for e in entities)),
     "entities":entities}
with open(P("site","online.js"),"w",encoding="utf-8") as f:
    f.write("window.ONLINE="+json.dumps(out,ensure_ascii=False,separators=(',',':'))+";")
print("\nwrote site/online.js")
