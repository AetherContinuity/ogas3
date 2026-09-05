"""OGAS3 — tapahtumaskeema.

Metodologinen ehto (lukittu 2026-09-04):
    Moottori ei muuta tapahtumien sisältöä. Se ainoastaan aggregoi,
    normalisoi ja laskee.

Kaikki kentät, joita ei voida johtaa nykyisestä spesifikaatiosta, ovat
None-sallivia ja niiden puuttuminen on VIRHE, ei nolla. Hiljainen
nollaksi muuttuminen on tässä järjestelmässä nimenomainen kielto:
puuttuva syöte ja nolla-arvoinen syöte ovat eri asioita.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# --------------------------------------------------------------------
# Tapahtumatyypit
# --------------------------------------------------------------------
# ROE v0.3 (5.9.2026) määrittelee viisi tapahtumatyyppiä.
# KORJATTU 5.9.2026: aiemmin vain ("D","O","S"), koska schema kirjoitettiin
# ennen kuin ROE oli saatavilla ja ainoa tunnettu kaava oli SP = D + O + S.
# L- ja IR-tapahtumat hylättiin silloin skeemavirheenä. Aukko paljastui
# vasta kun RRI-testit yrittivät luoda L-tapahtuman.
#
#   D   Structural Load Pressure       uusi kuorma
#   O   Ownership Transition Pressure  omistusrakenteen muutos
#   S   Flexibility/Capacity Erosion   säätökyvyn heikkeneminen
#   L   Institutional Influence        vaikuttamisyritys
#   IR  Irreversibility                peruuttamaton päätös
EVENT_TYPES = ("D", "O", "S", "L", "IR")

# Vain nämä kolme summautuvat Structural Pressureen. L ja IR ovat RRI:n
# kertoimia, eivät SP:n osia — ks. rri.py.
SP_TYPES = ("D", "O", "S")

# L-komponentit. Alueet 0–1, nimet spesifikaatiosta.
# I:n deterministinen laskenta EI ole spesifioitu -> intensity saa olla None
# ja se on tarkoituksellinen aukko, ei puute skeemassa.
L_COMPONENTS = ("intensity", "targeting", "policy_proximity", "uptake")

ISO = "%Y-%m-%dT%H:%M:%S%z"


class SchemaError(ValueError):
    """Nostetaan aina kun kenttä puuttuu tai on väärää tyyppiä.

    Turvalukko 1: puuttuva tai väärän tyyppinen kenttä EI saa hiljaisesti
    muuttua nollaksi.
    """


def parse_ts(value: Any, field_name: str) -> datetime:
    """ISO 8601, aikavyöhyke pakollinen.

    Naiivi aikaleima hylätään: kolmen aikaleiman vertailu eri
    vyöhykkeiltä on juuri se paikka, jossa off-by-one-virhe on
    havaitsematon.
    """
    if not isinstance(value, str):
        raise SchemaError(f"{field_name}: aikaleiman on oltava merkkijono, oli {type(value).__name__}")
    v = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(v)
    except ValueError as exc:
        raise SchemaError(f"{field_name}: ei kelvollinen ISO 8601 -aikaleima: {value!r}") from exc
    if dt.tzinfo is None:
        raise SchemaError(f"{field_name}: aikavyöhyke puuttuu ({value!r}) — naiivi aikaleima hylätään")
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class Evidence:
    """Yksittäinen todiste.

    retrieved_at on pakollinen. Perustelu: 2026 aikana havaittiin kolme
    rajapintaa, joiden osoite tai tietomalli muuttui vuoden sisällä
    (Hankeikkuna /api/v1 -> /api/v2, Suomen Pankki /v3/api -> /v4,
    ECB ICP -> HICP). source_url ilman hakuhetkeä on tarkistamaton
    väite parin vuoden päästä.
    """

    quote: str
    location: str
    source_url: str
    retrieved_at: datetime

    @staticmethod
    def from_dict(d: Any, path: str) -> "Evidence":
        if not isinstance(d, dict):
            raise SchemaError(f"{path}: evidence-alkion on oltava objekti")
        for k in ("quote", "location", "source_url", "retrieved_at"):
            if k not in d:
                raise SchemaError(f"{path}.{k}: pakollinen kenttä puuttuu")
        for k in ("quote", "location", "source_url"):
            if not isinstance(d[k], str) or not d[k].strip():
                raise SchemaError(f"{path}.{k}: oltava ei-tyhjä merkkijono")
        return Evidence(
            quote=d["quote"],
            location=d["location"],
            source_url=d["source_url"],
            retrieved_at=parse_ts(d["retrieved_at"], f"{path}.retrieved_at"),
        )


@dataclass(frozen=True)
class Event:
    """Yksi tapahtuma.

    Kolme aikaleimaa, kolme eri semantiikkaa:

      occurred_at   milloin asia tapahtui tai päätös tehtiin
      known_at      milloin tieto oli ulkopuolisen havaitsijan käytettävissä
      retrieved_at  milloin tämä järjestelmä haki lähteen

    Tämä mahdollistaa PRE/FULL-erottelun ilman look-aheadia:
      PRE   suodattaa known_at <= kuukauden loppu
      FULL  suodattaa occurred_at <= kuukauden loppu

    Yhdellä aikaleimalla lukkoa ei voi valvoa — se vain näyttää valvotulta.
    """

    event_id: str
    occurred_at: datetime
    known_at: datetime
    retrieved_at: datetime
    source: str
    source_url: str
    type: str
    subtype: str | None
    parameters: dict[str, Any]
    llm_classification: dict[str, float | None]
    irreversibility: float | None
    impact_weight: float | None
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    # -- johdannaiset ---------------------------------------------------
    @property
    def known_lag_days(self) -> float:
        """known_at − occurred_at, vuorokausina.

        Negatiivinen arvo on skeemavirhe (ks. validator).
        """
        return (self.known_at - self.occurred_at).total_seconds() / 86400.0
