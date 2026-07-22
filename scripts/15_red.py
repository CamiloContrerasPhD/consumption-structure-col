"""Red de marcas (Sitio 2, fase 2): grafo de co-localizacion + comunidades.
- Nodos: marcas. Arista (b,b') con peso = proximidad phi (min-condicional, como en 06).
- Poda: se conservan las aristas con phi >= umbral y ademas las top-3 de cada nodo
  (para que ningun nodo quede aislado del esqueleto).
- Comunidades: modularidad voraz (Clauset-Newman-Moore, networkx).
- Cada comunidad recibe el lean promedio (ponderado por locales) de sus marcas:
  ¿los "barrios" de marcas tienen color politico?
Output: site2/red.js  window.RD = {meta, nodes:[...], links:[...], comms:[...]}
"""
import os, json
import numpy as np
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

BASE = os.path.join(os.path.dirname(__file__), "..")
P = lambda *a: os.path.join(BASE, *a)

s = open(P("site2","complex.js"), encoding="utf-8").read()
CX = json.loads(s[s.index("=")+1:].rstrip().rstrip(";"))
brands = CX["brands"]; muniOrder = CX["muniOrder"]
nB = len(brands); nM = len(muniOrder)

# presence matrix M (nM x nB) from brandPresent
Mx = np.zeros((nM, nB))
for j, b in enumerate(brands):
    Mx[:, j] = CX["brandPresent"][b["brand"]]
ubiq = Mx.sum(0)

# phi: min-conditional proximity
cooc = Mx.T @ Mx
ub = np.where(ubiq==0, 1, ubiq)
phi = cooc / np.maximum(ub[:,None], ub[None,:])
np.fill_diagonal(phi, 0.0)

# ---- prune: edges phi>=THR plus top-3 per node ----
THR = 0.35
keep = set()
for i in range(nB):
    top = np.argsort(-phi[i])[:3]
    for j in top:
        if phi[i,j] > 0: keep.add((min(i,j), max(i,j)))
for i in range(nB):
    for j in range(i+1, nB):
        if phi[i,j] >= THR: keep.add((i,j))

G = nx.Graph()
for j, b in enumerate(brands): G.add_node(j)
for i, j in keep: G.add_edge(i, j, weight=float(phi[i,j]))

comms = list(greedy_modularity_communities(G, weight="weight"))
cid = {}
for c, mem in enumerate(comms):
    for j in mem: cid[j] = c

nodes = [{"id": b["brand"], "domain": b["domain"], "n": b["n"],
          "lean": b["lean"], "comm": cid[j]} for j, b in enumerate(brands)]
links = [{"source": brands[i]["brand"], "target": brands[j]["brand"],
          "w": round(float(phi[i,j]),3)} for i, j in sorted(keep)]

comms_out = []
for c, mem in enumerate(comms):
    mem = list(mem)
    w = np.array([brands[j]["n"] for j in mem], dtype=float)
    l = np.array([brands[j]["lean"] for j in mem])
    top = sorted(mem, key=lambda j: -brands[j]["n"])[:5]
    comms_out.append({"comm": c, "size": len(mem),
                      "lean": round(float((w*l).sum()/w.sum()),4),
                      "top": [brands[j]["brand"] for j in top],
                      "doms": sorted({brands[j]["domain"] for j in mem})})

meta = {"n_nodes": nB, "n_links": len(links), "n_comms": len(comms), "thr": THR,
        "desc": "Red de co-localizacion (phi min-condicional); poda phi>=0.35 + top-3 por nodo; "
                "comunidades por modularidad voraz (CNM)."}
with open(P("site2","red.js"), "w", encoding="utf-8") as f:
    f.write("window.RD=" + json.dumps({"meta": meta, "nodes": nodes, "links": links, "comms": comms_out},
                                      ensure_ascii=False, separators=(",",":")) + ";\n")

print(f"nodos={nB} aristas={len(links)} comunidades={len(comms)}")
for c in comms_out:
    print(f"  comm {c['comm']}: {c['size']:3d} marcas lean={c['lean']*100:+.0f} doms={','.join(c['doms'])[:40]} top={', '.join(c['top'][:3])}")
