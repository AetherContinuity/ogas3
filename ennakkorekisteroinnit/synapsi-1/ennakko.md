# SYNAPSI-1: ehdokassynapsit sähköjärjestelmän sarjojen yhteisesiintymistä, talvi 2026–2027 (ennakkokirjaus 28.11.2026)

Parametrit: `parametrit.json` (koneluettava, sitova). Moottori: `tools/synapsi.py` (tarkka kiertonollamalli; NB-häntä-p, `p_tarkka` rinnalla). Menetelmä on validoitu synteettisesti ja polttoainekokeessa 1.

**Kysymys.** Löytääkö deterministinen yhteisesiintymämoottori yhteyksiä, joita ei ole kirjattu tunnetuiksi? Kestävätkö ne tarkistuksen, ja toistuvatko ne?

**Aineisto.** 12 Fingrid-sarjaa 15 min resoluutiolla, 1.10.2026–31.3.2027. Datakeskuksille ja PtX-elektrolyysille ei ole omaa julkista sarjaa; ne sisältyvät kulutukseen (DS 124).

**Ajo.** Aikaisintaan 2.4.2027, kun molemmat keruut kattavat ikkunan. Moottoria ei ajeta talvidataan ennen sitä. Ajetaan koko ikkuna, kumpikin puolijakso erikseen ja herkkyysajo ilman 27.11.2026.

**Mittarit** (ei läpäisyrajaa; raportoidaan sellaisinaan):
1. **Tarkkuus:** ehdokkaista se osuus, jonka tarkistaja hyväksyy fysikaalisesti tai markkinaperusteisesti uskottavaksi assosiaatioksi (hyväksy / hylkää / avoin). Hyväksyntä ei tarkoita kausaalisuutta.
2. **Uutuus:** hyväksytyistä ne, jotka eivät ole `tunnetut`-listalla.
3. **Toistettavuus:** ehdokas löytyy kummaltakin puolijaksolta erikseen (sama pari, viive ± 1).

**Tunnetut kytkökset** (15 paria, `parametrit.json`) kirjattiin ennen kuin talven dataa on analysoitu. Claude laati listan fysiikan ja markkinamekanismin perusteella, ja Marko täydensi sitä sähkökattiloilla ja akuilla.

**Kontaminaatio, kirjattu:**
- Tarkistaja on Marko. Hänen järjestelmätietämyksensä on uutuuden raja, joten uutuus mittaa yhteyksiä, jotka puuttuvat tältä listalta ja tämän tarkistajan tiedosta. Se ei ole objektiivinen mitta.
- Kumpikin on nähnyt 27.11.2026 klo 16.15–19.15 tapahtuman (RP_margin 0–18 %, ylössäätöhinta jopa 5 001 €/MWh) WEM-L1:n välihavainnossa. Kirjaaja on nähnyt WEM-L1:n välihavainnon DS 244:stä, 373:sta ja 342:sta, mutta ei muita ikkunan sarjoja. Säännöt on asetettu fysiikan perusteella. Tapahtuman vaikutus näkyy herkkyysajosta.
- Ydinvoima on Markon mukaan poikkeustilassa ikkunan alussa, joten ydinvoiman aktivaatiot todennäköisesti kasautuvat siihen.

**Muutokset** parametreihin tai menetelmään kirjataan `poikkeama_N.md`:hen ennen ajoa. Ajon jälkeen niitä ei tehdä.
