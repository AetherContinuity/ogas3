"""OGAS3 — luokituskerros jäädytettyjen tapahtumien päälle.

MIKSI ERILLINEN KERROS
----------------------
Snapshot jäädyttää TODISTEEN (tapahtumat, kolme aikaleimaa, evidence)
ja jättää luokituksen (type, impact_weight, irreversibility,
llm_classification) tyhjäksi. Luokitus lisättiin aiemmin suunnitelman
mukaan "myöhemmin näihin jäädytettyihin tapahtumiin" — eli muokkaamalla
todistetta. Se rikkoo kaksi asiaa:

  1. Metodologinen ehto: moottori ei muuta tapahtumien sisältöä.
  2. Turvalukko 2: luokittelija joka tietää miten hankkeelle kävi, vie
     sen tiedon painoihin. Aikaleimat pysyvät puhtaina, painot eivät.
     Kolmen aikaleiman rakenne näyttäisi valvovan look-aheadia, mutta
     vuoto tapahtuisi kentässä jota mikään aikaleima ei koske.

Siksi luokitus on oma tietueensa, joka viittaa tapahtumaan tunnisteella
JA sisältötiivisteellä, ja jolla on oma aikaleima ja oma provenienssi.

TIETOHORISONTTI
---------------
Luokituksen puhtaus ratkeaa yhdestä vertailusta:

    horisontti  <=  PRE-raja + max_lag

    PRE-raja    tapahtuman known_at-kuukauden loppu (sama raja jolla
                aggregaattori sijoittaa tapahtuman PRE-kuukauteen)
    horisontti  viimeisin hetki, jonka tietoa luokittelija on voinut
                käyttää:
                  rule   PRE-raja. Deterministinen sääntö lukee vain
                         jäädytettyä todistetta.
                  llm    mallin knowledge_cutoff. Malli joka on
                         koulutettu tapahtumakuukauden jälkeisellä
                         aineistolla tietää lopputuloksen, eikä sitä
                         voi sokeuttaa promptilla. Puuttuva
                         knowledge_cutoff -> UNVERIFIED, ei CLEAN.
                  human  classified_at. Ihmistä ei voi sokeuttaa.

max_lag on valinta, ei oletus — kuten baseline-skaalauksen rajat. Se
annetaan eksplisiittisesti kutsussa ja kirjataan raporttiin.

PRE JA FULL
-----------
Samalle tapahtumalle saa olla useita luokituksia ajan mittaan.

    PRE   varhaisin CLEAN-luokitus. Myöhempi uudelleenluokittelu ei
          saa korvata sitä, mitä silloin olisi voitu päätellä.
    FULL  viimeisin luokitus puhtaudesta riippumatta.

PRE/FULL-ero laajenee siis aikaleimoista painoihin, ja sekin ero on
mittaustulos.

Status johdetaan aina. Tiedostoon kirjattua "contaminated"-lippua ei
lueta: itse ilmoitettu puhtaus on väite, ei havainto.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Literal

from aggregator import Mode, month_end, month_key
from schema import Event, SchemaError, parse_ts
from validator import validate_event

CLASSIFICATION_SCHEMA = "aci/classification/v0.1"

# Kentät jotka luokitus tuo. Kaikki muu tapahtumassa on todistetta ja
# kuuluu tiivisteeseen.
CLASS_FIELDS = ("type", "impact_weight", "irreversibility", "llm_classification")

CLASSIFIER_KINDS = ("rule", "llm", "human")

Status = Literal["CLEAN", "CONTAMINATED", "UNVERIFIED"]


class ClassificationError(SchemaError):
    pass


# ── Tiiviste ─────────────────────────────────────────────────────────
def event_hash(raw_event: dict) -> str:
    """Tiiviste jäädytetyn tapahtuman TODISTEOSASTA.

    Luokituskentät jätetään pois, jotta tiiviste on sama riippumatta
    siitä onko joku kirjoittanut niihin jotain. Jos todiste muuttuu
    (aikaleima, evidence, parametrit), tiiviste muuttuu ja luokitus
    lakkaa kelpaamasta.
    """
    clean = {k: v for k, v in raw_event.items() if k not in CLASS_FIELDS}
    blob = json.dumps(clean, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


# ── Tietue ───────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Classifier:
    kind: str
    id: str
    version: str
    knowledge_cutoff: datetime | None     # vain llm; None = tuntematon
    prompt_hash: str | None               # pakollinen llm:lle


@dataclass(frozen=True)
class ClassificationRecord:
    event_id: str
    event_hash: str
    classified_at: datetime
    classifier: Classifier
    values: dict[str, Any]                # CLASS_FIELDS, validoidaan tapahtuman kanssa


def _classifier_from_dict(d: Any, where: str) -> Classifier:
    if not isinstance(d, dict):
        raise ClassificationError(f"{where}: oltava objekti")
    for k in ("kind", "id", "version"):
        if not isinstance(d.get(k), str) or not d[k].strip():
            raise ClassificationError(f"{where}.{k}: pakollinen, ei-tyhjä merkkijono")
    kind = d["kind"]
    if kind not in CLASSIFIER_KINDS:
        raise ClassificationError(f"{where}.kind: oltava yksi {CLASSIFIER_KINDS}, oli {kind!r}")

    if "knowledge_cutoff" not in d:
        raise ClassificationError(
            f"{where}.knowledge_cutoff: kenttä puuttuu. Käytä eksplisiittistä "
            "null-arvoa jos tuntematon — puuttuva ja tuntematon eivät ole sama asia.")
    kc_raw = d["knowledge_cutoff"]
    kc = None if kc_raw is None else parse_ts(kc_raw, f"{where}.knowledge_cutoff")
    if kind != "llm" and kc is not None:
        raise ClassificationError(
            f"{where}.knowledge_cutoff: vain llm-luokittelijalla. {kind}-luokittelijan "
            "horisontti johdetaan, sitä ei ilmoiteta.")

    ph = d.get("prompt_hash")
    if kind == "llm" and (not isinstance(ph, str) or not ph.strip()):
        raise ClassificationError(
            f"{where}.prompt_hash: pakollinen llm-luokittelijalle — ilman sitä "
            "luokitusta ei voi toistaa eikä eri ajoja verrata.")
    if ph is not None and not isinstance(ph, str):
        raise ClassificationError(f"{where}.prompt_hash: oltava merkkijono tai null")
    return Classifier(kind=kind, id=d["id"], version=d["version"],
                      knowledge_cutoff=kc, prompt_hash=ph)


def record_from_dict(d: Any, index: int | None = None) -> ClassificationRecord:
    where = f"records[{index}]" if index is not None else "record"
    if not isinstance(d, dict):
        raise ClassificationError(f"{where}: oltava objekti")
    for k in ("event_id", "event_hash", "classified_at", "classifier") + CLASS_FIELDS:
        if k not in d:
            raise ClassificationError(f"{where}.{k}: pakollinen kenttä puuttuu")
    for k in ("event_id", "event_hash"):
        if not isinstance(d[k], str) or not d[k].strip():
            raise ClassificationError(f"{where}.{k}: oltava ei-tyhjä merkkijono")
    if "contaminated" in d or "status" in d:
        raise ClassificationError(
            f"{where}: 'contaminated'/'status' ei ole sallittu kenttä — puhtaus "
            "johdetaan aikaleimoista, itse ilmoitettua ei lueta.")
    return ClassificationRecord(
        event_id=d["event_id"],
        event_hash=d["event_hash"],
        classified_at=parse_ts(d["classified_at"], f"{where}.classified_at"),
        classifier=_classifier_from_dict(d["classifier"], f"{where}.classifier"),
        values={k: copy.deepcopy(d[k]) for k in CLASS_FIELDS},
    )


def load_records(path: str | Path) -> list[ClassificationRecord]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("_schema") != CLASSIFICATION_SCHEMA:
        raise ClassificationError(f"{path}: _schema oltava {CLASSIFICATION_SCHEMA!r}")
    recs = data.get("records")
    if not isinstance(recs, list):
        raise ClassificationError(f"{path}: 'records' oltava lista")
    return [record_from_dict(r, i) for i, r in enumerate(recs)]


# ── Puhtaus ──────────────────────────────────────────────────────────
def pre_cutoff(ev: Event) -> datetime:
    """Sama raja jolla aggregaattori sijoittaa tapahtuman PRE-kuukauteen."""
    return month_end(month_key(ev.known_at))


def horizon(rec: ClassificationRecord, ev: Event) -> datetime | None:
    c = rec.classifier
    if c.kind == "rule":
        return pre_cutoff(ev)
    if c.kind == "llm":
        return c.knowledge_cutoff          # None -> UNVERIFIED
    return rec.classified_at               # human


def status(rec: ClassificationRecord, ev: Event, max_lag: timedelta) -> tuple[Status, str]:
    h = horizon(rec, ev)
    limit = pre_cutoff(ev) + max_lag
    if h is None:
        return "UNVERIFIED", (f"{rec.classifier.id}: knowledge_cutoff tuntematon — "
                              "ei voida todeta, tunteeko malli lopputuloksen")
    if h <= limit:
        return "CLEAN", f"horisontti {h.isoformat()} <= raja {limit.isoformat()}"
    return "CONTAMINATED", (f"horisontti {h.isoformat()} > raja {limit.isoformat()} "
                            f"({(h - limit).days} vrk yli)")


# ── Yhdistäminen ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class JoinReport:
    mode: str
    max_lag_days: float
    accepted: dict[str, str]                      # event_id -> status
    rejected: tuple[tuple[str, str, str], ...]    # (event_id, status, syy)
    unclassified: tuple[str, ...]                 # ei hyväksyttyä luokitusta
    anomalous: tuple[str, ...]                    # snapshotin _anomaly-tapahtumat

    @property
    def coverage(self) -> float:
        n = len(self.accepted) + len(self.unclassified)
        return 0.0 if n == 0 else len(self.accepted) / n


def apply_classifications(
    raw_events: Iterable[dict],
    records: Iterable[ClassificationRecord],
    mode: Mode,
    max_lag: timedelta,
) -> tuple[list[Event], JoinReport]:
    """Yhdistää jäädytetyt tapahtumat ja luokitukset validiksi Event-listaksi.

    Ei muokkaa raw_events-listaa. Tapahtuma ilman hyväksyttyä luokitusta
    jää pois ja listataan `unclassified` — sitä ei tyypitetä eikä
    nollata.
    """
    if mode not in ("PRE", "FULL"):
        raise ValueError(f"tuntematon mode: {mode!r}")
    if not isinstance(max_lag, timedelta) or max_lag < timedelta(0):
        raise ClassificationError("max_lag: oltava ei-negatiivinen timedelta — "
                                  "raja on valinta, ei oletus")

    raws = list(raw_events)
    by_id: dict[str, dict] = {}
    for r in raws:
        eid = r.get("event_id")
        if eid in by_id:
            raise ClassificationError(f"duplikaatti event_id jäädytetyssä aineistossa: {eid!r}")
        by_id[eid] = r

    recs_by_event: dict[str, list[ClassificationRecord]] = {}
    for rec in records:
        raw = by_id.get(rec.event_id)
        if raw is None:
            raise ClassificationError(
                f"luokitus viittaa tapahtumaan jota ei ole: {rec.event_id!r}")
        actual = event_hash(raw)
        if rec.event_hash != actual:
            raise ClassificationError(
                f"{rec.event_id}: event_hash ei täsmää (luokitus {rec.event_hash}, "
                f"todiste {actual}). Todiste on muuttunut luokituksen jälkeen tai "
                "luokitus on tehty eri versiolle.")
        recs_by_event.setdefault(rec.event_id, []).append(rec)

    events: list[Event] = []
    accepted: dict[str, str] = {}
    rejected: list[tuple[str, str, str]] = []
    unclassified: list[str] = []
    anomalous: list[str] = []

    for eid, raw in by_id.items():
        cand = recs_by_event.get(eid, [])
        if raw.get("_anomaly"):
            # Snapshot on jo merkinnyt todisteen virheelliseksi (esim.
            # known_at ennen occurred_at). Sitä ei luokitella eikä
            # korjata — se raportoidaan erikseen, ei pudoteta hiljaa.
            if cand:
                raise ClassificationError(
                    f"{eid}: tapahtuma on merkitty anomaliaksi, sitä ei voi luokitella")
            anomalous.append(eid)
            continue
        # Todistetaso validoidaan ilman luokitusta aikaleimojen saamiseksi.
        probe = validate_event({**raw, "type": "D", "impact_weight": None,
                                "irreversibility": None,
                                "llm_classification": {k: None for k in
                                                       ("intensity", "targeting",
                                                        "policy_proximity", "uptake")}})
        for rec in cand:
            if rec.classified_at < probe.retrieved_at:
                raise ClassificationError(
                    f"{eid}: classified_at ({rec.classified_at.isoformat()}) ennen "
                    f"retrieved_at ({probe.retrieved_at.isoformat()}) — todistetta ei "
                    "voi luokitella ennen kuin se on haettu")

        chosen: ClassificationRecord | None = None
        chosen_status = ""
        if mode == "PRE":
            for rec in sorted(cand, key=lambda r: r.classified_at):
                st, why = status(rec, probe, max_lag)
                if st == "CLEAN":
                    chosen, chosen_status = rec, st
                    break
                rejected.append((eid, st, why))
        else:
            if cand:
                chosen = max(cand, key=lambda r: r.classified_at)
                chosen_status = status(chosen, probe, max_lag)[0]

        if chosen is None:
            unclassified.append(eid)
            continue
        merged = {**raw, **copy.deepcopy(chosen.values)}
        try:
            events.append(validate_event(merged))
        except SchemaError as exc:
            raise ClassificationError(f"{eid}: luokitus ei läpäise validointia: {exc}") from exc
        accepted[eid] = chosen_status

    report = JoinReport(
        mode=mode,
        max_lag_days=max_lag.total_seconds() / 86400.0,
        accepted=accepted,
        rejected=tuple(rejected),
        unclassified=tuple(unclassified),
        anomalous=tuple(anomalous),
    )
    return events, report
