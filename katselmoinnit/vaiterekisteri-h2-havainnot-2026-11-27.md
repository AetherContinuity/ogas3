# Täyttö v2: H1- ja H2-vertailun havainnot (27.11.2026)

Ensisijaiset tulokset ovat koneellisia raportteja, jotka on tuotettu ennen ajoa kirjatuilla säännöillä:
- `vaiterekisteri-h2-taytto-v2-2026-11-27.md`: H2 vs täytön v2 raakatulos (`tools/vaiterekisteri_h2.py`, commit 6637bd8)
- `vaiterekisteri-h1-taytto-v2-2026-11-27.md`: H1 vs täytön v2 raakatulos (`tools/vaiterekisteri_h1.py`, ennallaan)
- `vaiterekisteri-h2-taytto-1-lahtotaso-2026-11-27.md`: H2 vs täytön 1 raakatulos (lähtötaso)

Tulkitsija on kontaminoitunut: sama Claude-istunto kirjoitti H1:n ja H2:n. Alla oleva on tulkintaa, ei mittausta.

## Tulos

**H2: hylätty kriteerissä 0 molemmissa täytöissä.** Kohdeväitettä T (CN-030 luku 10, "Poolausarvo ja kapasiteettiketjun pienin lenkki …") ei poimittu kummassakaan täytössä. U1–U4, Q1, S1, P1 ja R1 jäivät myös poimimatta. Esiintymät osuivat vain kohtiin I1 (CN-030:004), O1 (SM-024:008) ja N1 (WP-020:008), ja O1 on `same_claim` I1:n kanssa (S030, eksplisiittinen), kuten H2 odotti. Lisäyksen 1 raportointitarkennukset jäivät käyttämättä, koska vertailu päättyi kriteeriin 0.

**H1: sama tulos kuin täytössä 1.** Kattavuuskriteerit 1–4 eivät täyty (D1, S1, S2 ja U1–U3 jäivät poimimatta; Q2b puuttuu). Tarkkuuskriteeri 5 ja kriteeri 7 täyttyvät. Ainoa ero on I2:n poiminta, eikä I2:lle tullut väärää yhteyttä.

## Mitä pyynnön muutos teki

| | täyttö 1 | täyttö v2 |
|---|---|---|
| esiintymiä | 31 | 37 |
| suhteita | 21 | 32 |
| saman paperin sisäisiä suhteita | 3 | 22 |
| CN-030:n esiintymiä / sisäisiä suhteita | 4 / 0 | 9 / 4 |
| related | – | 0 |

Sisäiset ketjut lisääntyivät seitsenkertaisesti, joten muutos toimi siinä, mitä pyyntö pyysi.

**Korjaus 27.11.2026 (ensimmäinen versio oli liian vahva).** Ensimmäinen versio väitti, että ketjut valikoituivat numeerisiin havaintoihin ja selittävät väitteet jäivät pois. Kun kaikki 22 sisäistä suhdetta luettiin, väite ei pidä:
- CN-008:ssa on selitysrakenne ilman lukuja: "Sama kolmen vajeen rakenne …" → mittausvaje, sanktiovaje ja korjausvaje (kolme eksplisiittistä depends_on-suhdetta).
- Rajaushuomiot (WP-020, CN-008, SM-024) on ketjutettu qualifies-suhteilla, ja SM-024:n "ei avointa palvelua eikä jatkuvuutta" nojaa yhteysinventaarioon.
- Numeerisia ketjuja on WP-020:ssa (CO₂-laskelma) ja CN-030:ssa (nettonykyarvo → "Tornio ei kanna"; läpäisyluvut → "läpäisy lähellä nollaa").

Kuvaavampi erottelu: poimituksi tuli rakenne, jonka paperi esittää koottuna yhteen kohtaan (luettelo, laskelma, rajaushuomio tai viittaus). Puuttuu kaksi testikohdetta: T, vaikka sen premissi U1 on samassa kappaleessa, ja F3:n ylävirta, joka on hajallaan eri osioissa. F3 itse poimittiin (WP-020:008), mutta vain rajausten kohteena. Kohteita on kaksi, joten väitetyypistä ei voi yleistää.

Kohdistusvirhe on suljettu pois: yksikään täytön v2 CN-030-esiintymä ei ala luvun 10 kohdasta "Miksi tätä ei ole laskettu", joten T ei ole kirjautunut väärään jänteeseen.

## Hypoteesit (ei testattu)

1. Määritelmä "aineistohavainto: … luku, mittaus, lähteen tieto tai laskelman tulos" voi ohjata poimijaa havaintoihin, jotka paperi esittää aineistona. T:n premissi U1 on toimijoiden työnjako, jota paperi ei esitä aineistona. (Korjauksen jälkeen heikompi kuin ensimmäisessä versiossa.)
2. Esiintymiä on noin 9–10 paperia kohden molemmissa täytöissä. Ajo päättyi normaalisti (31 342 / 48 000 tokenia), joten katto ei rajannut. Periaate "kattavuutta ei tavoitella yhteyksissä" ja vaatimus, että esiintymä on jonkin suhteen pääte, voivat yhdessä rajata määrää.
3. Related 0 johtunee pyynnön ohjeesta (H2 lisäys 1). Se ei vaikuttanut tähän tulokseen, koska molemmat testit päättyivät kattavuuteen ennen related-kohtia.

Uutta täyttöä ei pidä laatia näiden hypoteesien pohjalta tässä istunnossa: korjaus tulisi H1:n ja H2:n tuntijalta.
