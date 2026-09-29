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
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetchers import fetch_eduskunta, fetch_hankeikkuna, summarize  # noqa: E402
from decision_chain import (chains, fetch_votes, he_key, resolve_hanke,  # noqa: E402
                            statutes_published_between)

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
    ("LAINSAADANTO", "LAIN_VAHVISTAMINEN"),
]
# Lisätty 2026-09-29: ilman ketjun loppupään vaiheita Finlexissä
# vahvistuneet lait eivät liittyneet mihinkään hankkeeseen — syyskuun
# koeajossa 5/5 vahvistunutta HE:tä jäi ilman hanketta. PAATTYNYT haetaan
# vain ikkunan ajalta (muokattuPaivaAlku), koska koko arkisto on vuodesta 2001.


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

    y, m = (int(x) for x in month.split("-"))
    fx_start = date(y - 1, 12, 1) if m == 1 else date(y, m - 1, 1)
    fx_end = date(y, m, 1)

    queries = [(t, v, None) for t, v in HANKEIKKUNA_QUERIES] + [
        ("LAINSAADANTO", None, {"tila": ["PAATTYNYT"],
                                "muokattuPaivaAlku": f"{fx_start.isoformat()}T00:00:00"})]
    for tyyppi, vaihe, extra in queries:
        try:
            evs = fetch_hankeikkuna(valmisteluvaihe=vaihe, tyyppi=tyyppi, size=1000, extra=extra)
        except Exception as exc:                       # haku voi kaatua; se kirjataan
            per_query.append({"source": "Hankeikkuna", "tyyppi": tyyppi,
                              "valmisteluvaihe": vaihe, "error": str(exc)})
            continue
        for e in evs:
            d = e.to_dict()
            d["parameters"]["query_valmisteluvaihe"] = vaihe or "PAATTYNYT (ikkuna)"
            raw.append(d)
        per_query.append({"source": "Hankeikkuna", "tyyppi": tyyppi,
                          "valmisteluvaihe": vaihe, **({"extra": extra} if extra else {}),
                          **summarize(evs)})

    # Sama hanke voi osua kahteen kyselyyn (esim. LAIN_VAHVISTAMINEN ja
    # PAATTYNYT). Ensimmäinen esiintymä pidetään, duplikaatti kirjataan.
    seen, dedup, dups = set(), [], 0
    for d in raw:
        if d["event_id"] in seen:
            dups += 1
            continue
        seen.add(d["event_id"])
        dedup.append(d)
    raw = dedup
    if dups:
        per_query.append({"source": "Hankeikkuna", "note": f"{dups} duplikaattia poistettu kyselyjen väliltä"})

    # Finlex: edellisenä kalenterikuukautena julkaistut säädökset.
    # Kaappaus ajetaan kuun 1. päivänä, joten ikkuna on juuri päättynyt
    # kuukausi. known_at = datePublished osuu siis aina ikkunaan.
    try:
        fx, fx_log = statutes_published_between(fx_start, fx_end)
        raw.extend(e.to_dict() for e in fx)
        per_query.append(fx_log)
    except Exception as exc:
        per_query.append({"source": "Finlex", "window": [fx_start.isoformat(), fx_end.isoformat()],
                          "error": str(exc)})

    # Eduskunnan käsittelyvaiheet niille hankkeille, joilla on HE-numero.
    # Nämä ovat ainoa lähde, jossa occurred_at == known_at on perusteltu.
    he_numbers = sorted({
        k for d in raw if d["source"] in ("Hankeikkuna", "Finlex")
        for n in (d["parameters"].get("heNumerot") or [])
        if isinstance(n, str) and (k := he_key(n))
    })
    # HE:t joilla ei ole hanketta kaappauksessa (tyypillisesti Finlexistä
    # löytyneet, joiden hanke on päättynyt ennen ikkunaa). Haetaan
    # hanke HE-numerolla — muuten ketjun alku puuttuu.
    have = {k for d in raw if d["source"] == "Hankeikkuna"
            for n in (d["parameters"].get("heNumerot") or [])
            if isinstance(n, str) and (k := he_key(n))}
    seen_ids = {d["event_id"] for d in raw}
    for he in [h for h in he_numbers if h not in have]:
        try:
            evs, log = resolve_hanke(he)
        except Exception as exc:
            per_query.append({"source": "Hankeikkuna HE-haku", "tunnus": he, "error": str(exc)})
            continue
        for e in evs:
            if e.event_id not in seen_ids:
                raw.append(e.to_dict()); seen_ids.add(e.event_id)
        per_query.append(log)

    # KORJATTU 2026-09-29: aiemmin he_numbers[:40] — 2026-09-kaappauksessa
    # HE-numeroita oli 81, joten puolet jäi hakematta ilman merkintää.
    for he in he_numbers:
        try:
            evs = fetch_eduskunta(he)
        except Exception as exc:
            per_query.append({"source": "Eduskunta", "tunnus": he, "error": str(exc)})
            continue
        raw.extend(e.to_dict() for e in evs)
        per_query.append({"source": "Eduskunta", "tunnus": he, **summarize(evs)})

    # Äänestykset: jokainen HE jonka Hankeikkuna tai Finlex tuntee.
    # 'ei tietuetta' kirjataan omana tilanaan — se ei ole 'ei äänestetty'.
    for he in he_numbers:
        try:
            evs, log = fetch_votes(he)
        except Exception as exc:
            per_query.append({"source": "Eduskunta äänestys", "tunnus": he, "error": str(exc)})
            if "429" in str(exc):
                break            # käyttöehdot: volyymiraja, lopetetaan
            continue
        raw.extend(e.to_dict() for e in evs)
        per_query.append(log)

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
            "note": "Tämä tiedosto on TODISTE, ei tulos. Luokitus tehdään "
                    "erillisinä tietueina (classification.py), tätä tiedostoa "
                    "ei muokata.",
        },
        "totals": {
            "events": len(raw),
            "anomalies": len(anomalies),
            "sources": sorted({d["source"] for d in raw}),
        },
        "queries": per_query,
        "chains": chains(raw),
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

    # Tiivistelmät käyttöliittymälle. Kuivaharjoituksessa lasketaan
    # muistissa (savutesti), varsinaisessa ajossa kirjoitetaan kaikki
    # kuukaudet ja index.json uudelleen — deterministinen, joten vanhat
    # tiivistelmät eivät muutu ellei lähde muutu.
    from summary import summarize_snapshot, write_all
    if path:
        for w in write_all():
            print(f"  tiivistelmä  {w.name}  {w.stat().st_size:,} B")
    else:
        s = summarize_snapshot(d)
        print(f"  tiivistelmä (ei kirjoitettu)  {len(json.dumps(s, ensure_ascii=False)):,} B, "
              f"ketjut {s['chains_outcome']}")
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
