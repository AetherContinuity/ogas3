"""Q-001 poikkeama 2 — herkkyys ja diagnostiikka. Ei korvaa q001.py:tä.

Ajo:
  python3 ennakkorekisteroinnit/q001/q001_poikkeama_2.py H1|H1b|diag|yva
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from q001 import (H12_MIN_LOCKED, is_dt, is_ptx, laatija,  # noqa: E402
                  latest_trace, lausunnonantajat)


def _canon(names: list[str]) -> list[str]:
    from actors import canonical
    return sorted({canonical(x) or x for x in names})


def diag(tunnus: str) -> dict:
    t = latest_trace(tunnus, H12_MIN_LOCKED)
    nodes = [n for n in t.get("observed") or [] if n.get("doc_type") == "LAUSUNTO"]
    ilman = [n for n in nodes if not laatija(n)]
    return {"tunnus": tunnus, "trace_locked_at": t["_locked_at"], "lausunto_solmuja": len(nodes),
            "laatijattomia": len(ilman),
            "laatijattomat_esimerkit": [((n.get("evidence") or [{}])[0].get("quote") or "")[:100]
                                        for n in ilman[:10]]}


def h1_canonical() -> dict:
    t = latest_trace("TEM043:00/2026", H12_MIN_LOCKED)
    dt = [a for a in lausunnonantajat(t) if is_dt(a)]
    c = _canon(dt)
    return {"hypoteesi": "H1 (herkkyys: canonical)", "dt_nimet": dt, "dt_toimijat": c,
            "n_dt": len(c), "tulos": "TUETTU" if len(c) >= 3 else "KUMOTTU",
            "diag": diag("TEM043:00/2026")}


def h1b_canonical() -> dict:
    t = latest_trace("TEM043:00/2026", H12_MIN_LOCKED)
    sk = [a for a in lausunnonantajat(t) if is_dt(a) or is_ptx(a)]
    c = _canon(sk)
    return {"hypoteesi": "H1b (herkkyys: canonical)", "nimet": sk, "toimijat": c,
            "n": len(c), "tulos": "TUETTU" if len(c) >= 5 else "KUMOTTU"}


def yva() -> dict:
    """YVA-kaappauksen tila per snapshot ja D-hankkeiden loka–marraskuun
    nähtävilläolot: missä snapshotissa kukin ensimmäisen kerran näkyy."""
    RX = re.compile(r"datakeskus|palvelinkeskus|data ?cent", re.I)
    tila, nahty = {}, {}
    for p in sorted((ROOT / "snapshots").glob("20??-??.json")):
        s = json.loads(p.read_text(encoding="utf-8"))
        q = [x for x in s.get("queries") or [] if x.get("source") == "YVA"]
        n = sum(1 for e in s.get("events") or [] if e.get("source") == "YVA")
        tila[p.stem] = {"yva_tapahtumia": n, "virhe": (q[0].get("error") if q else "ei YVA-kyselyä")}
        for e in s.get("events") or []:
            pr = e.get("parameters") or {}
            if (e.get("source") == "YVA" and pr.get("vaihe") == "ohjelma_nahtavilla"
                    and RX.search(pr.get("hanke") or "")
                    and "2026-10-01" <= (e.get("known_at") or "")[:10] <= "2026-11-30"):
                nahty.setdefault(pr["slug"], {"hanke": pr.get("hanke"),
                                              "known_at": e["known_at"][:10],
                                              "ensin_snapshotissa": p.stem})
    return {"snapshotit": tila, "D_nahtavilla_10_11_2026": nahty}


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"H1": h1_canonical, "H1b": h1b_canonical, "yva": yva,
          "diag": lambda: [diag("TEM040:00/2026"), diag("TEM043:00/2026")]}.get(which)
    if not fn:
        raise SystemExit(__doc__)
    print(json.dumps(fn(), ensure_ascii=False, indent=2))
