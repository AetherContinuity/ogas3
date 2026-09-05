"""OGAS3 — tapahtumien validointi.

Turvalukko 1: puuttuva tai väärän tyyppinen kenttä ei muutu hiljaisesti
nollaksi. Jokainen puute nostaa SchemaErrorin ja kertoo mikä kenttä.

Suunnitteluvalinta: validointi on tiukka mutta EI täytä puuttuvia arvoja.
Erityisesti `intensity` saa olla None, koska I:n deterministinen laskenta
ei ole spesifioitu. None ja 0.0 ovat eri asioita ja pysyvät erillään läpi
koko ketjun.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from schema import EVENT_TYPES, L_COMPONENTS, Evidence, Event, SchemaError, parse_ts

REQUIRED = (
    "event_id", "occurred_at", "known_at", "retrieved_at",
    "source", "source_url", "type",
)


def _unit_interval(value: Any, path: str, allow_none: bool = True) -> float | None:
    if value is None:
        if allow_none:
            return None
        raise SchemaError(f"{path}: arvo puuttuu eikä None ole sallittu")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaError(f"{path}: oltava luku 0–1, oli {type(value).__name__}")
    v = float(value)
    if not (0.0 <= v <= 1.0):
        raise SchemaError(f"{path}: arvon on oltava välillä 0–1, oli {v}")
    return v


def validate_event(d: Any, index: int | None = None) -> Event:
    """Rakentaa Eventin tai nostaa SchemaErrorin. Ei koskaan palauta osittaista."""
    where = f"events[{index}]" if index is not None else "event"
    if not isinstance(d, dict):
        raise SchemaError(f"{where}: tapahtuman on oltava objekti")

    for k in REQUIRED:
        if k not in d:
            raise SchemaError(f"{where}.{k}: pakollinen kenttä puuttuu")

    eid = d["event_id"]
    if not isinstance(eid, str) or not eid.strip():
        raise SchemaError(f"{where}.event_id: oltava ei-tyhjä merkkijono")

    etype = d["type"]
    if etype not in EVENT_TYPES:
        raise SchemaError(f"{where}.type: oltava yksi {EVENT_TYPES}, oli {etype!r}")

    occurred = parse_ts(d["occurred_at"], f"{where}.occurred_at")
    known = parse_ts(d["known_at"], f"{where}.known_at")
    retrieved = parse_ts(d["retrieved_at"], f"{where}.retrieved_at")

    # Kausaalijärjestys. Tieto ei voi olla saatavilla ennen tapahtumaa,
    # eikä järjestelmä voi hakea sitä ennen kuin se oli saatavilla.
    if known < occurred:
        raise SchemaError(
            f"{where}: known_at ({known.isoformat()}) on ennen occurred_at "
            f"({occurred.isoformat()}) — tieto ei voi olla saatavilla ennen tapahtumaa"
        )
    if retrieved < known:
        raise SchemaError(
            f"{where}: retrieved_at ({retrieved.isoformat()}) on ennen known_at "
            f"({known.isoformat()}) — lähdettä ei voi hakea ennen kuin se on olemassa"
        )

    cls_in = d.get("llm_classification") or {}
    if not isinstance(cls_in, dict):
        raise SchemaError(f"{where}.llm_classification: oltava objekti")
    unknown = set(cls_in) - set(L_COMPONENTS)
    if unknown:
        raise SchemaError(f"{where}.llm_classification: tuntemattomat kentät {sorted(unknown)}")
    cls: dict[str, float | None] = {}
    for k in L_COMPONENTS:
        if k not in cls_in:
            raise SchemaError(
                f"{where}.llm_classification.{k}: kenttä puuttuu. "
                "Käytä eksplisiittistä null-arvoa, jos luokitusta ei ole tehty — "
                "puuttuva ja nolla eivät ole sama asia."
            )
        cls[k] = _unit_interval(cls_in[k], f"{where}.llm_classification.{k}")

    ev_in = d.get("evidence")
    if not isinstance(ev_in, list) or not ev_in:
        raise SchemaError(f"{where}.evidence: vaaditaan vähintään yksi todiste")
    evidence = tuple(Evidence.from_dict(e, f"{where}.evidence[{i}]") for i, e in enumerate(ev_in))

    params = d.get("parameters", {})
    if not isinstance(params, dict):
        raise SchemaError(f"{where}.parameters: oltava objekti")

    subtype = d.get("subtype")
    if subtype is not None and not isinstance(subtype, str):
        raise SchemaError(f"{where}.subtype: oltava merkkijono tai null")

    iw = _unit_interval(d.get("impact_weight"), f"{where}.impact_weight")
    irr = _unit_interval(d.get("irreversibility"), f"{where}.irreversibility")

    # ROE v0.3: impact_weight koskee VAIN D/O/S (ne menevät SP:hen).
    # intensity koskee VAIN L. Rajaukset valvotaan tässä, jotta väärässä
    # paikassa oleva arvo ei pääse laskentaan hiljaisesti.
    from schema import SP_TYPES
    if etype not in SP_TYPES and iw is not None:
        raise SchemaError(f"{where}.impact_weight: vain D/O/S saa painon, tyyppi on {etype}")
    if etype != "L" and cls.get("intensity") is not None:
        raise SchemaError(f"{where}.llm_classification.intensity: vain L-tapahtumalla "
                          f"on intensity, tyyppi on {etype}")

    return Event(
        event_id=eid,
        occurred_at=occurred,
        known_at=known,
        retrieved_at=retrieved,
        source=str(d["source"]),
        source_url=str(d["source_url"]),
        type=etype,
        subtype=subtype,
        parameters=params,
        llm_classification=cls,
        irreversibility=irr,
        impact_weight=iw,
        evidence=evidence,
    )


def validate_events(items: Iterable[Any]) -> list[Event]:
    events = [validate_event(d, i) for i, d in enumerate(items)]
    seen: dict[str, int] = {}
    for i, e in enumerate(events):
        if e.event_id in seen:
            raise SchemaError(
                f"events[{i}].event_id: duplikaatti {e.event_id!r} "
                f"(ensimmäinen esiintymä events[{seen[e.event_id]}])"
            )
        seen[e.event_id] = i
    return events


def load_events(path: str | Path) -> list[Event]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "events" in data:
        data = data["events"]
    if not isinstance(data, list):
        raise SchemaError("juuritason oltava lista tai objekti jossa 'events'-lista")
    return validate_events(data)
