"""OGAS3 — kuukausiaggregaatio.

Turvalukko 2: no look-ahead.

    PRE   suodattaa known_at   <= kuukauden loppu
    FULL  suodattaa occurred_at <= kuukauden loppu

PRE vastaa kysymykseen "mitä olisi voitu tietää silloin".
FULL vastaa kysymykseen "mitä jälkikäteen tiedämme tapahtuneen".

Turvalukko 3: FULL EI ole ennuste. Se on diagnostinen vertailusarja.
Se näkee valmisteluhistorian, jota reaaliaikainen havaitsija ei nähnyt,
ja siksi sen ja PRE:n ero on itsessään mittaustulos — ei virhe.

SP = D + O + S on ainoa lukittu kaava (johdettu esimerkistä
18.4 + 11.2 + 14.7 = 44.3). Kaikki muu on aggregointia ilman tulkintaa.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Literal

from schema import EVENT_TYPES, Event

Mode = Literal["PRE", "FULL"]


def month_key(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"


def month_end(key: str) -> datetime:
    """Kuukauden viimeinen hetki UTC:ssa (eksklusiivinen raja seuraavan alussa)."""
    y, m = (int(x) for x in key.split("-"))
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    return datetime(ny, nm, 1, tzinfo=timezone.utc)


def cutoff_field(mode: Mode) -> str:
    if mode == "PRE":
        return "known_at"
    if mode == "FULL":
        return "occurred_at"
    raise ValueError(f"tuntematon mode: {mode!r}")


@dataclass(frozen=True)
class MonthlyBucket:
    """Yhden kuukauden raakasummat. Ei skaalausta, ei painotusta."""

    month: str
    mode: Mode
    counts: dict[str, int]           # tyyppikohtainen tapahtumamäärä
    raw: dict[str, float]            # tyyppikohtainen impact_weight-summa
    event_ids: dict[str, tuple[str, ...]]
    unweighted: dict[str, tuple[str, ...]]   # tapahtumat joilla impact_weight puuttuu

    @property
    def sp_raw(self) -> float:
        """SP = D + O + S, raakayksiköissä. Skaalaus tehdään erikseen."""
        return sum(self.raw[t] for t in EVENT_TYPES)


def months_in_range(start: str, end: str) -> list[str]:
    ys, ms = (int(x) for x in start.split("-"))
    ye, me = (int(x) for x in end.split("-"))
    out: list[str] = []
    y, m = ys, ms
    while (y, m) <= (ye, me):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def aggregate(
    events: Iterable[Event],
    mode: Mode,
    months: list[str] | None = None,
) -> dict[str, MonthlyBucket]:
    """Aggregoi tapahtumat kuukausittain.

    Tapahtuma osuu kuukauteen sen MODEN mukaisen aikaleiman perusteella,
    ja se on mukana KAIKISSA sitä seuraavissa kuukausissa vain jos
    aggregaatti on kumulatiivinen — tämä toteutus EI ole kumulatiivinen:
    jokainen kuukausi sisältää vain sen kuukauden tapahtumat. Kumulatiivinen
    tulkinta on skaalaus- ja laskentakerroksen asia, ei aggregaatin.
    """
    evs = list(events)
    fld = cutoff_field(mode)

    by_month: dict[str, list[Event]] = defaultdict(list)
    for e in evs:
        by_month[month_key(getattr(e, fld))].append(e)

    if months is None:
        months = sorted(by_month) or []

    out: dict[str, MonthlyBucket] = {}
    for mk in months:
        bucket = by_month.get(mk, [])
        counts = {t: 0 for t in EVENT_TYPES}
        raw = {t: 0.0 for t in EVENT_TYPES}
        ids: dict[str, list[str]] = {t: [] for t in EVENT_TYPES}
        missing: dict[str, list[str]] = {t: [] for t in EVENT_TYPES}
        for e in bucket:
            counts[e.type] += 1
            ids[e.type].append(e.event_id)
            if e.impact_weight is None:
                # Puuttuva paino EI ole nolla. Se kirjataan erikseen ja
                # näkyy audit trailissa; summaan sitä ei lisätä eikä
                # oleteta miksikään.
                missing[e.type].append(e.event_id)
            else:
                raw[e.type] += e.impact_weight
        out[mk] = MonthlyBucket(
            month=mk,
            mode=mode,
            counts=counts,
            raw=raw,
            event_ids={t: tuple(ids[t]) for t in EVENT_TYPES},
            unweighted={t: tuple(missing[t]) for t in EVENT_TYPES},
        )
    return out


def visibility_lag(events: Iterable[Event]) -> dict[str, float]:
    """PRE/FULL-eron perusmittari: kuinka myöhään tieto tuli saataville.

    Tämä ei ole RRI:n osa. Se on diagnostiikkaa, joka kertoo kuinka paljon
    FULL voi erota PRE:stä rakenteellisesti.
    """
    lags = [e.known_lag_days for e in events]
    if not lags:
        return {"n": 0, "mean": 0.0, "median": 0.0, "max": 0.0}
    s = sorted(lags)
    n = len(s)
    median = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    return {"n": n, "mean": sum(s) / n, "median": median, "max": s[-1]}
