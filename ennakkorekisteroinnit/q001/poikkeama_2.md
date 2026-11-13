# Q-001 — poikkeama 2: toimijoiden yhdistäminen, pudonneet lausunnot, YVA-katko

**Kirjattu:** 2026-11-13, ennen yhtäkään H1–H4-mittausta.
**Peruste:** riippumaton katselmointi (`katselmoinnit/q001-vastaus-2026-11-13.md`,
Kimi K3.1 Pro), löydökset tarkistettu koodia ja dataa vasten.
**Lukitut tiedostot** (`q001.md`, `q001.py`, `lahto_*.json`) ovat ennallaan.
Ensisijaiset tulokset lasketaan lukitulla `q001.py`:llä.

## A. H1 ja H1b laskevat nimiä, eivät toimijoita

`q001.md` määrittelee DT:n toimijoina ja konserneina ("Google/Tuike").
`q001.py` laskee H1:ssä ja H1b:ssä erilliset nimimerkkijonot; H2 yhdistää
nimet `actors.canonical()`-funktiolla, H1 ja H1b eivät. Saman konsernin
kaksi lausujaa lasketaan kahdesti, mikä kallistaa kohti TUETTU-tulosta.

**Herkkyys:** H1 ja H1b raportoidaan lisäksi `canonical()`-yhdistetyillä
nimillä (`q001_poikkeama_2.py`). Jos ensisijainen ja herkkyystulos eroavat,
molemmat raportoidaan eikä ensisijaista muuteta.

## B. Laatijattomat lausunnot putoavat hiljaa

`lausunnonantajat()` ohittaa LAUSUNTO-solmut, joilta laatijaa ei saada.
Määrää ei raportoida. Tämä voi pienentää H1:n lukua ja H2:n leikkausta.

**Raportointi:** jokaiseen H1–H2-tulokseen liitetään LAUSUNTO-solmujen
kokonaismäärä ja laatijattomien määrä esimerkkeineen.

## C. Marraskuun 2026 snapshotista puuttuu YVA

`snapshots/2026-11.json`: `{"source": "YVA", "error": "yva-proxy HTTP 502"}`.
Index-haku epäonnistui kerran, koko YVA-kaappaus putosi, ja snapshot
tallentui ilman varoitusta. YVA-rekisteriä ei päivitetty.

Tieto ei katoa: keskeneräisten hankkeiden sivut haetaan joka ajossa, ja
aikataulurivit (myös loka–marraskuun nähtävilläolot) säilyvät sivuilla.
Joulukuun ajo palauttaa ne `known_at`-päivineen. H4 yhdistää tapahtumat
slugin mukaan kaikista snapshoteista, joten puuttuva kuukausi ei muuta
H4:n lukua, jos joulukuun kaappaus onnistuu.

**Korjaus instrumenttiin (ei vaikuta lukittuun mittauskoodiin):**
`yva.py` yrittää 5xx- ja verkkovirheissä kolmesti; `monthly-snapshot`
merkitsee ajon punaiseksi, jos jokin lähde palautti virheen.

**Tarkistus joulukuun ajon jälkeen:** `q001_poikkeama_2.py yva` listaa
kunkin snapshotin YVA-tilan ja D-hankkeiden nähtävilläolot 1.10.–30.11.2026
sekä ensimmäisen snapshotin, jossa kukin näkyy. Tulos kirjataan
`q001-tulokset.md`:hen H4:n yhteyteen.

## Katselmoinnin löydökset, joita ei kirjattu poikkeamaksi

- **H4 `known_at`.** Aiheeton: `yva.py` dokumentoi `known_at` = aikataulurivin
  päivä (kuulutuspäivä), joka vastaa menettelyn alkua. Katselmoijalla ei
  ollut `yva.py`:tä.
- **H3 `projectId` hankenumerona ja hankkeen nimi tunnistuksessa.** Kirjataan
  tulkintana H3:n raportointiin: lähtötaso (97 %) on laskettu samalla
  tavalla, joten vertailu lähtötasoon on johdonmukainen.
