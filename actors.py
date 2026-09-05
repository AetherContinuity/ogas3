"""OGAS3 — laatijan roolin luokittelu ja alias-taulukko.

`actor_role` on erilainen kuin muut kartoitukset tässä järjestelmässä.
`type` tulee Hankeikkunan `tyyppi`-kentästä, `occurred_at`
`laatimispaiva`-kentästä. Ne luetaan lähteestä. **Roolia ei ole
missään kentässä** — se on pääteltävä.

Siksi jokainen rooli saa `role_source`-merkinnän, ja se on pakollinen:

    "saanto"      pääte tunnistettiin mekaanisesti (ry, virasto, Oyj)
    "poikkeus"    nimetty päätös, perustelu tässä tiedostossa
    "extractor"   kielimalli tunnisti (esim. henkilönimi)
    None          ei ratkennut — EI arvata

Sama periaate kuin `actor_source: "laatija" | "nimeke"`. Ilman tätä ei
näy jälkikäteen mikä rooli on mekaaninen ja mikä pääteltyä.

ROOLIT (ROE v0.3 + yksi lisäys)
    minister · kansanedustaja · puolue · hallitus · etujarjesto
    tutkija · viranomainen · kunta · toimija
    yksityishenkilo   ← LISÄTTY: 430 laatijaa 752:sta esiintyy kerran,
                        ja osa niistä on yksityishenkilöitä. Suurin
                        yksittäinen ryhmä, eikä sitä ollut ROE:ssa.
"""

from __future__ import annotations

import re

ROLES = ("minister", "kansanedustaja", "puolue", "hallitus", "etujarjesto",
         "tutkija", "viranomainen", "kunta", "toimija", "yksityishenkilo")


# ── Nimetyt poikkeukset ──────────────────────────────────────────────
# Peruste on INTRESSI, ei oikeudellinen muoto. Sama periaate kuin
# muualla: mitataan mitä tapahtuu, ei mitä paperissa lukee.
EXCEPTIONS: dict[str, tuple[str, str]] = {
    "Suomen Kuntaliitto ry": (
        "etujarjesto",
        "Ajaa kuntien intressiä, ja kunnat ovat energiakysymyksessä "
        "OSAPUOLI: ne kaavoittavat, myyvät tontteja ja saavat "
        "kiinteistöveron. Lausunto on edunvalvontaa, ei hallinnon "
        "lausumista. Oikeudellinen muoto (ry) osuu tässä yhteen "
        "intressin kanssa, mutta peruste on intressi."),
    "Saamelaiskäräjät": (
        "etujarjesto",
        "Elinkeinointressi: poroelinkeino kärsii tuulivoimasta. "
        "HUOM: itsehallintoelin jolla on LAKISÄÄTEINEN "
        "neuvotteluvelvoite — sen lausunnon asema on eri kuin "
        "toimialaliiton. policy_proximity voi olla yli 0.40 ja se on "
        "tarkistettava tapauskohtaisesti, EI sääntönä."),
    "Fingrid Oyj": (
        "toimija",
        "Kantaverkkoyhtiö: siirto on sen alaa, tuotantoon se ei "
        "vaikuta. Lausunto tuotantoa koskevaan sääntelyyn on siis "
        "kannanotto, ei toimivallan käyttöä. Liittymisehdot ovat sen "
        "omaa aluetta — silloin lausunto ajaa omaa etua kuten "
        "yrityksellä. Ei viranomainen vaan monopoliyhtiö jolla on "
        "velvoitteita."),
}


# ── Alias-taulukko: MITATTU, ei pääteltyä ────────────────────────────
# Sama kuri kuin (n)-päätteessä, eri työkalu koska ongelma on eri.
# (n) oli MUOTOILU (sama toimija, eri kirjoitusasu) -> regex kelpasi.
# Tämä on ORGANISAATIOHIERARKIA ja kirjoitusasuvaihtelu -> yleinen
# sääntö abstrahoisi väärään suuntaan, sama ansa kuin YSO-hierarkiassa.
# Siksi luettelo, ei kaava. Jokainen rivi on todennettu aineistosta.
ALIASES: dict[str, str] = {
    # Sama organisaatio, eri kirjoitusasu
    "Elinkeinoelämän Keskusliitto EK": "Elinkeinoelämän keskusliitto EK",
    "Kilpailu- ja kuluttajavirasto KKV": "Kilpailu- ja kuluttajavirasto",
    "kilpailu- ja kuluttajavirasto*": "Kilpailu- ja kuluttajavirasto",
    "Luonnonvarakeskus": "Luonnonvarakeskus (Luke)",
    "Maa- ja metsätaloustuottajain Keskusliitto MTK r.y.":
        "Maa- ja metsätaloustuottajain Keskusliitto MTK ry",
    "Suomen Sähkönkäyttäjät ry (ELFi)": "Suomen Sähkönkäyttäjät ry",
    "Svenska lantbruksproducenternas centralförbund SLC r.f.":
        "Svenska lantbruksproducenternas centralförbund SLC rf",
    "Suomen ympäristökeskus SYKE": "Suomen ympäristökeskus (Syke)",

    # ORGANISAATIOHIERARKIA: yksikkö organisaation sisällä.
    # Tämä on eri luokka kuin kirjoitusasu — ja se oli aineiston
    # suurin yksittäinen ryhmittelyvirhe: SYKE näytti kolmelta eri
    # toimijalta (29 + 15 + 5 = 49) ja putosi kärkilistalla
    # kolmanneksi vaikka on toinen.
    "Suomen ympäristökeskuksen kv. YVA- ja SOVA -asiat":
        "Suomen ympäristökeskus (Syke)",
}

# EI YHDISTETÄ — mitattu ja tarkoituksella jätetty erilleen.
# Nämä näyttävät alias-ehdokkailta mutta ovat eri toimijoita.
NOT_ALIASES = {
    "Suomen luonnonsuojeluliitto Etelä-Karjala ry":
        "Piirijärjestö, ei sama toimija kuin liiton keskusjärjestö. "
        "Alueellisella yhdistyksellä on oma kanta ja oma intressi.",
    "Rakennustuoteteollisuus RTT ry - Betoniteollisuus ry:n harkkojaos":
        "Toimialajaos, jolla on kapeampi ja mahdollisesti eriävä "
        "intressi kuin kattojärjestöllä.",
}

# PIILOMERKKI: "Teknologian tutkimuskeskus VTT Oy" esiintyy kahdessa
# muodossa, joiden ero on U+200B (zero-width space) nimen lopussa.
# Sitä ei näe silmällä eikä se erotu tulosteessa. normalize() poistaa
# nollan levyiset merkit — ei alias-taulukolla, koska se ei ole
# kirjoitusasuvalinta vaan näkymätön roska.
_ZERO_WIDTH = re.compile(r'[\u200b\u200c\u200d\ufeff\u00ad]')
_INDEX_SUFFIX = re.compile(r'\s*\(\d+\)\s*$')


def canonical(name: str | None) -> str | None:
    """Kanoninen nimi ryhmittelyä varten: normalisointi + alias."""
    if not name:
        return None
    s = _ZERO_WIDTH.sub("", name)
    s = _INDEX_SUFFIX.sub("", s).strip()
    s = re.sub(r'\s{2,}', " ", s)
    return ALIASES.get(s, s) or None


# ── Sääntöpohjainen rooli ────────────────────────────────────────────
# KORJATTU: suomessa nämä ovat YHDYSSANOJA, joten sanaraja (\b) ei
# osu — `\bvirasto` ei tunnista sanaa "Energiavirasto". Pääte on
# oikea ankkuri: `virasto$`. Ensimmäinen versio jätti 204 nimeä
# ratkaisematta pääosin tästä syystä.
# ANKKURI: `X\b`, ei `X$` eikä `\bX`.
#   `\bvirasto`  ei osu "Energiavirasto" (yhdyssana, ei sanarajaa ennen)
#   `virasto$`   ei osu "Turvallisuus- ja kemikaalivirasto TUKES"
#                (nimen perässä lyhenne — 144 nimeä jäi tästä auki)
#   `virasto\b`  osuu molempiin
# Yhdyssanapäätteille sanaraja JÄLKEEN, erillisille sanoille (ry, Oyj)
# sanaraja molemmin puolin.
# role_confidence: onko pääte YKSIKÄSITTEINEN vai monitulkintainen.
#
# `role_source: "saanto"` kertoo että pääte tunnistettiin mekaanisesti.
# Se EI kerro onko pääte luotettava. "Energiavirasto" ON virasto;
# "Suomen ympäristökeskus" on sekä viranomainen ETTÄ tutkimuslaitos,
# eikä `keskus` ratkaise kumpi. Sääntö antaa molemmille saman arvon ja
# saman lähdemerkinnän — ilman tätä kenttää ero katoaa.
#
# Sama erottelu kuin actor_source: "laatija" | "nimeke": molemmat
# tuottavat nimen, toinen on luettu ja toinen johdettu.
#
#   0.9   pääte on yksikäsitteinen (ministeriö, ry, Oyj, kaupunki)
#   0.5   pääte osuu mutta rooli on tulkinnanvarainen
#
# Arvo EI ole ROE:n classification-confidence — se koskee Extractorin
# luokitusta. Tämä koskee sääntöä, ja se on eri asia.

_RULES: list[tuple[re.Pattern, str, float]] = [
    (re.compile(r'ministeriö\b', re.I), "viranomainen", 0.9),
    # keskusliitto ENNEN keskus-sääntöä: "Elinkeinoelämän keskusliitto EK"
    # ei ole viranomainen. Yhdyssanassa ei ole sanarajaa keskus|liitto
    # välissä, joten keskus\b ei osuisi — mutta järjestys on silti
    # kirjattava, koska se on merkityksellinen jos sääntöjä lisätään.
    (re.compile(r'keskusliitto\b', re.I), "etujarjesto", 0.9),
    # ELY-keskus ja AVI ENNEN yleistä keskus-sääntöä: niillä on
    # yksikäsitteinen rooli, eikä niitä pidä merkitä monitulkintaisiksi.
    # Järjestysvirhe löytyi mittaamalla: viisi ELY-keskusta sai 0.5.
    (re.compile(r'\b(ely-keskus|aluehallintovirasto|avi)\b', re.I), "viranomainen", 0.9),

    # MONITULKINTAINEN: `laitos` ja `keskus` osuvat sekä hallinto-
    # virastoihin (Energiavirasto, Verohallinto) että VALTION
    # TUTKIMUSLAITOKSIIN (SYKE 49, Luke 8, GTK, Ilmatieteen laitos,
    # THL, VATT). Jälkimmäiset ovat sekä `viranomainen` että `tutkija`,
    # ja ero on aito eikä nimellinen. Sääntö antaa `viranomainen` —
    # se on OSA vastausta, ei koko vastaus. role_confidence 0.5
    # säilyttää sen tiedon; poikkeus voi kumota sen myöhemmin.
    # `hallinto\b(?!-)`: osuu "Verohallinto" muttei "hallinto-oikeus".
    # Tuomioistuimet ovat tarkoituksella avoin kysymys, eikä yleinen
    # hallinto-pääte saa luokitella niitä viranomaisiksi.
    (re.compile(r'(virasto|lautakunta|hallitus|hallinto\b(?!-))\b(?!.*\b(ry|oyj|oy)\b)', re.I),
     "viranomainen", 0.9),
    (re.compile(r'(laitos|keskus)\b(?!.*\b(ry|oyj|oy)\b)', re.I),
     "viranomainen", 0.5),
    (re.compile(r'\b(ry|r\.y\.|rf|r\.f\.)\b', re.I), "etujarjesto", 0.9),
    (re.compile(r'(yhdistys|järjestö|kauppakamari)\b', re.I), "etujarjesto", 0.9),
    (re.compile(r'\b(oyj|oy|ab|abp|ltd|plc)\b', re.I), "toimija", 0.9),
    # kunta\b on turvallinen: "Satakuntaliitto" sisältää "kunta" mutta
    # ilman sanarajaa sen jälkeen, joten se EI osu — ja maakuntaliitot
    # jäävät tarkoituksella auki.
    (re.compile(r'(kaupunki|kunta|kaupunginhallitus|kunnanhallitus)\b', re.I), "kunta", 0.9),
    (re.compile(r'(yliopisto|korkeakoulu|ammattikorkeakoulu)\b', re.I), "tutkija", 0.9),
    (re.compile(r'paneeli\b', re.I), "tutkija", 0.9),
]

# TARKOITUKSELLA RATKAISEMATTA — neljä avointa roolikysymystä, jotka
# vaativat päätöksen eivätkä sääntöä. Näistä EI arvata:
#
#   tuomioistuimet        Korkein hallinto-oikeus 10, Helsingin ha-o 9,
#                         Markkinaoikeus, Vaasan/Turun ha-o.
#                         ROE:ssa ei ole roolia. `viranomainen` on
#                         lähin mutta väärä: tuomioistuin ei ole
#                         hallintoviranomainen.
#
#   maakuntaliitot        Uudenmaan liitto 10, Satakuntaliitto 8.
#                         Kuntien omistamia lakisääteisiä elimiä.
#                         Lähinnä `kunta`, mutta "liitto"-sääntö
#                         luokittelisi ne etujärjestöiksi — siksi
#                         `liitto` EI ole säännöissä lainkaan.
#
#   valtion tutkimus-     SYKE 49, Luke 8, GTK, Ilmatieteen laitos,
#   laitokset             THL, VATT. Sekä `viranomainen` että
#                         `tutkija`, ja ero on aito. `keskus\b`-sääntö
#                         osuu näihin viranomaisena — se on tietoinen
#                         valinta jonka voi kumota poikkeuksella.
#
#   yksityishenkilöt      430 laatijaa 752:sta esiintyy kerran.
#                         Henkilönimeä EI voi tunnistaa säännöllä:
#                         "Erkki Hurtig" on nimi, "Vaattovaara Mari"
#                         on nimi, "Keva" ei ole. Tämä on ainoa kohta
#                         jossa Extractor on säännön veroinen — malli
#                         tunnistaa henkilönimen, regex ei.
#                         role_source olisi silloin "extractor".


def actor_role(name: str | None) -> tuple[str | None, str | None, float | None, str | None]:
    """Palauttaa (rooli, role_source, role_confidence, perustelu).

    Ei koskaan arvaa: ratkaisemattomat palauttavat (None, None, None, syy).
    Sama periaate kuin muualla — merkitty puuttuva on parempi kuin
    väärä arvo.

    role_confidence erottaa yksikäsitteisen päätteen tulkinnanvaraisesta.
    Ilman sitä `role_source: "saanto"` väittäisi enemmän kuin on:
    "Energiavirasto" ja "Suomen ympäristökeskus" saisivat saman
    merkinnän, vaikka ensimmäinen on varma ja toinen ei.
    """
    c = canonical(name)
    if not c:
        return None, None, None, "nimi puuttuu"

    if c in EXCEPTIONS:
        role, reason = EXCEPTIONS[c]
        return role, "poikkeus", 0.9, reason

    for pat, role, conf in _RULES:
        if pat.search(c):
            note = "" if conf >= 0.9 else (
                " — MONITULKINTAINEN: pääte osuu myös valtion "
                "tutkimuslaitoksiin, jotka ovat sekä viranomainen että "
                "tutkija. Osa vastausta, ei koko vastaus.")
            return role, "saanto", conf, f"pääte tunnistettu: /{pat.pattern}/{note}"

    return None, None, None, ("sääntö ei tunnista — jätetään Extractorille "
                              "tai käsin ratkaistavaksi. EI arvata.")
