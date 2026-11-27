"""Polttoainekoe 1: analyysi data/polttoaine/ennakko.md:n mukaan (sarjat, säännöt ja moottorin parametrit kiinteät).

  python3 tools/polttoaine_analyysi.py --wob data/polttoaine/wob-fi.json --brent BRENT.csv --fx FX.csv --out data/polttoaine/tulos-1.json
Brent: datasets/oil-prices data/brent-daily.csv (Date,Price). FX: datasets/exchange-rates data/daily.csv (Date,Country,Value; Euro = EUR per USD).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import synapsi as sy  # noqa: E402

KYNNYS = {"brent": 5.0, "fx": 2.0, "fi95": 3.0, "fidiesel": 3.0}


def viikkokeskiarvo(paiv: dict[date, float], d: date) -> float | None:
    xs = [paiv[d - timedelta(days=k)] for k in range(1, 8) if (d - timedelta(days=k)) in paiv]
    return sum(xs) / len(xs) if xs else None


def muutos(x: list[float | None]) -> list[float | None]:
    return [None] + [None if a is None or b is None or a == 0 else 100 * (b - a) / a for a, b in zip(x, x[1:])]


def rakenna(wob: dict, brent: dict, fx: dict, alku: str | None = None, loppu: str | None = None):
    s95 = wob["sarjat"]["FI_price_wo_tax_euro95"]; sd = wob["sarjat"]["FI_price_wo_tax_diesel"]
    paivat = sorted(set(s95) | set(sd))
    paivat = [p for p in paivat if (alku is None or p >= alku) and (loppu is None or p < loppu)]
    dd = [date.fromisoformat(p) for p in paivat]
    # WOB on pääosin viikoittainen; aukot (esim. pyhät) näkyvät pidempänä välinä, muutosta ei laske yli 13 vrk:n välin
    taso = {"brent": [viikkokeskiarvo(brent, d) for d in dd], "fx": [viikkokeskiarvo(fx, d) for d in dd],
            "fi95": [s95.get(p) for p in paivat], "fidiesel": [sd.get(p) for p in paivat]}
    mu = {k: muutos(v) for k, v in taso.items()}
    for i in range(1, len(dd)):
        if (dd[i] - dd[i - 1]).days > 13:
            for k in mu:
                mu[k][i] = None
    sarjat, saannot = {}, {}
    for k, v in mu.items():
        sarjat[f"{k}_ylos"] = v; saannot[f"{k}_ylos"] = {"tyyppi": "kynnys", "ehto": ">=", "raja": KYNNYS[k]}
        sarjat[f"{k}_alas"] = v; saannot[f"{k}_alas"] = {"tyyppi": "kynnys", "ehto": "<=", "raja": -KYNNYS[k]}
    return paivat, sarjat, saannot


def luokittele(e: dict) -> str:
    a, b, d = e["a"], e["b"], e["viive"]
    fa, fb = a.split("_")[0], b.split("_")[0]
    sa, sb = a.split("_")[1], b.split("_")[1]
    if fa == "brent" and fb in ("fi95", "fidiesel") and sa == sb:
        if sa == "ylos" and d <= 2: return "H1"
        if sa == "alas" and d <= 3: return "H2"
        return "brent→fi muu viive"
    if {fa, fb} == {"fi95", "fidiesel"} and sa == sb and d == 0: return "H3"
    if fa in ("fi95", "fidiesel") and fb in ("brent", "fx") and d >= 1: return "H4 väärä positiivinen"
    if "fx" in (fa, fb): return "H5 fx"
    return "muu"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wob", required=True); ap.add_argument("--brent", required=True); ap.add_argument("--fx", required=True)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    wob = json.loads(Path(a.wob).read_text(encoding="utf-8"))
    brent = {date.fromisoformat(r["Date"]): float(r["Price"]) for r in csv.DictReader(open(a.brent)) if r["Price"]}
    fx = {date.fromisoformat(r["Date"]): float(r["Value"]) for r in csv.DictReader(open(a.fx)) if r["Country"] == "Euro" and r["Value"]}
    tulos = {}
    for nimi, (al, lo) in {"koko": (None, None), "2005-2015": (None, "2016-01-01"), "2016-2026": ("2016-01-01", None)}.items():
        paivat, sarjat, saannot = rakenna(wob, brent, fx, al, lo)
        r = sy.arvioi(sarjat, saannot, max_viive=4, min_siirto=16, p_menetelma="nb")  # poikkeama 1
        for e in r["ehdokkaat"]:
            e["luokka"] = luokittele(e)
        r["jakso"] = [paivat[0], paivat[-1]]
        tulos[nimi] = r
    s = json.dumps(tulos, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(s + "\n", encoding="utf-8")
    for nimi, r in tulos.items():
        print(f"== {nimi} {r['jakso']} viikkoja {r['n_varttia']} testejä {r['testeja']} kierroksia {r['kierroksia']} riittävät {r['kierrokset_riittavat']}")
        print("   tapahtumia", r["tapahtumia"])
        for e in r["ehdokkaat"]:
            print(f"   {e['luokka']:24} {e['a']:14} → {e['b']:14} viive {e['viive']}  {e['yhteisia']}/{e['n_a']} (odotettu {e['odotettu']})  p {e["p"]:.2e} (tarkka {e["p_tarkka"]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
