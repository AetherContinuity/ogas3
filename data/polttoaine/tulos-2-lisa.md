# Polttoainekoe 2: lisäanalyysit (28.11.2026, katselmoinnin jälkeen)

Lisäanalyysit eivät korvaa tulos-2:ta. Ne on tehty tulos-2:n jälkeen eivätkä ole ennakkokirjattuja. Raakatulos on `tulos-2-lisa.json`, koodi `tools/polttoaine_massa_lisa.py`.

**Nimitys.** Tulos-2:n "ehdollinen ajo" on tarkemmin **Brent-tapahtumasuodatus**. Siinä poistetaan aktivaatiot viikoilta, joilla tai joita edeltävällä viikolla Brent liikkui samaan suuntaan yli 5 %. Pienemmät Brent-liikkeet, pidemmät viiveet ja muut yhteisvaikutukset jäävät aineistoon. Suodatettu aineisto ei siis ole Brentistä riippumaton.

**L3 Havaintorajat.** Löytöjakso kattaa 3.1.2005–14.12.2015. Vahvistusjakso kattaa 4.1.2016–23.11.2026, koska viimeinen WOB-havainto on 23.11.2026.

**L1 Samat sarjat** (suodatetun ajon 40 sarjaa ja 810 paria molemmissa):

| | Ehdokkaita 2005–2015 | Tapahtumia | Säilyi 2016–2026 |
|---|---|---|---|
| ehdoton | 498 | 2 416 | 270 (54 %) |
| Brent-tapahtumasuodatus | 323 | 1 661 | 190 (59 %) |
| plasebo: sama määrä satunnaisia viikkoja poistettu (5 siementä) | 487–569 | 1 999–2 102 | — |

- Samoilla sarjoilla Brent-suodatus vähentää ehdokkaita 35 %.
- Satunnaisten viikkojen poisto ei vähennä ehdokkaita (487–569 vs 498).
- Vähennys on siis Brent-viikoille ominainen eikä johdu pelkästä tapahtumien määrän vähenemisestä.
- Brent-viikoilla on enemmän tapahtumia kuin satunnaisilla viikoilla (1 661 vs noin 2 040 jäljellä). Tämäkin osoittaa, että tapahtumat kasautuvat Brent-viikoille.
- Säilymisosuus ei samoillakaan sarjoilla laske suodatuksessa (54 % → 59 %).

**L2 NB-p:n kalibrointi tämän kokeen mittakaavassa** (85 sarjaa, 17 840 testiä).

Nollan saa, kun parin sarjat otetaan eri vuosikymmeniltä: tapahtumarakenne on todellinen, mutta todellista keskinäistä ajoitusta ei ole.

| Nolla | BH-ehdokkaita | Osuus p ≤ 0,05 | Osuus p ≤ 0,01 |
|---|---|---|---|
| A 2005–2015, B 2016–2026 | 0 | 0,023 | 0,0026 |
| A 2016–2026, B 2005–2015 | 0 | 0,030 | 0,0044 |

NB-p on tässä mittakaavassa konservatiivinen (osuudet nimellistasoa pienempiä), eikä BH tuota vääriä ehdokkaita.

Ensimmäinen kalibrointiyritys oli virheellinen. Siinä jokainen sarja kierrettiin omalla satunnaisella siirrollaan, ja se tuotti 2–7 "väärää" ehdokasta ajoa kohden. Syy: niissä pareissa, joiden siirtojen ero osui välille 0–4 viikkoa, todellinen kytkentä säilyi, joten asetelma ei ollut nolla. Tulos on kirjattu tähän, ettei sitä tulkita moottorin virheeksi.

**Toistettavuus.** Tulos-2:n maaparilistan järjestys vaihteli tasapelien kohdalla Pythonin hajautussiemenen mukaan. Järjestys on nyt deterministinen. Sisältö on ennallaan, ja `tulos-2.json` on tuotettu uudelleen.
