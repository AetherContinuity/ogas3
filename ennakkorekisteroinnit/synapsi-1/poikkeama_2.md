# SYNAPSI-1 — poikkeama 2: vertailutasot ja lisälöydön määritelmä (28.11.2026, ennen talvidatan analyysia)

**Syy.** Moottorin tulos ei yksinään kerro, löytääkö moottori mitään, mitä yksinkertaisempi menetelmä ei jo löydä. Polttoainekokeen jälkikäteinen vertailu (`data/polttoaine/korrelaatio-vertailu.md`) osoitti kaksi asiaa:
1. Moottorin viivelöydöt löytyivät myös viiveellisellä korrelaatioskannauksella.
2. Moottorin näennäinen maaryhmä oli aktivaatiorajan valintavaikutus.

Molemmat lukitaan tähän vertailuksi ennen kuin talvidataa katsotaan.

## Kolme vertailutasoa

| Taso | Kysymys | Toteutus |
|---|---|---|
| **K Korrelaatio** | Löytääkö moottori muuta kuin tavallisen (myös viiveellisen) yhteisvaihtelun? | Pearson ja Spearman 15 min ensimmäisistä differensseistä Δx, kaikki 132 suunnattua paria, viiveet 0–8 (A:n Δx hetkellä t vs B:n Δx hetkellä t + d), koko ikkuna ja puolijaksot erikseen. Klusterointi: average linkage, etäisyys 1 − \|r₀\|, katkaisut \|r₀\| ≥ 0,1 ja ≥ 0,2. Puuttuva vartti: pari jätetään pois siltä hetkeltä. |
| **T Tunnetut** | Palauttaako moottori tunnetun rakenteen? | `parametrit.json`:n 15 paria. Raportoidaan, montako tunnetuista moottori löytää ja montako korrelaatiotaso K löytää (\|r\| ≥ 0,1 jollakin viiveellä). |
| **H Holdout** | Säilyvätkö ehdokkaat? | Puolijaksot (ennakko.md): sama pari, viive ± 1, kummallakin puolijaksolla. |

**Korrelaatiorakenne** = pari {A, B}, jonka \|r\| (Pearson tai Spearman) on ≥ 0,1 jollakin viiveellä 0–8 jompaankumpaan suuntaan koko ikkunassa. Toissijainen raja 0,2 raportoidaan rinnalla.

## Lisälöydön määritelmä

Moottorin **lisälöytö** on ehdokas, joka täyttää kaikki seuraavat:
1. Läpäisee BH:n ja monipäiväisyyden (≥ 3 päivää, poikkeama 1).
2. Toistuu kummallakin puolijaksolla (taso H).
3. Tarkistaja hyväksyy sen (ennakko.md).
4. Ei ole tunnettujen listalla (taso T).
5. **Ei kuulu korrelaatiorakenteeseen:** \|r\| < 0,1 kaikilla viiveillä 0–8 molempiin suuntiin, sekä Pearsonilla että Spearmanilla.

**Viive-ehdokas** (raportoidaan erikseen, ei lisälöytö): ehdokas, joka täyttää kohdat 1–4 ja kuuluu korrelaatiorakenteeseen, mutta jonka viive d poikkeaa korrelaation huippuviiveestä vähintään 2 askelta. Viive-ehdokkaalle tehdään oma tarkistus: yhteisesiintymien määrä viiveellä d on kummallakin puolijaksolla suurempi kuin viiveillä d − 2 ja d + 2. Tarkistuksen läpäisevä viive-ehdokas on ehdokas lisäarvoksi, ei osoitettu lisäarvo.

**Ryhmä- ja keskittymäväitteet** (sarja, joka esiintyy monessa ehdokkaassa, tai sarjojen ryhmä) raportoidaan aina sarjojen aktivaatiomäärien rinnalla. Niitä ei esitetä löydöksinä, jos keskittyminen selittyy aktivaatiomäärillä (polttoainekokeen valintavaikutus).

## Tulossääntö

- Jos lisälöytöjä on 0, kirjataan: *moottorin lisäarvoa korrelaatioon ja tunnettuun rakenteeseen nähden ei osoitettu SYNAPSI-1:ssä.*
- Jos lisälöytöjä on ≥ 1, ne raportoidaan yksitellen perusteluineen. Lisäarvo on silloin ehdokas, jonka pitää toistua seuraavana talvena.
- Moottori voi siis hävitä vertailun, ja tämä kirjataan.

**Koneluettavana:** `poikkeama_2.json`. Vertailukoodi kirjoitetaan ja committataan ennen ajoa, ja se ajetaan samalla kertaa kuin moottori.
