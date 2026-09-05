"""OGAS3 — RRI:n laskenta. GATE 2, 3 ja 4.

Kaikki portit lukittu 5.9.2026. Tämä moduuli toteuttaa ne eikä keksi
mitään niiden ympärille.

    L(month)  = max(I × T × P × U) L-tapahtumista, oletus 0
    IR(month) = max(irreversibility) IR-tapahtumista, oletus 0
    SP(month) = D + O + S, aggregoitu ja skaalattu (0–300)
    RRI_raw   = SP × L × (1 + IR)
    RRI       = scale(RRI_raw, expanding | baseline | full-window)

RAKENTEELLISET VALINNAT JA NIIDEN PERUSTELUT
--------------------------------------------
Nämä ovat substantiivisia väitteitä siitä, miten institutionaalinen
paine muodostuu — eivät teknisiä parametreja. Ne kirjataan tähän, koska
koodi on ainoa paikka jossa ne pysyvät kaavan vieressä.

1. L on KERROIN, ei lisä (SP × L, ei SP + L).
   Jos RRI olisi SP + L, se nousisi pelkästä rakenteellisesta paineesta
   riippumatta siitä onko vaikuttaminen onnistunut — ja olisi silloin
   päällekkäinen SHI:n kanssa. RRI:n erillinen signaali syntyy siitä,
   että se mittaa painetta JOKA ONNISTUU.

2. IR on KERROIN, ei portti.
   Peruutettavakin paine on painetta. IR:n rooli on korostaa sitä, mikä
   on jo lukittu, ei suodattaa muuta pois.

3. L ja IR aggregoidaan MAKSIMINA, ei keskiarvona.
   Lukkiutuminen ei keskiarvoistu: jos yksi CHP puretaan, se on
   peruuttamaton riippumatta siitä montako peruttavaa päätöstä samassa
   kuussa tehtiin. Sama pätee vaikuttamiseen — onnistunut vaikuttaminen
   ei laimennu siitä, että samassa kuussa oli myös heikkoja yrityksiä.

4. Tyhjä kuukausi antaa RRI = 0 TARKOITUKSELLA.
   L = 0 nollaa tulon. "Ei vaikuttamista, ei painetta joka onnistuu" on
   mittaustulos, ei puuttuva arvo. Ero näkyy audit trailissa
   (basis-kentässä), jotta nolla-syy on aina jäljitettävissä.

5. Skaalaus on HAVAITTUUN maksimiin, ei teoreettiseen.
   Teoreettinen maksimi 300 × 1 × 2 = 600 ei ole saavutettavissa:
   realistinen L on 0,1–0,3, joten sarja jäisi pysyvästi alle 30:n ja
   käyttäisi kolmasosan asteikostaan. Havaittu maksimi käyttää samaa
   expanding/baseline/full-window-logiikkaa kuin SP — ja SAMAA LUKKOA:
   PRE ei saa käyttää tulevaa dataa.

HYLÄTTY ESIMERKKI
-----------------
Aiempi audit trail -esimerkki (SP 44.3 · L 0.1039 · IR 0.61 · RRI 35.6)
EI ole tämän kaavan mukainen: 44.3 × 0.1039 × 1.61 = 7.41, skaalattuna
teoreettiseen maksimiin 1.24. Ero on kolmikymmenkertainen.

Esimerkki hylättiin 5.9.2026, ei kaava. Perustelu: luvut olivat
havainnollistavia eivätkä laskennallisia — ne kuvasivat muotoa. Kaava on
johdettu rakenteellisista valinnoista 1–3, ei neljästä luvusta.
Tämä kirjataan, koska esimerkki oli pitkään ainoa numeerinen ankkuri.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from schema import L_COMPONENTS, Event

# L lasketaan vain L-tapahtumista, IR vain IR-tapahtumista (ROE v0.3).
# D/O/S menevät SP:hen eivätkä saa intensityä; L/IR eivät saa
# impact_weightia. Nämä vakiot ovat tässä, jotta rajaus on koodissa
# eikä pelkästään promptissa.
L_TYPE = "L"
IR_TYPE = "IR"


class RRIError(ValueError):
    pass


def compute_l(classification: dict) -> float | None:
    """L = I × T × P × U yhdelle tapahtumalle.

    Palauttaa None jos jokin komponentti puuttuu. None ja 0.0 ovat eri
    asioita: puuttuva luokitus ei ole nollavaikutus.
    """
    if not isinstance(classification, dict):
        raise RRIError("llm_classification puuttuu tai on väärää tyyppiä")
    vals = []
    for k in L_COMPONENTS:                       # intensity, targeting, policy_proximity, uptake
        v = classification.get(k)
        if v is None:
            return None
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise RRIError(f"llm_classification.{k}: oltava luku 0–1")
        if not (0.0 <= float(v) <= 1.0):
            raise RRIError(f"llm_classification.{k}: arvon oltava 0–1, oli {v}")
        vals.append(float(v))
    l = vals[0] * vals[1] * vals[2] * vals[3]
    return round(l, 6)


@dataclass(frozen=True)
class MonthlyLIR:
    """Kuukauden L ja IR maksimeina, sekä jälki siitä mistä ne tulivat."""

    month: str
    l: float
    l_source_event: str | None
    l_events_seen: int
    l_events_incomplete: tuple[str, ...]     # luokitus kesken -> EI laskettu nollaksi
    ir: float
    ir_source_event: str | None
    ir_events_seen: int

    @property
    def l_is_determined(self) -> bool:
        """Onko L todettu vai määrittämätön.

        L on todettu jos vähintään yhdellä L-tapahtumalla oli TÄYSI
        luokitus. Jos kaikki olivat kesken, l_best jäi alkuarvoonsa 0.0
        eikä l_source_event koskaan asettunut — ja se tila on eri asia
        kuin havaittu nolla.
        """
        return self.l_events_seen == 0 or self.l_source_event is not None

    @property
    def basis(self) -> str:
        # KORJATTU 2026-09-05: aiempi versio ei erottanut "kaikki
        # luokitukset kesken" tapauksesta "todettu nolla". Molemmissa
        # l == 0.0, mutta ensimmäisessä nolla on TIEDON PUUTE ja
        # toisessa HAVAINTO. Tämä on sama ero jota l_events_incomplete
        # -lista on olemassa säilyttämään — basis vain ei lukenut sitä.
        if self.l_events_seen == 0:
            return "ei L-tapahtumia — RRI = 0 tarkoituksella"
        if self.l_source_event is None:
            n = len(self.l_events_incomplete)
            return (f"L MÄÄRITTÄMÄTÖN: {self.l_events_seen} L-tapahtumaa, "
                    f"kaikkien {n} luokitus kesken. RRI:n nolla on tiedon "
                    f"puute, EI havainto.")
        if self.l == 0.0:
            return (f"L = 0 havaintona: tapahtuman {self.l_source_event} "
                    "luokitus oli täysi ja jokin komponentti nolla")
        return f"L max tapahtumasta {self.l_source_event}"


def monthly_l_ir(events: Iterable[Event], month_events: Iterable[str]) -> MonthlyLIR:
    """Kuukauden L ja IR. Kutsutaan yhden kuukauden tapahtumatunnuksilla."""
    raise NotImplementedError("käytä monthly_l_ir_from_events()")


def monthly_l_ir_from_events(month: str, events: Iterable[Event]) -> MonthlyLIR:
    evs = list(events)

    # KORJATTU 2026-09-05: l_src asetettiin vain jos val > l_best, ja
    # l_best oli alkuarvoltaan 0.0 — joten AITO NOLLA ei koskaan
    # ylittänyt sitä eikä lähdettä kirjattu. Täysin luokiteltu tapahtuma,
    # jonka L on nolla, näytti identtiseltä luokittelemattomalta.
    # Sama piilonolla-virhe kolmannessa kerroksessa. Nyt l_best on None
    # kunnes ensimmäinen TÄYSI luokitus nähdään.
    l_best, l_src, l_incomplete, l_n = None, None, [], 0
    for e in evs:
        if e.type != L_TYPE:
            continue
        l_n += 1
        val = compute_l(e.llm_classification)
        if val is None:
            # Luokitus kesken. EI lasketa nollaksi — se olisi sama virhe
            # kuin puuttuva impact_weight aggregaattorissa.
            l_incomplete.append(e.event_id)
            continue
        if l_best is None or val > l_best:
            l_best, l_src = val, e.event_id

    ir_best, ir_src, ir_n = 0.0, None, 0
    for e in evs:
        if e.type != IR_TYPE:
            continue
        ir_n += 1
        if e.irreversibility is None:
            continue
        if e.irreversibility > ir_best:
            ir_best, ir_src = float(e.irreversibility), e.event_id

    return MonthlyLIR(
        month=month, l=round(l_best if l_best is not None else 0.0, 6),
        l_source_event=l_src,
        l_events_seen=l_n, l_events_incomplete=tuple(l_incomplete),
        ir=round(ir_best, 6), ir_source_event=ir_src, ir_events_seen=ir_n,
    )


def compute_rri_raw(sp: float, l: float, ir: float) -> float:
    """RRI_raw = SP × L × (1 + IR). Skaalaamaton."""
    for name, v, hi in (("SP", sp, 300.0), ("L", l, 1.0), ("IR", ir, 1.0)):
        if v is None or not isinstance(v, (int, float)) or isinstance(v, bool):
            raise RRIError(f"{name}: oltava luku, oli {v!r}")
        if not (0.0 <= float(v) <= hi):
            raise RRIError(f"{name}: arvon oltava 0–{hi:g}, oli {v}")
    return round(float(sp) * float(l) * (1.0 + float(ir)), 6)


def scale_rri(raw_by_month: dict[str, float], method: str,
              baseline_max: float | None = None) -> dict[str, float]:
    """RRI_raw -> 0–100 havaittuun maksimiin.

    method:
      expanding    max vain kuukauteen N asti nähdyistä — PRE
      baseline     ennalta lukittu max, annettava eksplisiittisesti — PRE
      full-window  koko ikkunan max — VAIN FULL

    Sama lukko kuin scaler.py:ssä: expanding ei katso eteenpäin, ja
    full-window on kielletty PRE-tilassa. Degeneroitunut tapaus
    (max == 0) palauttaa 0 — ei 50 eikä 100.
    """
    months = sorted(raw_by_month)
    out: dict[str, float] = {}

    if method == "baseline":
        if baseline_max is None or baseline_max <= 0:
            raise RRIError("baseline vaatii positiivisen baseline_max-arvon "
                           "— ennalta lukittu raja on valinta, ei oletus")
        return {m: round(min(100.0, raw_by_month[m] / baseline_max * 100.0), 4)
                for m in months}

    if method == "expanding":
        for i, m in enumerate(months):
            hi = max(raw_by_month[x] for x in months[: i + 1])
            out[m] = 0.0 if hi <= 0 else round(min(100.0, raw_by_month[m] / hi * 100.0), 4)
        return out

    if method == "full-window":
        hi = max(raw_by_month.values()) if raw_by_month else 0.0
        return {m: (0.0 if hi <= 0 else round(raw_by_month[m] / hi * 100.0, 4))
                for m in months}

    raise RRIError(f"tuntematon skaalausmenetelmä: {method!r}")
