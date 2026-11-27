"""Datavahti (erillinen ogas3:n Hankeikkuna-vahdista, vahti.py): datasarjojen ja lukittujen tiedostojen terveystarkistus (data/datavahti/sarjat.json).

Deterministinen, ei kielimallia. Ei korjaa mitään, ei muuta määrittelyjä. Kirjoittaa tilan
data/datavahti/tila.json ja tulostaa muuttuneet tilat (workflow avaa niistä issuen).

TILAT
  OK                    kaikki tarkistukset läpi
  VANHENTUNUT           uusin piste tai keruu vanhempi kuin sallittu
  AUKKO                 puuttuvia jaksoja tai resoluutio muu kuin odotettu
  EPÄUSKOTTAVA          arvo rajojen ulkopuolella, vakio- tai nollasarja (kun sarjan pitäisi vaihdella),
                        lukitun tiedoston tiiviste muuttunut tai lukittu arvo ei toistu
  RAJAPINTA             proxy ei noudata ikkunaa tai kokoa (hiljainen väärä vastaus)
  EI_TARKISTETTAVISSA   haku tai luku epäonnistui; tarkistamaton ei ole OK
Kausiriippuvat keruut kauden ulkopuolella: OK, syy "ei kaudella".

Käyttö: python3 tools/datavahti.py [--sarjat data/datavahti/sarjat.json] [--tila data/datavahti/tila.json] [--juuri .]
Exit 0 aina kun ajo valmistui; muutokset stdoutiin (rivi per muutos, alkaa "MUUTOS ").
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
UA = {"User-Agent": "curl/8.0 (ACI-ogas3-vahti)", "Accept": "application/json"}


def _aika(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def hae(ds: int, alku: datetime, loppu: datetime, yrit: int = 3) -> list[dict]:
    f = "%Y-%m-%dT%H:%M:%SZ"
    q = urllib.parse.urlencode({"ds": ds, "start": alku.strftime(f), "end": loppu.strftime(f), "size": 400})
    for i in range(yrit):
        try:
            with urllib.request.urlopen(urllib.request.Request(PROXY + "?" + q, headers=UA), timeout=60) as r:
                d = json.loads(r.read())
            if isinstance(d, dict) and "error" in d:  # 429 tulee HTTP 200:na
                raise RuntimeError(str(d["error"])[:100])
            return d.get("data", []) if isinstance(d, dict) else []
        except Exception:
            if i == yrit - 1:
                raise
            time.sleep(6 + 2 * i)
    return []


def tarkista_sarja(s: dict, rivit: list[dict], nyt: datetime) -> tuple[str, list[str]]:
    syyt, tila = [], "OK"

    def aseta(t, syy):
        nonlocal tila
        syyt.append(syy)
        if tila == "OK" or t == "EPÄUSKOTTAVA":
            tila = t

    pts = []
    for r in rivit:
        try:
            pts.append((_aika(r["startTime"]), r["value"]))
        except (KeyError, TypeError, ValueError):
            return "EPÄUSKOTTAVA", ["rivin rakenne poikkeaa (startTime/value)"]
    if not pts:
        return "AUKKO", ["ikkunassa ei yhtään pistettä"]
    pts.sort()
    uusin = pts[-1][0]
    if nyt - uusin > timedelta(hours=s["max_viive_h"]):
        aseta("VANHENTUNUT", f"uusin piste {uusin:%Y-%m-%d %H:%M} UTC")
    ajat = [t for t, _ in pts]
    if len(set(ajat)) != len(ajat):
        aseta("EPÄUSKOTTAVA", f"kaksoisaikaleimoja {len(ajat) - len(set(ajat))}")
    vali = timedelta(minutes=s["resoluutio_min"])
    erot = [b - a for a, b in zip(ajat, ajat[1:]) if b != a]
    if erot and min(erot) != vali:
        aseta("AUKKO", f"resoluutio {min(erot)} ≠ {vali}")
    aukot = sum(1 for e in erot if e > vali)
    if aukot:
        aseta("AUKKO", f"{aukot} aukkoa ikkunassa")
    arvot = [v for _, v in pts]
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) for v in arvot):
        aseta("EPÄUSKOTTAVA", "ei-numeerinen arvo")
        return tila, syyt
    ulko = [v for v in arvot if not (s["min"] <= v <= s["max"])]
    if ulko:
        aseta("EPÄUSKOTTAVA", f"{len(ulko)} arvoa rajojen [{s['min']}, {s['max']}] ulkopuolella (esim. {ulko[0]})")
    if len(arvot) >= 4 and len(set(arvot)) == 1 and (s.get("vaihtelee") or arvot[0] == 0 and s["min"] > 0):
        aseta("EPÄUSKOTTAVA", f"vakiosarja ({arvot[0]}) {len(arvot)} pisteessä")
    return tila, syyt


def tarkista_rajapinta(rt: dict, rivit: list[dict]) -> tuple[str, list[str]]:
    a, b = _aika(rt["alku"]), _aika(rt["loppu"])
    try:
        ajat = [_aika(r["startTime"]) for r in rivit]
    except (KeyError, TypeError, ValueError):
        return "RAJAPINTA", ["rivin rakenne poikkeaa"]
    ulko = [t for t in ajat if not (a <= t < b)]
    if ulko:
        return "RAJAPINTA", [f"{len(ulko)} pistettä pyydetyn ikkunan ulkopuolella (start/end ohitettu?)"]
    if len(ajat) != rt["odotetut"]:
        return "RAJAPINTA", [f"{len(ajat)} pistettä, odotettiin {rt['odotetut']} (size ohitettu?)"]
    return "OK", []


def tarkista_tiedosto(t: dict, juuri: Path) -> tuple[str, list[str]]:
    p = juuri / t["polku"]
    try:
        b = p.read_bytes()
    except OSError as e:
        return "EI_TARKISTETTAVISSA", [f"ei luettavissa ({type(e).__name__})"]
    h = hashlib.sha256(b).hexdigest()[:16]
    if t.get("lukittu") and h != t["sha256_16"]:
        return "EPÄUSKOTTAVA", [f"lukitun tiedoston tiiviste {h} ≠ {t['sha256_16']}"]
    x = t.get("toisto")
    if not x:
        return "OK", []
    try:
        d = json.loads(b)
        if x["tyyppi"] == "talvimeri_rivi":
            n = [r["odotuksia"] for r in d["rivit"] if r["merialue"] == x["merialue"] and r["kuukausi"] == x["kuukausi"]]
            if n != [x["odotuksia"]]:
                return "EPÄUSKOTTAVA", [f"lukittu arvo ei toistu: {n} ≠ [{x['odotuksia']}]"]
        elif x["tyyppi"] == "wem_l1_vertailu":
            sys.path.insert(0, str(Path(__file__).parent))
            import wem_lopputulos as wl
            spec = json.loads((juuri / "data/wem-lopputulos/rekisterointi.json").read_text(encoding="utf-8"))
            spec["ikkuna"].update(alku="2025-10-01T00:00:00Z", loppu="2026-04-01T00:00:00Z")
            m = wl.laske(spec, d["data"])["muuttujat"]
            if m != spec["vertailutaso"]["arvot"]:
                return "EPÄUSKOTTAVA", [f"vertailutaso ei toistu: {m}"]
    except Exception as e:  # noqa: BLE001
        return "EI_TARKISTETTAVISSA", [f"toisto epäonnistui ({type(e).__name__}: {str(e)[:80]})"]
    return "OK", []


def tarkista_keruu(k: dict, juuri: Path, nyt: datetime) -> tuple[str, list[str]]:
    if nyt.month not in k["kaudella_kk"]:
        return "OK", ["ei kaudella"]
    try:
        d = json.loads((juuri / k["polku"]).read_text(encoding="utf-8"))
        haettu = _aika(str(d[k["kentta"]]))
    except FileNotFoundError:
        return "VANHENTUNUT", ["keruutiedosto puuttuu kaudella"]
    except Exception as e:  # noqa: BLE001
        return "EI_TARKISTETTAVISSA", [f"ei luettavissa ({type(e).__name__})"]
    ika = (nyt - haettu).days
    if ika > k["max_ika_vrk"]:
        return "VANHENTUNUT", [f"haettu {ika} vrk sitten"]
    return "OK", []


def aja(sarjat: dict, juuri: Path, nyt: datetime, hakija=hae, tauko: float = 2.0) -> dict:
    tilat = {}
    for s in sarjat["fingrid"]:
        try:
            rivit = hakija(s["ds"], nyt - timedelta(hours=6), nyt)
            t, syyt = tarkista_sarja(s, rivit, nyt)
        except Exception as e:  # noqa: BLE001
            t, syyt = "EI_TARKISTETTAVISSA", [f"haku epäonnistui ({type(e).__name__}: {str(e)[:80]})"]
        tilat[s["id"]] = {"tila": t, "syyt": syyt}
        time.sleep(tauko)
    rt = sarjat["rajapintatesti"]
    try:
        t, syyt = tarkista_rajapinta(rt, hakija(rt["ds"], _aika(rt["alku"]), _aika(rt["loppu"])))
    except Exception as e:  # noqa: BLE001
        t, syyt = "EI_TARKISTETTAVISSA", [f"haku epäonnistui ({type(e).__name__})"]
    tilat[rt["id"]] = {"tila": t, "syyt": syyt}
    for f in sarjat["tiedostot"]:
        t, syyt = tarkista_tiedosto(f, juuri)
        tilat[f["id"]] = {"tila": t, "syyt": syyt}
    for k in sarjat["keruut"]:
        t, syyt = tarkista_keruu(k, juuri, nyt)
        tilat[k["id"]] = {"tila": t, "syyt": syyt}
    return {"ajettu": nyt.isoformat(timespec="seconds"), "tilat": tilat, "ei_viela": sarjat.get("ei_viela", [])}


def muutokset(vanha: dict | None, uusi: dict) -> list[str]:
    v = (vanha or {}).get("tilat", {})
    out = []
    for k, x in uusi["tilat"].items():
        ed = v.get(k, {}).get("tila")
        if ed != x["tila"] and not (ed is None and x["tila"] == "OK"):
            out.append(f"MUUTOS {k}: {ed or '—'} → {x['tila']}" + (f" ({'; '.join(x['syyt'])})" if x["syyt"] else ""))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sarjat", default="data/datavahti/sarjat.json")
    ap.add_argument("--tila", default="data/datavahti/tila.json")
    ap.add_argument("--juuri", default=".")
    a = ap.parse_args(argv)
    sarjat = json.loads(Path(a.sarjat).read_text(encoding="utf-8"))
    tp = Path(a.tila)
    try:
        vanha = json.loads(tp.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        vanha = None
    uusi = aja(sarjat, Path(a.juuri), datetime.now(timezone.utc))
    tp.parent.mkdir(parents=True, exist_ok=True)
    tp.write_text(json.dumps(uusi, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for k, x in uusi["tilat"].items():
        print(f"{k:16} {x['tila']:20} {'; '.join(x['syyt'])}")
    for m in muutokset(vanha, uusi):
        print(m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
