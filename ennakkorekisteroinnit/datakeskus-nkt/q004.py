"""Q-004 — mittaukset. LUKITTU yhdessä q004.md:n kanssa.
Korjaukset uusina tiedostoina (q004_poikkeama_N.py + poikkeama_N.md) ennen tulosta.
Ajo: python3 ennakkorekisteroinnit/datakeskus-nkt/q004.py EHTO|H1|H2|H3   (PxWeb ACI-proxyn kautta)
Vain vakiokirjasto.
"""
from __future__ import annotations

import itertools
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

PX = "https://aci-pxweb-proxy.ruotsalainen-marko.workers.dev/"
PERUS, LOPPU = "2025", "2029"
EHTO_VUODET = ["2026", "2027", "2028", "2029"]
TOIMIALAT_15AF = ["J62_J63", "L681_L68209_L683"]   # tietojenkäsittely; muu kiinteistötoiminta (ei asunnot)
TOIMIALAT_12GU = ["J", "L"]
EHTO_RAJA_MEUR = 8000.0     # kumulatiivinen P51K 2026–29 − 4 × P51K 2025
H1_RAJA_PP = 0.3
H2_RAJA_PP = 0.2


def _post(polku, valinnat):
    q = {"query": [{"code": k, "selection": {"filter": "item", "values": v}} for k, v in valinnat.items()],
         "response": {"format": "json-stat2"}}
    req = urllib.request.Request(PX + "?p=" + urllib.parse.quote(polku, safe="/"), data=json.dumps(q).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "OGAS3/0.1 q004"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    dims = [[c for c, _ in sorted(d["dimension"][k]["category"]["index"].items(), key=lambda x: x[1])] for k in d["id"]]
    return dict(zip(itertools.product(*dims), d["value"]))


def _summa(t, vuosi, *avain):
    xs = [x for k, x in t.items() if vuosi in k and all(a in k for a in avain)]
    return None if not xs or any(x is None for x in xs) else sum(xs)


def _bkt(vuodet):
    t = _post("StatFin/ntp/15a9.px", {"taloustoimi_1_20180101": ["B1GMH", "B5N"], "timeperiod_y": vuodet,
                                       "contentscode": ["ntp-cp"]})
    return {y: (_summa(t, y, "B1GMH"), _summa(t, y, "B5N")) for y in vuodet}


def _15af(taloustoimi, vuodet):
    return _post("StatFin/ntp/15af.px", {"taloustoimi_1_20180101": [taloustoimi], "sektoriluokitus_7_20230101": ["S1"],
                                          "toimiala_79_20180101": TOIMIALAT_15AF, "varojenluokitus_5_20180101": ["N0"],
                                          "timeperiod_y": vuodet, "contentscode": ["ntp-cp"]})


def tila(ok):
    return {True: "tuettu", False: "kumoutui", None: "aineisto puutteellinen"}[ok]


def ehto():
    t = _15af("P51K", [PERUS] + EHTO_VUODET)
    perus = _summa(t, PERUS)
    vuodet = {y: _summa(t, y) for y in EHTO_VUODET}
    lisays = None if perus is None or any(v is None for v in vuodet.values()) else sum(vuodet.values()) - 4 * perus
    ok = None if lisays is None else lisays >= EHTO_RAJA_MEUR
    return {"H": "EHTO", "p51k_perus": perus, "p51k": vuodet, "lisays_meur": lisays, "raja_meur": EHTO_RAJA_MEUR,
            "tulos": {True: "täyttyi", False: "ei täyttynyt", None: "aineisto puutteellinen"}[ok]}


def h1():
    t = _15af("P51CK", [PERUS, LOPPU])
    b = _bkt([PERUS, LOPPU])
    osuus = {y: None if _summa(t, y) is None or not b[y][0] else _summa(t, y) / b[y][0] * 100 for y in (PERUS, LOPPU)}
    ero = None if None in osuus.values() else osuus[LOPPU] - osuus[PERUS]
    return {"H": "H1", "kuluminen_pct_bkt": osuus, "ero_pp": ero, "raja_pp": H1_RAJA_PP,
            "tulos": tila(None if ero is None else ero >= H1_RAJA_PP)}


def h2():
    t = _post("StatFin/ssij/12gu.px", {"toimiala_79_20180101": TOIMIALAT_12GU, "varojenluokitus_5_20180101": ["F0"],
                                        "timeperiod_y": [PERUS, LOPPU], "valtio_27_20180101": ["ULK"],
                                        "contentscode": ["NII"]})
    b = _bkt([PERUS, LOPPU])
    osuus = {y: None if _summa(t, y) is None or not b[y][0] else _summa(t, y) / b[y][0] * 100 for y in (PERUS, LOPPU)}
    ero = None if None in osuus.values() else osuus[LOPPU] - osuus[PERUS]
    return {"H": "H2", "fdi_tuotto_ulos_pct_bkt": osuus, "ero_pp": ero, "raja_pp": H2_RAJA_PP,
            "tulos": tila(None if ero is None else ero >= H2_RAJA_PP)}


def h3():
    vuodet = [str(y) for y in range(2021, int(LOPPU) + 1)]
    b = _bkt(vuodet)
    ero = {y: None if None in b[y] or not b[y][0] else (b[y][0] - b[y][1]) / b[y][0] * 100 for y in vuodet}
    return {"H": "H3", "kuvaileva": True, "bkt_miinus_nettokansantulo_pct_bkt": ero}


def main():
    fn = {"EHTO": ehto, "H1": h1, "H2": h2, "H3": h3}.get(sys.argv[1] if len(sys.argv) > 1 else "")
    if not fn:
        raise SystemExit(__doc__)
    r = fn()
    r["mitattu"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
