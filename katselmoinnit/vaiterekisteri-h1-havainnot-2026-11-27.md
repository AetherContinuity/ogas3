# H1, ensisijainen vertailu — havainnot

Kirjoittaja: Claude (Opus 5.5), istunto joka laati H1:n. **Kontaminoitunut tulkitsija**: tämä tiedosto tulkitsee tulosta, ei muuta sitä. Varsinainen tulos: `vaiterekisteri-h1-ensisijainen-2026-11-27.md`, sääntö `tools/vaiterekisteri_h1.py` (commit 369c7a0, kirjattu ennen ajoa).

## Tulos lyhyesti

H1 ei mene läpi. Kriteerit 5 ja 7 täyttyvät, 1–4 eivät, 6 ei ole testattavissa.

## Mitä tulos mittaa

1. **Hylkäys johtuu kattavuudesta, ei vääristä suhteista.** Kimi poimi 31 esiintymää neljästä pitkästä paperista (WP-020 10, SM-024 10, CN-008 7, CN-030 4). F3 poimittiin (WP-020:005), mutta D1, S1, S2, X2, I2 ja U1–U3 eivät. Kriteerit 1–3 kaatuvat siihen, että kohdat puuttuvat, eivät väärään luokitteluun.
2. **Poiminta painottui eksplisiittisiin ristiviittauksiin.** Lähes kaikki poimitut kohdat ovat 27.11.2026 lisättyjä rajaushuomioita ja SM-024:n kohtia, jotka viittaavat toisiinsa nimeltä. Paperin sisäisiä argumenttiketjuja (premissi → johtopäätös → suositus) Kimi ei poiminut: `depends_on`-suhteita on kolme, ja niistä kaksi on SM-024:n viittauksia CN-030:een.
3. **Väärien riippuvuuksien välttäminen onnistui (kriteeri 5).** X1 ja I1 poimittiin, eikä kumpaakaan kytketty F3:een riippuvuutena tai samana väitteenä. I1 kytkettiin oikein SM-024:n tiivistelmään (`same_claim`). Tämä on H1:n tiukin kriteeri, ja se täyttyi niillä kohdilla, jotka poimittiin.
4. **Q2b:ssä Kimi ja H1 ovat eri mieltä, ja Kimin luenta on tekstissä perusteltu.** H1 odotti CN-008:n rajaushuomion rajaavan F3:a (ja S1:tä). Kimi kirjasi sen rajaavan CN-008:n kannattavuusväitettä (X1). Rajaushuomion teksti alkaa: "Tiivistelmän 'taloudellisesti kannattava' ja yllä oleva kolmen vajeen diagnoosi koskevat kokonaismallia." Se rajaa siis molempia. Koska S1:tä ei poimittu, F3:n puolta ei voinut kirjata. H1:tä ei muuteta; erimielisyys kirjataan tähän.

## Johtopäätös

Vaiheen 1 työkalu toimi: tulos validoitui, kyselyt ja kohdistus ovat deterministisiä. Vaiheen 2 täyttöprosessilla on matala kattavuus mutta tässä aineistossa hyvä tarkkuus. Rekisteri, joka täytetään tällä prosessilla, löytäisi korjauksen jälkeen ne väitteet, jotka viittaavat korjattuun nimeltä, mutta ei paperin sisäisiä riippuvuuksia. Juuri ne olivat H1:n kohde (D1, U1–U3).

Seuraava kysymys ei ole H1:n muuttaminen vaan täyttöprosessi: pitääkö poiminnan kattaa paperin sisäiset argumenttiketjut, ja miten se pyydetään ilman, että pyyntö ohjaa kohti H1:tä. Pyynnön laatii taas istunto, joka ei ole nähnyt H1:tä.

Toissijaista vertailua (ihmisen korjaama versio) ei ole tehty.
