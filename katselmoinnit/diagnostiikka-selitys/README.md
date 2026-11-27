# Diagnostiikka: jääkö selittävä väite pois määritelmän vai poimintakyvyn takia? (kirjattu 27.11.2026 ennen ajoja)

Synteettinen koe. Ei hyväksymistesti, ei H3:n korvike, eikä sen tulosta käytetä H1:n tai H2:n tulosten uudelleentulkintaan. Koe diagnosoi täyttöpyynnön v2 ohjetta yhdellä keksityllä paperilla.

**Paperi.** `korpus/papers/dg-001-seudullinen-talvikunnossapito.html` (DG-001, keksitty). Siinä ei ole lukuja, laskelmia eikä lähdeviittauksia. Sisältö:
- K, kohdeväite (Johtopäätökset, viimeinen kappale, 4. virke): "Yhteisen varakaluston arvo ei kuulu kenenkään tehtävään, koska se syntyy vasta, kun verkot tarkastellaan yhdessä."
- P, K:n premissi samassa kappaleessa: "Kunta arvioi katuverkkoa, maakunta päätieverkkoa ja pelastuslaitos hälytysreittejä. Kukin hoitaa oman osuutensa."
- C, positiivinen kontrolli (koottu luettelorakenne): "Sama kahden vajeen rakenne …" sekä tietovaje ja sopimusvaje.

**Ehdot.** Pyynnöt ovat täytön v2 ohje sellaisenaan. Yhteiset muutokset molempiin ehtoihin: otsikko, "yksi paperi", aineistolista, sallittu paperitunnus DG-001 ja merkintämääritelmän viittauksen poisto, koska paperissa ei ole merkintöjä. Ehtojen välillä eroaa vain yksi rivi (tarkistettu diffillä):
- A (nykyinen): `- aineistohavainto: paperin esittämä havainto, luku, mittaus, lähteen tieto tai laskelman tulos.`
- B (neutraali): `- aineistohavainto: paperin esittämä lähtötieto tai väite, johon jokin toinen väite nojaa.`

Kolme ajoa kumpaakin ehtoa (`dg-a1..3`, `dg-b1..3`, samat tiedostot tavu tavulta ehdon sisällä). Kaikissa Kimi K3.1 Pro, effort max, katto 48000. Raakavastaukset committautuvat workflow'sta ennen tulkintaa.

**Mittarit ajoa kohden** (kohdistus kuten `tools/vaiterekisteri_h2.py`: lainauksen alkukohta virkkeen jänteessä):
- M1: K on poimittu esiintymäksi.
- M2: K depends_on P (suora suhde).
- M3: kontrolli. C on poimittu ja vähintään yksi vaje on suhteessa C:hen. Jos M3 ei täyty, ajo raportoidaan kontrollin osalta epäonnistuneena.

**Tulkintasääntö** (M1, ajoja kolmesta, vain ajot joissa M3 täyttyy):
- B ≥ 2 ja A ≤ 1: määritelmävaikutus tuettu.
- A ≤ 1 ja B ≤ 1: määritelmä ei selitä. Tuettu on poimintakyky tai jokin molempien ehtojen yhteinen ohje.
- A ≥ 2 ja B ≥ 2: kumpikaan ei selitä synteettisessä kokeessa. H2:n puuttumisen syy on jossain, mitä koe ei toista, esimerkiksi pitkässä tekstissä tai kilpailevissa väitteissä.
- A ≥ 2 ja B ≤ 1: raportoidaan sellaisenaan.

Rajoitteet: yksi paperi, kolme toistoa. Paperi on lyhyt, joten tekstin pituus ei ole kontrolloitu muuttuja. Kirjoittaja tuntee H2:n, ja K on muotoiltu sen kohdeväitteen rakenteen mukaan tarkoituksella.
