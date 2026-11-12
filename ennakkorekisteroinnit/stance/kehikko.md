# Stance — koodauskehikko ja validointiprotokolla

**Tila:** LUONNOS — lukittuu kun tämä tiedosto yhdistetään `main`-haaraan.
Lukituksen jälkeen tätä tiedostoa ei muuteta; korjaukset uusina tiedostoina
(`poikkeama_N.md`), kuten Q-001:ssä.

**Rekisteröijä:** Marko Ruotsalainen · **Luonnos:** 12.11.2026

## Miksi

`extractor.py` lukee lausunnosta rakenteesta kaiken muun (targeting
lomakkeesta, intensity roolista, policy_proximity määritelmästä). Yksi
suure jää: **kannattaako lausuja luonnosta vai vastustaako, ja missä
kohdin**. Se on tekstin tulkintaa, ja siihen tarvitaan luokittelija.

Tämä kehikko kiinnittää ennen kuin yksikään malli näkee yhtään lausuntoa:
mitä luokitellaan, millä luokilla, miten luokittelija validoidaan ja millä
säännöllä se otetaan käyttöön tai hylätään.

Q-001 ei käytä stancea. Tämä ei koske sen ennakkorekisteröintiä.

## Luokitteluyksikkö

Yksikkö on **vastaus**, ei lausunto. Extractorin `StatementForm.answers`
jakaa lausunnon kysymys–vastaus-pareihin; kukin pari luokitellaan erikseen.
Lausunto voi kannattaa lukua 3 ja vastustaa lukua 5, ja koko lausunnon
yksi arvo hävittäisi juuri sen tiedon jota `targeting` mittaa.

| form_type | yksikkö |
|---|---|
| kysymyksittäin / pykälittäin | jokainen vastaus erikseen, `Muuta kommentoitavaa` mukaan lukien |
| yksi_kentta, vapaa_asiakirja | koko teksti yhtenä yksikkönä |
| tunnistamaton, parse_confidence low | **ei luokitella**. Jäsentimen vika korjataan ensin |
| is_empty | **ei luokitella**. Tyhjällä lausunnolla ei ole kantaa, se on jo merkitty |

Lausuntotason arvo johdetaan yksiköistä deterministisesti (ks. Johdettu
lausuntotaso), ei luokitella erikseen.

## Luokat

Kanta suhteutetaan **luonnoksen ehdotukseen**, ei sen tavoitteeseen.

| luokka | määritelmä |
|---|---|
| `kannattaa` | Hyväksyy ehdotuksen sellaisenaan tai esittää vain teknisiä/kielellisiä korjauksia, jotka eivät muuta sisältöä. |
| `kannattaa_muutoksin` | Hyväksyy ehdotuksen perusratkaisun, mutta vaatii vähintään yhden sisällöllisen muutoksen. |
| `vastustaa` | Vastustaa ehdotusta, vaatii sen poistamista tai lykkäämistä, tai vaatii muutosta joka kumoaa ehdotuksen perusmekanismin. |
| `ei_kantaa` | Kommentoi ottamatta kantaa: tiedoksianto, kysymys, kuvaus omasta toiminnasta, "ei lausuttavaa". |
| `epaselva` | Teksti sisältää kannan, mutta luokittelija ei pysty sijoittamaan sitä yllä oleviin. Eri asia kuin `ei_kantaa`. |

### Rajasäännöt

1. **Tavoite vs. keino.** "Kannatamme tavoitetta, mutta esitetty keino on
   väärä" → `vastustaa`. Tavoitteen kannatus ei ole ehdotuksen kannatus.
2. **Muutos vs. kumoaminen.** Muutosvaatimus on `kannattaa_muutoksin`, jos
   ehdotus toimisi muutoksen jälkeen samalla mekanismilla. Jos muutos
   poistaa mekanismin (esim. etusijamenettelystä etusijan), → `vastustaa`.
3. **Laajennusvaatimus.** "Ehdotus on hyvä, mutta sen pitäisi koskea myös
   X:ää" → `kannattaa_muutoksin`.
4. **Kanta puuttuvaan.** Vastaus, joka vaatii luonnokseen jotain mitä siinä
   ei ole ottamatta kantaa siihen mitä siinä on → `kannattaa_muutoksin`,
   jos vaatimus on lisäys; `ei_kantaa`, jos se on pelkkä huomautus.
5. **Ehdollinen kanta.** "Kannatamme, jos X" → `kannattaa_muutoksin`
   (ehto = muutosvaatimus).
6. **Ristiriita samassa vastauksessa.** Ratkaisee vastauksen loppupäätelmä,
   jos sellainen on; muuten `epaselva`.

### Perustelu-ote

Jokaiseen luokitukseen liitetään **yksi lainaus** vastauksen tekstistä
(enintään 300 merkkiä), johon luokitus perustuu. `ei_kantaa` voi jättää
otteen tyhjäksi.

Ote tarkistetaan deterministisesti: sen on löydyttävä vastauksen
tekstistä sellaisenaan (välilyönnit normalisoituina). Ote, jota tekstissä
ei ole, on **hallusinaatio**, ja luokitus hylätään. Tämä on sama
periaate kuin `evidence[].quote` muualla OGAS3:ssa.

## Johdettu lausuntotaso

Lausunnon arvo lasketaan yksiköistä, ei luokitella:

- kaikki kantaa ottavat yksiköt samaa luokkaa → se luokka
- vähintään yksi `vastustaa` ja vähintään yksi kannattava → `ristiriitainen`
- muuten (`kannattaa` + `kannattaa_muutoksin`) → `kannattaa_muutoksin`
- ei yhtään kantaa ottavaa yksikköä → `ei_kantaa`

`epaselva`-yksiköt eivät osallistu johtamiseen; niiden määrä raportoidaan.

## Tietueen muoto

`classification.py`:n `llm_classification` hyväksyy vain L-komponentit
(`intensity, targeting, policy_proximity, uptake`) lukuina väliltä 0–1.
Stance on luokka, ei luku, eikä se ole RRI:n L-komponentti. Sille ei ole
paikkaa nykyisessä skeemassa.

**Päätetty:** oma skeema `aci/stance/v0.1`. Tietue viittaa tapahtumaan
samalla tavalla kuin `ClassificationRecord` (event_id + event_hash,
classified_at, classifier: kind, id, version, knowledge_cutoff,
prompt_hash) ja lisää:

- yksikön tunnisteen: vastauksen indeksi + `section`
- `stance` (yksi viidestä luokasta) ja `quote`
- `response_model`: rajapinnan palauttama mallitunniste
- `effort`

Nykyiseen `classification.py`:hin ei kosketa.

## Tietohorisontti

`classification.py` vaatii llm-luokittelijalle `knowledge_cutoff`:n.
Moonshot ei julkaise Kimi K3.1 Pro:n cutoffia, eikä rajapinta tarjoa
päivättyjä tunnisteita eikä `system_fingerprint`:iä (llm-probe 12.11.2026:
mallit `kimi-k3`, `kimi-k3.1-pro`, `kimi-k3.1-pro-highspeed`; vastauksen
`model` = pyydetty alias). Mallin vaihtumista ei voi havaita rajapinnasta.

Siksi kaksi rajaa:

| raja | arvo | pätee |
|---|---|---|
| **varma** | `classified_at` | aina. Malli ei voi tietää luokitushetken jälkeisestä, vaihtui se tai ei |
| **ehdollinen** | mallin julkaisupäivä (Kimi K3.1 Pro: 2026-10-23) | vain jos mallia ei ole vaihdettu saman tunnisteen takana |

Julkaisupäivä on yläraja eikä cutoff: se arvioi horisontin liian
myöhäiseksi, joten virhe tuottaa vain ylimääräisiä CONTAMINATED-merkintöjä,
ei koskaan väärää CLEAN-tulosta.

**Ensisijainen tulos lasketaan varmalla rajalla.** Ehdollinen raportoidaan
rinnalla, kuten Q-001:n poikkeama 1:n herkkyystulos. Jos tulokset eroavat,
ero raportoidaan tapahtumittain eikä ensisijaista muuteta.

Jos luokittelijan cutoff on julkaistu, ehdollisena rajana käytetään
julkaistua arvoa.

| luokittelija | ehdollinen raja | peruste |
|---|---|---|
| Kimi K3.1 Pro (`kimi-k3.1-pro`) | 2026-10-23 | julkaisupäivä, yläraja. Pätee vain jos mallia ei vaihdettu |
| Claude Sonnet 5.5 (`claude-sonnet-5-5`) | 2026-06-30 | julkaistu training data cutoff "Jun 2026", kuukauden loppu. Anthropicin mukaan jokainen mallitunniste on kiinnitetty snapshot, joten raja ei riipu vaihtumisoletuksesta |

Epäsymmetria on mittauksen ominaisuus, ei vika: Sonnetin ehdollinen raja
on dokumentoitu, Kimin johdettu.

Jokaiseen tietueeseen tallennetaan vastauksen `model`-kenttä. Jos arvo
muuttuu kesken ajon, ajo keskeytyy.

Jatkuvassa seurannassa luokittelu ajetaan kuukausiajon yhteydessä, jolloin
varma raja riittää eikä mallin vaihtumisella ole merkitystä.

## Validointi

Validointi mittaa luokittelijan yhtäpitävyyttä ihmisen kanssa. Se ei tuota
RRI-dataa, joten validointiaineiston tietohorisontilla ei ole merkitystä.

### Otos

- **Perusjoukko:** energia-aiheisten Hankeikkuna-hankkeiden (`teksti`-haku,
  ks. policy-proxy) LAUSUNTO-asiakirjat, joiden lausuntoaika päättyi ennen
  1.10.2026.
- **Poissuljettu:** TEM040:00/2026 ja TEM043:00/2026 (tuotantoaineistoa),
  rekisteröijän oma lausunto, `is_empty`, `tunnistamaton`, `parse_confidence: low`.
- **Valinta:** perusjoukko järjestetään `sha256(uuid)`-arvon mukaan ja
  otetaan 20 ensimmäistä. Ei käsin valintaa. Perusjoukon tunnistelista ja
  valitut 20 kirjataan tiedostoon `otos.json` ennen koodausta.
- Yksiköitä kertyy arviolta 60–100. Kappa lasketaan yksikkötasolla.

### Järjestys

1. `otos.json` committataan.
2. Rekisteröijä koodaa kaikki yksiköt käsin tämän kehikon mukaan,
   näkemättä yhtään mallin tulosta → `ihminen.json`, committataan.
   Commitin aikaleima todistaa järjestyksen.
3. Vasta tämän jälkeen mallit ajetaan.

### Ajot

| malli | reasoning_effort | toistot |
|---|---|---|
| Kimi K3.1 Pro | low, max | 2 kertaa kumpikin |
| Claude Sonnet 5.5 (`claude-sonnet-5-5`) | low, high (oletus) | 2 kertaa kumpikin |

Lämpötila ei ole säädettävissä kaikissa malleissa, joten kahdella toistolla
mitataan mallin oma vakaus. Prompt, skeema ja `prompt_hash` kirjataan
tiedostoon `prompt.md` ennen ajoja eikä niitä muuteta ajojen välillä.

### Mittarit

- **κ (Cohen, painottamaton)** mallin ja ihmisen välillä, yksikkötasolla, kaikki viisi luokkaa
- κ mallin kahden toiston välillä (vakaus)
- κ Kimin ja vertailumallin välillä
- sekaannusmatriisi luokittain
- otteiden tarkistuksen hylkäysosuus
- todelliset tokenimäärät ja hinta (`usage`)

### Päätössääntö

Malli × effort-taso, jolle:

| ehto | tulos |
|---|---|
| κ(ihminen) ≥ 0,60 **ja** otehylkäys ≤ 5 % **ja** κ(toistot) ≥ 0,80 | otetaan käyttöön |
| κ(ihminen) 0,40–0,60 | käyttöön vain kahden mallin yhtäpitävissä yksiköissä; eroavat → `epaselva` |
| κ(ihminen) < 0,40 tai otehylkäys > 5 % | hylätään |

Jos mallin kumpikin effort-taso ylittää käyttöönottorajan, valitaan halvempi.
Jos kumpikin malli ylittää rajan, käyttöön otetaan avoimen painon malli
(toistettavuus), ellei ero ihmisyhtäpitävyydessä ole > 0,10.

## Tunnettu vinouma: kehikon laatija

Tämän kehikon luonnosteli Claude (Anthropic) rekisteröijän ohjauksessa, ja
vertailumalli on Anthropicin. Rajasääntöjen sanamuoto voi siksi osua
Clauden lukutapaan paremmin kuin Kimin, mikä kallistaisi mallien välistä
vertailua Sonnetin hyväksi. Päätössääntö vertaa kumpaakin mallia
rekisteröijän käsikoodaukseen, ei malleja toisiinsa, mikä rajaa vaikutusta
mutta ei poista sitä. Lukija voi arvioida sen tämän kirjauksen perusteella.

Rekisteröijä on lukenut rajasäännöt 1–6 ja hyväksynyt ne sellaisinaan
(12.11.2026).

## Ajoympäristö

GitHub Actions. Avaimet salaisuuksina `MOONSHOT_API_KEY` ja
`OGAS3ANTH_API_KEY`. Hinnat 12.11.2026: kummallakin mallilla 2 $ / 10 $
per miljoona syöte-/tulostetokenia.
