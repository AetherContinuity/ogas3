# OGAS3 — ohje Claude-istunnoille

Lue tämä ennen kuin muutat mitään. Repo on Marko Ruotsalaisen (ACI) mittausjärjestelmä
suomalaisen lainvalmistelun seurantaan. Kieli: suomi, kuiva ja suora.

## Pysyvät säännöt

- **Lukitut tiedostot eivät muutu.** Ennakkorekisteröinnit (`ennakkorekisteroinnit/*/q*.md`,
  `kehikko.md`, `prompt.md`, `ihminen.json`, `otos.json`) ja niiden mittauskoodi on lukittu
  yhdistettäessä. Korjaus = uusi `poikkeama_N.md` (+ tarvittaessa `*_poikkeama_N.py`),
  kirjattuna ENNEN tulosta, jota se koskee. Ensisijainen tulos lasketaan aina lukitulla koodilla.
- **Muutokset PR:nä**, ei suoraan mainiin. Käyttäjä yhdistää.
- **Snapshotit ovat todisteita**, niitä ei muokata.
- **Ei API-avaimia keskusteluun.** Avaimet ovat GitHub Actions -salaisuuksina:
  `MOONSHOT_API_KEY` (Kimi), `OGAS3ANTH_API_KEY` (Claude API, workspace-rajattu).
- Vain vakiokirjasto (ks. `monthly-snapshot.yml`).

## Kimi K3.1 Pro (Moonshot AI) — kaksi roolia

Otettu mukaan 12.11.2026. Avoimen painon malli, OpenAI-yhteensopiva API
(`https://api.moonshot.ai/v1`, malli `kimi-k3.1-pro`). Ei päivättyjä snapshot-tunnisteita
eikä `system_fingerprint`:iä; knowledge cutoffia ei ole julkaistu.

### 1. Luokittelija (stance) — validoitu, ei vielä tuotannossa

- Tehtävä: lausunnon vastauksen kanta luonnokseen (kannattaa / kannattaa_muutoksin /
  vastustaa / ei_kantaa / epaselva). Kaikki muu putkessa on determinististä.
- Validointi `ennakkorekisteroinnit/stance/`: `kehikko.md` → `otos.json` → `ihminen.json`
  → `stance.py` → `arviointi.md`. Tila ja johtopäätökset: **`tila.md`**.
- Tulos: kaikki neljä (Kimi low/max, Sonnet 5.5 low/high) läpäisivät lukitun säännön;
  valinta **Kimi low** (κ 0,634, toistot 0,947, 0 keksittyä otetta, 0 muotovirhettä).
- Rajoitteet: mittapuu oli nopea käsikoodaus (`rajoite_1.md`), n = 31, luottamusvälit
  päällekkäin. Kehikon aukko: perustelujen täydennyspyyntöjä ei voi luokitella ilman
  luonnoksen sisältöä. **Ennen tuotantoa kehikko v0.2** (lista `tila.md`:ssä).
- Tietohorisontti: varma raja `classified_at`, ehdollinen julkaisupäivä 2026-10-23.
- Tietueet `aci/stance/v0.1`, ei `classification.py`:n `llm_classification`-kenttää.

### 2. Riippumaton katselmoija — käytössä

- `tools/katselmointi.py` + workflow `katselmointi` (käsin). Pyyntö tiedostona
  `katselmoinnit/<nimi>-pyynto.txt`, vastaus committautuu `<nimi>-vastaus-<pvm>.md`.
  Vastaus striimataan (ilman striimausta yhteys katkesi ~17,5 min kohdalla, aether-one).
  Oletus max-effort, katto 48k; molemmat workflow-syötteitä. **Katto sisältää
  päättelytokenit**: Q-001-katselmointi käytti 29 456 / 32 000, josta päättelyä 23 647.
- Katselmointi on **lausunto, ei mittaus**. Jokainen löydös tarkistetaan koodia ja dataa
  vasten ennen kuin siitä kirjataan mitään.
- Ensimmäinen (13.11.2026): Q-001:n mittauskoodi vs esirekisteröinti → Q-001
  `poikkeama_2.md` (toimijoiden yhdistäminen, pudonneet lausunnot) ja YVA-kaappauksen
  502-vika (`yva.py` uudelleenyritys, lähdevirheet punaiseksi).
- Pyyntöön mukaan kaikki, mitä katselmoija tarvitsee (myös apumoduulit kuten `yva.py`,
  `actors.py`): Kimillä ei ole verkkoa eikä repoa. Rivinumerot koodiin. Kielto ehdottaa
  lukittujen rajojen muuttamista.

Katselmoija kannattaa vain, kun ulkoista mittapuuta ei ole. Jos testivektorit, synteesi
tai tahallinen rikkominen (negatiivikontrolli) ratkaisee kysymyksen, ne ovat halvempia
ja varmempia kuin lausunto.

### Mihin Kimiä EI käytetä

- **Lukittuihin mittauksiin** (Q-001 H1–H4 ovat laskentaa kiinteillä listoilla).
- Liitosavaimiin, aikaleimoihin, diaarinumeroiden poimintaan: regex ja koodi.
- Mittapuuksi itselleen: Kimi arvioi huonosti omaa suoritustaan.

## Tunnetut ansat

- `stance.py`:n jäsennin ottaa `{`…`}` ahneesti (poikkeama 2): Sonnet kirjoitti 6/62
  kertaa JSONin perään korjausyrityksen. Korjattava ennen tuotantoa.
- Workflow-artefaktit: lataa vain jobin omat tiedostot (koko hakemisto ylikirjoitti
  tuoreet tulokset, ajo 43391570301). Tulos-commitissa `git pull --rebase` ennen pushia.
- Re-run ajaa vanhan commitin version; uusi ajo aina "Run workflow" -napista.
- Katselmointi-workflow haaralla: commit-vaihe rebasoi ajohaaran päälle (ennen mainin päälle → push hylättiin, vastaus hävisi, ajo 43918481837).
- Anthropic-avain ilman workspace-rajausta → HTTP 400 ennen mallia.
- Snapshotin lähdevirhe ei kaada kaappausta; katso `queries[].error`.

## Aikataulu

- Q-001 H1/H1b/H2: mitataan 1.12.2026 kaappauksen tracesta (lukittu ≥ 8.11.).
  Lisäksi `q001_poikkeama_2.py H1|H1b|diag|yva`.
- H3 maaliskuu 2027, H4 snapshotit 11/2026–4/2027.
