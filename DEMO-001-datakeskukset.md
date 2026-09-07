# DEMO-001 — Datakeskukset ja sähköjärjestelmä

**Kolmen instrumentin yhteisajo · 7.9.2026 · Aether Continuity Institute**

Aihe: Ylen 5.9.2026 julkaisema juttu *"Tutkijat: Luonto ei kestä
datakeskusten aiheuttamaa kasvavaa energiankulutusta"* ja siinä esitetyt
väitteet.

---

## Mitä tämä raportti on

Ensimmäinen ajo, jossa WEM, OGAS2 ja OGAS3 katsovat samaa kysymystä.
Tarkoitus ei ole vastata siihen mitä datakeskuksista pitäisi ajatella,
vaan näyttää **mitä mittarit näyttävät ja mitä ne eivät näytä.**

Jokainen luku on merkitty:

| merkintä | tarkoittaa |
|---|---|
| **[M]** | mitattu, lähde nimetty |
| **[L]** | laskettu mitatusta, kaava avattu |
| **[A]** | asetettu tai arvioitu, ei johdettu |
| **[—]** | ei mitattavissa nykyisillä lähteillä |

Erottelu ei ole koristetta. Tämän raportin pääväite on, että kolme
neljäsosaa julkisesta keskustelusta koskee asioita joita **ei ole
mitattu**, ja että se on tunnistettavissa.

---

## 1 · Fyysinen kerros — mitä on mitattu

**Kulutus kasvaa 84,7 → 118,5 TWh vuoteen 2030, +40 %.** [M]
Fingridin ennuste, Motivan grafiikka. Ajurit: datakeskukset ja
sähkökattilahankkeet.

**CHP-kapasiteettia on poistunut −650 MW.** [M]
SM-015:n monitori, käsin koottu laitostason tiedoista.

**Korvaavaa kaasumoottorikapasiteettia rakenteilla 160–180 MW.** [M]
Tornio 43 MW käytössä 1.4.2026 (Wärtsilä, neljä moottoria, asennus
7/2025). Lappeenranta ~40–45 MW, valmis 2030. Kotka ja Oripää
lupavaiheessa.

Korvaavuus on siis **noin neljännes** poistuneesta — ja se maksetaan
vaihtamalla kotimainen polttoaine tuontiin:

| | CHP | kaasumoottori |
|---|---|---|
| investointi | vaihtelee | kotimainen (Wärtsilä) [M] |
| polttoaine | kotimainen hake, turve [M] | tuonti-LNG / putkikaasu [M] |
| polttoaineketjun työllisyys | korjuu, kuljetus, terminaalit [M] | putki tai säiliöauto |
| velvoitevarastointi | **ei ole** [M] | 3 kk, mutta vain yhdyskunnille [M] |

Haapaniemellä on pakkaspäivinä yli sata rekkaa vuorokaudessa. [M]
Turvealan työllisyys 2 300 → 400–500 htv. [M]

**SE1:n vientimarginaali supistuu +14 → −1 TWh 2026–2030.** [M]
Svenska kraftnätin ennuste. Suomen tuontimarginaali kapenee samaan
aikaan kun kulutus kasvaa.

---

## 2 · WEM — kestävyys, ei hinta

EPP (Endurance Pressure Proxy) on WEM:n mittari sähköjärjestelmän
kestävyydelle:

```
EPP = (1−FS)·0,30 + SP·0,30 + DP_t·0,20 + WR·0,20 + persistPremium
```

**Nykytila W168:** [L]

| komponentti | arvo | mitä mittaa |
|---|---|---|
| FS firm share | 0,596 | (ydin + vesi) / kulutus |
| SP stressitunnit | 0,633 | gap > kulutus·5 % |
| DP_t kysyntäpaine | **1,000 KATOSSA** | lämpötilakorjattu |
| WR tuulen osuus | 0,117 | variabiliteettiriski |
| **EPP** | **0,654** | |

**Varaus, joka on luettava ennen lukua:** `DP_t` on katossa. Yksi
neljästä painosta on lukossa eikä erottele mitään. EPP näyttää täydeltä
luvulta vaikka viidennes siitä on vakio. WEM merkitsee tämän itse.

### Skenaariot [L]

WEM:n `calcWindowScenario(slice, dcMW, chpPct)` samalta ikkunalta.
FS ja WR laskettu kulutuksesta ja tuotannosta; **SP on arvio** [A] —
se vaatii tuntisarjan eikä ole johdettavissa keskiarvoista.

| skenaario | DC MW | CHP | FS | EPP | S_ENERGY |
|---|---|---|---|---|---|
| Nykytila | 0 | 0 % | 0,596 | 0,654 | 65,4 |
| 2027 | +500 | −5 % | 0,563 | 0,684 | 68,4 |
| 2027 | +1500 | −15 % | 0,507 | 0,743 | 74,3 |
| 2030 | +3000 | −30 % | 0,441 | 0,812 | 81,2 |
| 2030 + CHP −40 % | +3000 | −40 % | 0,441 | 0,812 | 81,2 |

**Kaksi viimeistä ovat identtiset**, ja se on havainto eikä virhe:
`SP` saturoituu 1,000:een jo 3000 MW:n kohdalla, ja FS ei muutu koska
kulutus on sama. **Saturaatiopisteen jälkeen syvempi CHP-leikkaus ei
enää näy EPP:ssä.** Kaksi neljästä komponentista on silloin lukossa.

Tämän yli ei saa ekstrapoloida.

---

## 3 · OGAS2 — järjestelmäterveys

SHI yhdistää neljä kerrosta. S_ENERGY luetaan WEM:n EPP:stä, ei lasketa
uudelleen — kaksi laskentaa samalla nimellä olisi pahempi kuin puuttuva
kytkentä.

| skenaario | S_ENERGY | SHI | luokka |
|---|---|---|---|
| Nykytila | 65,4 | **44,7** | ORANGE |
| 2027 +500 MW | 68,4 | 43,3 | ORANGE |
| 2027 +1500 MW | 74,3 | 40,6 | ORANGE |
| 2030 +3000 MW | 81,2 | **32,6** | RED |

Muut kerrokset pidetty vakiona: R_PUBLIC 63,8, E_REAL 30,
X_EXTERNAL 28. [M/A — R_PUBLIC mitattu, muut osin asetettuja]

**Kolme huomiota.**

Fingridin oma kulutusennuste vie SHI:n punaiselle vuoteen 2030
mennessä, muiden kerrosten pysyessä paikallaan. Se ei ole ACI:n
skenaario vaan siirtoverkkoyhtiön.

Compound-kytkentä aktivoituu: se vaatii että sekä S_ENERGY että
R_PUBLIC ylittävät 50, ja nykytilassa molemmat ylittävät. Kytkentä
kasvaa 1,8 → 3,5 pistettä. Mekanismi: energiakustannus vaatii julkista
kompensaatiota, mikä kaventaa liikkumavaraa, mikä vähentää kykyä
puskuroida seuraavaa shokkia.

Ja **sitova rajoite vaihtui**. Ennen WEM-kytkentää R_PUBLIC kantoi
49 % painotetusta stressistä; nyt S_ENERGY kantaa 44 %. Aiempi
johtopäätös — "energiainterventiot eivät kosketa sitovaa rajoitetta" —
oli väärän syötteen tulos.

**Varaus:** OGAS2:n interventioiden `patch`-arvot ovat asetettuja [A]
eivätkä johdettuja. Sitä ei ole korjattu.

---

## 4 · OGAS3 — institutionaalinen kerros

Tässä on raportin varsinainen tulos.

### Mitä on päätetty [M]

| toimi | summa | milloin |
|---|---|---|
| Sähkövero luokkaan I: 0,05 → 2,24 snt/kWh | +47 M€/v | voimaan 1.7.2026 |
| Datakeskusten 30 M€ tukimalli poistettu | −30 M€ | budjettiriihi 2.9.2026 |

Molemmat ovat **verotusta**. Molemmat ovat pieniä.

### Mitä on kesken [M]

| hanke | tila | lausuntoja |
|---|---|---|
| `TEM040:00/2026` datakeskusrekisteri | lausunnolla 3.9.–2.10.2026 | **0** |
| `TEM043:00/2026` sähkömarkkinalaki | perustettu, ei asiakirjoja | 0 |
| `LA 27/2026` liittymisehdot (Vestman) | talousvaliokunnassa 1.9.2026 | — |

`LA 27/2026` on saanut yli sata allekirjoitusta, ja tekijän mukaan
allekirjoituksia on kaikista eduskuntapuolueista. Sisältö: suurten
datakeskusten olisi vastattava omasta kulutuksestaan uudella
tuotannolla, säätövoimalla tai kulutusjoustolla.

**Ne kolme ovat kaikki liian tuoreita tuottamaan mitattavaa
vaikuttamista.**

### Uptake — mitä ei voi mitata [—]

ROE:n `uptake` mittaa näkyykö kanta päätöksessä. Kaikilla kolmella
hankkeella se on **määrittämätön, ei nolla.**

Ero on olennainen ja se on koko OGAS3:n rakenteen ydin:

```
uptake = 0      näyttöä siitä ettei kantaa omaksuttu
uptake = None   ei vielä tiedetä
```

Lausunto ei voi todistaa uptakea eikä sen puuttumista, koska se
kirjoitetaan **ennen** päätöstä. Ainoa lähde jossa nolla on havainto
on täysistunnon äänestys — ja `LA 27/2026`:sta ei ole äänestetty.

### Aineiston laajuus [M]

Energiahankkeiden lausuntoaineisto, haettu Hankeikkunan
vapaasanahaulla kymmenellä hakusanalla:

```
173 hanketta (1997–2026), joista 70 vuodesta 2020
50 hanketta tuotti 2 265 lausuntoa
752 uniikkia laatijaa
```

Toistuvuusjakauma on jyrkästi vino: **430 laatijaa (57 %) esiintyy
kerran**, ja kaksitoista antaa yli kaksikymmentä lausuntoa.

Kärki: Energiateollisuus ry 41 · SYKE 49 (kolmen kirjoitusasun
yhdistämisen jälkeen) · Valtiovarainministeriö 33 · Kuntaliitto 27 ·
EK 27 · Energiavirasto 26.

**Kahdenkymmenen kärjessä on kuusi ministeriötä ja neljä muuta
viranomaista.** Lausuntokierroksen aktiivisin osallistuja on hallinto
itse.

**Ja `datakeskus`-hakusanalla osumia on kaksi.** [M] Aihe, josta
tutkijat, Fingrid ja sata kansanedustajaa puhuvat, on säädösvalmistelun
aineistossa lähes olematon.

---

## 5 · Havainto: instrumenttien ero

Yhdistettynä aineisto tuottaa yhden väitteen, jota ei ole julkaistu
muualla:

> **Päätetty on se mikä on pientä ja nopeaa. Päättämättä on se mikä on
> suurta ja hidasta. Ero ei ole tahdon puute vaan instrumenttien ero.**

Verotus on VM:n toimialaa ja liikkuu talousarviossa vuosittain.
Sähkövero nostettiin heinäkuussa; tukimalli poistettiin syyskuussa.
Molemmat toteutuivat.

Liittymisehdot, joustovelvoite ja kapasiteettimekanismi ovat
sähkömarkkinalakia. Ne vaativat hallituksen esityksen,
lausuntokierroksen ja eduskuntakäsittelyn.

**Ja Hankeikkuna-mittaus antaa sille aikamitan:** [M]

| valmisteluvaihe | näkyvyysviive, mediaani |
|---|---|
| LAUSUNTOMENETTELY | 7 vrk |
| PERUSVALMISTELU | 15 vrk |
| VALTIONEUVOSTON_PAATOKSENTEKO | 19 vrk |
| EDUSKUNTAKASITTELY | 20 vrk |
| Eduskunta (istunto) | 0 vrk |

Maksimi 662 vrk. Ja kaksi kolmasosaa hankkeista puuttui
`asettamisPaiva`, mikä olisi pudottanut ne PRE-sarjasta kokonaan.

Tämä on **sama havainto kuin Kestävyyspaneelin Linnasella** — *"Päättämättä
jättäminen on myös päätös"* — mutta se kertoo lisäksi **miksi**.

---

## 6 · Mitä tämä raportti ei osaa sanoa

Rehellisyyden vuoksi, ja koska tämä on demo:

**Uptake on mittaamatta.** Kaikilla kolmella hankkeella `None`. Sarja
on kirjattu mutta arvoa ei ole.

**Extractor on ajamatta.** 2 265 lausunnon `targeting`,
`policy_proximity` ja `intensity` ovat luokittelematta. Ne vaativat
PDF:n sisällön ja kielimallin.

**`patch`-arvot ovat asetettuja.** OGAS2:n interventioiden vaikutus
S_ENERGYyn on käsin annettu luku ilman johtoa — ja LDR-50:n kohdalla
etumerkkikin on epäselvä, koska se voi korvata joko sähkökattilan
(positiivinen) tai CHP:n lämmöntuotannon (negatiivinen).

**WEM-snapshot on paikkamerkki.** Komponentit ovat havaituista
lukemista, `SP` skenaarioissa on arvio, ja tiedosto odottaa WEM:n
vientipainiketta.

**D- ja O-tapahtumia ei ole lainkaan.** Liittymähakemukset ovat
Fingridin jonossa eivätkä julkisia — ja hakija saa esiintyä
nimettömänä, vastaus on voimassa kaksi kuukautta. Omistusmuutokset ovat
kolmensadan kunnanvaltuuston pöytäkirjoissa.

**Ja tämä viimeinen on raportin kiinnostavin kohta.** `TEM040:00/2026`
— datakeskusrekisteri — on täsmälleen sen aukon täyttämistä. Jos se
toteutuu, OGAS3:n suurin puuttuva lähde syntyy lainsäädännöllä.

Se on lausunnolla 2.10.2026 asti, ja lausuntoja on nolla.

---

## Lähteet

**Mitattu:** Fingrid (kulutusennuste, tuotantosarjat) · ENTSO-E
(day-ahead FI) · Svenska kraftnät (SE1) · Hankeikkuna (hankkeet,
lausunnot, asiakirjat) · Eduskunta (käsittelyvaiheet, äänestykset) ·
Valtiokonttori (kirjanpitoyksiköt) · Yle 5.9.2026 · Tornion Voima /
Wärtsilä / EPV.

**Laskettu:** WEM v2.7.5 (EPP, FS, SP, DP_t, WR) · OGAS2 v2.8 (SHI,
kerrospainot) · OGAS3 (aikaleimat, aggregaatio, roolit).

**Ei mitattu, kirjattu auki:** uptake · targeting · policy_proximity ·
intensity · impact_weight · patch-arvot · D- ja O-tapahtumat.

---

*Instrumentit ja koodi: aethercontinuity.org. Ei auditoitua
taloustietoa. Kaikki asetetut arvot on merkitty [A] eikä niitä pidä
lukea mittaustuloksina.*
