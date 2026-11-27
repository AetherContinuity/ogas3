# SYNAPSI-1 — poikkeama 1: monipäiväisyysehto (28.11.2026, ennen talvidatan analyysia)

**Syy.** Yksi poikkeuksellinen tapahtuma, kuten 27.11.2026 iltapäivä, voi tuottaa useita aktivaatioita usealle sarjalle ja täyttää yksinään parin yhteisesiintymät. Jaksotus estää yhden pitkän tapahtuman monistumisen, mutta ei saman päivän toistuvia lyhyitä tapahtumia. Herkkyysajo ilman 27.11. kattaa vain yhden tunnetun päivän.

**Muutos.**
- `synapsi.arvioi(..., askelia_paivassa=96, min_paivia=3)`.
- Ehdokas kelpaa vain, jos sen yhteisesiintymät jakautuvat vähintään kolmelle eri UTC-päivälle. Päivä on A-tapahtuman vuorokausi ikkunan alusta laskettuna.
- Alle kolmen päivän ehdokkaat raportoidaan erikseen (`hylatyt_monipaivaisyys`) eivätkä ne ole ehdokkaita.
- Jokaiselle ehdokkaalle raportoidaan päivien lukumäärä.

**Ennallaan:** aktivaatiot, viive, nollamalli, NB-p, BH, tunnetut kytkökset, mittarit, puolijaksot ja herkkyysajo. Monipäiväisyys tarkistetaan BH:n jälkeen, joten se ei muuta testimäärää.

**Validointi synteettisellä datalla** (`tests/test_synapsi.py`):
- yhden päivän 12 kytkettyä tapahtumaa: BH hyväksyy, monipäiväisyys karsii (≤ 2 päivää)
- kymmenelle päivälle jakautunut sama kytkös: säilyy

**Koneluettavana:** `poikkeama_1.json`.
