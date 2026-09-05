"""OGAS3 — kuukausittainen tilannekaappaus.

Ajetaan GitHub Actionsissa kerran kuussa. Tulos commitoidaan hakemistoon
snapshots/ ja se on sarjan ainoa muisti — versionhallinta on tietokanta.

MIKSI TÄMÄ AJETAAN ENNEN KUIN RRI-KAAVA ON LUKITTU
--------------------------------------------------
PRE-sarja väittää mittaavansa sitä, mitä olisi voitu tietää kyseisenä
kuukautena. Jos ensimmäinen sarja tuotetaan taannehtivasti sen jälkeen
kun kaava on valmis, väite ei pidä: ajohetkellä tiedetään jo mitä
tapahtui, ja look-ahead on rakenteessa eikä koodissa.

Siksi tämä kaappaa TODISTEEN nyt ja jättää LUOKITUKSEN myöhemmäksi:

    kaapataan       tapahtumat, kolme aikaleimaa, todisteet, anomaliat
    ei kaapata      type (D/O/S), impact_weight, intensity
    ei lasketa      SP, L, IR, RRI

Kun ROE valmistuu, luokitus lisätään näihin jo jäädytettyihin
tapahtumiin. Havainto on silloin lukossa, eikä sitä voi enää värittää
sillä mitä tapahtui myöhemmin.

`expanding`-skaalaus vaatii lisäksi kuukausia takanaan: yhdellä
kuukaudella se antaa nollan (ks. tests/test_all.py). Sarjan on siis
alettava nyt riippumatta siitä, milloin kaava valmistuu.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetchers import fetch_eduskunta, fetch_hankeikkuna, summarize  # noqa: E402

SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots"

# Hankeikkunan haut. Jokainen on oma sarjansa; valmisteluvaihe on osa
# tapahtuman merkitystä eikä pelkkä suodatin.
# ANSA: valmisteluvaiheen enum-listaa EI saa rajapinnasta.
# GET /api/v2/valmisteluvaiheet on 404. Arvot on luettava aineistosta
# itsestään (kohde.valmisteluvaihe ja etapit[].valmisteluvaihe).
# Väärä arvo palauttaa 400 "Invalid request parameters", ei tyhjää —
# tämä on poikkeus päivän muihin ansoihin: se ainakin valittaa.
#
# Todennetut arvot 5.9.2026, esiintymismäärä 32 hankkeen etapeissa:
#   PERUSVALMISTELU 54 · EDUSKUNTAKASITTELY 38 · LAUSUNTOMENETTELY 37
#   VALTIONEUVOSTON_PAATOKSENTEKO 25 · JATKOVALMISTELU 22
#   ESIVALMISTELU 19 · LAIN_VAHVISTAMINEN 3 · VALMISTUNUT 1
HANKEIKKUNA_QUERIES = [
    ("LAINSAADANTO", "EDUSKUNTAKASITTELY"),
    ("LAINSAADANTO", "LAUSUNTOMENETTELY"),
    ("LAINSAADANTO", "PERUSVALMISTELU"),
    ("LAINSAADANTO", "VALTIONEUVOSTON_PAATOKSENTEKO"),
]


def git_sha() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10
        ).stdout.strip() or None
    except Exception:
        return None


def _existing_events(month: str) -> int | None:
    """Kuukauden nykyisen (jo commitoidun) snapshotin tapahtumamäärä, jos tiedosto on olemassa."""
    p = SNAPSHOT_DIR / f"{month}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))["totals"]["events"]
    except Exception:
        return None


def run(month: str | None = None, dry_run: bool = False) -> tuple[Path | None, dict]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    month = month or f"{now.year:04d}-{now.month:02d}"

    raw: list[dict] = []
    per_query = []

    for tyyppi, vaihe in HANKEIKKUNA_QUERIES:
        try:
            evs = fetch_hankeikkuna(valmisteluvaihe=vaihe, tyyppi=tyyppi, size=1000)
        except Exception as exc:                       # haku voi kaatua; se kirjataan
            per_query.append({"source": "Hankeikkuna", "tyyppi": tyyppi,
                              "valmisteluvaihe": vaihe, "error": str(exc)})
            continue
        for e in evs:
            d = e.to_dict()
            d["parameters"]["query_valmisteluvaihe"] = vaihe
            raw.append(d)
        per_query.append({"source": "Hankeikkuna", "tyyppi": tyyppi,
                          "valmisteluvaihe": vaihe, **summarize(evs)})

    # Eduskunnan käsittelyvaiheet niille hankkeille, joilla on HE-numero.
    # Nämä ovat ainoa lähde, jossa occurred_at == known_at on perusteltu.
    he_numbers = sorted({
        n for d in raw
        for n in (d["parameters"].get("heNumerot") or [])
        if isinstance(n, str)
    })
    for he in he_numbers[:40]:
        try:
            evs = fetch_eduskunta(he)
        except Exception as exc:
            per_query.append({"source": "Eduskunta", "tunnus": he, "error": str(exc)})
            continue
        raw.extend(e.to_dict() for e in evs)
        per_query.append({"source": "Eduskunta", "tunnus": he, **summarize(evs)})

    anomalies = [d for d in raw if d.get("_anomaly")]

    snap = {
        "month": month,
        "captured_at": now.isoformat(),
        "captured_by": os.environ.get("GITHUB_WORKFLOW") or "local",
        "run_url": (f"{os.environ.get('GITHUB_SERVER_URL','')}/"
                    f"{os.environ.get('GITHUB_REPOSITORY','')}/actions/runs/"
                    f"{os.environ.get('GITHUB_RUN_ID','')}")
                   if os.environ.get("GITHUB_RUN_ID") else None,
        "git_sha": git_sha(),
        "status": {
            "classification": "DEFERRED — ROE/D-O-S-kartta ei ole lukittu",
            "rri": "NOT SPECIFIED — ks. audit.compute_rri",
            "note": "Tämä tiedosto on TODISTE, ei tulos. Luokitus lisätään "
                    "myöhemmin näihin jäädytettyihin tapahtumiin.",
        },
        "totals": {
            "events": len(raw),
            "anomalies": len(anomalies),
            "sources": sorted({d["source"] for d in raw}),
        },
        "queries": per_query,
        "events": raw,
    }

    if dry_run:
        return None, snap

    SNAPSHOT_DIR.mkdir(exist_ok=True)
    out = SNAPSHOT_DIR / f"{month}.json"
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return out, snap


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("month", nargs="?", default=None)
    ap.add_argument("--dry-run", action="store_true",
                     help="hae ja tarkista, älä kirjoita snapshotia — savutesti käsinajolle")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    month = args.month or f"{now.year:04d}-{now.month:02d}"
    prev_n = _existing_events(month)   # luetaan ENNEN mahdollista ylikirjoitusta

    path, d = run(month, dry_run=args.dry_run)
    label = path.name if path else f"{d['month']}.json (ei kirjoitettu — --dry-run)"
    print(f"{label}: {d['totals']['events']} tapahtumaa, "
          f"{d['totals']['anomalies']} anomaliaa, lähteet {d['totals']['sources']}")
    for q in d["queries"]:
        if "error" in q:
            print(f"  VIRHE  {q.get('source')} {q.get('valmisteluvaihe') or q.get('tunnus')}: {q['error'][:90]}")

    has_errors = any("error" in q for q in d["queries"])
    if prev_n is not None and not has_errors:
        delta = d["totals"]["events"] - prev_n
        if delta != 0:
            print(f"  HUOM  tapahtumamäärä muuttunut olemassa olevasta: "
                  f"{prev_n} -> {d['totals']['events']} (Δ{delta:+d}) — "
                  "hankkeita tullut tai kadonnut kesken kuukauden, ei rutiinia")
