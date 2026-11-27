# Polttoainekoe 2: synapsien massa ja karsinta (kirjattu 28.11.2026 ennen ajoa ja ennen kuin muiden maiden sarjoja on nähty)

**Tarkoitus.** Tuotetaan ehdokassynapsien massa ja mitataan, kuinka suuri osa siitä (a) selittyy yhteisellä tunnetulla ajurilla ja (b) säilyy riippumattomalla vahvistusjaksolla. Kirjaaja on nähnyt Suomen sarjat (koe 1) ja EU-keskiarvojen viimeiset rivit, ei muiden maiden sarjoja.

**Aineisto.**
- EU Weekly Oil Bulletin -hintahistoria, verottomat hinnat (Prices wo taxes), kaikki maat, joilla on sekä Euro-super 95- että dieselsarake (`XX_price_wo_tax_euro95`, `XX_price_wo_tax_diesel`). EU- ja EUR-keskiarvot jätetään pois.
- Brent ja EUR/USD kuten kokeessa 1.

**Sarjat ja aktivaatiot.**
- Viikkomuutos-%. Jokainen maa × tuote × suunta on oma sarjansa: ylös ≥ +3 %, alas ≤ −3 %.
- Yli 13 vuorokauden aukko → muutos None.
- Sarja otetaan mukaan, jos sillä on vähintään 20 aktivaatiota kummallakin jaksolla.

**Parit.** Vain saman suunnan parit (ylös → ylös, alas → alas), eri sarjojen välillä, kaikki suunnatut. Suunnanvaihtoparit jätetään pois (koe 1: ne ovat todennäköisesti mittausmelua tai sykliä). Viive 0–4 viikkoa, vähimmäissiirto 16, NB-p, BH α = 0,05.

**Jaksot.**
- Löytö: 2005-01-01 – 2015-12-31, kaikki parit.
- Vahvistus: 2016-01-01 – 2026-12-31. Vain löytöjakson ehdokkaat (sama pari ja viive) testataan, BH niiden joukon yli. Ehdokas *säilyy*, jos se läpäisee vahvistuksen.

**Ajurin karsinta (ehdollinen ajo).** Samat ajot toistetaan niin, että kustakin sarjasta poistetaan aktivaatiot, joiden viikolla tai edellisellä viikolla Brentin viikkomuutos on samaan suuntaan yli 5 %. Jäljelle jäävät tapahtumat ovat Brentistä riippumattomia. Synapsi, joka häviää ehdollisessa ajossa, selittyy Brentillä.

**Raportoidaan:**
- ehdokkaiden määrä löytöjaksolla, säilyneiden määrä ja osuus, ehdoton ja ehdollinen erikseen
- säilyneiden jakauma: viive 0 vs ≥ 1; maaparit (sama maa eri tuote / eri maa)
- tunnistettavat ryhmät (esim. naapurimaat, euron ulkopuoliset)

**Odotukset** (kuvailevat, ei läpäisyrajaa):
- **E1** Ehdoton massa on suuri ja koostuu enimmäkseen viiveen 0 pareista.
- **E2** Ehdollinen ajo poistaa suurimman osan ehdottomista ehdokkaista.
- **E3** Säilymisosuus on ehdollisessa ajossa pienempi kuin ehdottomassa.
- **E4** Ehdollisessa ajossa säilyvät ovat enimmäkseen saman maan bensiini ↔ diesel -pareja tai alueellisia ryhmiä. Ryhmiä ei nimetä etukäteen.

**Rajaus.** Synapsi on assosiaatio, ei kausaalisuus. Tunnettu ajuri on vain Brent. Muut yhteiset tekijät (valuutat, verotus, jalostamomarginaalit) jäävät mukaan ja näkyvät synapseina.
