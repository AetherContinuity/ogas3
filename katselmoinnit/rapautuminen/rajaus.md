# Tutkimuskäyttö 1: SM-009:n diagnostinen ketju, korpuksen rajaus (27.11.2026)

**Tarkoitus.** Tehdä tarkasteltavaksi ketju, jonka SM-009 § 03 esittää: "Measurement gap → Sanction gap → Correction gap → Structural decay". Tarkoitus ei ole todistaa ketjua. Ketjun linkit ovat tarkasteltavia väitteitä, eivät hyväksyttyjä premissejä. Myös negatiivinen tulos on mahdollinen: linkki voi puuttua, nojata vain toiseen synteesiin tai olla paperissa itsessään rajattu.

Hyväksymistestiä ei tehdä, eikä tulosjoukkoa lukita ennalta.

**Korpus.** `AetherContinuity/aethercontinuity.github.io`, main @ `1f3f4fb` (27.11.2026).

| Paperi | Tiedosto | Viimeisin muutos | sha256 (16) | Peruste |
|---|---|---|---|---|
| SM-009 | papers/sm-009-diagnostic-paradigm.html | 1b84318 | a61d20b4a7025687 | Esittää ketjun (§ 03) ja sen rajaukset ("What the Paradigm Does Not Claim"); tapaukset sanktiovajeesta |
| SM-007 | papers/sm-007-convergence-finding.html | 946bdb1 | 6e2732041c6a4e89 | Rinnakkainen synteesi: yhteinen rakenteellinen ehto ("no actor owns the whole") |
| CN-004 | papers/cn-004-distributed-optimisation.html | 1b84318 | aea8bad97015953e | Kilpaileva tulkinta: korjattava koordinaatiovika vai demokraattisen järjestelmän rakenteellinen ominaisuus; käsittelee rapautumista ("degradation") |
| WP-013 | papers/wp-013-two-scenarios-2030.html | 1b84318 | 59b92d973aaf1879 | SM-009 viittaa: viiveen kustannuksen epälineaarisuus (ketjun loppupää) |
| WP-015 | papers/wp-015-residualization-spot-markets.html | bd689c6 | 0fb827818452d80f | SM-009 viittaa: "the mechanism producing the crisis" (puskurien heikkeneminen) |
| CN-007 | papers/cn-007-miksi-jarkevaet-asiat-eivat-etene.html | 1b84318 | d563dae33b4155dd | Ketjun suomenkielinen sovellus yhteen tapaukseen (kapasiteettimekanismi) |

Korjaus 27.11.2026: CN-004:n, WP-013:n ja CN-007:n "viimeisin muutos" (1b84318) oli väärin. Rajaus tehtiin matalasta kloonista, jossa 1b84318 on historian juuri ja näyttää lisäävän kaikki tiedostot. Oikeat arvot ovat 7ce7d43, c934af8 ja fa39e64 (täyttöpyyntö, ogas3 #54). sha256-tunnisteet olivat oikein.

Yhteensä noin 217 kt HTML:ää. Purettuna se on arviolta 140 000 merkkiä, noin 10 % enemmän kuin täytössä v2. Katto kannattaa harkita uudelleen, koska täyttö v2 käytti 31 342 / 48 000.

**Valintamenetelmä.**
1. Termihaku koko korpuksesta (kirjainkoko ei ratkaise): `three[- ]gap|kolmen vajeen|three gaps|kolme vajetta`, `measurement gap|mittausvaje`, `sanction gap|sanktiovaje`, `correction gap|korjausvaje|repair gap`, `structural (decay|erosion|degradation)|rapautu|institutional decay|degradation accelerates|erosion`, `SM-009`. Osumia 43 tiedostossa.
2. Valintasääntö: (a) ketjun esittävä paperi; (b) papereista, joihin SM-009 viittaa, ne, joita se käyttää ketjun loppupään (korjausvaje → rapautuminen) perusteena; (c) synteesit ja muistiot, jotka esittävät samalle havainnolle rinnakkaisen tai kilpailevan selityksen; (d) yksi lyhyt sovellus.
3. Pois rajattu:
   - TN-014 (HEM-sovellus, laaja, sovellus eikä ketjun perustelu);
   - WP-020, CN-008, SM-024 (jo rekisterissä, pidetään erillään);
   - SP-009 ("erosion" on veropohjan eroosio, eri käsite);
   - WP-016, WP-017, WP-018 (mittausinstrumentit, joihin SM-009 viittaa mittausvajeen operationalisointina; ottaminen mukaan laajentaisi aineiston WP-sarjan yli);
   - muut papereita, joissa SM-009 vain mainitaan (CN-009, SM-010, SM-017 jne.).

   Rajaus tarkoittaa, että ketjun alkupään (mittausvaje → sanktiovaje) näyttö tulee pääosin SM-009:stä itsestään. Tämä on tiedostettu rajoite, ja raportin on todettava se.
4. Rajauksen teki Claude (Opus 5.5). Istunto on nähnyt aiemman väiterekisterityön, mutta se ei koske näitä papereita.

**Menettely.**
1. Puhdas istunto laatii täyttöpyynnön tämän rajauksen pohjalta. Se ei avaa sivuston SEURANTA.md:tä eikä ogas3:n `katselmoinnit/`-hakemiston väiterekisteri- ja diagnostiikkatiedostoja; vain täytön v2 pyyntöä saa käyttää pohjana.
2. Kimi täyttää (katselmointi-workflow), raakatulos tallennetaan muuttamattomana, ja tarkista ajetaan korpusta vasten.
3. **Ennen raakatuloksen avaamista** kirjataan lähdeluenta: mitkä ketjun linkit papereissa ovat, missä kohdissa ja millä perusteella, ja mitä vaihtoehtoisia selityksiä papereissa esitetään. Muuten vertailu "rekisteri vs tavallinen lukeminen" vinoutuu rekisterin hyväksi.
4. Katselmointi: jokainen olennainen suhde tarkistetaan lähdetekstistä. `perusta`-kenttää ei käytetä suodattimena, koska se ei ole toistettava (synteettinen koe, ogas3 #52). Kentän arvo säilytetään sellaisenaan. Kirjataan puuttuvat yhteydet, katkenneet ketjut ja ristiriidat.
5. Raportti: mitä rekisteri teki näkyväksi lähdeluentaan verrattuna, mitä se ei näyttänyt ja mitä se näytti väärin.
