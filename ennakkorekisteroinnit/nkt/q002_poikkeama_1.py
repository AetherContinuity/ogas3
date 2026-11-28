"""Q-002 poikkeama 1: H1, P51C taulusta nasa_10_nf_tr (S1, PAID). Ks. poikkeama_1.md.
Kaava, kynnys ja loppuvuoden sääntö ovat lukitun q002.py:n vakioita ja apureita.
Ajo: python3 ennakkorekisteroinnit/nkt/q002_poikkeama_1.py H1"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import q002 as L  # noqa: E402


def _arvo(t, *avain):
    for k, x in t.items():
        if all(a in k for a in avain):
            return x
    return None


def h1() -> dict:
    maat = L.H1_MAAT + L.H1_RAPORTOI
    vuodet = [str(y) for y in range(L.H1_ALKU, max(L.H1_LOPPU_EHDOKKAAT) + 1)]
    b_cp, _ = L.es("nama_10_gdp", geo=maat, na_item="B1GQ", unit="CP_MNAC", time=vuodet)
    c_cp, _ = L.es("nasa_10_nf_tr", geo=maat, na_item="P51C", sector="S1", direct="PAID",
                   unit="CP_MNAC", time=vuodet)
    vol, volyksikko = None, None
    for u in ("CLV20_MNAC", "CLV15_MNAC", "CLV10_MNAC"):
        try:
            v, _ = L.es("nama_10_gdp", geo=maat, na_item="B1GQ", unit=u, time=vuodet)
        except Exception:
            continue
        if any(x is not None for x in v.values()):
            vol, volyksikko = v, u
            break
    pop, _ = L.es("nama_10_pe", geo=maat, na_item="POP_NC", unit="THS_PER", time=vuodet)
    sarja = {}
    for g in maat:
        s = {}
        for y in vuodet:
            b, c = _arvo(b_cp, g, y), _arvo(c_cp, g, y)
            bv = _arvo(vol, g, y) if vol else None
            p = _arvo(pop, g, y)
            s[y] = ((b - c) * bv / b) / p if None not in (b, c, bv, p) and b and p else None
        sarja[g] = s
    loppu = next((str(y) for y in L.H1_LOPPU_EHDOKKAAT
                  if all(sarja[g].get(str(y)) is not None for g in L.H1_MAAT)), None)
    muutos = {}
    for g in maat:
        a = sarja[g].get(str(L.H1_ALKU))
        b = sarja[g].get(loppu) if loppu else None
        muutos[g] = round((b / a - 1) * 100, 2) if a and b else None
    ok, ero = None, None
    if loppu and all(muutos[g] is not None for g in L.H1_MAAT):
        ero = muutos["FI"] - (muutos["SE"] + muutos["DK"]) / 2
        ok = ero <= L.H1_RAJA_PP
    return {"H": "H1", "poikkeama": 1, "volyymiyksikko": volyksikko, "alku": L.H1_ALKU, "loppu": loppu,
            "muutos_pct": muutos, "ero_FI_vs_ka_SE_DK_pp": None if ero is None else round(ero, 2),
            "raja_pp": L.H1_RAJA_PP, "tulos": L.tila(ok),
            "sarja": {g: {y: (None if x is None else round(x, 4)) for y, x in s.items()} for g, s in sarja.items()}}


if __name__ == "__main__":
    if sys.argv[1:] != ["H1"]:
        raise SystemExit(__doc__)
    r = h1()
    r["mitattu"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(json.dumps(r, ensure_ascii=False, indent=1))
