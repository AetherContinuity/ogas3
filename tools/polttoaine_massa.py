"""Polttoainekoe 2: synapsien massa, Brent-ajurin karsinta ja löytö/vahvistus (data/polttoaine/ennakko-2.md).

  python3 tools/polttoaine_massa.py --wob data/polttoaine/wob-kaikki.json --brent BRENT.csv --out data/polttoaine/tulos-2.json
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import synapsi as sy  # noqa: E402
from polttoaine_analyysi import muutos, viikkokeskiarvo  # noqa: E402

JAKSOT = {"loyto": ("2005-01-01", "2016-01-01"), "vahvistus": ("2016-01-01", "2027-01-01")}
K_FI, K_BRENT, MIN_AKT, VIIVE, MS = 3.0, 5.0, 20, 4, 16


def sarjat_jaksolle(wob: dict, brent: dict, alku: str, loppu: str, ehdollinen: bool, plasebo: int | None = None):
    paivat = sorted({p for s in wob["sarjat"].values() for p in s if alku <= p < loppu})
    dd = [date.fromisoformat(p) for p in paivat]
    aukko = [i > 0 and (dd[i] - dd[i - 1]).days > 13 for i in range(len(dd))]
    b = muutos([viikkokeskiarvo(brent, d) for d in dd])
    b_ylos = {i for i, v in enumerate(b) if v is not None and not aukko[i] and v >= K_BRENT}
    b_alas = {i for i, v in enumerate(b) if v is not None and not aukko[i] and v <= -K_BRENT}
    if plasebo is not None:  # lisäanalyysi: yhtä monta satunnaista viikkoa Brent-viikkojen sijaan
        import random
        r = random.Random(plasebo)
        b_ylos = set(r.sample(range(1, len(dd)), len(b_ylos))); b_alas = set(r.sample(range(1, len(dd)), len(b_alas)))
    out = {}
    for nimi, s in wob["sarjat"].items():
        if nimi[:3] in ("EU_", "EUR"):  # ennakko-2: EU- ja EUR-keskiarvot pois
            continue
        maa, tuote = nimi[:2], nimi.rsplit("_", 1)[1]
        m = muutos([s.get(p) for p in paivat])
        m = [None if aukko[i] else v for i, v in enumerate(m)]
        for suunta, ehto, ajuri in (("ylos", lambda v: v >= K_FI, b_ylos), ("alas", lambda v: v <= -K_FI, b_alas)):
            x = [1.0 if (v is not None and ehto(v)) else (None if v is None else 0.0) for v in m]
            if ehdollinen:
                x = [0.0 if (v == 1.0 and (i in ajuri or i - 1 in ajuri)) else v for i, v in enumerate(x)]
            out[f"{maa}_{tuote}_{suunta}"] = x
    return paivat, out


def aja(wob, brent, ehdollinen: bool) -> dict:
    sa = {"tyyppi": "kynnys", "ehto": ">=", "raja": 1}
    tulos = {}
    sar = {}
    for j, (al, lo) in JAKSOT.items():
        _, sar[j] = sarjat_jaksolle(wob, brent, al, lo, ehdollinen)
    mukana = [k for k in sar["loyto"] if k in sar["vahvistus"]
              and all(len(sy.aktivaatiot(sar[j][k], sa)) >= MIN_AKT for j in JAKSOT)]
    parit = [(a, b) for a in mukana for b in mukana if a != b and a.rsplit("_", 1)[1] == b.rsplit("_", 1)[1]]
    L = sy.arvioi({k: sar["loyto"][k] for k in mukana}, {k: sa for k in mukana}, max_viive=VIIVE, min_siirto=MS,
                  p_menetelma="nb", parit=parit)
    ehd = {(e["a"], e["b"], e["viive"]) for e in L["ehdokkaat"]}
    # vahvistus: vain löytöehdokkaiden parit; BH ehdokasjoukon (pari×viive) yli
    V = sy.arvioi({k: sar["vahvistus"][k] for k in mukana}, {k: sa for k in mukana}, max_viive=VIIVE, min_siirto=MS,
                  p_menetelma="nb", rajaus=ehd)
    sail = {(e["a"], e["b"], e["viive"]) for e in V["ehdokkaat"]}

    def kuvaa(joukko):
        c = Counter()
        for a, b, d in joukko:
            c["viive0" if d == 0 else "viive>=1"] += 1
            c["sama_maa" if a[:2] == b[:2] else "eri_maa"] += 1
        return dict(c)
    maaparit = Counter(tuple(sorted((a[:2], b[:2]))) for a, b, _ in sail if a[:2] != b[:2])
    return {"sarjoja": len(mukana), "pareja": len(parit), "testeja_loyto": L["testeja"], "ehdokkaita_loyto": len(ehd),
            "testeja_vahvistus": V["testeja"], "sailyi": len(sail), "sailymisosuus": round(len(sail) / len(ehd), 3) if ehd else None,
            "loyto_kuvaus": kuvaa(ehd), "sailyneet_kuvaus": kuvaa(sail),
            "sailyneet_maaparit_top": [[f"{x}-{y}", n] for (x, y), n in sorted(maaparit.items(), key=lambda t: (-t[1], t[0]))[:25]],
            "sailyneet": sorted(sail), "ehdokkaat_loyto": sorted(ehd)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wob", required=True); ap.add_argument("--brent", required=True); ap.add_argument("--out")
    a = ap.parse_args(argv)
    wob = json.loads(Path(a.wob).read_text(encoding="utf-8"))
    brent = {date.fromisoformat(r["Date"]): float(r["Price"]) for r in csv.DictReader(open(a.brent)) if r["Price"]}
    raportti = {}
    for nimi, ehdol in (("ehdoton", False), ("ehdollinen", True)):
        raportti[nimi] = aja(wob, brent, ehdol)
    if a.out:
        Path(a.out).write_text(json.dumps(raportti, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for nimi, r in raportti.items():
        print(f"== {nimi}: sarjoja {r['sarjoja']}, pareja {r['pareja']}, testejä {r['testeja_loyto']}")
        print(f"   löytö: {r['ehdokkaita_loyto']} ehdokasta {r['loyto_kuvaus']}")
        print(f"   vahvistus: {r['sailyi']} säilyi ({r['sailymisosuus']}) {r['sailyneet_kuvaus']}")
        print("   maaparit:", r["sailyneet_maaparit_top"][:15])
    return 0


if __name__ == "__main__":
    sys.exit(main())
