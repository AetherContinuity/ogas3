"""OGAS3 — Extractor: lausunnon rakenteen luenta.

Tämä EI ole kielimalliluokitin. Se oli alkuperäinen suunnitelma, ja se
osoittautui vääräksi kokeessa 9.9.2026.

LÖYTÖ: Lausuntopalvelun lausunto on LOMAKE, ei essee.
------------------------------------------------------------------
Hankkeella on N kysymystä, tyypillisesti yksi per luonnoksen luku.
Kukin kysymys on pari: valintakenttä `(strategian luku X)` ja sitä
seuraava vapaa tekstikenttä `Avoin vastaus ...`. Lopussa on yleinen
kenttä `Muuta kommentoitavaa`.

Mihin kysymyksiin vastattiin, ON kohdistumisen mittari. Sitä ei tarvitse
päätellä tekstistä — se on rakenteessa.

Viisi lausuntoa TEM005:00/2025:sta (energia- ja ilmastostrategia):

    rooli          luvut   merkkejä  kohdistuu
    etujärjestö     0/12       1222  vain yleinen kenttä
    toimija        10/10       5827  ruotsinkielinen lomake
    kunta           1/12       1869  luku 3 (vaikutusarviot)
    viranomainen    0/12       1790  vain yleinen kenttä
    tutkija        12/12      17494  kaikki luvut 2.2–2.12

    HUOM: `toimija` luettiin ENSIN tyhjäksi lausunnoksi (0/0, 0 merkkiä)
    ja se raportoitiin havaintona. VÄÄRIN — lomake oli ehjä,
    jäsennin oli yksikielinen. Ks. SECTION-regexin kommentti.

MITÄ TÄSTÄ SEURAA
-----------------
1. `targeting` luetaan lomakkeesta. Deterministinen, toistettava,
   ei kielimallia.

2. `intensity` EI SKAALAUDU KATTAVUUDELLA. Ilmastopaneelin 12/12 ei
   ole vahvempaa vaikuttamista vaan eri rooli: se on lakisääteinen
   asiantuntijaelin joka lausuu kokonaisuudesta. Jos intensity
   skaalattaisiin kattavuudella, se saisi automaattisesti korkeimman
   arvon — ja se olisi sama virhe kuin `impact_weight`-kaavassa:
   MÄÄRÄ EI OLE VOIMAKKUUS.

   ROE määrittelee intensityn TOIMIJAN TYYPIN kautta (0.20 yksittäinen,
   0.40 organisaatio, 0.70 useiden yhteinen, 1.00 enemmistön aloite).
   Se tulee actor_role:sta, ei tekstistä.

3. TYHJÄ LAUSUNTO ei ole intensity 0.40 vaan EI KANTAA LAINKAAN.
   HUOM: tyhjä tulos on erotettava JÄSENTIMEN VIASTA. `is_empty` ja
   `parse_confidence: low` ovat eri asioita, ja ero on todennettu:
   ruotsinkielinen lausunto näytti tyhjältä kunnes jäsennin korjattiin.
   Se on kirjattu, laskettu ja näkyy lausuntomäärässä — mutta siinä ei
   ole sisältöä. Ilman omaa merkintää se tuottaisi vaikuttamista jota
   ei tapahtunut. Sama vikaluokka kuin muut tässä järjestelmässä:
   olemassa oleva tietue, tyhjä sisältö, näyttää havainnolta.

4. Kielimallia tarvitaan enää YHTEEN kysymykseen: onko kanta puolesta
   vai vastaan, ja mitä se vaatii. Kaikki muu on rakenteessa.
   Sitä EI ole toteutettu tässä.

RAJOITE: LOMAKE VAIHTELEE HANKKEITTAIN
--------------------------------------
`(strategian luku X)` on TEM005:n oma muoto. Toisilla hankkeilla
kysymykset on otsikoitu toisin. Jäsennin tunnistaa yleisen
`otsikko → Avoin vastaus` -parin ja poimii luvun jos se on
otsikossa — muttei oleta sitä.

Jos hankkeen lomake ei jäsenny, tulos on `questions: []` ja
`parse_confidence: "low"`. Se EI ole sama kuin "ei vastattu mihinkään".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# LOMAKE ON KAKSIKIELINEN — havaittu 9.9.2026.
#
# Sama lausuntokierros tuottaa suomen- JA ruotsinkielisiä lomakkeita.
# Kristinestads näringslivscentral vastasi ruotsiksi, ja ensimmäinen
# jäsennin antoi sille `0/0` ja `parse_confidence: low`. Se OLISI
# luettu "lomake ei jäsentynyt" — mutta lomake oli ehjä, jäsennin oli
# yksikielinen.
#
# Muoto eroaa myös rakenteellisesti: suomeksi "(strategian luku 2.2)",
# ruotsiksi "(kapitel 2.2 i strategin)" — numero on ERI KOHDASSA
# sulkeiden sisällä. Ja numerossa voi olla välilyönti: "kapitel 2. 9".
SECTION = re.compile(
    r'\((?:strategian\s+)?(?:luku|kohta|kappale)\s+([\d.\s]+?)\)'      # fi
    r'|\((?:kapitel|avsnitt|punkt)\s+([\d.\s]+?)(?:\s+i\s+strategin)?\)',  # sv
    re.I)

# Vapaa tekstikenttä. Muoto vaihtelee kielen ja hankkeen mukaan.
FREE = re.compile(
    r'^(avoin vastaus|vapaa kommentti|vapaat kommentit|perustelut'
    r'|fritt svar|fria kommentarer|motivering)\b', re.I)

# Yleinen loppukenttä.
GENERAL = re.compile(
    r'^(muuta kommentoitavaa|muut huomiot|lopuksi'
    r'|övriga kommentarer|övrigt|annat att kommentera)\b', re.I)

# Sivunumerointi ja alatunniste, ei sisältöä.
NOISE = re.compile(r'Lausuntopalvelu\.fi|^\d+/\d+$')

# Tyhjä vastaus lomakkeessa.
EMPTY = {"-", "–", "—", ""}


@dataclass
class Answer:
    section: str | None          # "2.2" tai None (yleinen kenttä)
    chars: int
    text: str


@dataclass
class StatementForm:
    answers: list[Answer] = field(default_factory=list)
    n_questions_seen: int = 0
    parse_confidence: str = "high"   # high | low

    @property
    def sections_answered(self) -> list[str]:
        return sorted(
            {a.section for a in self.answers if a.section},
            key=lambda s: [int(x) for x in s.split(".")])

    @property
    def total_chars(self) -> int:
        return sum(a.chars for a in self.answers)

    @property
    def is_empty(self) -> bool:
        """Lausunto ilman sisältöä.

        EI sama kuin 'ei kantaa mitään lukua kohtaan'. Tyhjä lausunto
        on tietue jossa ei ole tekstiä lainkaan — se on kirjattu,
        laskettu ja näkyy lausuntomäärässä, muttei sisällä kantaa.
        """
        return self.total_chars == 0

    @property
    def general_only(self) -> bool:
        """Vastattu vain yleiseen kenttään, ei yhteenkään lukuun."""
        return (not self.is_empty) and not self.sections_answered


def parse_form(text: str) -> StatementForm:
    """Jäsentää Lausuntopalvelun lomakkeen. Ei tulkitse sisältöä."""
    lines = [l.rstrip() for l in text.split("\n")]

    marks: list[tuple[int, str, str | None]] = []
    for i, l in enumerate(lines):
        s = l.strip()
        if not s or NOISE.search(s):
            continue
        if l.startswith("  "):          # sisennetty = vastaus, ei otsikko
            continue
        if FREE.match(s):
            marks.append((i, "free", None))
        elif GENERAL.match(s):
            marks.append((i, "general", None))
        else:
            m = SECTION.search(s)
            if m:
                # Kaksi ryhmää: fi ja sv. Vain toinen osuu.
                num = (m.group(1) or m.group(2) or "").replace(" ", "")
                marks.append((i, "section", num))

    form = StatementForm()
    form.n_questions_seen = sum(1 for _, k, _ in marks if k == "section")

    # Lomake ei jäsentynyt: ei yhtään tunnistettua kenttää.
    # Se EI tarkoita ettei vastattu mihinkään.
    if not marks:
        form.parse_confidence = "low"
        return form

    current: str | None = None
    for k, (i, kind, num) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        body = " ".join(
            x.strip() for x in lines[i + 1:end]
            if x.startswith("  ") and x.strip() and not NOISE.search(x))
        body = re.sub(r"\s+", " ", body).strip()

        if kind == "section":
            current = num
            key = num
        elif kind == "free":
            # Vapaa kenttä kuuluu EDELTÄVÄLLE luvulle jos sellainen on.
            key = current
            current = None            # kulutettu — ei liitetä kahdesti
        else:
            key = None                # yleinen kenttä

        if body and body not in EMPTY:
            form.answers.append(Answer(section=key, chars=len(body), text=body))

    return form


def roe_from_form(form: StatementForm, actor_role: str | None,
                  is_joint: bool = False) -> dict[str, Any]:
    """Muodostaa ROE-arvot lomakkeesta ja roolista.

    EI kutsu kielimallia. `stance` (puolesta/vastaan) jää None:ksi —
    se on ainoa kohta jossa kielimallia tarvittaisiin, eikä sitä ole
    toteutettu.
    """
    # ── policy_proximity ────────────────────────────────────────────
    # Lausuntomenettely ON määritelmän mukaan 0.40. Ei arvioida.
    proximity = 0.40

    # ── intensity ───────────────────────────────────────────────────
    # ROE:n asteikko on TOIMIJAN TYYPIN mukainen. EI kattavuuden.
    if form.is_empty:
        intensity = None            # ei kantaa — ks. is_empty
        intensity_note = ("TYHJÄ LAUSUNTO: tietue on olemassa muttei sisältöä. "
                          "EI ole intensity 0.40. Laskeutuu lausuntomäärään "
                          "mutta ei vaikuttamiseen.")
    elif is_joint:
        intensity = 0.70
        intensity_note = "useiden toimijoiden yhteinen lausunto"
    elif actor_role == "yksityishenkilo":
        intensity = 0.20
        intensity_note = "yksittäinen toimija"
    elif actor_role is None:
        intensity = None
        intensity_note = ("actor_role tuntematon — intensity ei ole "
                          "johdettavissa. EI oleteta 0.40.")
    else:
        intensity = 0.40
        intensity_note = f"organisaation kannanotto (rooli {actor_role})"

    # ── targeting ───────────────────────────────────────────────────
    # LUETAAN LOMAKKEESTA. Ei päätellä tekstistä.
    secs = form.sections_answered
    if form.parse_confidence == "low":
        targeting = None
        t_note = ("lomake ei jäsentynyt — targeting EI ole luettavissa. "
                  "Tämä on eri asia kuin 'ei vastattu mihinkään'.")
    elif form.is_empty:
        targeting = None
        t_note = "tyhjä lausunto, ei kohdetta"
    elif secs:
        targeting = None            # numeroarvoa EI keksitä
        t_note = (f"kohdistuu lukuihin {', '.join(secs)} "
                  f"({len(secs)}/{form.n_questions_seen} kysymyksestä). "
                  "Numeroarvo vaatii ROE-päätöksen siitä, miten kattavuus "
                  "kartoittuu asteikolle — sitä EI ole tehty.")
    else:
        targeting = None
        t_note = ("vastattu vain yleiseen kenttään, ei yhteenkään lukuun. "
                  "Voi tarkoittaa laajaa kantaa TAI kantaa siihen mitä "
                  "luonnoksesta PUUTTUU — jälkimmäistä ROE:n asteikko ei kata.")

    return {
        "intensity": intensity,
        "_intensity_note": intensity_note,
        "targeting": targeting,
        "_targeting_note": t_note,
        "policy_proximity": proximity,
        "_policy_proximity_note": "lausuntomenettely = 0.40 määritelmän mukaan",
        "uptake": None,
        "_uptake_note": ("MÄÄRITTÄMÄTÖN, ei nolla. Lausunto kirjoitetaan ENNEN "
                         "päätöstä eikä voi todistaa uptakea eikä sen "
                         "puuttumista. Mitattavissa vain täysistunnon "
                         "äänestyksestä."),
        "stance": None,
        "_stance_note": ("puolesta/vastaan vaatii kielimallin. EI TOTEUTETTU. "
                         "Se on ainoa suure jota rakenteesta ei saa."),
        # Rakenteesta luetut faktat, ei arvioita.
        "form": {
            "sections_answered": secs,
            "n_questions": form.n_questions_seen,
            "total_chars": form.total_chars,
            "is_empty": form.is_empty,
            "general_only": form.general_only,
            "parse_confidence": form.parse_confidence,
        },
    }
