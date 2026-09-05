"""OGAS3 — audit trail ja tarkoituksellinen aukko.

Vaatimus: jokaisesta kuukausiarvosta pitää pystyä kysymään
"mistä tämä luku syntyi" ja saada vastaus, joka johtaa yksittäisiin
tapahtumiin ja niiden todisteisiin.

Tämä on tärkeämpi ominaisuus kuin mikään näkymä.
"""

from __future__ import annotations

from typing import Iterable

from aggregator import MonthlyBucket
from scaler import ScaledMonth
from schema import EVENT_TYPES, Event

RRI_SPEC_STATUS = "NOT SPECIFIED (2026-09-04)"


def compute_rri(*args, **kwargs):
    """RRI-kaavaa EI ole spesifioitu — tätä ei saa arvata.

    Annettu esimerkki:

        SP  = 44.3
        L   = 0.1039   (= I × T × P × U)
        IR  = 0.61
        RRI = 35.6

    ei riitä johtamaan kaavaa yksikäsitteisesti. Esimerkiksi
    SP × L × (1 + IR) = 7.4, mikä ei ole 35.6. Useita muitakin muotoja
    voidaan sovittaa neljään lukuun, ja niiden valitseminen olisi uuden
    metodologian keksimistä eikä sen toteuttamista.

    Lisäksi I:n (Influence Intensity) deterministinen laskenta ei ole
    spesifioitu, joten L:ää ei voi laskea tapahtumista edes silloin kun
    RRI:n kaava tunnetaan.

    Tämä NotImplementedError on tietoinen lukko, ei keskeneräisyys.
    """
    raise NotImplementedError(
        "RRI formula is not yet formally specified. "
        "SP = D + O + S and L = I x T x P x U are locked; the combination "
        "of SP, L and IR into RRI is not derivable from the available example."
    )


def compute_l(_classification) -> float:
    """L = I × T × P × U — kaava tunnetaan, mutta I:tä ei voi laskea.

    Kolme neljästä komponentista tulee luokituksesta. I (Influence
    Intensity) on merkitty spesifikaatiossa määrittelemättömäksi, joten
    tulon laskeminen kolmesta ja I:n olettaminen ykköseksi olisi
    hiljainen oletus — täsmälleen se, mitä turvalukko 1 kieltää.
    """
    raise NotImplementedError(
        "L requires I (Influence Intensity); its deterministic computation "
        "is not specified. Assuming I = 1.0 would silently change the result."
    )


def explain_month(
    month: str,
    bucket: MonthlyBucket,
    scaled: ScaledMonth,
    events: Iterable[Event],
) -> dict:
    """Palauttaa täyden jäljen yhdelle kuukaudelle.

    Sisältää: raakasummat, skaalatut arvot, käytetyt rajat, skaalaustavan,
    tapahtumatunnukset tyypeittäin, painottamattomat tapahtumat ja
    todisteiden osoitteet hakuhetkineen.
    """
    by_id = {e.event_id: e for e in events}
    contributions = []
    for t in EVENT_TYPES:
        for eid in bucket.event_ids[t]:
            e = by_id.get(eid)
            contributions.append({
                "event_id": eid,
                "type": t,
                "impact_weight": None if e is None else e.impact_weight,
                "weight_missing": e is not None and e.impact_weight is None,
                "occurred_at": None if e is None else e.occurred_at.isoformat(),
                "known_at": None if e is None else e.known_at.isoformat(),
                "known_lag_days": None if e is None else round(e.known_lag_days, 2),
                "source": None if e is None else e.source,
                "evidence": [] if e is None else [
                    {"quote": ev.quote[:160], "location": ev.location,
                     "source_url": ev.source_url,
                     "retrieved_at": ev.retrieved_at.isoformat()}
                    for ev in e.evidence
                ],
            })

    return {
        "month": month,
        "mode": bucket.mode,
        "scaling": scaled.scaling,
        "n_months_in_basis": scaled.n_months_in_basis,
        "counts": dict(bucket.counts),
        "raw": {t: round(bucket.raw[t], 4) for t in EVENT_TYPES},
        "bounds": {t: [round(v, 4) for v in scaled.bounds[t]] for t in EVENT_TYPES},
        "contribution": {t: scaled.scaled[t] for t in EVENT_TYPES},
        "structural_pressure": scaled.structural_pressure,
        "unweighted_events": {t: list(bucket.unweighted[t]) for t in EVENT_TYPES},
        "L": {"status": "NOT COMPUTABLE", "reason": "I (Influence Intensity) not specified"},
        "IR": {"status": "NOT AGGREGATED", "reason": "IR aggregation formula not locked"},
        "RRI": {"status": RRI_SPEC_STATUS},
        "events": contributions,
    }


def format_explain(x: dict) -> str:
    """Ihmisluettava audit trail — sama muoto kuin spesifikaation esimerkissä."""
    lines = [f"{x['month']}  [{x['mode']} / {x['scaling']}]"]
    for t in EVENT_TYPES:
        lines.append(
            f"  {t} contribution: {x['contribution'][t]:>7.1f}"
            f"   (raaka {x['raw'][t]:.4f}, n={x['counts'][t]}, "
            f"rajat {x['bounds'][t][0]:.4f}..{x['bounds'][t][1]:.4f})"
        )
    lines.append(f"  Structural Pressure: {x['structural_pressure']:.1f}")
    miss = [e for lst in x["unweighted_events"].values() for e in lst]
    if miss:
        lines.append(f"  ! impact_weight puuttuu: {', '.join(miss)} (EI laskettu nollaksi)")
    lines.append(f"  L:   {x['L']['status']} — {x['L']['reason']}")
    lines.append(f"  IR:  {x['IR']['status']} — {x['IR']['reason']}")
    lines.append(f"  RRI: {x['RRI']['status']}")
    return "\n".join(lines)
