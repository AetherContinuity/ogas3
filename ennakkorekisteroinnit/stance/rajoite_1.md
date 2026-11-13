# Stance — rajoite 1: käsikoodauksen huolellisuus

**Kirjattu:** 2026-11-13, Kimin tulosten jälkeen, ennen Sonnetin ajoa.
**Lukittu `ihminen.json`** on ennallaan. Tämä ei muuta yhtään koodia.

## Kirjaus

Rekisteröijä toteaa, että käsikoodaus (`ihminen.json`, 12.–13.11.2026)
tehtiin nopeasti ja osin tekstin silmäilyn perusteella, ei jokaista
yksikköä kokonaan rajasääntöjä vasten lukien. Koodaus ei siksi ole
huolellinen totuusaineisto.

## Seuraus tulkinnalle

Ensisijainen κ mittaa mallin yhtäpitävyyttä **nopean ihmislukemisen**
kanssa, ei luokittelun oikeellisuutta. Mallin todellinen tarkkuus voi olla
raportoitua parempi tai huonompi; tämä aineisto ei erota niitä.
Päätössääntö sovelletaan lukitusti, mutta tulos raportoidaan tämän
rajoitteen kanssa.

## Toissijainen analyysi (suunniteltu, ei vielä tehty)

1. Kun sekä Kimi että Sonnet on ajettu: yksiköt, joissa mallit ovat
   yksimielisiä ihmistä vastaan, ja yksiköt, joissa mallit ovat keskenään
   eri mieltä, listataan.
2. Rekisteröijä lukee nämä yksiköt kokonaan rajasääntöjä vasten ja kirjaa
   ratkaisun perusteluineen tiedostoon `ratkaisu.json`.
3. **Sokkoutus ei toteudu:** rekisteröijä on nähnyt Kimin luokitukset
   erimielisistä yksiköistä (13.11.2026). Ratkaisu voi siksi kallistua
   mallin suuntaan. Tämä raportoidaan toissijaisen tuloksen yhteydessä.
4. Toissijainen κ raportoidaan ensisijaisen rinnalla, ei sen sijaan.

Vahvin korjaus olisi toinen ihmiskoodaaja, joka koodaa otoksen näkemättä
rekisteröijän tai mallien luokituksia. Ihmisten välinen κ kertoisi
tehtävän vaikeuden ja mallin tuloksen vertailutason.
