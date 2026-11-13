# Stance — poikkeama 2: jäsennin ja tulosten tallennus

**Kirjattu:** 2026-11-13, Sonnet high -tulosten jälkeen. Ensisijainen
tulos ja päätössääntö pysyvät lukitun koodin mukaisina.

## A. Jäsennin ei tee sitä mitä sen kuvaus lupaa

`stance.py`:n `jasenna()` on dokumentoitu ottamaan *ensimmäisen*
JSON-objektin, mutta toteutus (`re.search(r"\{.*\}", …, re.S)`) ottaa
ensimmäisestä `{`:stä viimeiseen `}`:iin. Kun malli kirjoittaa objektin
jälkeen lisätekstiä ja toisen objektin, jäsennys epäonnistuu.

Sonnet high teki näin 6 kertaa 62:sta (toisto 1: 4, toisto 2: 2): se
lisäsi kentän (`note`, `quote2`), huomasi ohjeen rikkomisen ja kirjoitti
"Korjaan:" + uuden objektin. Yksi lisäksi katkesi kesken merkkijonon.
Kimi ei tehnyt näin kertaakaan 124 vastauksessa.

**Ensisijainen:** lukitun T1:n mukaan nämä ovat virheitä = erimielisyyksiä.
Muodon noudattaminen on mallin ominaisuus, ja se kuuluu tulokseen.

**Herkkyys:** `arviointi.py` lukee jäsennysvirheet uudelleen ensimmäisestä
kokonaisesta objektista (`raw_decode`) ja raportoi κ:n rinnalla. Ei
muuta päätössääntöä. `stance.py`:n jäsennintä ei muuteta validoinnin
aikana, jotta kaikki ajot jäsennetään samalla koodilla; korjaus tehdään
ennen tuotantokäyttöä.

## B. Tulosten tallennusvirhe workflow'ssa

Ajossa 43391570301 jokainen job latasi artefaktiksi koko `tulokset/`-
hakemiston, joka sisälsi repoon jo committatut tiedostot. Arviointijobin
`merge-multiple`-latauksessa sonnet:high-artefaktin mukana tulleet
**vanhat** `sonnet_low_*.json` (kaikki HTTP 400 -virheitä) ylikirjoittivat
sonnet:low-jobin tuoreet tulokset. Lokin mukaan sonnet:low ajoi
onnistuneesti (0,35 $), mutta tulos ei päätynyt repoon.

Korjaus: kukin job lataa vain omat tiedostonsa (`<malli>_<effort>_*.json`).
sonnet:low ajetaan uudelleen; committoidut tiedostot ovat edelleen
pelkkiä hylättyjä pyyntöjä, joten `stance.py`:n uudelleenajosääntö
koskee niitä. Ensimmäisen onnistuneen sonnet:low-ajon tuloksia ei ole
nähty eikä käytetä.
