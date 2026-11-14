"""Gera a base própria código postal -> concelho e freguesia.

Fontes (ambas oficiais e abertas):
  - CAOP 2025, Direção-Geral do Território: limites das freguesias (GeoPackage).
  - Endereços INSPIRE do INE (via OpenAddresses, CC BY 4.0): pontos com código postal e coordenadas.

Método: cada endereço é colocado na freguesia cujo polígono o contém; cada código postal
fica com a freguesia onde cai a maioria dos seus endereços.

Uso: python gerar_base_cp.py <pasta com caop/*.gpkg e enderecos.geojson.gz> <pasta de saída>
"""
import collections, glob, gzip, json, os, re, sqlite3, sys, time

import numpy as np
import shapely
from pyproj import Transformer
from shapely import STRtree

SRC, OUT = sys.argv[1], sys.argv[2]
t0 = time.time()


def wkb_from_gpkg(blob):
    """Salta o cabeçalho GeoPackage e devolve o WKB."""
    assert blob[:2] == b"GP"
    env = (blob[3] >> 1) & 7
    return blob[8 + {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[env]:]


# 1. Polígonos das freguesias, por região (cada região tem o seu sistema de coordenadas).
regions = []  # (nome, srs, tree, [indice global da freguesia], transformer)
freg = []     # [dtmnfr, freguesia, municipio]
for f in sorted(glob.glob(os.path.join(SRC, "caop", "*.gpkg"))):
    c = sqlite3.connect(f)
    for table, srs in c.execute("select table_name, srs_id from gpkg_contents where table_name like '%\\_freguesias' escape '\\'").fetchall():
        geoms, idx = [], []
        for blob, code, name, mun in c.execute(f'select geom, dtmnfr, freguesia, municipio from "{table}"'):
            geoms.append(shapely.from_wkb(wkb_from_gpkg(blob)))
            idx.append(len(freg))
            freg.append([code, name, mun])
        regions.append((table, srs, STRtree(geoms), np.array(idx), Transformer.from_crs(4326, srs, always_xy=True)))
        print(table, srs, len(geoms))
print("freguesias:", len(freg), "municipios:", len({x[2] for x in freg}))


def region_of(lon, lat):
    if lon > -10.5:
        return "cont"
    if lat < 34:
        return "ram"
    return "raa_oci" if lon < -30 else "raa_cen"


REG = {r[0].split("_freguesias")[0][:7]: r for r in regions}  # cont, ram, raa_cen, raa_oci
assert set(REG) == {"cont", "ram", "raa_cen", "raa_oci"}, list(REG)

# 2. Endereços: extrai código postal e coordenadas de cada linha.
rx = re.compile(r'"postcode": "(\d{4})-(\d{3})".*?"coordinates": \[(-?[\d.]+), (-?[\d.]+)\]')
votes = collections.defaultdict(collections.Counter)  # cp7 -> {indice freguesia: n}
total = sem_cp = fora = 0
buf = {k: ([], [], []) for k in REG}


def flush(k):
    global fora
    cps, lons, lats = buf[k]
    if not cps:
        return
    _, _, tree, idx, tr = REG[k]
    x, y = tr.transform(np.array(lons), np.array(lats))
    pts = shapely.points(x, y)
    pi, gi = tree.query(pts, predicate="within")
    seen = np.zeros(len(cps), dtype=bool)
    for p, g in zip(pi.tolist(), gi.tolist()):
        if not seen[p]:
            seen[p] = True
            votes[cps[p]][int(idx[g])] += 1
    fora += int((~seen).sum())
    buf[k] = ([], [], [])


with gzip.open(os.path.join(SRC, "enderecos.geojson.gz"), "rt", encoding="utf8") as fh:
    for line in fh:
        total += 1
        m = rx.search(line)
        if not m:
            sem_cp += 1
            continue
        lon, lat = float(m.group(3)), float(m.group(4))
        k = region_of(lon, lat)
        b = buf[k]
        b[0].append(m.group(1) + m.group(2)); b[1].append(lon); b[2].append(lat)
        if len(b[0]) >= 200000:
            flush(k)
        if total % 1000000 == 0:
            print(f"{total:,} endereços, {time.time()-t0:.0f}s", flush=True)
for k in REG:
    flush(k)
print(f"endereços: {total:,}; sem código postal válido: {sem_cp:,}; fora de qualquer freguesia: {fora:,}")

# 3. Maioria por código postal.
result, forte, n1 = {}, 0, 0
for cp, cnt in votes.items():
    (best, n), tot = cnt.most_common(1)[0], sum(cnt.values())
    result[cp] = (best, n, tot)
    forte += n / tot >= 0.9
    n1 += tot == 1
print(f"códigos postais: {len(result):,}; com 90% ou mais dos endereços na mesma freguesia: {forte:,}; com um só endereço: {n1:,}")

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "cp_freguesia.json"), "w", encoding="utf8") as fh:
    json.dump({"freguesias": freg, "cp": result}, fh, ensure_ascii=False)
print(f"feito em {time.time()-t0:.0f}s")
