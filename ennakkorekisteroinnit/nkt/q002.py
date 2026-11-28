"""Q-002 — mittaukset. LUKITTU yhdessä q002.md:n kanssa.

Tätä tiedostoa EI muuteta rekisteröinnin jälkeen. Korjaus uutena tiedostona
(q002_poikkeama_N.py) ja kirjauksena poikkeama_N.md ENNEN tulosta, jota se koskee.

Ajo:  python3 ennakkorekisteroinnit/nkt/q002.py H1|H2|H3|H4
      H1 tarvitsee Eurostatin (vain GitHub Actions, workflow q002).
      H2–H4 hakevat Tilastokeskuksen PxWebin ACI-proxyn kautta.
Tuloste: JSON stdoutiin; workflow tallentaa sen tiedostoon tulokset/<H>-<pvm>.json.
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
ES = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
UA = {"User-Agent": "OGAS3/0.1 q002", "Accept": "application/json"}

# ── kiinteät määritelmät ────────────────────────────────────────────────
H1_MAAT = ["FI", "SE", "DK"]          # testi
H1_RAPORTOI = ["NO"]                  # raportoidaan, ei testissä (öljy)
H1_ALKU = 2008
H1_LOPPU_EHDOKKAAT = [2025, 2024]     # viimeinen vuosi, joka on kaikilla H1_MAAT
H1_RAJA_PP = -5.0                     # FI − ka(SE, DK) on oltava ≤ tämä

H2_VARAT_POIS = ["N111", "N114"]      # asuinrakennukset, asejärjestelmät
H2_JAKSO_A = [2005, 2006, 2007, 2008]
H2_JAKSO_B = [2022, 2023, 2024, 2025]
H2_RAJA_PP = -1.0                     # ka(B) − ka(A) on oltava ≤ tämä

H3_MAA = "643"                        # Venäjä, StatFin valtio_27_20180101
H3_JAKSO_A = [2019, 2020, 2021]
H3_JAKSO_B = [2023, 2024, 2025]
H3_RAJA_OSUUS = 0.25

H4_PERUS = 2024
H4_LOPPU = 2027


# ── apurit ──────────────────────────────────────────────────────────────
def _get(url: str, data: bytes | None = None) -> dict:
    h = dict(UA)
    if data is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def jsonstat(d: dict) -> dict[tuple, float | None]:
    """json-stat2 → {(koodi, koodi, ...): arvo}. category.index on dict koodi→paikka
    (PxWeb) tai lista; value on lista (PxWeb) tai dict paikka→arvo (Eurostat)."""
    ids = d["id"]
    dims = []
    for k in ids:
        ix = d["dimension"][k]["category"]["index"]
        dims.append([c for c, _ in sorted(ix.items(), key=lambda x: x[1])] if isinstance(ix, dict) else list(ix))
    val = d["value"]
    out = {}
    for i, combo in enumerate(itertools.product(*dims)):
        v = val[i] if isinstance(val, list) else val.get(str(i))
        out[combo] = v
    return out, ids


def px(polku: str, valinnat: dict[str, list[str]]) -> tuple[dict, list]:
    q = {"query": [{"code": k, "selection": {"filter": "item", "values": v}} for k, v in valinnat.items()],
         "response": {"format": "json-stat2"}}
    return jsonstat(_get(PX + "?p=" + urllib.parse.quote(polku, safe="/"), json.dumps(q).encode()))


def es(taulu: str, **param) -> tuple[dict, list]:
    pairs = [(k, x) for k, v in param.items() for x in (v if isinstance(v, list) else [v])]
    return jsonstat(_get(ES + taulu + "?" + urllib.parse.urlencode(pairs)))


def ka(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def tila(ok: bool | None) -> str:
    return {True: "tuettu", False: "kumoutui", None: "aineisto puutteellinen"}[ok]


# ── H1: NKT henkeä kohden, FI vs SE, DK ────────────────────────────────
def h1() -> dict:
    """NKT_reaali = (B1GQ − P51C) käyvin hinnoin × (B1GQ volyymi / B1GQ käyvin),
    eli NKT deflatoituna BKT:n implisiittisellä hintaindeksillä, kansallisessa
    valuutassa. Henkeä kohden: nama_10_pe POP_NC (THS_PER)."""
    maat = H1_MAAT + H1_RAPORTOI
    vuodet = [str(y) for y in range(H1_ALKU, max(H1_LOPPU_EHDOKKAAT) + 1)]
    cp, _ = es("nama_10_gdp", geo=maat, na_item=["B1GQ", "P51C"], unit="CP_MNAC", time=vuodet)
    vol, volyksikko = None, None
    for u in ("CLV20_MNAC", "CLV15_MNAC", "CLV10_MNAC"):
        try:
            v, _ = es("nama_10_gdp", geo=maat, na_item="B1GQ", unit=u, time=vuodet)
        except Exception:
            continue
        if any(x is not None for x in v.values()):
            vol, volyksikko = v, u
            break
    pop, _ = es("nama_10_pe", geo=maat, na_item="POP_NC", unit="THS_PER", time=vuodet)

    def arvo(t, *avain):
        for k, x in t.items():
            if all(a in k for a in avain):
                return x
        return None

    sarja = {}
    for g in maat:
        s = {}
        for y in vuodet:
            b, c = arvo(cp, g, y, "B1GQ"), arvo(cp, g, y, "P51C")
            bv = arvo(vol, g, y, "B1GQ") if vol else None
            p = arvo(pop, g, y)
            s[y] = ((b - c) * bv / b) / p if None not in (b, c, bv, p) and b and p else None
        sarja[g] = s
    loppu = next((str(y) for y in H1_LOPPU_EHDOKKAAT
                  if all(sarja[g].get(str(y)) is not None for g in H1_MAAT)), None)
    muutos = {}
    for g in maat:
        a, b = sarja[g].get(str(H1_ALKU)), sarja[g].get(loppu) if loppu else None
        muutos[g] = round((b / a - 1) * 100, 2) if a and b else None
    ok = None
    if loppu and all(muutos[g] is not None for g in H1_MAAT):
        ero = muutos["FI"] - (muutos["SE"] + muutos["DK"]) / 2
        ok = ero <= H1_RAJA_PP
    else:
        ero = None
    return {"H": "H1", "volyymiyksikko": volyksikko, "alku": H1_ALKU, "loppu": loppu,
            "muutos_pct": muutos, "ero_FI_vs_ka_SE_DK_pp": None if ero is None else round(ero, 2),
            "raja_pp": H1_RAJA_PP, "tulos": tila(ok),
            "sarja": {g: {y: (None if x is None else round(x, 4)) for y, x in s.items()} for g, s in sarja.items()}}


# ── H2: tuotannollisen pääoman nettoinvestoinnit / BKT ─────────────────
def h2() -> dict:
    vuodet = [str(y) for y in H2_JAKSO_A + H2_JAKSO_B]
    varat = ["N0"] + H2_VARAT_POIS + ["N111_N112", "N112", "N113", "N115", "N116", "N117"]
    t, ids = px("StatFin/ntp/15af.px", {
        "taloustoimi_1_20180101": ["P51K", "P51CK"], "sektoriluokitus_7_20230101": ["S1"],
        "toimiala_79_20180101": ["SSS"], "varojenluokitus_5_20180101": varat,
        "timeperiod_y": vuodet, "contentscode": ["ntp-cp"]})
    b, _ = px("StatFin/ntp/15a9.px", {"taloustoimi_1_20180101": ["B1GMH"], "timeperiod_y": vuodet,
                                       "contentscode": ["ntp-cp"]})

    def v(tt, var, y):
        for k, x in t.items():
            if tt in k and var in k and y in k:
                return x
        return None

    bkt = {y: next((x for k, x in b.items() if y in k), None) for y in vuodet}
    rivit = {}
    for y in vuodet:
        net = {}
        for var in varat:
            g, c = v("P51K", var, y), v("P51CK", var, y)
            net[var] = None if None in (g, c) else g - c
        tuot = (None if net["N0"] is None or any(net[x] is None for x in H2_VARAT_POIS)
                else net["N0"] - sum(net[x] for x in H2_VARAT_POIS))
        rivit[y] = {"tuotannollinen_pct_bkt": None if tuot is None or not bkt[y] else round(tuot / bkt[y] * 100, 3),
                    **{f"{var}_pct_bkt": None if net[var] is None or not bkt[y] else round(net[var] / bkt[y] * 100, 3)
                       for var in varat}}
    a = ka(rivit[str(y)]["tuotannollinen_pct_bkt"] for y in H2_JAKSO_A)
    bb = ka(rivit[str(y)]["tuotannollinen_pct_bkt"] for y in H2_JAKSO_B)
    puuttuu = any(rivit[str(y)]["tuotannollinen_pct_bkt"] is None for y in H2_JAKSO_A + H2_JAKSO_B)
    ero = None if a is None or bb is None else bb - a
    ok = None if puuttuu or ero is None else ero <= H2_RAJA_PP
    return {"H": "H2", "ka_A": a and round(a, 3), "ka_B": bb and round(bb, 3),
            "ero_pp": None if ero is None else round(ero, 3), "raja_pp": H2_RAJA_PP,
            "tulos": tila(ok), "vuodet": rivit}


# ── H3: Venäjän suorien sijoitusten tuotto vs ensitulojen pudotus ──────
def h3() -> dict:
    vuodet = [str(y) for y in H3_JAKSO_A + H3_JAKSO_B]
    f, _ = px("StatFin/ssij/12gu.px", {"toimiala_79_20180101": ["SSS"], "varojenluokitus_5_20180101": ["F0"],
                                         "timeperiod_y": vuodet, "valtio_27_20180101": [H3_MAA],
                                         "contentscode": ["NIO", "KNO"]})
    e, _ = px("StatFin/ntp/15a9.px", {"taloustoimi_1_20180101": ["D1_D4N"], "timeperiod_y": vuodet,
                                       "contentscode": ["ntp-cp"]})

    def fv(c, y):
        return next((x for k, x in f.items() if c in k and y in k), None)

    nio = {y: fv("NIO", y) for y in vuodet}
    kno = {y: fv("KNO", y) for y in vuodet}
    ens = {y: next((x for k, x in e.items() if y in k), None) for y in vuodet}
    pud_ru = None if any(nio[str(y)] is None for y in H3_JAKSO_A + H3_JAKSO_B) else \
        ka(nio[str(y)] for y in H3_JAKSO_A) - ka(nio[str(y)] for y in H3_JAKSO_B)
    pud_ens = None if any(ens[str(y)] is None for y in H3_JAKSO_A + H3_JAKSO_B) else \
        ka(ens[str(y)] for y in H3_JAKSO_A) - ka(ens[str(y)] for y in H3_JAKSO_B)
    osuus = None if pud_ru is None or not pud_ens or pud_ens <= 0 else pud_ru / pud_ens
    ok = None if osuus is None else osuus >= H3_RAJA_OSUUS
    return {"H": "H3", "venaja_fdi_tuotto_meur": nio, "venaja_muut_kannan_muutokset_meur": kno,
            "ensitulot_netto_meur": ens, "pudotus_venaja_meur": pud_ru, "pudotus_ensitulot_meur": pud_ens,
            "osuus": None if osuus is None else round(osuus, 3), "raja": H3_RAJA_OSUUS, "tulos": tila(ok)}


# ── H4: puolustusmenojen kasvun kohdistuminen (kuvaileva) ──────────────
def h4() -> dict:
    vuodet = [str(H4_PERUS), str(H4_LOPPU)]
    m, _ = px("StatFin/jmete/12a6.px", {"sektoriluokitus_7_20230101": ["S13"],
                                          "taloustoimi_1_20180101": ["OTES", "P51K"],
                                          "julkisyht_teht_3_20010101": ["SSS", "G02"],
                                          "timeperiod_y": vuodet, "contentscode": ["jmete-bkt_suhde"]})
    s, _ = px("StatFin/ntp/15ah.px", {"sektoriluokitus_7_20230101": ["S13"], "taloustoimi_1_20180101": ["B9"],
                                       "timeperiod_y": vuodet, "contentscode": ["ntp-bkt_suhde"]})

    def mv(tt, f_, y):
        return next((x for k, x in m.items() if tt in k and f_ in k and y in k), None)

    out = {}
    for y in vuodet:
        g, tot = mv("OTES", "G02", y), mv("OTES", "SSS", y)
        out[y] = {"puolustus_pct": g, "muut_menot_pct": None if None in (g, tot) else round(tot - g, 2),
                  "puolustus_investoinnit_pct": mv("P51K", "G02", y),
                  "nettoluotonanto_pct": next((x for k, x in s.items() if y in k), None)}
    return {"H": "H4", "kuvaileva": True, "vuodet": out}


def main() -> int:
    h = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"H1": h1, "H2": h2, "H3": h3, "H4": h4}.get(h)
    if not fn:
        raise SystemExit(__doc__)
    r = fn()
    r["mitattu"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
