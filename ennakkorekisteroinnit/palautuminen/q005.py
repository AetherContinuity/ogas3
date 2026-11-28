"""Q-005 — mittaukset. LUKITTU yhdessä q005.md:n kanssa.
Korjaukset uusina tiedostoina (q005_poikkeama_N.py + poikkeama_N.md) ennen tulosta.
Ajo: python3 ennakkorekisteroinnit/palautuminen/q005.py H1   (Eurostat: vain GitHub Actions, workflow q005)
NKT henkeä kohden lasketaan kuten Q-002 poikkeama 1 (P51C taulusta nasa_10_nf_tr). Vain vakiokirjasto.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "nkt"))
import q002 as L  # noqa: E402  (es, jsonstat, tila)

MAAT = ["FI", "SE", "DK"]
VUODET = [str(y) for y in range(2007, 2032)]
# shokki: (lähtövuosi ennen shokkia, pohjaikkuna). Mittausvuosi = pohjavuosi + HORISONTTI.
SHOKKI_A = ("2008", [str(y) for y in range(2009, 2016)])   # finanssikriisi + Nokia + Venäjä 2014 (yhdistetty)
SHOKKI_B = ("2019", [str(y) for y in range(2020, 2027)])   # korona + energia/korko + Venäjä 2022 (yhdistetty)
HORISONTTI = 4


def _arvo(t, *avain):
    return next((x for k, x in t.items() if all(a in k for a in avain)), None)


def sarja():
    b_cp, _ = L.es("nama_10_gdp", geo=MAAT, na_item="B1GQ", unit="CP_MNAC", time=VUODET)
    c_cp, _ = L.es("nasa_10_nf_tr", geo=MAAT, na_item="P51C", sector="S1", direct="PAID", unit="CP_MNAC", time=VUODET)
    vol, yks = None, None
    for u in ("CLV20_MNAC", "CLV15_MNAC", "CLV10_MNAC"):
        try:
            v, _ = L.es("nama_10_gdp", geo=MAAT, na_item="B1GQ", unit=u, time=VUODET)
        except Exception:
            continue
        if any(x is not None for x in v.values()):
            vol, yks = v, u
            break
    pop, _ = L.es("nama_10_pe", geo=MAAT, na_item="POP_NC", unit="THS_PER", time=VUODET)
    s = {}
    for g in MAAT:
        s[g] = {}
        for y in VUODET:
            b, c, p = _arvo(b_cp, g, y), _arvo(c_cp, g, y), _arvo(pop, g, y)
            bv = _arvo(vol, g, y) if vol else None
            s[g][y] = ((b - c) * bv / b) / p if None not in (b, c, bv, p) and b and p else None
    return s, yks


def ero(s, vertailu):
    """G_t = ln FI_t − keskiarvo(ln vertailu_t)."""
    out = {}
    for y in VUODET:
        xs = [s[g][y] for g in ["FI"] + vertailu]
        out[y] = None if any(x is None or x <= 0 for x in xs) else \
            math.log(s["FI"][y]) - sum(math.log(s[g][y]) for g in vertailu) / len(vertailu)
    return out


def palautuminen(G, shokki):
    """R = (G_mittaus − G_min) / (G_lähtö − G_min). None jos aineisto puuttuu;
    'ei pudotusta' jos G_min ≥ G_lähtö; 'pohja ikkunan lopussa' jos minimi on ikkunan viimeinen vuosi."""
    lahto, ikkuna = shokki
    if G.get(lahto) is None or any(G.get(y) is None for y in ikkuna):
        return {"R": None, "huom": "aineisto puutteellinen"}
    ymin = min(ikkuna, key=lambda y: G[y])
    gmin = G[ymin]
    mitt = str(int(ymin) + HORISONTTI)
    if G.get(mitt) is None:
        return {"R": None, "pohjavuosi": ymin, "mittausvuosi": mitt, "huom": "mittausvuosi ei vielä saatavilla"}
    if gmin >= G[lahto]:
        return {"R": None, "huom": "ei pudotusta"}
    R = (G[mitt] - gmin) / (G[lahto] - gmin)
    return {"R": round(R, 3), "pohjavuosi": ymin, "mittausvuosi": mitt, "pudotus_log": round(G[lahto] - gmin, 4),
            "huom": "pohja ikkunan lopussa" if ymin == ikkuna[-1] else ""}


def h1():
    s, yks = sarja()
    tulos = {}
    for nimi, vert in (("SE_DK", ["SE", "DK"]), ("SE", ["SE"]), ("DK", ["DK"])):
        G = ero(s, vert)
        tulos[nimi] = {"A": palautuminen(G, SHOKKI_A), "B": palautuminen(G, SHOKKI_B),
                       "G": {y: None if v is None else round(v, 4) for y, v in G.items()}}
    a, b = tulos["SE_DK"]["A"]["R"], tulos["SE_DK"]["B"]["R"]
    ok = None if a is None or b is None else b < a
    herkkyys = {n: (None if tulos[n]["A"]["R"] is None or tulos[n]["B"]["R"] is None
                    else tulos[n]["B"]["R"] < tulos[n]["A"]["R"]) for n in ("SE", "DK")}
    return {"H": "H1", "volyymiyksikko": yks, "R_A": a, "R_B": b, "tulos": L.tila(ok),
            "herkkyys_samansuuntainen": herkkyys, "vertailut": tulos,
            "sarja": {g: {y: None if x is None else round(x, 4) for y, x in v.items()} for g, v in s.items()}}


if __name__ == "__main__":
    if sys.argv[1:] != ["H1"]:
        raise SystemExit(__doc__)
    r = h1()
    r["mitattu"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(json.dumps(r, ensure_ascii=False, indent=1))
