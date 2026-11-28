# Q-002 poikkeama 1 — H1: kiinteän pääoman kuluminen eri Eurostat-taulusta

**Kirjattu:** 28.11.2026, ennen kuin H1:n tulosta on nähty.

## Mitä tapahtui

Lukittu `q002.py` hakee kulumisen (P51C) taulusta `nama_10_gdp`. Siinä taulussa ei ole P51C:tä.
Ensimmäinen ajo (workflow `q002`, 28.11.2026, `tulokset/H1-2026-11-28.json`) palautti kaikille maille
ja vuosille `null` ja tuloksen "aineisto puutteellinen". Lukuarvoja ei syntynyt eikä nähty.

Syy selvitettiin diagnostiikalla (`tools/q002_diag.py`, haara `q002-diag`), joka tulostaa vain
vastausten rakenteen: dimensiot, kategoriakoodit ja arvojen määrän, ei yhtään lukuarvoa. Havainnot:

- `nama_10_gdp`, na_item P51C: na_item-dimensio on tyhjä, 0 arvoa.
- `nasa_10_nf_tr`, na_item P51C, sector S1, direct PAID, unit CP_MNAC: arvoja on DK:lle, FI:lle ja
  SE:lle 2008–2025 (54). Norjaa ei ole.
- `nama_10_gdp` B1GQ (CP_MNAC, CLV20_MNAC) ja `nama_10_pe` POP_NC: arvoja kaikille neljälle maalle.

## Korjaus

`q002_poikkeama_1.py H1` laskee H1:n samalla kaavalla ja samoilla kynnyksillä kuin lukittu koodi.
Ainoa muutos on, että P51C haetaan taulusta `nasa_10_nf_tr` (sector S1, direct PAID, unit CP_MNAC).
B1GQ, volyymiyksikkö ja väestö haetaan kuten ennen. Norja jää pois, koska kulumista ei ole saatavilla.
Norja ei ollut testissä alun perinkään.

Ensisijainen tulos on lukitun koodin tulos ("aineisto puutteellinen"). Poikkeaman tulos raportoidaan
sen rinnalla ja merkitään poikkeamaksi.
