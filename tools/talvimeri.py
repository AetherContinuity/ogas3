"""Talvimerenkulun odotusajat merialueittain (SM-024 § 09, ennakkokirjaus).

Mittaa kauppa-alusten jäänmurtaja-avustuksen odotukset (Digitraffic Marine,
winter-navigation v2, aktiviteetti WAIT) ja kohdistaa ne merialueelle
Suomen satamakäyntien (port-call v1) perusteella.

JULKAISURAJAUS (päätetty 26.11.2026): tulosteeseen menee vain koosteita
(merialue × kuukausi: lukumäärä, mediaani, p90). Ei alusten nimiä, IMO- tai
MMSI-numeroita, jäänmurtajien nimiä, sijainteja eikä yksittäisiä tapahtumia.
Raakadata pysyy ajon muistissa; siitä tallennetaan vain SHA-256 todisteeksi.
Data on CC BY 4.0 (Fintraffic / digitraffic.fi), mutta yksittäisten alusten
ja murtajien liikkeitä ei välitetä eteenpäin.

KOHDISTUSSÄÄNTÖ (lukittu ennen talven 2026–2027 tulosta)
- WAIT-tapahtuma kohdistetaan Suomen satamaan, jos saman aluksen satamakäynnin
  saapumisaika (ata) on välillä [WAIT alku, +72 h] (tuleva) tai lähtöaika (atd)
  välillä [WAIT alku -72 h, WAIT alku] (lähtevä). Lähempi voittaa.
- Merialue sataman koordinaateista (port-call/v1/ports, ssnLocations):
    Suomenlahti   lat < 60.75 ja lon >= 22.9
    Saaristomeri  lat < 60.75 ja lon <  22.9  (ml. Ahvenanmaa)
    Selkämeri     60.75 <= lat < 63.5
    Perämeri      lat >= 63.5  (ml. Merenkurkku pohjoispuoli)
- Kohdistamattomat (ei Suomen satamakäyntiä ikkunassa, esim. Venäjän tai Viron
  satamiin menevät) raportoidaan omana rivinään.
- Odotus = endTime - startTime tunteina; avoimet (ei endTime) jätetään pois.

Käyttö:
  python3 tools/talvimeri.py --base https://meri.digitraffic.fi \
      --from 2025-10-01 --out data/talvimeri/2025-2026.json
  (työtilasta: --base 'https://aci-policy-proxy.ruotsalainen-marko.workers.dev/?meri=')
Vain vakiokirjasto.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone

UA = {"Digitraffic-User": "ACI/ogas3-talvimeri", "Accept": "application/json",
      "User-Agent": "Mozilla/5.0 (ACI-ogas3-talvimeri/1.0)"}
IKKUNA = timedelta(hours=72)


def hae(base: str, polku: str, tries: int = 4) -> bytes:
    if base.endswith("="):  # proxy: ?meri=<koodattu polku>
        url = base + urllib.parse.quote(polku, safe="")
    else:
        url = base.rstrip("/") + "/" + polku
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == tries - 1:
                raise RuntimeError(f"{polku}: {e}") from e
            time.sleep(5 * (i + 1))
    raise AssertionError


def t(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def merialue(lat: float, lon: float) -> str:
    if lat >= 63.5:
        return "Perämeri"
    if lat >= 60.75:
        return "Selkämeri"
    return "Suomenlahti" if lon >= 22.9 else "Saaristomeri"


def p90(xs: list[float]) -> float | None:
    """Lähimmän sijan menetelmä; alle 10 havainnolla ei raportoida."""
    if len(xs) < 10:
        return None
    s = sorted(xs)
    return s[math.ceil(0.9 * len(s)) - 1]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://meri.digitraffic.fi")
    ap.add_argument("--from", dest="alku", required=True, help="YYYY-MM-DD")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    raw_v = hae(a.base, f"api/winter-navigation/v2/vessels?activeFrom={a.alku}T00:00:00Z")
    raw_p = hae(a.base, "api/port-call/v1/ports")
    sha = hashlib.sha256()
    sha.update(raw_v)
    sha.update(raw_p)

    alueet: dict[str, str] = {}
    for f in json.loads(raw_p)["ssnLocations"]["features"]:
        g = f.get("geometry")
        if f["locode"].startswith("FI") and g:
            lon, lat = g["coordinates"][:2]
            alueet[f["locode"]] = merialue(lat, lon)

    alukset = [v for v in json.loads(raw_v)["vessels"] if v.get("type") != "Icebreaker"]
    odotukset = []  # (imo, alku, tunnit)
    for v in alukset:
        for x in v.get("activities", []):
            if x["type"] == "WAIT" and x.get("endTime"):
                s, e = t(x["startTime"]), t(x["endTime"])
                odotukset.append((v.get("imo"), s, (e - s).total_seconds() / 3600))

    kaynnit: dict[int, list[tuple[str, datetime | None, datetime | None]]] = {}
    for imo in sorted({o[0] for o in odotukset if o[0]}):
        raw = hae(a.base, f"api/port-call/v1/port-calls?imo={imo}&from={a.alku}T00:00:00Z")
        sha.update(raw)
        rows = []
        for pc in json.loads(raw).get("portCalls", []):
            for d in pc.get("portAreaDetails") or [{}]:
                rows.append((pc["portToVisit"], t(d.get("ata")), t(d.get("atd"))))
        kaynnit[imo] = rows
        time.sleep(0.2)

    kooste: dict[tuple[str, str], list[float]] = defaultdict(list)
    for imo, s, h in odotukset:
        paras, ero = "kohdistamaton", None
        for loc, ata, atd in kaynnit.get(imo, []):
            for aika, ok in ((ata, ata and s <= ata <= s + IKKUNA), (atd, atd and s - IKKUNA <= atd <= s)):
                if ok and loc in alueet:
                    d = abs((aika - s).total_seconds())
                    if ero is None or d < ero:
                        paras, ero = alueet[loc], d
        kooste[(paras, s.strftime("%Y-%m"))].append(h)

    rivit = [
        {"merialue": al, "kuukausi": kk, "odotuksia": len(xs),
         "mediaani_h": round(statistics.median(xs), 2), "p90_h": None if p90(xs) is None else round(p90(xs), 2)}
        for (al, kk), xs in sorted(kooste.items())
    ]
    out = {
        "lahde": "Fintraffic / digitraffic.fi (CC BY 4.0): winter-navigation v2, port-call v1",
        "haettu": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "activeFrom": a.alku,
        "raaka_sha256": sha.hexdigest(),
        "kauppa_aluksia": len(alukset),
        "odotuksia_yht": len(odotukset),
        "rajaus": "vain koosteet; ei alustunnisteita, murtajia, sijainteja eikä yksittäisiä tapahtumia",
        "rivit": rivit,
    }
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(json.dumps({k: out[k] for k in ("kauppa_aluksia", "odotuksia_yht", "raaka_sha256")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
