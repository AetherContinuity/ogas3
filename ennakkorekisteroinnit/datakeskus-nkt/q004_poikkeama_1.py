"""Q-004 poikkeama 1: kuvaileva arvonlisämittari (ks. poikkeama_1.md). Ei kumoamisehtoa.
Ajo: python3 ennakkorekisteroinnit/datakeskus-nkt/q004_poikkeama_1.py KUVAILE [--twh X --lahde "..."]"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import q004 as L  # noqa: E402


def kuvaile(twh=None, lahde=None):
    v = [L.PERUS, L.LOPPU]
    t = L._post("StatFin/ntp/15ad.px", {"sektoriluokitus_7_20230101": ["S1"], "taloustoimi_1_20180101": ["B1GPH", "B2N"],
                                         "toimiala_79_20180101": L.TOIMIALAT_15AF, "timeperiod_y": v,
                                         "contentscode": ["ntp-cp"]})
    k = L._15af("P51CK", v)
    out = {y: {"B1GPH": L._summa(t, y, "B1GPH"), "B2N": L._summa(t, y, "B2N"), "P51CK": L._summa(k, y)} for y in v}
    d = {x: None if out[L.LOPPU][x] is None or out[L.PERUS][x] is None else out[L.LOPPU][x] - out[L.PERUS][x]
         for x in ("B1GPH", "B2N", "P51CK")}
    suhde = {x: None if d[x] is None or not d["P51CK"] else round(d[x] / d["P51CK"], 3) for x in ("B1GPH", "B2N")}
    per_twh = "aineisto puutteellinen" if not twh else {x: out[L.LOPPU][x] and round(out[L.LOPPU][x] / twh, 1)
                                                         for x in ("B1GPH", "B2N")}
    return {"H": "KUVAILE", "poikkeama": 1, "tasot_meur": out, "muutos_meur": d, "muutos_per_kulumisen_muutos": suhde,
            "per_twh_meur": per_twh, "twh": twh, "twh_lahde": lahde}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("komento", choices=["KUVAILE"])
    ap.add_argument("--twh", type=float)
    ap.add_argument("--lahde")
    a = ap.parse_args()
    r = kuvaile(a.twh, a.lahde)
    r["mitattu"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(json.dumps(r, ensure_ascii=False, indent=1))
