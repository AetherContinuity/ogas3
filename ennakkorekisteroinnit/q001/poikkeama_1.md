# Q-001 — poikkeama 1: YVA-vaiheiden tunnistus laajeni lukituksen jälkeen

**Kirjattu:** 2026-10-01, ennen yhtäkään H4:n mittaussnapshotia (ensimmäinen on 2026-11).
**Koskee:** H4. H1, H1b, H2 ja H3 eivät käytä YVA-vaiheita.
**Lukitut tiedostot** (`q001.md`, `q001.py`, `lahto_*.json`) ovat ennallaan.

## Mitä muuttui

H4 laskee YVA-tapahtumat, joiden `vaihe == "ohjelma_nahtavilla"`. Vaiheen
asettaa aci-yva-proxy hankesivun tekstistä. Lukitushetkellä (82b3bde,
2026-09-30) tunnistus vaati sanan **"nähtävillä"**.

OGAS3:n ensimmäinen täysi kaappaus (2026-10-01, run 36862714217) löysi
32 tunnistamatonta aikataulua riviä, mm.:

    YVA-ohjelma oli kuultavana 4.11.-5.12.2022.

Proxy hyväksyy 2026-10-01 alkaen nähtävilläolon synonyymeinä myös
**"kuultavana"** ja **"kuulutus"**. Lisäksi uudet vaiheet
`taydennyspyynto` ja `selostus_lausunto` sekä ei-vaihe `yleisotilaisuus`
(ne eivät vaikuta H4:ään).

## Miksi tämä on poikkeama

Muutos voi vain **lisätä** `ohjelma_nahtavilla`-tapahtumia. H4:n ennuste on
`>= 3`, joten muutos kallistaa tulosta kohti TUETTU-tulosta. Instrumentin
parannus lukituksen jälkeen on silti instrumentin vaihto.

## Miten H4 raportoidaan

1. **Ensisijainen = lukittu instrumentti.** Jokaisen YVA-tapahtuman
   `evidence[0].quote` on alkuperäinen aikataulurivi. H4 lasketaan
   uudelleen soveltamalla siihen lukitushetken säännöllistä lauseketta:

       /(arviointi|yva-)ohjelm\S*[^.]{0,40}?nähtävillä/i

   ja ohittamalla rivit, joihin aiempi järjestys (perusteltu päätelmä,
   ohjelmalausunto) osuisi ensin. Vain tämä luku ratkaisee TUETTU/KUMOTTU.
2. **Herkkyys = nykyinen instrumentti.** `q001.py H4` sellaisenaan.
   Raportoidaan rinnalla. Jos tulokset eroavat, ero raportoidaan
   hankkeittain eikä ensisijaista tulosta muuteta.

Laskenta tehdään uudessa tiedostossa (`q001_poikkeama_1.py`) ennen
ensimmäistä H4-mittausta. `q001.py`:tä ei muuteta.
