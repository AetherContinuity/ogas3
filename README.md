# OGAS3 — RRI-moottori v0.1

**Ensimmäinen commit. Sisältää vain sen, mikä on todistettavissa nykyisestä
spesifikaatiosta. RRI:n laskenta on tarkoituksella lukitsematta.**

## Metodologinen ehto

> Moottori ei muuta tapahtumien sisältöä. Se ainoastaan aggregoi,
> normalisoi ja laskee.

## Mitä on lukittu

| | |
|---|---|
| `SP = D + O + S` | Johdettu esimerkistä 18,4 + 11,2 + 14,7 = 44,3 |
| `L = I × T × P × U` | Kaavan muoto tunnetaan |
| I, T, P, U ∈ [0,1] | Influence Intensity · Targeting · Policy Proximity · Uptake |

## Mitä EI ole lukittu — ja miksi koodi kieltäytyy

`compute_rri()` ja `compute_l()` nostavat `NotImplementedError`.

**RRI.** Annettu SP 44,3 · L 0,1039 · IR 0,61 · RRI 35,6 ei riitä
johtamaan kaavaa yksikäsitteisesti. `SP × L × (1+IR)` antaa 7,4.
Useita muotoja voi sovittaa neljään lukuun, ja valinta niiden välillä
olisi uuden metodologian keksimistä.

**L.** Kolme neljästä komponentista tulee luokituksesta, mutta I:n
deterministinen laskenta ei ole spesifioitu. `I = 1.0` olettaminen
muuttaisi tuloksen hiljaisesti.

**IR.** Aggregointikaava ei ole lukittu. Suunta tunnetaan
(lainsäädäntö matala → CHP-purku erittäin korkea), painotus ei.

## Neljä turvalukkoa

**1 · Schema validation.** Puuttuva tai väärän tyyppinen kenttä nostaa
`SchemaError` ja nimeää kentän. Puuttuva ja nolla ovat eri asioita ja
pysyvät erillään läpi ketjun — `impact_weight: null` kirjataan
`unweighted`-listalle eikä summata nollana.

**2 · No look-ahead.** Kolme aikaleimaa, kolme semantiikkaa:

    occurred_at   milloin tapahtui
    known_at      milloin oli ulkopuolisen havaittavissa
    retrieved_at  milloin järjestelmä haki lähteen

    PRE   suodattaa known_at    <= kuukauden loppu
    FULL  suodattaa occurred_at <= kuukauden loppu

Yhdellä aikaleimalla lukkoa ei voisi valvoa — se vain näyttäisi valvotulta.
Validaattori vaatii `occurred_at ≤ known_at ≤ retrieved_at`.

Look-aheadin toinen piilopaikka on **normalisointi**. PRE ei saa käyttää
koko aineiston min/max-arvoja. Kaksi sallittua tilaa, kumpikaan ei ole
oletus:

    expanding   rajat vain kuukauteen N asti nähdyistä kuukausista
    baseline    ennalta lukitut rajat, annettava eksplisiittisesti

`scale_full()` kieltäytyy PRE-bucketista.

**3 · FULL ei ole ennuste.** Se on diagnostinen vertailusarja. Se näkee
valmisteluhistorian, jota reaaliaikainen havaitsija ei nähnyt, joten
PRE/FULL-ero on itsessään mittaustulos.

**4 · Audit trail.** `explain_month()` palauttaa raakasummat, skaalatut
arvot, käytetyt rajat, skaalaustavan, tapahtumatunnukset, painottamattomat
tapahtumat ja todisteet hakuhetkineen.

## Todiste hakuhetkineen

`retrieved_at` on pakollinen jokaisessa todisteessa. Perustelu: vuoden 2026
aikana havaittiin kolme rajapintaa, joiden osoite tai tietomalli muuttui
saman vuoden sisällä — Hankeikkuna `/api/v1` → `/api/v2`, Suomen Pankki
`/v3/api` → `/v4`, ECB `ICP` → `HICP`. `source_url` ilman hakuhetkeä on
tarkistamaton väite parin vuoden päästä.

## Ajoympäristö

Python 3.12, **ei riippuvuuksia** — pelkkä vakiokirjasto. Jokainen
riippuvuus on ylläpidettävä ja jokainen versionosto on mahdollinen
hiljainen muutos.

Moottori ei aja selaimessa eikä Cloudflare-workerissa, toisin kuin muu
ACI-pino. Se ajetaan **GitHub Actionsissa kerran kuussa** ja tulos
commitoidaan hakemistoon `snapshots/`.

Syy on PRE-sarjan luotettavuus. Sarja väittää mittaavansa sitä, mitä
olisi voitu tietää kyseisenä kuukautena. Se väite on todennettavissa vain
jos ajohetki on kolmannen osapuolen kirjaama — paikallisessa ajossa
`retrieved_at` on ajajan koneen kello, CI:ssä se on ajolokissa yhdessä
commit-SHA:n kanssa.

Sivutuote: **commitoitu `snapshots/` ON aikasarja.** Erillistä
tietokantaa ei tarvita.

## Nolla-piste

Ensimmäinen kaappaus ajettiin 5.9.2026, **ennen kuin RRI-kaava on
lukittu**. Se on tarkoituksellista: jos ensimmäinen sarja tuotettaisiin
taannehtivasti kaavan valmistuttua, ajohetkellä tiedettäisiin jo mitä
tapahtui ja look-ahead olisi rakenteessa eikä koodissa.

Kaappaus jäädyttää TODISTEEN ja jättää LUOKITUKSEN myöhemmäksi:

    kaapataan     tapahtumat, kolme aikaleimaa, todisteet, anomaliat
    ei kaapata    type (D/O/S), impact_weight, intensity
    ei lasketa    SP, L, IR, RRI

Lisäksi `expanding`-skaalaus vaatii kuukausia takanaan — yhdellä
kuukaudella se antaa nollan. Sarjan on siis alettava riippumatta siitä,
milloin kaava valmistuu.

**2026-09:** 1 116 tapahtumaa, 3 anomaliaa, 2 lähdettä.

| Kysely | n | molemmat aikaleimat | mediaaniviive |
|---|---|---|---|
| HI · EDUSKUNTAKASITTELY | 32 | 32 | 20 vrk |
| HI · LAUSUNTOMENETTELY | 88 | 87 | 7 vrk |
| HI · PERUSVALMISTELU | 21 | 21 | 15 vrk |
| HI · VALTIONEUVOSTON_PAATOKSENTEKO | 43 | 43 | 19 vrk |
| Eduskunta (932 tapahtumaa) | — | — | 0 vrk |

Viive kasvaa valmistelun edetessä: lausuntomenettelyssä 7 vrk,
eduskuntakäsittelyssä 20. Eduskunta on nolla, koska istunto on julkinen
tapahtuma — ainoa lähde, jossa `occurred_at == known_at` on perusteltu
eikä oletus.

## Päätösketjun loppupää (`decision_chain.py`)

Kuukausikaappaus kattaa ketjun alusta loppuun:

```
Hankeikkuna   valmistelu, lausunnot, LAIN_VAHVISTAMINEN,
              PAATTYNYT (vain ikkunan ajalta muokatut)       oma raportti
Eduskunta     käsittelyvaiheet                                virallinen
Eduskunta     täysistuntoäänestykset (?votes=)                virallinen
Finlex        edellisenä kuukautena julkaistut säädökset      virallinen
```

Liitosavain on HE-numero: Hankeikkunan `heTiedot.heNumerot`, Finlexin
esityöt-osio (`preliminaryWork`) ja äänestysten `eduskuntatunnus`.
Snapshotin `chains`-kenttä kokoaa HE-kohtaisesti mitä ketjusta on
havaittu. Lopputulos on vahvin havaittu tila: `säädös vahvistettu`,
`eduskunta päättänyt` (vastaus annettu — voi olla hylkäävä), `äänestetty`,
`eduskunnassa` tai `määrittämätön` — ei koskaan "hylätty" pelkän puuttuvan
tiedon perusteella. Finlex-ikkuna on yksi kuukausi, joten vanhemmat lait
tunnistetaan Eduskunnan vastauksesta, eivät säädöksestä.

| Lähde | occurred_at | known_at |
|---|---|---|
| Finlex | dateIssued (vahvistus) | datePublished |
| Äänestys | aanestysalkuaika | sama — täysistunto on julkinen |

Ansat:

- **Äänestysreitin 404 ei ole "ei äänestetty".** Hyväksyminen ilman
  äänestystä, keskeneräinen käsittely ja olematon HE näyttävät samalta.
  Tila kirjataan `ei tietuetta`.
- **Finlexin `FRBRauthor` on eduskunta myös ministeriön asetuksille.**
  Kenttää ei käytetä. Säädöslaji luetaan `finlex:typeStatute`-kentästä.
- **HE-viittaus luetaan vain esitöistä.** Leipätekstin HE-maininta voi
  koskea toisen lain esitöitä.
- **Finlexin listausrajapinta palauttaa 10 riviä kerrallaan.** Kuukausi
  haetaan siksi numerojärjestyksessä: binäärihaku ensimmäiseen
  ikkunaan osuvaan numeroon, 20 numeron marginaali taaksepäin, eteenpäin
  kunnes 15 peräkkäistä on ikkunan ulkopuolella. `max_calls` nostaa
  virheen, se ei katkaise hiljaa.
- **Hankeikkunan hakuskeemassa ei ole HE-kenttää.** HE:n hanke haetaan
  `teksti`-kentällä, joka rankkaa eikä suodata ("HE 24/2026" → 4 hanketta,
  1 oikea). Tulos suodatetaan tarkalla vertailulla `heNumerot`-kenttään
  (`resolve_hanke`). Kaappaus tekee tämän jokaiselle HE:lle, jonka hanke
  ei muuten osunut kyselyihin.
- **Säädös ei ole automaattisesti IR eikä äänestys lausunnon uptake.**
  Ne ovat syötteitä luokitukselle. `type` jää `null`.
- Äänestyksistä talletetaan ryhmä- ja hallitus/oppositio-jakaumat,
  ei kansanedustajakohtaisia rivejä.

## Vaikuttaminen (`avoimuus.py`)

Avoimuusrekisterin toimintailmoitukset (VTV, CC BY 4.0), uusin
ilmoituskausi kerran kuussa. Tapahtumaksi otetaan aihe, joka viittaa
hankkeeseen tunnuksella (`contactTopicProject.projectId` = Hankeikkunan
tunnus). Kausi 1–6/2026: 1 240 ilmoitusta, 4 819 aihetta, joista 635
hankkeisiin (308 hanketta). Vapaatekstiaiheita ei tulkita hankkeiksi.

| | |
|---|---|
| occurred_at | **yläraja**: min(kauden loppu, ilmoituspäivä) — päivää ei ilmoiteta |
| known_at | ilmoituspäivä |
| kohteet | organisaatio / osasto — ei henkilönimiä |

Näkyvyysviive on siksi alaraja (mediaani ~59 vrk, todellinen jopa puoli
vuotta pidempi). Vaikuttamisen kohteena olleet hankkeet, joita
vaihekyselyt eivät tuoneet, haetaan yhdellä tunnuslistakutsulla, jotta ne
liittyvät HE-ketjuihin (koeajossa 15 → 108 ketjua). Hankkeet ilman HE:tä
näkyvät tiivistelmässä erikseen (`vaikuttaminen.ilman_ketjua`).

**Ilmoitettu vaikuttaminen ei ole vaikutus.** Määrä kertoo ketjun
kiinnostavuudesta ilmoitusvelvollisille, ei siitä, muuttiko se mitään.
Vaikuttaminen ei muuta ketjun lopputulosta.

## YVA (`yva.py`)

Ympäristövaikutusten arvioinnin vaiheet ymparisto.fi-hankesivuilta
(aci-yva-proxy jäsentää sivun tekstistä). YVA on ainoa julkinen lähde,
jossa suuri uusi kuorma — datakeskus, teollisuus, voimalaitos — näkyy
ennen investointi- ja liittymäpäätöstä. Fingridin liittymisjono ei ole
julkinen.

| vaihe | merkitys |
|---|---|
| ohjelma_nahtavilla | menettely alkaa |
| ohjelma_lausunto | yhteysviranomaisen lausunto ohjelmasta |
| selostus_nahtavilla | arviointiselostus nähtävillä |
| taydennyspyynto | yhteysviranomaisen täydennyspyyntö (viivästys) |
| selostus_lausunto | lausunto selostuksesta = menettely päättyy (YVA-laki ennen 16.5.2017) |
| perusteltu_paatelma | menettely päättyy |

"Nähtävillä" kattaa myös "kuultavana" ja "kuulutus" (proxy 2026-10-01).
Yleisötilaisuus tunnistetaan mutta ei ole vaihe: lokissa `tunnettuja_ohitettu`.

occurred_at = known_at = kuulutettu päivä. Tulevaksi kuulutettu vaihe
ei ole tapahtuma (ohitetaan, lasketaan lokiin). Tunnistamattomat
aikataulurivit kirjataan lokiin esimerkkeineen, ei pudoteta.

Kuorma: ~790 hankesivua. Rekisteri `snapshots/yva-rekisteri.json`
muistaa tilan; joka kuu haetaan vain uudet, keskeneräiset (~240) ja yli
180 vrk sitten tarkistetut. Ensimmäinen ajo hakee kaikki (~27 min).
Koeajo 29.9.2026: 789 sivua, 532 vaihetta, 4 hakuvirhettä (haetaan
uudelleen seuraavalla kerralla), 539 sivua ilman tunnistettavaa
aikataulua (vanha sivupohja).

## Tiivistelmät käyttöliittymälle (`summary.py`)

Snapshot on todiste, noin 9 Mt kuukaudessa. Käyttöliittymä lukee
tiivistelmää, joka lasketaan Pythonissa samasta tiedostosta:

```
snapshots/YYYY-MM.summary.json   ~60 kt: ketjut, lähdekohtaiset määrät,
                                 viiveet, anomaliat, virheet
snapshots/index.json             kuukaudet + tracet (seurantalista,
                                 uusin per aihe _supersedes-ketjusta)
```

**Käyttöliittymä ei laske mitään.** Kaksi laskentaa samalla nimellä
ajautuvat erilleen (OGAS2). Tiivistelmä sitoo itsensä lähteeseensä
sha256-tiivisteellä (`source_sha256`), ja `index.json` kertoo täsmääkö
se yhä (`summary_matches_snapshot`). `rri` on `null` kunnes tapahtumia on
luokiteltu — tyhjä on rehellisempi kuin nolla.

Kuukausiajo kirjoittaa tiivistelmät. `index.yml` päivittää ne kun
`traces/`-hakemistoon lisätään trace. Käsin: `python3 summary.py`.

## Nosto seurantaan (`promote.py`)

Ketju nostetaan issue-lomakkeella (`.github/ISSUE_TEMPLATE/nosto.yml`,
monitorin "Nosta seurantaan" -linkki esitäyttää sen). `promote.yml`
käsittelee noston automaattisesti vain jos tekijä on omistaja, jäsen tai
avustaja; muut odottavat labelia `hyväksytty`.

```
seuranta/<aika>-<avain>-<käyttäjä>.json   yksi muuttumaton tiedosto per nosto
  promoted_at, promoted_by, approved_by
  he, tunnus (haetaan HE:stä jos puuttuu)
  peruste                                  nostajan teksti sellaisenaan
  state_at_promotion                       ketjun tila uusimmassa tiivistelmässä
```

Trace on aihekohtainen: ensimmäinen nosto tekee sen, kuukausiajo
(`promote.py refresh`) päivittää uuden revision. Saman ketjun uusi nosto
on uusi kirjaus, ei uusi trace.

**Seurantalista on valittu otos.** `index.json` laskee jokaiselle nostolle
`ennen_ratkaisua` nostohetken tilasta. Jälkikäteen nostettua ketjua ei
voi käyttää todisteena siitä, että asia olisi nähty ajoissa. Yleistävät
väitteet tehdään koko kaappauksesta, ei seurantalistasta.

## Luokituskerros (`classification.py`)

Snapshot jäädyttää todisteen. Luokitus (type, impact_weight,
irreversibility, llm_classification) EI kirjoiteta jäädytettyyn
tapahtumaan, vaan omaksi tietueekseen:

```
classifications/YYYY-MM.json   _schema: aci/classification/v0.1
  event_id, event_hash         sidos todisteeseen (tiiviste ilman luokituskenttiä)
  classified_at
  classifier                   kind rule|llm|human, id, version,
                               knowledge_cutoff (llm, null = tuntematon), prompt_hash (llm pakollinen)
  type, impact_weight, irreversibility, llm_classification
```

Syy: luokittelija joka tietää miten hankkeelle kävi, vie tiedon
painoihin. Aikaleimat pysyisivät puhtaina, painot eivät.

Puhtaus johdetaan, ei ilmoiteta: `horisontti <= PRE-raja + max_lag`.
PRE-raja on tapahtuman known_at-kuukauden loppu. Horisontti on
`rule`: PRE-raja · `llm`: knowledge_cutoff · `human`: classified_at.
Tuloksena CLEAN, CONTAMINATED tai UNVERIFIED. `max_lag` annetaan
kutsussa, sille ei ole oletusta.

PRE käyttää varhaisinta CLEAN-luokitusta, FULL viimeisintä. Luokittelematon
tapahtuma jää pois ja listataan, snapshotin `_anomaly`-tapahtumat
raportoidaan erikseen. Takautuvasti ihmisen luokittelema 2026-09 on
rakenteellisesti CONTAMINATED — PRE-sarjan puhdas luokitus vaatii
luokittelun samassa kuukausiajossa kuin kaappauksen.

## Rakenne

    schema.py                tapahtumaskeema, aikaleimasemantiikka
    snapshot.py              kuukausikaappaus, CI:n sisääntulopiste
    .github/workflows/       monthly-snapshot.yml, cron 1. pv klo 06 UTC
    snapshots/               commitoidut kaappaukset = aikasarja
    validator.py             turvalukko 1
    aggregator.py            turvalukko 2, kuukausibucketit, SP raakana
    scaler.py                D/O/S → 0–100, expanding | baseline | full-window
    audit.py                 turvalukko 4 + tarkoitukselliset NotImplementedError
    synthetic_events.json    45 tapahtumaa, 2 ilman painoa, viiveitä 0–51 vrk
    classification.py        luokituskerros jäädytetyn todisteen päälle
decision_chain.py        Finlex-säädökset, täysistuntoäänestykset, HE-ketjut
summary.py               tiivistelmät ja index.json käyttöliittymälle
yva.py                   YVA-menettelyn vaiheet, rekisteri muuttuvista sivuista
avoimuus.py              Avoimuusrekisterin vaikuttamisilmoitukset hankkeisiin
promote.py               nosto seurantaan (issue -> seuranta/ + trace), kuukausipäivitys
tests/test_all.py        testit

## Rajapinta-ansat

- **`valmisteluvaihe`-enumia ei saa rajapinnasta.** `GET /api/v2/valmisteluvaiheet`
  on 404; arvot on luettava aineistosta. Väärä arvo palauttaa
  400 `Invalid request parameters` — poikkeuksellisesti se siis valittaa
  eikä palauta tyhjää. Todennetut arvot: `PERUSVALMISTELU`,
  `EDUSKUNTAKASITTELY`, `LAUSUNTOMENETTELY`,
  `VALTIONEUVOSTON_PAATOKSENTEKO`, `JATKOVALMISTELU`, `ESIVALMISTELU`,
  `LAIN_VAHVISTAMINEN`, `VALMISTUNUT`.
- **`asettamisPaiva` puuttuu enemmistöltä.** Varakenttä `aloitusPaiva`
  nostaa kattavuuden 12/32 → 32/32. Kentät EIVÄT ole sama asia — käytetty
  kenttä kirjataan `parameters.occurred_at_source`.

## Ajo

    python3 tests/test_all.py

## Synteettisen aineiston tulos

Näkyvyysviive: mediaani 3 vrk, keskiarvo 17,4, maksimi 51.

PRE ja FULL eroavat toisistaan systemaattisesti — huhtikuussa PRE 0,0 ja
FULL 80,9, helmikuussa PRE 200,0 ja FULL 78,5. Ero ei ole virhe: se on
sen mittari, kuinka paljon myöhemmin tullut tieto muuttaa kuvaa.
Tapahtumien kokonaismäärä on molemmissa sama.

## Seuraava askel

Ei oikeaa Hankeikkuna/Finlex/EK-dataa ennen kuin ROE/RRI-spesifikaatio
löytyy. Laskentakone on todistettu; kaavaa ei saa keksiä sen ympärille.

Kun spesifikaatio löytyy, lukittavaa on kolme asiaa: RRI:n kaava
SP:stä, L:stä ja IR:stä; I:n deterministinen laskenta; IR:n aggregointi.
