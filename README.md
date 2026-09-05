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
    tests/test_all.py        17 testiä

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

    python3 tests/test_all.py        # 17/17

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
