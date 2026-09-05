"""OGAS3 — skaalaus D/O/S → 0…100.

Tässä on look-aheadin toiseksi tavallisin piilopaikka: normalisointi.

    PRE-skaalaus EI saa käyttää koko aineiston min/max-arvoja, koska
    silloin syyskuun PRE-tulos tietäisi jo joulukuun datan.

Kaksi sallittua PRE-tilaa:

    "expanding"  min/max lasketaan vain kuukauteen N asti nähdyistä
                 kuukausista. Kausaalisesti puhdas mutta epävakaa alussa.

    "baseline"   ennalta lukittu min/max, annettu eksplisiittisesti.
                 Vakaa, mutta baseline on itsessään valinta ja se
                 kirjataan tulokseen.

FULL saa käyttää koko ikkunan skaalausta — se on diagnostinen
vertailusarja, ei reaaliaikainen mittari (turvalukko 3).

Kumpaakaan ei haudata koodiin oletuksena: tila on annettava eksplisiittisesti.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from aggregator import MonthlyBucket
from schema import SP_TYPES as EVENT_TYPES  # skaalataan vain SP:n osat

PreMode = Literal["expanding", "baseline"]


class ScalingError(ValueError):
    pass


@dataclass(frozen=True)
class ScaledMonth:
    month: str
    mode: str                     # "PRE" | "FULL"
    scaling: str                  # "expanding" | "baseline" | "full-window"
    raw: dict[str, float]
    scaled: dict[str, float]      # 0–100
    bounds: dict[str, tuple[float, float]]
    n_months_in_basis: int

    @property
    def structural_pressure(self) -> float:
        """SP = D + O + S skaalatuista komponenteista.

        Ainoa lukittu kaava. Esimerkki 18.4 + 11.2 + 14.7 = 44.3.
        """
        return round(sum(self.scaled[t] for t in EVENT_TYPES), 4)


def _scale(value: float, lo: float, hi: float) -> float:
    if hi <= lo:
        # Degeneroitunut väli: yksi havainto tai kaikki samoja.
        # Palautetaan 0, EI 50 eikä 100 — nolla on ainoa arvo, joka ei
        # väitä sijaintia jakaumassa jota ei ole.
        return 0.0
    return max(0.0, min(100.0, (value - lo) / (hi - lo) * 100.0))


def scale_pre(
    buckets: dict[str, MonthlyBucket],
    pre_mode: PreMode,
    baseline: dict[str, tuple[float, float]] | None = None,
) -> dict[str, ScaledMonth]:
    for b in buckets.values():
        if b.mode != "PRE":
            raise ScalingError(f"scale_pre sai {b.mode}-bucketin kuukaudelta {b.month}")

    months = sorted(buckets)
    out: dict[str, ScaledMonth] = {}

    if pre_mode == "baseline":
        if not baseline or set(baseline) != set(EVENT_TYPES):
            raise ScalingError(
                "baseline-tila vaatii eksplisiittiset rajat kaikille tyypeille "
                f"{EVENT_TYPES} — ennalta lukittu baseline on valinta, ei oletus"
            )
        for mk in months:
            b = buckets[mk]
            out[mk] = ScaledMonth(
                month=mk, mode="PRE", scaling="baseline",
                raw=dict(b.raw),
                scaled={t: round(_scale(b.raw[t], *baseline[t]), 4) for t in EVENT_TYPES},
                bounds=dict(baseline),
                n_months_in_basis=0,
            )
        return out

    if pre_mode != "expanding":
        raise ScalingError(f"tuntematon pre_mode: {pre_mode!r}")

    for i, mk in enumerate(months):
        seen = months[: i + 1]                     # vain kuukauteen N asti
        bounds = {}
        for t in EVENT_TYPES:
            vals = [buckets[m].raw[t] for m in seen]
            bounds[t] = (min(vals), max(vals))
        b = buckets[mk]
        out[mk] = ScaledMonth(
            month=mk, mode="PRE", scaling="expanding",
            raw=dict(b.raw),
            scaled={t: round(_scale(b.raw[t], *bounds[t]), 4) for t in EVENT_TYPES},
            bounds=bounds,
            n_months_in_basis=len(seen),
        )
    return out


def scale_full(buckets: dict[str, MonthlyBucket]) -> dict[str, ScaledMonth]:
    """Koko ikkunan skaalaus. Sallittu VAIN FULL-tilassa."""
    for b in buckets.values():
        if b.mode != "FULL":
            raise ScalingError(
                f"scale_full sai {b.mode}-bucketin kuukaudelta {b.month} — "
                "koko ikkunan skaalaus PRE-tilassa on piilotettu look-ahead"
            )
    months = sorted(buckets)
    bounds = {}
    for t in EVENT_TYPES:
        vals = [buckets[m].raw[t] for m in months]
        bounds[t] = (min(vals), max(vals)) if vals else (0.0, 0.0)
    return {
        mk: ScaledMonth(
            month=mk, mode="FULL", scaling="full-window",
            raw=dict(buckets[mk].raw),
            scaled={t: round(_scale(buckets[mk].raw[t], *bounds[t]), 4) for t in EVENT_TYPES},
            bounds=bounds,
            n_months_in_basis=len(months),
        )
        for mk in months
    }
