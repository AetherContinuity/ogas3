# Polttoainekoe 2: tulos (28.11.2026)

Ennakkokirjaus `ennakko-2.md` (8594144); analyysikoodi committattu ennen ajoa. Ensimmäisessä ajossa mukana oli EU-keskiarvo, vaikka ennakkokirjaus rajasi sen pois. Ajo uusittiin kirjauksen mukaisesti, ja vain jälkimmäinen raportoidaan; ensimmäisen luvut olivat lähes samat (2 302 / 1 375). Raakatulos `tulos-2.json`, WOB sha256 39a1250bd36a13e6.

| | Ehdoton | Ehdollinen (Brent-viikot poistettu) |
|---|---|---|
| sarjoja (≥ 20 aktivaatiota kummallakin jaksolla) | 85 | 40 |
| pareja / testejä löytöjaksolla | 3 568 / 17 840 | 810 / 4 050 |
| ehdokkaita 2005–2015 | 2 196 (viive 0: 1 478) | 323 (viive 0: 292) |
| säilyi 2016–2026 | 1 291 (58,8 %) | 190 (58,8 %) |
| säilyneistä viive 0 | 1 048 | 180 |
| säilyneistä sama maa (bensiini ↔ diesel) | 80 | 34 |

**Odotukset:**
- **E1 toteutui.** Massa on suuri (2 196 ehdokasta), ja kaksi kolmasosaa on viiveen 0 pareja.
- **E2 toteutui osittain.** Ehdokkaita on 85 % vähemmän. Osa vähenemisestä johtuu kuitenkin siitä, että Brent-viikkojen poiston jälkeen vain 40 sarjaa täytti aktivaatiorajan. Parikohtaisesti ehdokkaita on 0,62 / pari → 0,40 / pari, joten Brent selittää osan, mutta ei suurinta osaa.
- **E3 ei toteutunut.** Säilymisosuus on molemmissa sama (58,8 %).
- **E4 ei toteutunut sellaisenaan.** Säilyneistä vain 18 % on saman maan pareja. Säilyneet keskittyvät maihin LU, DK, SE, BE, DE, EE ja FI (eniten esiintymiä LU 66, DK 58, SE 53).

**Mitä tämä näyttää:**
- **Brent ei ole massan ainoa yhteinen ajuri.** Sen poiston jälkeen jää ryhmä maita, joiden verottomat hinnat liikkuvat samalla viikolla, ja tämä ryhmä toistuu toisella vuosikymmenellä.
- **Ryhmän ilmeinen ehdokasselitys** on yhteinen tukkuhinta (Luoteis-Euroopan jalostetut tuotteet) ja nopea läpimeno kuluttajahintaan. Tietääkseni Luxemburgissa on viranomaisen asettama enimmäishinta, joka seuraa tukkunoteerauksia; tätä ei tarkistettu.
- **Moottori ei nimeä ajuria.** Se näyttää, että ajuri on, ja ketkä sitä seuraavat. Seuraava karsintakierros olisi ehdollistaa tukkuhintaan samalla tavalla kuin Brentiin, mutta tukkuhintasarjaa ei tässä ollut.
- **Viiveellisiä säilyneitä on vain 10,** esimerkiksi DK → HU ja HU → SI viiveellä 1. Ne voivat johtua maiden eri raportointipäivistä. Tätä ei tarkistettu.

**Johtopäätös rajattuna:** Massa syntyy helposti, ja suurin osa siitä on yhteisten ajurien varjoja. Karsinta riippumattomalla jaksolla säilytti noin 59 % kummassakin ajossa, joten toistuvuus yksin ei erota varjoa todellisesta rakenteesta. Erottelun tekee ajurin ehdollistaminen. Se on mahdollista vain, kun ajuri on mitattavissa ja nimetty.
