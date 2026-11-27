"""Sarjakeruu: Fingrid-sarjat 15 min resoluutiolla synapsikokeen aineistoksi (ei analyysia).

Kerää data/sarjat/<talvi>.json -tiedostoon sarjat, joita WEM-L1:n keruu ei tallenna.
1 ja 3 min sarjat keskiarvoistetaan 15 min varteiksi (vartti kelpaa, jos ≥ 60 % pisteistä on olemassa).
Inkrementaalinen: jatkaa viimeisestä tallennetusta vartista (−24 h päällekkäisyys, jälkikäteen
täydentyneet vartit päivittyvät). Data: Fingrid Open Data, CC BY 4.0.

  python3 tools/sarjakeruu.py --alku 2026-10-01 --loppu 2027-04-01 --out data/sarjat/2026-2027.json
Vain vakiokirjasto.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from wem_lopputulos import hae, _iso, _aika  # noqa: E402

SARJAT = {124: 15, 75: 15, 188: 3, 191: 3, 201: 3, 202: 3,
          371: 1,            # sähkökattiloiden kulutus (summa), 1 min, 3.12.2024 alkaen
          398: 3, 399: 3}    # akkuvarastot: purku, lataus
# ds: resoluutio min. Datakeskusten ja elektrolyysin kuormalle ei ole löydetty omaa Fingrid-sarjaa (27.11.2026).


def vartti(t: datetime) -> datetime:
    return t.replace(minute=t.minute - t.minute % 15, second=0, microsecond=0)


def keraa_ds(ds: int, res: int, alku: datetime, loppu: datetime, tauko: float) -> tuple[dict, list[str], list[str]]:
    askel = timedelta(minutes=res * 380)  # proxy: ≤ 400 riviä/kutsu
    kerat, virheet, raaka = defaultdict(list), [], []
    t = alku
    while t < loppu:
        u = min(t + askel, loppu)
        try:
            rivit = hae(ds, t, u)
            raaka.append(json.dumps(rivit, sort_keys=True))
            for r in rivit:
                st = _aika(r["startTime"])
                if alku <= st < loppu and isinstance(r.get("value"), (int, float)):
                    kerat[vartti(st)].append(r["value"])
        except Exception as e:  # noqa: BLE001
            virheet.append(f"DS {ds} {_iso(t)}–{_iso(u)}: {type(e).__name__}: {str(e)[:100]}")
        t = u
        time.sleep(tauko)
    vaadittu = max(1, -(-15 * 3 // (5 * res)))  # ≥ 60 % vartin pisteistä: 1 min → 9, 3 min → 3, 15 min → 1
    out = {_iso(k): round(sum(v) / len(v), 2) for k, v in kerat.items() if len(v) >= vaadittu}
    return out, virheet, raaka


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--alku", required=True); ap.add_argument("--loppu", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--tauko", type=float, default=2.0)
    a = ap.parse_args(argv)
    p = Path(a.out)
    vanha = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"sarjat": {}}
    nyt = datetime.now(timezone.utc)
    ik_alku = _aika(a.alku + "T00:00:00Z"); ik_loppu = min(_aika(a.loppu + "T00:00:00Z"), vartti(nyt))
    sarjat, virheet, raaka = dict(vanha.get("sarjat", {})), [], []
    for ds, res in SARJAT.items():
        s = dict(sarjat.get(str(ds), {}))
        alku = max(ik_alku, _aika(max(s)) - timedelta(hours=24)) if s else ik_alku
        uudet, v, r = keraa_ds(ds, res, alku, ik_loppu, a.tauko)
        s.update(uudet); sarjat[str(ds)] = dict(sorted(s.items())); virheet += v; raaka += r
    out = {"lahde": "Fingrid Open Data (CC BY 4.0) aci-fingrid-proxyn kautta; 3 min sarjat keskiarvoistettu 15 min varteiksi",
           "haettu": nyt.isoformat(timespec="seconds"), "ikkuna": [_iso(ik_alku), _iso(ik_loppu)],
           "resoluutio_lahteessa_min": {str(k): v for k, v in SARJAT.items()},
           "tama_ajo_raaka_sha256": hashlib.sha256("\n".join(raaka).encode()).hexdigest(), "virheet": virheet,
           "sarjat": sarjat}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print({k: len(v) for k, v in sarjat.items()}, "virheitä", len(virheet))
    return 0


if __name__ == "__main__":
    sys.exit(main())
