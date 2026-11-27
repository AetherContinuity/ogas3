# Polttoainekoe 1: synapsimoottori todellisella datalla, jossa yhteydet tunnetaan (kirjattu 28.11.2026 ennen ajoa)

Tarkoitus: tarkistaa, löytääkö moottori (tools/synapsi.py) tunnetun yhteyden raakaöljystä pumppuhintoihin ja jättääkö se löytämättä yhteyden, jota ei pitäisi olla. Kyse ei ole uuden tiedon etsimisestä. Kirjaaja on nähnyt EU-keskiarvojen viimeiset rivit sekä Brentin ja valuuttakurssin viimeiset havainnot, mutta ei Suomen sarjaa.

**Aineisto** (julkinen):
- **EU Weekly Oil Bulletin**, hintahistoria 2005–: Suomen Euro-super 95 ja diesel ilman veroja, EUR/1000 l, maanantain hinnat. Verottomat siksi, että verojen muutokset eivät ole markkinasignaali.
- **Brent spot**, USD/bbl, päivittäinen (EIA; `datasets/oil-prices`, GitHub).
- **EUR per USD**, päivittäinen (`datasets/exchange-rates`, GitHub; FRED-lähde).

**Sarjat** (viikoittain, kohdistus WOB-päivään):
- brent_usd ja eur_per_usd: kauppapäivien keskiarvo välillä [WOB-päivä − 7 vrk, WOB-päivä − 1 vrk].
- fi95 ja fidiesel: WOB-arvo sellaisenaan.
- Muutos lasketaan prosentteina edellisestä viikosta. Puuttuva viikko on None, eikä se aktivoidu.

**Aktivaatiot**: jokainen suunta on oma sarjansa, kynnys viikkomuutokselle.
- brent_ylos ≥ +5 %, brent_alas ≤ −5 %
- fx_ylos ≥ +2 % (euro heikkenee), fx_alas ≤ −2 %
- fi95_ylos ≥ +3 %, fi95_alas ≤ −3 %, fidiesel_ylos ≥ +3 %, fidiesel_alas ≤ −3 %

**Moottori**: suurin viive 4 viikkoa, vähimmäissiirto 16 viikkoa, tarkka kiertonollamalli, BH α = 0,05.

**Odotukset**
- **H1** brent_ylos → fi95_ylos ja fidiesel_ylos, viive 0–2.
- **H2** brent_alas → fi95_alas ja fidiesel_alas, viive 0–3.
- **H3** fi95_* ↔ fidiesel_* saman suunnan pari, viive 0: yhteinen shokki.
- **H4** ei ehdokkaita fi* → brent_* tai fi* → fx_* viiveellä ≥ 1 (Suomen pumppuhinta ei liikuta Brentiä eikä valuuttaa). Jokainen tällainen on väärä positiivinen.
- **H5** fx: ei odotusta. Raportoidaan sellaisenaan.
- Ylös- ja alas-viiveiden ero (rockets and feathers) raportoidaan kuvailevasti. Sitä ei testata.

**Tulkinta**
- Moottori toimii tällä datalla, jos H1 tai H2 löytyy ja H4:ssä on 0 ehdokasta.
- Jos H4:ssä on ehdokkaita, nollamalli ei hallitse tämän datan rakennetta (esimerkiksi shokkien klusteroitumista), ja se raportoidaan.
- Toistettavuus: sama ajo erikseen jaksoille 2005–2015 ja 2016–2026.
