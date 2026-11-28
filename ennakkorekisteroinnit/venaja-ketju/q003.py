"""Q-003 — mittaukset. LUKITTU yhdessä q003.md:n kanssa.

Korjaukset uusina tiedostoina (q003_poikkeama_N.py + poikkeama_N.md) ennen tulosta.
Ajo:  python3 ennakkorekisteroinnit/venaja-ketju/q003.py H1|H2|H3
Kaikki lähteet (Eurostat, Luke statdb) vain GitHub Actionsista: workflow q003.
Vain vakiokirjasto.
"""
from __future__ import annotations

import itertools
import json
import statistics
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "OGAS3/0.1 q003", "Accept": "application/json"}
ES = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
LUKE = "https://statdb.luke.fi/PxWeb/api/v1/fi/LUKE/"

JAKSO_A = ["2011", "2012", "2013"]
JAKSO_B = ["2015", "2016", "2017"]

# H1: raakamaito 3,7 % rasvaa, EUR / 100 kg
H1_TUOTE = "12111000"
H1_VERTAILU = ["BE", "BG", "CZ", "DK", "DE", "EE", "IE", "EL", "ES", "FR", "HR", "IT", "CY", "LV",
               "LT", "LU", "HU", "MT", "NL", "AT", "PL", "PT", "RO", "SI", "SK", "SE"]   # EU27 pl. FI
H1_RAPORTOI = ["SE", "DK", "EE"]
H1_RAJA = -5.0      # FI / mediaani -suhteen muutos A → B, % ; tuettu jos ≤ raja

# H2: maidontuottajat vuoden lopussa (Luke maitot 0600, MTVLOP_KPL)
H2_A = ("2008", "2013")
H2_B = ("2014", "2019")
H2_RAJA_PP = 1.0    # vähenemisvauhti B − A, pp/v ; tuettu jos ≥ raja

# H3: vastaanotettu maitomäärä (MTVASTM_L = VASTM_L)
H3_RAJA = -3.0      # määrän muutos ka A → ka B, % ; tuettu jos > raja (määrä ei pudonnut)


def _get(url, data=None):
    h = dict(UA)
    if data is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def jsonstat(d):
    ids = d["id"]
    dims = []
    for k in ids:
        ix = d["dimension"][k]["category"]["index"]
        dims.append([c for c, _ in sorted(ix.items(), key=lambda x: x[1])] if isinstance(ix, dict) else list(ix))
    val = d["value"]
    return {combo: (val[i] if isinstance(val, list) else val.get(str(i)))
            for i, combo in enumerate(itertools.product(*dims))}


def luke(taulu, valinnat):
    q = {"query": [{"code": k, "selection": {"filter": "item", "values": v}} for k, v in valinnat.items()],
         "response": {"format": "json-stat2"}}
    return jsonstat(_get(LUKE + urllib.parse.quote(taulu), json.dumps(q).encode()))


def hae(t, *avain):
    return next((x for k, x in t.items() if all(a in k for a in avain)), None)


def ka(xs):
    xs = list(xs)
    return None if not xs or any(x is None for x in xs) else sum(xs) / len(xs)


def tila(ok):
    return {True: "tuettu", False: "kumoutui", None: "aineisto puutteellinen"}[ok]


def h1():
    maat = ["FI"] + H1_VERTAILU
    pairs = [("prod_ani", H1_TUOTE), ("currency", "EUR")] + [("geo", g) for g in maat] + \
            [("time", y) for y in JAKSO_A + JAKSO_B]
    t = jsonstat(_get(ES + "apri_ap_anouta?" + urllib.parse.urlencode(pairs)))
    hinta = {g: {y: hae(t, g, y) for y in JAKSO_A + JAKSO_B} for g in maat}
    kat = {g: (ka(hinta[g][y] for y in JAKSO_A), ka(hinta[g][y] for y in JAKSO_B)) for g in maat}
    mukana = [g for g in H1_VERTAILU if None not in kat[g]]
    med_a = statistics.median(kat[g][0] for g in mukana) if mukana else None
    med_b = statistics.median(kat[g][1] for g in mukana) if mukana else None
    fi_a, fi_b = kat["FI"]
    muutos = None
    if None not in (fi_a, fi_b, med_a, med_b) and med_a and med_b:
        muutos = ((fi_b / med_b) / (fi_a / med_a) - 1) * 100
    ok = None if muutos is None else muutos <= H1_RAJA
    return {"H": "H1", "fi_ka": kat["FI"], "mediaani_ka": (med_a, med_b), "n_vertailu": len(mukana),
            "mukana": mukana, "suhde_A": None if not med_a or fi_a is None else round(fi_a / med_a, 4),
            "suhde_B": None if not med_b or fi_b is None else round(fi_b / med_b, 4),
            "muutos_pct": None if muutos is None else round(muutos, 2), "raja_pct": H1_RAJA,
            "raportoi": {g: kat[g] for g in H1_RAPORTOI}, "tulos": tila(ok), "hinnat": hinta}


def _vauhti(s, a, b):
    x, y = s.get(a), s.get(b)
    if x is None or y is None or not x:
        return None
    n = int(b) - int(a)
    return ((y / x) ** (1 / n) - 1) * 100


def h2():
    vuodet = sorted({*H2_A, *H2_B})
    t = luke("maa/maitot/v/0600_maitot.px", {"INFO": ["MTVLOP_KPL"], "A": vuodet})
    s = {y: hae(t, y) for y in vuodet}
    va, vb = _vauhti(s, *H2_A), _vauhti(s, *H2_B)
    ero = None if va is None or vb is None else -(vb - va)   # nopeampi väheneminen = positiivinen
    ok = None if ero is None else ero >= H2_RAJA_PP
    return {"H": "H2", "tuottajat": s, "vauhti_A_pct_v": va and round(va, 3), "vauhti_B_pct_v": vb and round(vb, 3),
            "kiihtyminen_pp": None if ero is None else round(ero, 3), "raja_pp": H2_RAJA_PP, "tulos": tila(ok)}


def h3():
    vuodet = JAKSO_A + JAKSO_B
    t = luke("maa/maitot/v/0600_maitot.px", {"INFO": ["VASTM_L"], "A": vuodet})
    s = {y: hae(t, y) for y in vuodet}
    a, b = ka(s[y] for y in JAKSO_A), ka(s[y] for y in JAKSO_B)
    m = None if a is None or b is None or not a else (b / a - 1) * 100
    ok = None if m is None else m > H3_RAJA
    p = luke("maa/tuohin/v/0600_tuohin.px", {"INFO": ["TUOHIN_KESKIM_CL"], "A": vuodet})
    hinta = {y: hae(p, y) for y in vuodet}
    return {"H": "H3", "maara_l": s, "muutos_pct": None if m is None else round(m, 2), "raja_pct": H3_RAJA,
            "tulos": tila(ok), "raportoi_tuottajahinta_c_l": hinta}


def main():
    fn = {"H1": h1, "H2": h2, "H3": h3}.get(sys.argv[1] if len(sys.argv) > 1 else "")
    if not fn:
        raise SystemExit(__doc__)
    r = fn()
    r["mitattu"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
