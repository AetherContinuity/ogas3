"""OGAS3 — tiivistelmät käyttöliittymälle.

MIKSI ERILLINEN TIEDOSTO
------------------------
Kuukausisnapshot on todiste: kaikki tapahtumat, kolme aikaleimaa,
evidence. Se on noin 9 Mt — liikaa selaimelle ja puhelimelle. Käyttö-
liittymä lukee siksi tiivistelmän, joka lasketaan TÄSSÄ, Pythonissa,
samasta tiedostosta.

KÄYTTÖLIITTYMÄ EI LASKE MITÄÄN. OGAS2:n opetus: kaksi laskentaa samalla
nimellä (Python ja JavaScript) ajautuvat erilleen, ja ero huomataan vasta
kun luvut eivät täsmää. Kaikki mitä sivulla näkyy on laskettu täällä.

Tiivistelmä on johdannainen. Se ei muuta snapshotia, ja sen voi aina
laskea uudelleen: `python3 summary.py` kirjoittaa kaikki uudelleen.
Tiivistelmä sitoo itsensä lähteeseensä sha256-tiivisteellä, jotta
sivulta voi todeta mistä tiedostosta luvut ovat.

TUOTOKSET
---------
snapshots/YYYY-MM.summary.json    yhden kuukauden tiivistelmä
snapshots/index.json              kuukaudet + tracet (seurantalista)
"""

from __future__ import annotations

import glob
import hashlib
import json
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from decision_chain import chains as build_chains
from decision_chain import he_key

ROOT = Path(__file__).resolve().parent
SNAPSHOT_DIR = ROOT / "snapshots"
TRACE_DIR = ROOT / "traces"
SUMMARY_SCHEMA = "aci/ogas3-summary/v0.1"
# Järjestys vahvimmasta havainnosta heikoimpaan. Sama lista kulkee
# tiivistelmässä (outcome_order), jotta käyttöliittymä ei kovakoodaa tiloja.
OUTCOME_ORDER = ["säädös vahvistettu", "eduskunta päättänyt", "äänestetty",
                 "eduskunnassa", "määrittämätön"]
INDEX_SCHEMA = "aci/ogas3-index/v0.1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _lag_days(e: dict) -> float | None:
    try:
        a = datetime.fromisoformat(e["occurred_at"])
        b = datetime.fromisoformat(e["known_at"])
    except (TypeError, ValueError, KeyError):
        return None
    return (b - a).total_seconds() / 86400.0


def _chain_titles(events: list[dict]) -> dict[str, str]:
    """HE -> nimeke. Järjestys: Finlex-säädös, Hankeikkuna, Eduskunta.

    Nimeke on tunnistamista varten, ei tulkintaa: se luetaan sellaisenaan
    lähteen evidence-lainauksesta.
    """
    prio = {"Finlex": 0, "Hankeikkuna": 1, "Eduskunta": 2}
    best: dict[str, tuple[int, str]] = {}
    for e in events:
        src = e.get("source")
        if src not in prio:
            continue
        p = e.get("parameters") or {}
        if src == "Eduskunta":
            hes = [p.get("eduskuntatunnus", "")]
            q = (e.get("evidence") or [{}])[0].get("quote", "")
            title = q.split(" — ", 1)[1] if " — " in q else q
        elif src == "Finlex":
            hes = p.get("heNumerot") or []
            title = p.get("nimeke") or ""
        else:
            hes = p.get("heNumerot") or []
            title = (e.get("evidence") or [{}])[0].get("quote", "")
        for h in hes:
            k = he_key(h or "")
            if k and title and (k not in best or prio[src] < best[k][0]):
                best[k] = (prio[src], title.strip()[:200])
    return {k: v[1] for k, v in best.items()}


def summarize_snapshot(snap: dict, source_file: str | None = None,
                       source_sha256: str | None = None) -> dict:
    events: list[dict] = snap.get("events") or []
    by_source = Counter(e.get("source") for e in events)
    typed = sum(1 for e in events if e.get("type") is not None)

    lag: dict[str, dict] = {}
    for src in sorted(by_source):
        xs = sorted(x for e in events if e.get("source") == src
                    and not e.get("_anomaly") and (x := _lag_days(e)) is not None)
        lag[src] = ({"n": len(xs), "median": round(statistics.median(xs), 1),
                     "max": round(xs[-1], 1)} if xs else {"n": 0})

    # Ketjut: snapshotissa jos kaappaus on uudempi, muuten johdetaan
    # samalla funktiolla. Kumpikin on sama laskenta, ei kaksi eri.
    ch = snap.get("chains")
    derived = ch is None
    if ch is None:
        ch = build_chains(events)
    titles = _chain_titles(events)
    chain_rows = [{
        "he": he,
        "nimeke": titles.get(he),
        "hankkeet": c["hankkeet"],
        "eduskunta_vaiheet": c["eduskunta_vaiheet"],
        "eduskunta_vastaus": c.get("eduskunta_vastaus"),
        "aanestykset": len(c["aanestykset"]),
        "saadokset": c["saadokset"],
        "outcome": c["outcome"],
    } for he, c in ch.items()]
    order = {o: i for i, o in enumerate(OUTCOME_ORDER)}
    chain_rows.sort(key=lambda r: (order.get(r["outcome"], 9), r["he"]))

    queries = snap.get("queries") or []
    errors = [{"source": q.get("source"),
               "kohde": q.get("valmisteluvaihe") or q.get("tunnus") or q.get("window"),
               "error": str(q["error"])[:300]} for q in queries if "error" in q]
    vote_status = Counter(
        ("ei tietuetta" if q.get("status") == "ei tietuetta" else "äänestyksiä")
        for q in queries if q.get("source") == "Eduskunta äänestys" and "error" not in q)

    return {
        "_schema": SUMMARY_SCHEMA,
        "_note": "Johdannainen. Laskettu summary.py:llä snapshotista; käyttöliittymä "
                 "ei laske mitään itse.",
        "month": snap.get("month"),
        "source_file": source_file,
        "source_sha256": source_sha256,
        "captured_at": snap.get("captured_at"),
        "captured_by": snap.get("captured_by"),
        "run_url": snap.get("run_url"),
        "git_sha": snap.get("git_sha"),
        "status": snap.get("status"),
        "totals": {
            "events": len(events),
            "anomalies": sum(1 for e in events if e.get("_anomaly")),
            "by_source": dict(sorted(by_source.items())),
            "typed": typed,
            "untyped": len(events) - typed,
        },
        "hankeikkuna_vaiheet": dict(sorted(Counter(
            e.get("subtype") for e in events if e.get("source") == "Hankeikkuna").items(),
            key=lambda kv: str(kv[0]))),
        "finlex_lajit": dict(sorted(Counter(
            e.get("subtype") for e in events if e.get("source") == "Finlex").items(),
            key=lambda kv: str(kv[0]))),
        "visibility_lag_days": lag,
        "_lag_note": "known_at − occurred_at, anomaliat pois. Eduskunta ja äänestykset "
                     "ovat 0 rakenteellisesti: istunto on julkinen tapahtuma.",
        "votes_lookup": dict(vote_status),
        "_votes_note": "'ei tietuetta' ei tarkoita 'ei äänestetty' — hyväksyminen ilman "
                       "äänestystä ja keskeneräinen käsittely näyttävät samalta.",
        "outcome_order": OUTCOME_ORDER,
        "chains_outcome": dict(Counter(r["outcome"] for r in chain_rows)),
        "chains_derived_here": derived,
        "chains": chain_rows,
        "anomalies": [{"event_id": e["event_id"], "source": e.get("source"),
                       "note": str(e["_anomaly"])[:300]}
                      for e in events if e.get("_anomaly")],
        "errors": errors,
        "finlex_window": next((q for q in queries if q.get("source") == "Finlex"), None),
        "rri": None,
        "_rri_note": "Ei laskettu: tapahtumia ei ole luokiteltu. Tyhjä kenttä on "
                     "rehellisempi kuin nolla.",
    }


def write_summary(snapshot_path: Path) -> Path:
    snap = json.loads(snapshot_path.read_text(encoding="utf-8"))
    s = summarize_snapshot(snap, source_file=snapshot_path.name,
                           source_sha256=_sha256(snapshot_path))
    out = snapshot_path.with_name(snapshot_path.stem + ".summary.json")
    out.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def build_index() -> dict:
    from traces import load_trace, summarize as trace_summary

    months = []
    for p in sorted(SNAPSHOT_DIR.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].json")):
        sp = p.with_name(p.stem + ".summary.json")
        s = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else None
        months.append({
            "month": p.stem,
            "snapshot": p.name,
            "summary": sp.name if sp.exists() else None,
            "events": s["totals"]["events"] if s else None,
            "anomalies": s["totals"]["anomalies"] if s else None,
            "sources": sorted(s["totals"]["by_source"]) if s else None,
            "chains_outcome": s["chains_outcome"] if s else None,
            "summary_matches_snapshot": (s["source_sha256"] == _sha256(p)) if s else None,
        })

    traces = []
    for f in sorted(glob.glob(str(TRACE_DIR / "*.json"))):
        try:
            t = load_trace(f)
            ts = trace_summary(t)
            raw = json.loads(Path(f).read_text(encoding="utf-8"))
            traces.append({
                "file": Path(f).name,
                "tunnus": t.subject.get("tunnus"),
                "subject": ts["subject"],
                "domain": ts["domain"],
                "locked_at": ts["locked_at"],
                "revision": ts["revision"],
                "content_hash": ts["content_hash"],
                "hash_matches": ts["hash_matches"],
                "observed": ts["observed"],
                "expected": ts["expected"],
                "known_at_missing": ts["known_at_missing"],
                "state": raw.get("_state"),
                "supersedes": (raw.get("_supersedes") or {}).get("file"),
            })
        except Exception as exc:                     # rikkinäinen trace näkyy, ei katoa
            traces.append({"file": Path(f).name, "error": str(exc)[:300]})

    # Seurantalista: uusin trace kutakin aihetta kohden. Ketju päätellään
    # _supersedes-kentästä, ei tiedostonimestä.
    superseded = {t.get("supersedes") for t in traces if t.get("supersedes")}
    for t in traces:
        t["latest"] = t["file"] not in superseded and "error" not in t

    # Nostot. ennen_ratkaisua lasketaan TÄSSÄ nostohetken tilasta:
    # True = eduskunta ei ollut vielä päättänyt, False = oli, None = tila
    # tuntematon (ketju ei ollut kaappauksessa). Käyttöliittymä ei päättele.
    decided = {"säädös vahvistettu", "eduskunta päättänyt"}
    promotions = []
    for p in sorted((ROOT / "seuranta").glob("*.json")) if (ROOT / "seuranta").exists() else []:
        r = json.loads(p.read_text(encoding="utf-8"))
        oc = (r.get("state_at_promotion") or {}).get("outcome")
        promotions.append({
            "file": p.name, "promoted_at": r.get("promoted_at"), "promoted_by": r.get("promoted_by"),
            "approved_by": r.get("approved_by"), "he": r.get("he"), "tunnus": r.get("tunnus"),
            "peruste": (r.get("peruste") or "")[:500], "outcome_at_promotion": oc,
            "ennen_ratkaisua": None if oc is None else oc not in decided,
            "issue": (r.get("issue") or {}).get("url"),
        })

    return {
        "_schema": INDEX_SCHEMA,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "months": months,
        "traces": traces,
        "promotions": promotions,
    }


def write_all() -> list[Path]:
    written = []
    for p in sorted(SNAPSHOT_DIR.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].json")):
        written.append(write_summary(p))
    idx = SNAPSHOT_DIR / "index.json"
    idx.write_text(json.dumps(build_index(), ensure_ascii=False, indent=1), encoding="utf-8")
    written.append(idx)
    return written


if __name__ == "__main__":
    for p in write_all():
        print(f"{p.relative_to(ROOT)}  {p.stat().st_size:,} B")
