"""WEM-L1: fyysisten lopputulosten mittaus (data/wem-lopputulos/rekisterointi.json). Ei ennuste.

  kerää:   python3 tools/wem_lopputulos.py kerää --out data/wem-lopputulos/2026-2027.json
           (Fingrid DS 244/373/342 ACI-proxyn kautta, 3 vrk ikkunat, ≤ 400 riviä/kutsu)
  arvioi:  python3 tools/wem_lopputulos.py arvioi data/wem-lopputulos/rekisterointi.json \
               --aineisto data/wem-lopputulos/2026-2027.json [--pvm YYYY-MM-DD] [--out TILA.json]

Aineisto: {"lahde", "haettu", "ikkuna", "raaka_sha256", "data": {startTime: {offered_up, activated, price}}}
(sama kenttärakenne kuin vertailutasossa rp-margin-talvi-2025-2026.json). Data on Fingrid Open Data, CC BY 4.0.
Vain vakiokirjasto.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROXY = "https://aci-fingrid-proxy.ruotsalainen-marko.workers.dev/"
UA = {"User-Agent": "curl/8.0 (ACI-ogas3-wem-lopputulos)", "Accept": "application/json"}
KENTTA = {244: "price", 373: "offered_up", 342: "activated"}


def _iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _aika(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def hae(ds: int, alku: datetime, loppu: datetime, yrit: int = 4) -> list[dict]:
    q = urllib.parse.urlencode({"ds": ds, "start": _iso(alku).replace(".000", ""), "end": _iso(loppu).replace(".000", ""), "size": 400})
    for i in range(yrit):
        try:
            with urllib.request.urlopen(urllib.request.Request(PROXY + "?" + q, headers=UA), timeout=60) as r:
                d = json.loads(r.read())
            if isinstance(d, dict) and "error" in d:
                raise RuntimeError(d["error"])
            return d.get("data", [])
        except Exception:
            if i == yrit - 1:
                raise
            time.sleep(6 + 2 * i)
    return []


def keraa(alku: datetime, loppu: datetime, tauko: float = 2.0) -> tuple[dict, list[str], bytes]:
    data: dict[str, dict] = {}
    virheet, raaka = [], []
    for ds, kentta in KENTTA.items():
        t = alku
        while t < loppu:
            u = min(t + timedelta(days=3), loppu)
            try:
                rivit = hae(ds, t, u)
                raaka.append(json.dumps(rivit, sort_keys=True))
                for r in rivit:
                    st = _aika(r["startTime"])
                    if st.minute % 15 or st.second or not (alku <= st < loppu):
                        continue  # DS 342: 1 min endTime, startTime vartin alussa
                    if isinstance(r.get("value"), (int, float)):
                        data.setdefault(_iso(st), {})[kentta] = r["value"]
            except Exception as e:
                virheet.append(f"DS {ds} {_iso(t)}–{_iso(u)}: {type(e).__name__}: {str(e)[:120]}")
            t = u
            time.sleep(tauko)
    return data, virheet, "\n".join(raaka).encode()


def laske(spec: dict, data: dict) -> dict:
    ik = spec["ikkuna"]
    a, b = _aika(ik["alku"]), _aika(ik["loppu"])
    vartit = []
    t = a
    while t < b:
        vartit.append(_iso(t)); t += timedelta(minutes=15)
    arvot = {"margin": {}, "hinta": {}}
    for v in vartit:
        r = data.get(v, {})
        up, act, pr = r.get("offered_up"), r.get("activated"), r.get("price")
        if isinstance(up, (int, float)) and isinstance(act, (int, float)) and up > 0:
            arvot["margin"][v] = (up - max(0, act)) / up
        if isinstance(pr, (int, float)):
            arvot["hinta"][v] = pr
    puuttuu = {k: [v for v in vartit if v not in arvot[k]] for k in arvot}
    tulos = {"odotetut_vartit": len(vartit),
             "kelpaavat": {k: len(arvot[k]) for k in arvot},
             "puuttuvat": {k: {"lkm": len(puuttuu[k]), "valit": _valit(puuttuu[k])} for k in arvot},
             "muuttujat": {}}
    for m in spec["muuttujat"]:
        xs = arvot[m["lahde"]].values()
        n = sum(1 for x in xs if (x < m["raja"] if m["ehto"] == "<" else x >= m["raja"]))
        tulos["muuttujat"][m["nimi"]] = n
    return tulos


def _valit(vs: list[str]) -> list[list[str]]:
    out = []
    for v in vs:
        if out and _aika(v) - _aika(out[-1][1]) == timedelta(minutes=15):
            out[-1][1] = v
        else:
            out.append([v, v])
    return out[:50]


def arvioi(spec: dict, polku: Path, pvm: datetime) -> dict:
    t = {"id": spec["id"], "arvioitu": pvm.date().isoformat(), "tila": None, "syyt": []}
    try:
        d = json.loads(polku.read_text(encoding="utf-8"))
    except FileNotFoundError:
        t.update(tila="HAVAINTO_PUUTTUU"); t["syyt"].append(f"aineisto puuttuu: {polku}"); return t
    except (OSError, ValueError) as e:
        t.update(tila="HAVAINTO_PUUTTUU"); t["syyt"].append(f"aineisto ei jäsenny ({type(e).__name__})"); return t
    if not isinstance(d, dict) or not isinstance(d.get("data"), dict) or not d.get("raaka_sha256"):
        t.update(tila="HAVAINTO_PUUTTUU"); t["syyt"].append("data- tai raaka_sha256-kenttä puuttuu"); return t
    mitattu = laske(spec, d["data"])
    t["aineisto_haettu"], t["raaka_sha256"] = d.get("haettu"), d["raaka_sha256"]
    t["keruuvirheet"] = d.get("virheet", [])
    loppu = _aika(spec["ikkuna"]["loppu"])
    try:
        haettu = _aika(str(d.get("haettu")))
    except ValueError:
        t.update(tila="HAVAINTO_PUUTTUU"); t["syyt"].append("haettu-aika ei jäsenny"); return t
    if any(v == 0 for v in mitattu["kelpaavat"].values()):
        t.update(tila="HAVAINTO_PUUTTUU", valihavainto=mitattu)
        t["syyt"].append("jokin lähde puuttuu kokonaan"); return t
    if haettu < loppu or pvm < loppu:
        t.update(tila="HAVAINTO_PUUTTUU", valihavainto=mitattu)
        t["syyt"].append(f"ikkuna kesken (päättyy {loppu.date()}); välihavainto ei ole tulos"); return t
    t.update(tila="MITATTU", tulos=mitattu, vertailutaso=spec["vertailutaso"]["arvot"], sisakkaisyys=spec["sisakkaisyys"])
    if mitattu["puuttuvat"]["margin"]["lkm"] or mitattu["puuttuvat"]["hinta"]["lkm"]:
        t["syyt"].append("puuttuvia vartteja; ks. tulos.puuttuvat (puuttuva ≠ nolla)")
    return t


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    k = sp.add_parser("kerää"); k.add_argument("--spec", default="data/wem-lopputulos/rekisterointi.json"); k.add_argument("--out", required=True)
    a = sp.add_parser("arvioi"); a.add_argument("spec"); a.add_argument("--aineisto", required=True); a.add_argument("--pvm"); a.add_argument("--out")
    x = ap.parse_args(argv)
    if x.cmd == "kerää":
        spec = json.loads(Path(x.spec).read_text(encoding="utf-8"))
        nyt = datetime.now(timezone.utc)
        alku, loppu = _aika(spec["ikkuna"]["alku"]), min(_aika(spec["ikkuna"]["loppu"]), nyt.replace(minute=nyt.minute - nyt.minute % 15, second=0, microsecond=0))
        data, virheet, raaka = keraa(alku, loppu)
        out = {"lahde": "Fingrid Open Data (CC BY 4.0), DS 244/373/342 aci-fingrid-proxyn kautta",
               "haettu": nyt.isoformat(timespec="seconds"), "ikkuna": [_iso(alku), _iso(loppu)],
               "raaka_sha256": hashlib.sha256(raaka).hexdigest(), "virheet": virheet,
               "data": dict(sorted(data.items()))}
        Path(x.out).parent.mkdir(parents=True, exist_ok=True)
        Path(x.out).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        print(f"vartteja {len(data)}, keruuvirheitä {len(virheet)}")
        return 0
    spec = json.loads(Path(x.spec).read_text(encoding="utf-8"))
    pvm = datetime.fromisoformat(x.pvm).replace(tzinfo=timezone.utc) if x.pvm else datetime.now(timezone.utc)
    t = arvioi(spec, Path(x.aineisto), pvm)
    s = json.dumps(t, ensure_ascii=False, indent=1)
    if x.out:
        Path(x.out).write_text(s + "\n", encoding="utf-8")
    print(s[:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
