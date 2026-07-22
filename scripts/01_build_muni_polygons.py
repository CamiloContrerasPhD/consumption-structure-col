"""Build municipio polygons from Overpass admin_level=6 dump.
Output: data/processed/muni_polygons.pkl  (list of dicts: divipola, name, dept, geom)
"""
import json, pickle, os, sys
from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "muni_boundaries.json")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "muni_polygons.pkl")

d = json.load(open(RAW, encoding="utf-8"))
els = d["elements"]
node = {}
way = {}
rels = []
for e in els:
    t = e["type"]
    if t == "node":
        node[e["id"]] = (e["lon"], e["lat"])
    elif t == "way":
        way[e["id"]] = e.get("nodes", [])
    elif t == "relation":
        rels.append(e)

print(f"nodes={len(node)} ways={len(way)} rels={len(rels)}", file=sys.stderr)

out = []
skipped = 0
for r in rels:
    tags = r.get("tags", {})
    outer_lines, inner_lines = [], []
    for m in r.get("members", []):
        if m["type"] != "way":
            continue
        nodes = way.get(m["ref"])
        if not nodes or len(nodes) < 2:
            continue
        coords = [node[n] for n in nodes if n in node]
        if len(coords) < 2:
            continue
        ls = LineString(coords)
        (inner_lines if m.get("role") == "inner" else outer_lines).append(ls)
    if not outer_lines:
        skipped += 1
        continue
    try:
        outer = unary_union(list(polygonize(outer_lines)))
        if inner_lines:
            inner = unary_union(list(polygonize(inner_lines)))
            outer = outer.difference(inner)
        if outer.is_empty:
            skipped += 1
            continue
    except Exception as ex:
        skipped += 1
        continue
    out.append({
        "divipola": tags.get("divipola", ""),
        "name": tags.get("name", ""),
        "dept": tags.get("is_in:state") or tags.get("DANE:departamento", ""),
        "geom": outer,
    })

print(f"built={len(out)} skipped={skipped}", file=sys.stderr)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
pickle.dump(out, open(OUT, "wb"))
print("wrote", OUT, file=sys.stderr)
