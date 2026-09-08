"""OGAS3 — Decision Trace: validointi ja muunnos tapahtumiksi.

Decision Trace on yhden päätösketjun lukittu tilannekuva. Se syntyi
7.9.2026 kun TEM040, Harjulinja ja Länsirata kirjattiin — ja ne olivat
JSON-tiedostoja jotka noudattivat kaavaa MUTTA EIVÄT KULKENEET MOOTTORIN
LÄPI. Tämä moduuli sulkee sen kuilun.

KESKEINEN RAKENNE: observed vs. expected
----------------------------------------
    observed   tapahtunut. Kolme aikaleimaa, lähde, evidence.
               Muunnettavissa Eventiksi.
    expected   EI OLE TAPAHTUMA. Odotettu vaihe ilman aikaleimoja.
               EI MUUNNETA. Ei koskaan.

Ero ei ole kosmeettinen. `expected`-solmuilla on usein `estimate`-kenttä
("vko 44/2026", "2030–2032"), ja se on houkutteleva lukea aikaleimana.
Jos niin tehdään, sarja täyttyy tapahtumista joita ei ole tapahtunut —
ja PRE/FULL-erottelu menettää merkityksensä, koska tulevaisuus on
kirjattu havainnoksi.

Tämä moduuli KIELTÄYTYY muuntamasta expected-solmuja. Se on sama lukko
kuin compute_rri():n NotImplementedError aikanaan: rakenne näkyy, arvoa
ei keksitä.

MITÄ MUUNNOS EI TEE
-------------------
Se ei luokittele. Trace-solmulla ei ole D/O/S/L/IR-tyyppiä eikä
ROE:n asteikkoarvoja — ne ovat Extractorin työtä. Muunnos tuottaa
RawEvent-tasoisen rakenteen, ei validia Eventiä.

Poikkeus: solmu jolla on eksplisiittinen `event_type` muunnetaan sillä.
Sitä ei pääapäätellä `node_id`:stä tai kuvauksesta.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from schema import EVENT_TYPES, SchemaError, parse_ts

TRACE_SCHEMA = "aci/decision-trace/v0.1"

# ── REVISIO JA SISÄLTÖTIIVISTE (lisätty 2026-09-08) ──────────────────
#
# VIKA JOKA TÄMÄN AIHEUTTI: lansirata-trace lähetettiin NELJÄSTI, ja
# jokaisessa luki `_locked_at: 2026-09-07`. Tiedosto kasvoi 4 372 ->
# 14 961 tavuun, mutta lukituspäivä pysyi samana. Vanhempi versio olisi
# hiljaisesti korvannut uudemman, jos vastaanottaja ei olisi diffannut
# SISÄLTÖÄ — polun tarkistus ei olisi riittänyt.
#
# `_locked_at` kertoo MIHIN HETKEEN HAVAINNOT ON RAJATTU. Se ei kerro
# MIKÄ VERSIO tiedostosta on käsillä. Ne ovat eri asioita, ja niiden
# sekoittaminen teki "lukitusta" merkityksettömän.
#
# Sama kaava kuin OGAS2 v2.3:n versiolohkossa: revisio kertoo mitä
# pitäisi olla, tiiviste mitä on. Jos revisio unohtuu, tiiviste muuttuu
# silti.
#
# Tiiviste lasketaan KAIKESTA PAITSI _content_hash-kentästä itsestään,
# avainjärjestys normalisoituna. Ei kryptografinen: tarkoitus on havaita
# ero, ei estää väärennöstä.
import hashlib


def content_hash(d: dict) -> str:
    """FNV-tyylinen sisältötiiviste, 12 merkkiä. Vakaa avainjärjestykselle."""
    clean = {k: v for k, v in d.items() if k != "_content_hash"}
    blob = json.dumps(clean, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]

# Toimialueet. Lisätty koska ROE:n D/O/S on määritelty ENERGIAJÄRJESTELMÄN
# kautta (kuorma megawatteina, omistus energiayhtiössä, säätökyvyn
# poistuma) eivätkä ne yleisty sellaisenaan.
#
# Vaihtoehto olisi ollut abstrahoida D:tä muotoon "uusi vaade rajalliseen
# jaettuun resurssiin", joka kattaisi sekä datakeskuksen että Länsiradan.
# Se HYLÄTTIIN: se on sama virhe kuin YSO-hierarkiassa, jossa nouseminen
# teki käsitteistä abstraktimpia eikä käyttökelpoisempia ja yleisin
# asiasana päätyi sanaan "ominaisuudet".
#
# Jokainen toimialue määrittelee D/O/S ERIKSEEN tai jättää ne tyhjäksi.
# Ei koskaan peri energiamääritelmää.
DOMAINS = ("energia", "fiskaali", "liikenne", "ymparisto")

# Päätöselin. ROE:n uptake-asteikko on määritelty EDUSKUNNAN päätösten
# kautta ("laki tai päätös on kannan mukainen"). Kirkkonummen valtuusto
# hylkäsi Länsiradan osakassopimuksen 8.12.2025 — se on mitattu äänestys
# ja aito hylkäys, mutta se EI OLE ASTEIKOLLA.
#
# Kenttä erottaa ne. Uptake on mitattavissa kunnallisesta päätöksestä,
# mutta sitä EI lasketa yhteen eduskunnan uptaken kanssa.
DECISION_BODIES = ("eduskunta", "valtioneuvosto", "kunnanvaltuusto",
                   "viranomainen", "EU", "yhtiokokous")


class TraceError(ValueError):
    pass


@dataclass(frozen=True)
class TraceNode:
    node_id: str
    kind: str                      # "observed" | "expected"
    raw: dict[str, Any]

    @property
    def is_observed(self) -> bool:
        return self.kind == "observed"


@dataclass
class Trace:
    schema: str
    locked_at: str
    revision: int
    content_hash_stored: str | None
    content_hash_actual: str
    subject: dict[str, Any]
    domain: str | None
    observed: list[TraceNode] = field(default_factory=list)
    expected: list[dict[str, Any]] = field(default_factory=list)
    caveats: dict[str, str] = field(default_factory=dict)

    @property
    def hash_matches(self) -> bool | None:
        """None jos tiivistettä ei ole tallennettu — se on eri asia kuin
        ristiriita. Vanhat tracet on kirjoitettu ennen tätä kenttää."""
        if self.content_hash_stored is None:
            return None
        return self.content_hash_stored == self.content_hash_actual

    @property
    def n_observed(self) -> int:
        return len(self.observed)

    @property
    def n_expected(self) -> int:
        return len(self.expected)


def load_trace(path: str | Path) -> Trace:
    """Lukee ja validoi trace-tiedoston. Ei muunna."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))

    schema = d.get("_schema")
    if schema != TRACE_SCHEMA:
        raise TraceError(f"tuntematon skeema {schema!r}, odotettu {TRACE_SCHEMA!r}")

    if not d.get("_locked_at"):
        raise TraceError("_locked_at puuttuu. Trace on LUKITTU tilannekuva; "
                         "ilman lukituspäivää se on nykytilan kuvaus eikä sarjan "
                         "jäsen.")

    rev = d.get("_revision", 1)
    if not isinstance(rev, int) or rev < 1:
        raise TraceError(f"_revision on {rev!r}, odotettu positiivinen kokonaisluku. "
                         "Sama _locked_at eri sisällöllä vaatii uuden revision — "
                         "muuten vanhempi tiedosto korvaa uudemman hiljaa.")
    stored = d.get("_content_hash")
    actual = content_hash(d)
    if stored is not None and stored != actual:
        raise TraceError(
            f"_content_hash ei täsmää: tallennettu {stored}, laskettu {actual}. "
            "Tiedostoa on muutettu tiivisteen laskemisen jälkeen. Laske tiiviste "
            "uudelleen JA nosta _revision — älä vain päivitä tiivistettä.")

    domain = d.get("domain")
    if domain is not None and domain not in DOMAINS:
        raise TraceError(f"tuntematon domain {domain!r}, sallitut {DOMAINS}")

    obs: list[TraceNode] = []
    for i, n in enumerate(d.get("observed") or []):
        nid = n.get("node_id")
        if not nid:
            raise TraceError(f"observed[{i}]: node_id puuttuu")
        if n.get("kind") != "observed":
            raise TraceError(f"observed[{i}] ({nid}): kind on {n.get('kind')!r}, "
                             "odotettu 'observed'")
        if not n.get("occurred_at"):
            raise TraceError(f"observed[{i}] ({nid}): occurred_at puuttuu. "
                             "Havaittu solmu ilman tapahtumahetkeä ei ole havainto.")
        if not n.get("evidence"):
            raise TraceError(f"observed[{i}] ({nid}): evidence puuttuu")
        # known_at SAA olla None — se tarkoittaa "julkiseksitulohetkeä ei
        # tiedetä", ja se on eri asia kuin nolla viivettä. Harjulinjan
        # YVA-ohjelmassa sitä ei ole dokumentissa.
        obs.append(TraceNode(nid, "observed", n))

    exp = list(d.get("expected") or [])
    for i, e in enumerate(exp):
        if "occurred_at" in e:
            raise TraceError(
                f"expected[{i}] ({e.get('step')!r}): sisältää occurred_at-kentän. "
                "Odotettu vaihe EI OLE TAPAHTUMA eikä sillä saa olla "
                "tapahtumahetkeä. Jos se on tapahtunut, siirrä se "
                "observed-listalle.")

    caveats = {k: v for k, v in d.items()
               if k.startswith("_") and isinstance(v, str)}

    return Trace(schema=schema, locked_at=d["_locked_at"],
                 revision=rev, content_hash_stored=stored, content_hash_actual=actual,
                 subject=d.get("subject") or {}, domain=domain,
                 observed=obs, expected=exp, caveats=caveats)


def to_raw_events(t: Trace) -> tuple[list[dict], list[dict]]:
    """Muuntaa observed-solmut RawEvent-muotoon.

    Palauttaa (events, skipped). `skipped` kertoo mitä ei voitu muuntaa
    ja miksi — sitä EI pudoteta hiljaa.

    expected-solmuja ei muunneta lainkaan eikä niitä listata skipped-
    listalle: ne eivät ole ehdokkaita.
    """
    events: list[dict] = []
    skipped: list[dict] = []

    for n in t.observed:
        r = n.raw
        try:
            occ = parse_ts(r["occurred_at"], f"{n.node_id}.occurred_at")
        except SchemaError as e:
            skipped.append({"node_id": n.node_id, "reason": str(e)})
            continue

        known = None
        if r.get("known_at"):
            try:
                known = parse_ts(r["known_at"], f"{n.node_id}.known_at")
            except SchemaError as e:
                skipped.append({"node_id": n.node_id, "reason": str(e)})
                continue

        if known is not None and known < occ:
            skipped.append({
                "node_id": n.node_id,
                "reason": f"known_at ({known.date()}) ennen occurred_at "
                          f"({occ.date()}) — kausaalijärjestys rikki. "
                          "EI korjata automaattisesti."})
            continue

        et = r.get("event_type")
        if et is not None and et not in EVENT_TYPES:
            skipped.append({"node_id": n.node_id,
                            "reason": f"event_type {et!r} ei ole {EVENT_TYPES}"})
            continue

        events.append({
            "event_id": f"TRACE:{t.subject.get('tunnus') or t.subject.get('nimi','?')}"
                        f":{n.node_id}",
            "occurred_at": occ.isoformat(),
            "known_at": known.isoformat() if known else None,
            "retrieved_at": r.get("retrieved_at"),
            "source": r.get("source"),
            "source_url": (r["evidence"][0] or {}).get("source_url"),
            # type EI PÄÄTELLÄ. Vain eksplisiittinen event_type kelpaa.
            "type": et,
            "subtype": r.get("doc_type"),
            "parameters": {
                "domain": t.domain,
                "decision_body": r.get("decision_body"),
                "occurred_at_source": r.get("occurred_at_source"),
                "occurred_at_precision": r.get("occurred_at_precision"),
                "source_class": r.get("source_class"),
                "trace_locked_at": t.locked_at,
            },
            "llm_classification": {"intensity": None, "targeting": None,
                                   "policy_proximity": None, "uptake": None},
            "irreversibility": None,
            "impact_weight": None,
            "evidence": r["evidence"],
            "_known_at_missing": known is None,
        })

    return events, skipped


def summarize(t: Trace) -> dict:
    events, skipped = to_raw_events(t)
    typed = [e for e in events if e["type"] is not None]
    no_known = [e for e in events if e["_known_at_missing"]]
    return {
        "subject": t.subject.get("nimi") or t.subject.get("tunnus"),
        "domain": t.domain,
        "locked_at": t.locked_at,
        "revision": t.revision,
        "content_hash": t.content_hash_actual,
        "hash_matches": t.hash_matches,
        "_hash_note": "None = tiivistettä ei tallennettu tiedostoon. Se on eri "
                      "asia kuin ristiriita; vanhat tracet on kirjoitettu ennen "
                      "tätä kenttää.",
        "observed": t.n_observed,
        "expected": t.n_expected,
        "_expected_note": "EI muunneta tapahtumiksi. Ei koskaan.",
        "converted": len(events),
        "skipped": len(skipped),
        "skipped_detail": skipped,
        "typed": len(typed),
        "untyped": len(events) - len(typed),
        "_untyped_note": "type on None: luokitus on Extractorin työ eikä sitä "
                         "päätellä node_id:stä tai kuvauksesta.",
        "known_at_missing": len(no_known),
        "_known_at_note": "known_at None tarkoittaa 'julkiseksitulohetkeä ei "
                          "tiedetä'. Se on eri asia kuin nolla viivettä.",
        "caveats": list(t.caveats.keys()),
    }
