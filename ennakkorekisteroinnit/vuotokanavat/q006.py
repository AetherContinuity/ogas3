"""Q-006 — mittaukset. LUKITTU yhdessä q006.md:n kanssa.
Korjaukset uusina tiedostoina (q006_poikkeama_N.py + poikkeama_N.md) ennen tulosta.
Ajo: python3 ennakkorekisteroinnit/vuotokanavat/q006.py H1|H2|H3   (PxWeb ACI-proxyn kautta)
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
STU_VANHA = "StatFin_Passiivi/stu/statfinpas_stu_pxt_125m.px"        # 2010–2019, maaryhmät
STU_UUSI = "StatFin/stu/13k8.px"                                     # 2020–2024, SSS
ULKOY_VANHA = "StatFin_Passiivi/ulkoy/statfinpas_ulkoy_pxt_12nd_2021.px"  # 2004–2021
ULKOY_UUSI = "StatFin/ulkoy/13ws.px"                                 # 2021–2024
MAARYHMAT = ["EU15X246", "EU28XEU15", "EURXEU28", "AFR", "021", "013_005", "AAS_OSE"]

ALKU, LOPPU = "2010", "2024"
H1_RAJA_PCT = 10.0     # C1:n suhteellinen kasvu ALKU→LOPPU, %
H2_RAJA_PP = 2.0       # C2:n kasvu ALKU→LOPPU, pp
SAUMA_RAJA_PCT = 5.0   # 2021 vanha vs uusi ero, jonka ylittyessä sauma merkitään


def _post(polku, valinnat):
    q = {"query": [{"code": k, "selection": {"filter": "item", "values": v}} for k, v in valinnat.items()],
         "response": {"format": "json-stat2"}}
    req = urllib.request.Request(PX + "?p=" + urllib.parse.quote(polku, safe="/"), data=json.dumps(q).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "OGAS3/0.1 q006"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    dims = [[c for c, _ in sorted(d["dimension"][k]["category"]["index"].items(), key=lambda x: x[1])] for k in d["id"]]
    return dict(zip(itertools.product(*dims), d["value"]))


def _summa(t, *avain):
    xs = [x for k, x in t.items() if all(a in k for a in avain)]
    return None if not xs or any(x is None for x in xs) else sum(xs)


def stu(tieto_vanha, tieto_uusi):
    v = _post(STU_VANHA, {"Vuosi": [str(y) for y in range(2010, 2020)], "Maaryhmä": MAARYHMAT, "Tiedot": [tieto_vanha]})
    u = _post(STU_UUSI, {"timeperiod_y": [str(y) for y in range(2020, 2025)], "valtio_27_20180101": ["SSS"],
                         "contentscode": [tieto_uusi]})
    out = {str(y): _summa(v, str(y)) for y in range(2010, 2020)}
    out.update({str(y): _summa(u, str(y)) for y in range(2020, 2025)})
    return out


def ulkoy():
    tiedot_v = ["henkmaara", "henkiloston_osuus", "liikevaihto", "liikevaihdon_osuus"]
    v = _post(ULKOY_VANHA, {"Vuosi": [str(y) for y in range(2004, 2022)], "Tiedot": tiedot_v})
    u = _post(ULKOY_UUSI, {"timeperiod_y": [str(y) for y in range(2021, 2025)],
                           "contentscode": ["ulkoy-henkmaara", "henkiloston_osuus", "ulkoy-liikevaihto", "liikevaihdon_osuus"]})
    nimet = dict(zip(["ulkoy-henkmaara", "henkiloston_osuus", "ulkoy-liikevaihto", "liikevaihdon_osuus"], tiedot_v))
    out = {}
    for y in range(2004, 2022):
        out[str(y)] = {t: _summa(v, str(y), t) for t in tiedot_v}
    sauma = {}
    for y in range(2021, 2025):
        uusi = {nimet[t]: _summa(u, str(y), t) for t in nimet}
        if str(y) == "2021":
            sauma = {"vanha": out["2021"], "uusi": uusi}
        out[str(y)] = uusi            # uusi taulu ensisijainen vuodesta 2021
    return out, sauma


def _saumaliput(sauma):
    liput = {}
    for t in ("henkmaara", "henkiloston_osuus"):
        a, b = (sauma.get("vanha") or {}).get(t), (sauma.get("uusi") or {}).get(t)
        liput[t] = None if not a or b is None else round((b / a - 1) * 100, 2)
    return liput, any(x is not None and abs(x) > SAUMA_RAJA_PCT for x in liput.values())


def tila(ok):
    return {True: "tuettu", False: "kumoutui", None: "aineisto puutteellinen"}[ok]


def c1():
    """C1 = suomalaisten ulkomaisten tytäryhtiöiden henkilöstö / Suomen yritysten henkilöstö,
    jossa nimittäjä = ulkoy henkmaara / (henkiloston_osuus / 100) samana vuonna."""
    s = stu("henkilosto", "henkilosto")
    u, sauma = ulkoy()
    c = {}
    for y in s:
        hm, os_ = (u.get(y) or {}).get("henkmaara"), (u.get(y) or {}).get("henkiloston_osuus")
        nim = None if not hm or not os_ else hm / (os_ / 100)
        c[y] = None if s[y] is None or not nim else s[y] / nim
    return s, u, c, sauma


def h1():
    s, u, c, sauma = c1()
    a, b = c.get(ALKU), c.get(LOPPU)
    m = None if not a or b is None else (b / a - 1) * 100
    liput, katkos = _saumaliput(sauma)
    return {"H": "H1", "C1": {y: None if x is None else round(x, 4) for y, x in c.items()},
            "stu_henkilosto": s, "muutos_pct": None if m is None else round(m, 2), "raja_pct": H1_RAJA_PCT,
            "tulos": tila(None if m is None else m >= H1_RAJA_PCT),
            "sauma_stu_2019_2020": "ei päällekkäistä vuotta; ei testattavissa", "sauma_ulkoy_2021_pct": liput,
            "sauma_merkitty": katkos}


def h2():
    u, sauma = ulkoy()
    c2 = {y: (u[y] or {}).get("henkiloston_osuus") for y in u}
    a, b = c2.get(ALKU), c2.get(LOPPU)
    ero = None if a is None or b is None else b - a
    liput, katkos = _saumaliput(sauma)
    return {"H": "H2", "C2_henkiloston_osuus": c2,
            "C2_liikevaihdon_osuus": {y: (u[y] or {}).get("liikevaihdon_osuus") for y in u},
            "ero_pp": None if ero is None else round(ero, 2), "raja_pp": H2_RAJA_PP,
            "tulos": tila(None if ero is None else ero >= H2_RAJA_PP),
            "kuvaileva_2008_2024_pp": None if c2.get("2008") is None or b is None else round(b - c2["2008"], 2),
            "sauma_ulkoy_2021_pct": liput, "sauma_merkitty": katkos}


def h3():
    r1, r2 = h1(), h2()
    c1a, c1b = r1["C1"].get(ALKU), r1["C1"].get(LOPPU)
    c2 = r2["C2_henkiloston_osuus"]
    k1 = None if not c1a or c1b is None else (c1b / c1a - 1) * 100
    k2 = None if not c2.get(ALKU) or c2.get(LOPPU) is None else (c2[LOPPU] / c2[ALKU] - 1) * 100
    return {"H": "H3", "kuvaileva": True, "C1_suht_muutos_pct": k1 and round(k1, 2), "C2_suht_muutos_pct": k2 and round(k2, 2),
            "nopeampi": None if k1 is None or k2 is None else ("tuotanto ulos (C1)" if k1 > k2 else "omistus sisään (C2)")}


if __name__ == "__main__":
    fn = {"H1": h1, "H2": h2, "H3": h3}.get(sys.argv[1] if len(sys.argv) > 1 else "")
    if not fn:
        raise SystemExit(__doc__)
    r = fn()
    r["mitattu"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(json.dumps(r, ensure_ascii=False, indent=1))
