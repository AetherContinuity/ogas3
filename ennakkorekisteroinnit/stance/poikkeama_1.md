# Stance — poikkeama 1: `parse_confidence low` ohitusperusteena

**Kirjattu:** 2026-11-12, ennen käsikoodausta ja ennen yhtäkään mallin ajoa.
**Koskee:** kehikko.md, osio Otos → Poissuljettu.
**Lukittu `kehikko.md`** on ennallaan.

## Ristiriita kehikossa

Kehikon yksikkötaulukko sanoo, että `yksi_kentta` ja `vapaa_asiakirja`
luokitellaan kokonaisena tekstinä. Otos-osio sulkee pois kaikki, joilla
`parse_confidence: low`. Extractor antaa näille kahdelle tyypille **aina**
`low`, koska niissä ei ole kysymyksiä (`n_questions_seen == 0` →
`low`, extractor.py). `low` tarkoittaa extractorissa "targeting ei ole
luettavissa", ei "teksti ei jäsentynyt". Kirjaimellisesti luettuna otos
sulkee pois juuri ne tyypit, jotka yksikkötaulukko ottaa mukaan.

Virhe on kehikon laatijan (Claude), ei aineiston.

## Ensimmäinen ajo (kirjaimellinen sääntö) — hylätty

- perusjoukko 5 871 lausuntoa, 375 hanketta
- 20 hyväksyttyä vaati 319 läpikäyntiä; **299 ohitettiin**, joista 170
  `parse_confidence low`
- 17/20 kahdesta hankkeesta (YM069:00/2024: 10, YM012:00/2024: 6 +
  TEM035:00/2023: 3), kaikki vuodelta 2026, ei yhtään `yksi_kentta`- tai
  `vapaa_asiakirja`-lausuntoa

Otos olisi edustanut vain Lausuntopalvelun pykälälomakkeita kahdesta
hankkeesta. Tuloksia ei käytetty, eikä tekstejä luettu.

## Korjaus

`parse_confidence: low` on ohitusperuste vain, kun `form_type` on
`kysymyksittain` tai `pykalittain` (kysymyslomake jäsentyi osittain).
`yksi_kentta` ja `vapaa_asiakirja` otetaan mukaan yksikkötaulukon mukaan.

Kaikki muu ennallaan: perusjoukko, sha256(uuid)-järjestys, N = 20.

## Toinen ajo (korjattu sääntö) — käytössä

- 20 hyväksyttyä, 17 ohitettua (tyhjä teksti 8, is_empty 6, ei-PDF 3)
- 18 hanketta, laatimispäivät 2021–2026
- `yksi_kentta` 17, `pykalittain` 2, `vapaa_asiakirja` 1
- **31 yksikköä**, yhteensä 56 059 merkkiä

## Havaitut rajoitteet (ei korjata, raportoidaan)

1. **Yksiköitä on vähemmän kuin kehikon arvio (60–100).** Viiden luokan
   κ 31 yksiköllä on epätarkka. Tulosten yhteydessä raportoidaan κ:n
   luottamusväli (bootstrap, yksiköt). Päätössääntö sovelletaan
   pistearvoon kuten lukittu, mutta väli kertoo kuinka paljon sille voi
   antaa painoa.
2. **Perusjoukko on väljä.** Hakutermi `energia` osuu myös hankkeisiin,
   joissa energia on sivuasia (esim. ajoneuvohankinnat, verotus). Otos
   edustaa lausuntoja yleisesti, ei sähkömarkkinalakia. Stance on
   lajityypin ominaisuus, joten tämä hyväksytään.
3. **Muut kuin PDF-asiakirjat** (.doc, .docx, .rtf) ohitetaan.
   Toisessa ajossa 3 kpl.
4. **Extractor vuotaa allekirjoituskenttiä vastauksiksi.** Esim.
   yksikkö, jonka teksti on vain lausujan yhteyshenkilön nimi ja
   organisaatio. Ne jäävät otokseen sellaisinaan ja koodataan kuten
   muutkin (todennäköisesti `ei_kantaa`). Extractorin korjaus on erillinen
   asia eikä koske tätä otosta.
