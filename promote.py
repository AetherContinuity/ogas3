"""OGAS3 — ketjun nosto seurantaan.

Nosto tehdään GitHub-issuella (lomake .github/ISSUE_TEMPLATE/nosto.yml).
Workflow promote.yml kutsuu tätä vain, jos issuen tekijä on repon
omistaja, organisaation jäsen tai avustaja. Muiden nostoja ei käsitellä
automaattisesti — rajaus koskee proxyjen ja ylävirran kuormaa, ja sitä
että seurantalista on analyytikoiden valinta eikä julkinen huomio.

MITÄ NOSTO KIRJAA
-----------------
Yksi muuttumaton tiedosto per nosto: seuranta/<aika>-<avain>-<käyttäjä>.json

    promoted_at          issuen luontihetki (GitHubin kirjaama, ei ajajan kello)
    promoted_by          GitHub-käyttäjä
    he, tunnus           ketju; tunnus haetaan HE:stä jos puuttuu
    peruste              nostajan oma teksti, sellaisenaan
    state_at_promotion   ketjun lopputulos uusimmassa tiivistelmässä
                         nostohetkellä — tästä erotetaan ennen ratkaisua
                         tehdyt nostot jälkikäteen tehdyistä
    issue                issuen numero ja osoite

Tiedostoa ei koskaan muuteta. Saman ketjun toinen nosto on uusi tiedosto;
trace on aihekohtainen ja yhteinen, sitä ei tehdä toista kertaa.

MIKSI YKSI TIEDOSTO PER NOSTO
-----------------------------
Yhteinen seuranta.json tuottaisi push-konflikteja kun kaksi nostoa
käsitellään peräkkäin, ja sen muokkaushistoria olisi diffeissä eikä
tiedostoissa. Append-only-hakemistossa kumpaakaan ongelmaa ei ole.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEURANTA = ROOT / "seuranta"
TRACES = ROOT / "traces"
SNAPSHOTS = ROOT / "snapshots"
TUNNUS_RE = re.compile(r"^[A-ZÄÖ]{2,4}\d{3}:\d{2}/\d{4}$")
ALLOWED = ("OWNER", "MEMBER", "COLLABORATOR", "APPROVED")
# APPROVED: muun kuin avustajan nosto, jolle avustaja on lisännyt labelin
# "hyväksytty". Labelin voi lisätä vain kirjoitusoikeudellinen käyttäjä.


class PromoteError(ValueError):
    pass


# ── Issue-lomakkeen jäsennys ─────────────────────────────────────────
def parse_issue_body(body: str) -> dict:
    """GitHubin issue-lomake tuottaa '### Otsikko\\n\\narvo' -lohkot.
    '_No response_' tarkoittaa tyhjää kenttää."""
    fields: dict[str, str] = {}
    for m in re.finditer(r"^###\s+(.+?)\s*\n+(.*?)(?=^###\s|\Z)", body or "", re.S | re.M):
        v = m.group(2).strip()
        fields[m.group(1).strip().lower()] = "" if v == "_No response_" else v
    def pick(*names):
        for n in names:
            for k, v in fields.items():
                if k.startswith(n):
                    return v
        return ""
    return {"he": pick("he"), "tunnus": pick("hankkeen tunnus", "tunnus"),
            "peruste": pick("peruste")}


# ── Tila nostohetkellä ───────────────────────────────────────────────
def latest_summary() -> dict | None:
    files = sorted(SNAPSHOTS.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].summary.json"))
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else None


def state_at_promotion(he: str | None, tunnus: str | None, summary: dict | None) -> dict:
    if not summary:
        return {"outcome": None, "summary": None, "note": "ei tiivistelmää"}
    row = None
    for r in summary.get("chains") or []:
        if (he and r["he"] == he) or (tunnus and tunnus in (r.get("hankkeet") or [])):
            row = r
            break
    return {
        "summary": summary.get("month"),
        "summary_sha256": summary.get("source_sha256"),
        "outcome": row["outcome"] if row else None,
        "eduskunta_vastaus": row.get("eduskunta_vastaus") if row else None,
        "saadokset": row.get("saadokset") if row else None,
        "note": None if row else "ketju ei ollut uusimmassa kaappauksessa — tila tuntematon, ei 'ei ratkaistu'",
    }


# ── Nosto ────────────────────────────────────────────────────────────
def _key(he: str | None, tunnus: str | None) -> str:
    base = tunnus or he or "tuntematon"
    return re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-")


def trace_exists(tunnus: str) -> Path | None:
    stem = tunnus.replace(":", "").replace("/", "-")
    found = sorted(TRACES.glob(f"{stem}-trace-*.json"))
    return found[-1] if found else None


def promote(*, he_in: str, tunnus_in: str, peruste: str, login: str,
            association: str, created_at: str, issue_number: int | None,
            issue_url: str | None, approved_by: str | None = None,
            resolve=None, snapshot=None) -> dict:
    from decision_chain import he_key, resolve_hanke
    resolve = resolve or resolve_hanke
    if snapshot is None:
        from snapshot_trace import make_snapshot as snapshot

    if association not in ALLOWED:
        raise PromoteError(f"{login} ({association}) ei ole avustaja — nostoa ei käsitellä automaattisesti")
    he = he_key(he_in) if he_in else None
    if he_in and not he:
        raise PromoteError(f"HE-numero ei jäsenny: {he_in!r} (muoto 'HE 24/2026')")
    tunnus = tunnus_in.strip() or None
    if tunnus and not TUNNUS_RE.match(tunnus):
        raise PromoteError(f"hankkeen tunnus ei jäsenny: {tunnus!r} (muoto 'TEM032:00/2023')")
    if not he and not tunnus:
        raise PromoteError("anna HE-numero tai hankkeen tunnus")
    if not peruste.strip():
        raise PromoteError("peruste puuttuu — nosto ilman perustetta ei ole analysoitavissa")

    resolved_by = "annettu"
    if not tunnus:
        hits, _log = resolve(he)
        if len(hits) != 1:
            raise PromoteError(f"{he}: Hankeikkunasta löytyi {len(hits)} hanketta, "
                               "anna tunnus käsin")
        tunnus = hits[0].parameters["tunnus"]
        resolved_by = "HE-haku (teksti + tarkka heNumerot)"

    ts = datetime.fromisoformat(created_at.replace("Z", "+00:00")).astimezone(timezone.utc)
    record = {
        "_schema": "aci/ogas3-promotion/v0.1",
        "_note": "Muuttumaton. Uusi nosto = uusi tiedosto.",
        "promoted_at": ts.replace(microsecond=0).isoformat(),
        "promoted_by": login,
        "association": association,
        "approved_by": approved_by,
        "he": he,
        "tunnus": tunnus,
        "tunnus_source": resolved_by,
        "peruste": peruste.strip(),
        "state_at_promotion": state_at_promotion(he, tunnus, latest_summary()),
        "issue": {"number": issue_number, "url": issue_url},
    }
    SEURANTA.mkdir(exist_ok=True)
    name = f"{ts.strftime('%Y-%m-%dT%H%M%S')}-{_key(he, tunnus)}-{re.sub(r'[^A-Za-z0-9-]', '', login)}.json"
    path = SEURANTA / name
    if path.exists():
        raise PromoteError(f"{name} on jo olemassa — nostoa ei kirjoiteta yli")
    path.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")

    prev = trace_exists(tunnus)
    trace_path, trace_note = None, None
    if prev is None:
        trace_path, _ = snapshot(tunnus, TRACES, subject_extra={"he": he} if he else None)
        trace_note = "ensimmäinen trace tehty"
    else:
        trace_path, trace_note = prev, "trace oli jo olemassa — päivittyy kuukausiajossa"
    return {"record": path, "trace": trace_path, "trace_note": trace_note, "tunnus": tunnus, "he": he}


def refresh(today: str | None = None, snapshot=None) -> list[dict]:
    """Kuukausiajo: uusi trace-revisio jokaiselle seurannassa olevalle
    tunnukselle. Samana päivänä jo tehtyä ei tehdä uudelleen (tiedostonimi
    on päiväkohtainen, eikä lukittua tracea kirjoiteta yli)."""
    if snapshot is None:
        from snapshot_trace import make_snapshot as snapshot
    today = today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tunnukset = sorted({json.loads(p.read_text(encoding="utf-8"))["tunnus"]
                        for p in SEURANTA.glob("*.json")} if SEURANTA.exists() else set())
    out = []
    for t in tunnukset:
        prev = trace_exists(t)
        if prev and prev.name.endswith(f"-trace-{today}.json"):
            out.append({"tunnus": t, "status": "tänään jo tehty"})
            continue
        try:
            p, _ = snapshot(t, TRACES, today=today, prev_path=prev)
            out.append({"tunnus": t, "status": "päivitetty", "file": p.name})
        except Exception as exc:                     # yksi epäonnistunut ei kaada muita
            out.append({"tunnus": t, "status": "virhe", "error": str(exc)[:200]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("issue", help="käsittele nostoissue (event.json GitHub Actionsista)")
    a.add_argument("event_json")
    sub.add_parser("refresh", help="päivitä kaikkien seurattujen tracet")
    args = ap.parse_args()

    if args.cmd == "refresh":
        res = refresh()
        for r in res:
            print(f"{r['tunnus']:20s} {r['status']} {r.get('file') or r.get('error') or ''}")
        return 1 if any(r["status"] == "virhe" for r in res) else 0

    ev = json.loads(Path(args.event_json).read_text(encoding="utf-8"))
    iss = ev["issue"]
    f = parse_issue_body(iss.get("body") or "")
    association, approved_by = iss.get("author_association", "NONE"), None
    if ev.get("action") == "labeled" and (ev.get("label") or {}).get("name") == "hyväksytty":
        association, approved_by = "APPROVED", ev["sender"]["login"]
    msg_path = Path("promote-result.md")
    try:
        r = promote(he_in=f["he"], tunnus_in=f["tunnus"], peruste=f["peruste"],
                    login=iss["user"]["login"], association=association, approved_by=approved_by,
                    created_at=iss["created_at"], issue_number=iss["number"], issue_url=iss["html_url"])
    except Exception as exc:
        msg_path.write_text(f"**Nostoa ei tehty.** {exc}\n", encoding="utf-8")
        print(exc, file=sys.stderr)
        return 2
    msg_path.write_text(
        f"**Nostettu seurantaan:** {r['he'] or ''} `{r['tunnus']}`\n\n"
        f"- nostokirjaus: `{r['record'].relative_to(ROOT)}`\n"
        f"- trace: `{Path(r['trace']).relative_to(ROOT)}` — {r['trace_note']}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
