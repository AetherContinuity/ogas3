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
from schema import EVENT_TYPES, SP_TYPES, Event

# GATE 4 lukittu 5.9.2026. Laskenta on moduulissa rri.py; tässä vain
# audit trail. Aiempi NotImplementedError poistettiin vasta kun kaikki
# neljä porttia olivat kiinni — ei aiemmin.
RRI_SPEC_STATUS = "LOCKED 2026-09-05 — SP x L x (1+IR), ks. rri.py"

from rri import (compute_l, compute_rri_raw, monthly_l_ir_from_events,  # noqa: E402
                 scale_rri, MonthlyLIR)


def explain_month(
    month: str,
    bucket: MonthlyBucket,
    scaled: ScaledMonth,
    events: Iterable[Event],
    lir: "MonthlyLIR | None" = None,
    rri_scaled: float | None = None,
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

    if lir is None:
        lir_block = {"status": "NOT COMPUTED", "reason": "lir-parametria ei annettu"}
        ir_block = dict(lir_block)
        rri_block = dict(lir_block)
    else:
        raw = compute_rri_raw(scaled.structural_pressure, lir.l, lir.ir)
        lir_block = {"value": lir.l, "source_event": lir.l_source_event,
                     "events_seen": lir.l_events_seen,
                     "incomplete_classification": list(lir.l_events_incomplete),
                     "aggregation": "max", "basis": lir.basis}
        ir_block = {"value": lir.ir, "source_event": lir.ir_source_event,
                    "events_seen": lir.ir_events_seen, "aggregation": "max"}
        rri_block = {"formula": "SP x L x (1 + IR)",
                     "SP": scaled.structural_pressure, "L": lir.l, "IR": lir.ir,
                     "raw": raw, "scaled": rri_scaled,
                     "status": RRI_SPEC_STATUS}

    return {
        "month": month,
        "mode": bucket.mode,
        "scaling": scaled.scaling,
        "n_months_in_basis": scaled.n_months_in_basis,
        "counts": dict(bucket.counts),
        "raw": {t: round(bucket.raw[t], 4) for t in SP_TYPES},
        "bounds": {t: [round(v, 4) for v in scaled.bounds[t]] for t in SP_TYPES},
        "contribution": {t: scaled.scaled[t] for t in SP_TYPES},
        "structural_pressure": scaled.structural_pressure,
        "unweighted_events": {t: list(bucket.unweighted[t]) for t in SP_TYPES},
        "L": lir_block,
        "IR": ir_block,
        "RRI": rri_block,
        "events": contributions,
    }


def format_explain(x: dict) -> str:
    """Ihmisluettava audit trail — sama muoto kuin spesifikaation esimerkissä."""
    lines = [f"{x['month']}  [{x['mode']} / {x['scaling']}]"]
    for t in SP_TYPES:
        lines.append(
            f"  {t} contribution: {x['contribution'][t]:>7.1f}"
            f"   (raaka {x['raw'][t]:.4f}, n={x['counts'][t]}, "
            f"rajat {x['bounds'][t][0]:.4f}..{x['bounds'][t][1]:.4f})"
        )
    lines.append(f"  Structural Pressure: {x['structural_pressure']:.1f}")
    miss = [e for lst in x["unweighted_events"].values() for e in lst]
    if miss:
        lines.append(f"  ! impact_weight puuttuu: {', '.join(miss)} (EI laskettu nollaksi)")
    L, IR, R = x["L"], x["IR"], x["RRI"]
    if "value" in L:
        lines.append(f"  L  = {L['value']:.4f}  (max, {L['events_seen']} L-tapahtumaa"
                     + (f", lähde {L['source_event']}" if L["source_event"] else "")+")")
        if L["incomplete_classification"]:
            lines.append(f"     ! luokitus kesken: {', '.join(L['incomplete_classification'])}"
                         " (EI laskettu nollaksi)")
        lines.append(f"  IR = {IR['value']:.4f}  (max, {IR['events_seen']} IR-tapahtumaa"
                     + (f", lähde {IR['source_event']}" if IR["source_event"] else "")+")")
        lines.append(f"  RRI_raw = {R['SP']:.1f} x {R['L']:.4f} x (1 + {R['IR']:.4f}) = {R['raw']:.4f}")
        if R["scaled"] is not None:
            lines.append(f"  RRI = {R['scaled']:.1f}")
        lines.append(f"     {L['basis']}")
    else:
        lines.append(f"  L/IR/RRI: {L['status']}")
    return "\n".join(lines)
