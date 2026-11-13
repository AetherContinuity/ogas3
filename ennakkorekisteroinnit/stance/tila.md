# Stance — validoinnin tila 13.11.2026

## Tulos (ensisijainen, lukittu päätössääntö)

Kaikki neljä yhdistelmää läpäisivät käyttöönottorajan. Valinta sääntöjen
mukaan: **Kimi K3.1 Pro, effort low** (κ 0,634; toistojen κ 0,947;
otehylkäys 0 %; muotovirheitä 0/62; 0,34 $ / 62 kutsua).
Ks. `arviointi.md`, `poikkeama_1.md`, `poikkeama_2.md`, `rajoite_1.md`.

## Mitä tulos tarkoittaa

Mallit ovat samaa mieltä rekisteröijän nopean koodauksen kanssa noin
neljässä yksikössä viidestä. Tulos ei erottele malleja toisistaan
(luottamusvälit päällekkäin) eikä kerro luokittelun oikeellisuutta,
koska mittapuu ei ole huolellinen.

## Toissijainen analyysi — keskeytetty

Aloitettu yksiköstä 3 (`ratkaisu.json`): ratkaisematon. Rekisteröijän
arvio: erimielisyyksiä ei voi ratkaista ilman luonnosten sisältöä, ja
rekisteröijän oma luenta ei ole objektiivinen mittapuu. Muut 7
erimielisyysyksikköä (4, 6, 10, 12, 24, 27, 31) jätetään ratkaisematta
tällä aineistolla.

## Havaittu kehikon aukko

Kun lausuja pyytää täydentämään perusteluja tai ohjeistamaan tulkintaa,
raja `kannattaa` / `kannattaa_muutoksin` ei ratkea lausunnosta. Mallit
ratkaisivat sen johdonmukaisesti `kannattaa_muutoksin`-suuntaan; ihminen
ei pystynyt ratkaisemaan sitä lainkaan.

## Ennen tuotantokäyttöä (kehikko v0.2)

1. Luonnoksen tiivistelmä luokittelijan syötteeseen (ihmiselle ja mallille sama).
2. Sääntö perustelujen täydennys- ja tulkintapyynnöille.
3. Jatkokäytön vaatimus kirjataan: aggregaatit (kannatusosuudet) vai
   yksittäisluokitukset. κ 0,6 voi riittää edelliseen, ei jälkimmäiseen.
4. Kaksi riippumatonta ihmiskoodaajaa ja suurempi, luokittain
   ositettu otos; ihmisten välinen κ vertailutasoksi.
5. `stance.py`:n jäsennin korjataan ottamaan ensimmäinen JSON-objekti (poikkeama 2).
