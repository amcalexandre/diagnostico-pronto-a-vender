"""Converte cp_freguesia.json (saída de gerar_base_cp.py) nos ficheiros que a página lê: docs/cp/NN.json.

Um ficheiro por cada dois primeiros algarismos do código postal:
  {"f": [[concelho, freguesia], ...],          tabela local de freguesias
   "c": {"1500": {"001": 3, ...}, ...},        código postal -> índice em "f"
   "d": {"1500": "Lisboa", ...}}               concelho dominante da zona postal (90% ou mais), para códigos que não constam

Uso: python gerar_ficheiros.py <cp_freguesia.json> <pasta docs/cp>
"""
import collections, json, os, sys

src, out = sys.argv[1], sys.argv[2]
d = json.load(open(src, encoding="utf8"))
F, CP = d["freguesias"], d["cp"]
NOME = {"4201": "Lagoa (Açores)"}  # único nome de concelho repetido na CAOP (Lagoa, no Algarve e nos Açores)
conc = lambda i: NOME.get(F[i][0][:4], F[i][2])

os.makedirs(out, exist_ok=True)
for old in os.listdir(out):
    os.remove(os.path.join(out, old))
groups = collections.defaultdict(dict)
for cp, (i, n, tot) in CP.items():
    groups[cp[:2]][cp] = i
total = 0
for p2, items in sorted(groups.items()):
    loc, f, c, dom = {}, [], collections.defaultdict(dict), collections.defaultdict(collections.Counter)
    for cp, i in sorted(items.items()):
        if i not in loc:
            loc[i] = len(f); f.append([conc(i), F[i][1]])
        c[cp[:4]][cp[4:]] = loc[i]
        dom[cp[:4]][conc(i)] += 1
    dd = {}
    for cp4, cnt in dom.items():
        name, n = cnt.most_common(1)[0]
        if n / sum(cnt.values()) >= 0.9:
            dd[cp4] = name
    path = os.path.join(out, p2 + ".json")
    with open(path, "w", encoding="utf8") as fh:
        json.dump({"f": f, "c": c, "d": dd}, fh, ensure_ascii=False, separators=(",", ":"))
    total += os.path.getsize(path)
print(len(groups), "ficheiros,", len(CP), "códigos postais,", round(total / 1e6, 2), "MB")
