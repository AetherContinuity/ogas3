"""Polttoainekoe 2, jälkikäteinen vertailu: korrelaatiomatriisi + klusterointi vs synapsimoottori (28.11.2026).

EI ennakkokirjattu: tehty moottorin tuloksen (tulos-2) jälkeen. Sama aineisto (wob-kaikki.json, EU/EUR pois),
samat maa×tuote-sarjat kuin moottorin ehdottomassa ajossa, samat jaksot, sama viikkomuutos-% ja aukkosääntö.
Vertailuryhmä lukittu tulos-2.md:stä: LU, DK, SE, BE, DE, EE, FI.

V1 Pearson ja Spearman viikkomuutoksista, raaka ja Brent-residuaali (OLS Brentin viikkomuutokseen viiveillä 0 ja 1).
V2 Hierarkkinen klusterointi (etäisyys 1 − r; average ja complete linkage; katkaisu r ≥ 0,3 / 0,4 / 0,5),
   ryhmän paras vastaavuus (Jaccard maatasolla).
V3 Moottorin viiveelliset säilyneet (viive ≥ 1): viiveellinen Pearson ja sen sija kaikkien parien
   saman viiveen korrelaatioissa, sekä parin samanaikainen r.
Vain vakiokirjasto.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import polttoaine_massa as pm  # noqa: E402
from polttoaine_analyysi import muutos, viikkokeskiarvo  # noqa: E402

RYHMA = {"LU", "DK", "SE", "BE", "DE", "EE", "FI"}


def muutokset(wob, brent, alku, loppu):
    paivat = sorted({p for s in wob["sarjat"].values() for p in s if alku <= p < loppu})
    dd = [date.fromisoformat(p) for p in paivat]
    aukko = [i > 0 and (dd[i] - dd[i - 1]).days > 13 for i in range(len(dd))]
    b = [None if aukko[i] else v for i, v in enumerate(muutos([viikkokeskiarvo(brent, d) for d in dd]))]
    out = {}
    for nimi, s in wob["sarjat"].items():
        if nimi[:3] in ("EU_", "EUR"):
            continue
        m = muutos([s.get(p) for p in paivat])
        out[f"{nimi[:2]}_{nimi.rsplit('_', 1)[1]}"] = [None if aukko[i] else v for i, v in enumerate(m)]
    return out, b


def pearson(x, y):
    p = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    n = len(p)
    if n < 30:
        return None
    mx = sum(a for a, _ in p) / n; my = sum(b for _, b in p) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a, _ in p)); sy = math.sqrt(sum((b - my) ** 2 for _, b in p))
    return None if sx == 0 or sy == 0 else sum((a - mx) * (b - my) for a, b in p) / (sx * sy)


def ranks(v):
    idx = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and v[idx[j + 1]] == v[idx[i]]:
            j += 1
        for k in range(i, j + 1):
            r[idx[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(x, y):
    p = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(p) < 30:
        return None
    return pearson(ranks([a for a, _ in p]), ranks([b for _, b in p]))


def residuaali(x, b):
    rows = [(i, x[i], b[i], b[i - 1]) for i in range(1, len(x)) if None not in (x[i], b[i], b[i - 1])]
    if len(rows) < 30:
        return x
    # OLS x ~ 1 + b0 + b1 (normaaliyhtälöt 3×3)
    X = [(1.0, r[2], r[3]) for r in rows]; Y = [r[1] for r in rows]
    A = [[sum(X[k][i] * X[k][j] for k in range(len(X))) for j in range(3)] for i in range(3)]
    c = [sum(X[k][i] * Y[k] for k in range(len(X))) for i in range(3)]
    for i in range(3):  # Gauss
        piv = A[i][i]
        for j in range(i + 1, 3):
            f = A[j][i] / piv
            A[j] = [A[j][k] - f * A[i][k] for k in range(3)]; c[j] -= f * c[i]
    beta = [0.0] * 3
    for i in (2, 1, 0):
        beta[i] = (c[i] - sum(A[i][k] * beta[k] for k in range(i + 1, 3))) / A[i][i]
    out = [None] * len(x)
    for (i, xi, b0, b1) in rows:
        out[i] = xi - (beta[0] + beta[1] * b0 + beta[2] * b1)
    return out


def klusteroi(nimet, r, kynnys, linkage):
    ryhmat = [{n} for n in nimet]

    def etaisyys(g, h):
        ds = [1 - r[(a, b)] if r.get((a, b)) is not None else 2.0 for a in g for b in h]
        return sum(ds) / len(ds) if linkage == "average" else max(ds)
    while True:
        best = None
        for i in range(len(ryhmat)):
            for j in range(i + 1, len(ryhmat)):
                d = etaisyys(ryhmat[i], ryhmat[j])
                if best is None or d < best[0]:
                    best = (d, i, j)
        if best is None or best[0] > 1 - kynnys:
            return ryhmat
        _, i, j = best
        ryhmat[i] |= ryhmat.pop(j)


def jaccard_maat(ryhmat):
    paras = (0.0, None)
    for g in ryhmat:
        maat = {n[:2] for n in g}
        j = len(maat & RYHMA) / len(maat | RYHMA)
        if j > paras[0]:
            paras = (j, sorted(maat))
    return round(paras[0], 3), paras[1]


def main() -> int:
    wob = json.loads(Path("data/polttoaine/wob-kaikki.json").read_text(encoding="utf-8"))
    brent = {date.fromisoformat(r["Date"]): float(r["Price"]) for r in csv.DictReader(open(sys.argv[1])) if r["Price"]}
    t2 = json.loads(Path("data/polttoaine/tulos-2.json").read_text(encoding="utf-8"))
    moottori_sarjat = sorted({a.rsplit("_", 1)[0] for a, b, d in t2["ehdoton"]["ehdokkaat_loyto"]} |
                             {b.rsplit("_", 1)[0] for a, b, d in t2["ehdoton"]["ehdokkaat_loyto"]})
    out = {"huom": "jälkikäteinen, ei ennakkokirjattu", "sarjoja": len(moottori_sarjat), "jaksot": {}}
    for j, (al, lo) in pm.JAKSOT.items():
        M, b = muutokset(wob, brent, al, lo)
        M = {k: M[k] for k in moottori_sarjat if k in M}
        R = {k: residuaali(v, b) for k, v in M.items()}
        nim = sorted(M)
        tul = {}
        for nimi, D in (("raaka", M), ("brent_residuaali", R)):
            rp = {(a, c): pearson(D[a], D[c]) for a in nim for c in nim if a < c}
            rp.update({(c, a): v for (a, c), v in list(rp.items())})
            rs = {(a, c): spearman(D[a], D[c]) for a in nim for c in nim if a < c}
            arvot = [v for (a, c), v in rp.items() if a < c and v is not None]
            klus = {}
            for link in ("average", "complete"):
                for kyn in (0.3, 0.4, 0.5):
                    g = klusteroi(nim, rp, kyn, link)
                    klus[f"{link}_r{kyn}"] = {"ryhmia": len([x for x in g if len(x) > 1]), "paras_vastaavuus": jaccard_maat(g)}
            tul[nimi] = {"pearson_mediaani": round(sorted(arvot)[len(arvot) // 2], 3),
                         "spearman_mediaani": round(sorted(v for (a, c), v in rs.items() if v is not None)[len(rs) // 2], 3),
                         "ryhman_sisainen_pearson_mediaani": round(sorted(v for (a, c), v in rp.items() if a < c and v is not None and a[:2] in RYHMA and c[:2] in RYHMA and a[:2] != c[:2])[0:][len([1 for (a, c), v in rp.items() if a < c and v is not None and a[:2] in RYHMA and c[:2] in RYHMA and a[:2] != c[:2]]) // 2], 3),
                         "ryhma_vs_muut_pearson_mediaani": round(sorted(v for (a, c), v in rp.items() if a < c and v is not None and ((a[:2] in RYHMA) != (c[:2] in RYHMA)))[len([1 for (a, c), v in rp.items() if a < c and v is not None and ((a[:2] in RYHMA) != (c[:2] in RYHMA))]) // 2], 3),
                         "klusterointi": klus}
            if nimi == "brent_residuaali" and j == "loyto":
                RR = D
        out["jaksot"][j] = tul
        if j == "loyto":
            # V3: moottorin viiveelliset säilyneet (suodatettu ajo) löytöjakson residuaaleilla
            v3 = []
            for a, c, d in t2["ehdollinen"]["sailyneet"]:
                if d < 1:
                    continue
                x, y = RR[a.rsplit("_", 1)[0]], RR[c.rsplit("_", 1)[0]]
                r_d = pearson(x[:-d], y[d:]); r_0 = pearson(x, y)
                kaikki_d = sorted((abs(pearson(RR[p][:-d], RR[q][d:]) or 0), p, q) for p in nim for q in nim if p != q)[::-1]
                sija = next(i for i, (_, p, q) in enumerate(kaikki_d, 1) if p == a.rsplit("_", 1)[0] and q == c.rsplit("_", 1)[0])
                v3.append({"pari": f"{a} → {c}", "viive": d, "r_viive": round(r_d, 3), "r_0": round(r_0, 3),
                           "sija_viiveella": f"{sija}/{len(kaikki_d)}"})
            out["V3_viiveelliset"] = v3
    Path("data/polttoaine/korrelaatio-vertailu.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
