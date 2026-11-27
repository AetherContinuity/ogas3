# Polttoainekoe 1: tulos (28.11.2026)

Ennakkokirjaus `ennakko.md` (766a5da) ja poikkeama 1 (a4c7d1c) ennen ajoa. Raakatulos `tulos-1.json`.

**Aineisto:**
- WOB FI sha256 39a1250bd36a13e6, 1 094 viikkoa 3.1.2005–23.11.2026
- Brent `datasets/oil-prices` 8fb522ca4a54312d
- FX `datasets/exchange-rates` 247c31ac3ad40e5a

**Testit:** 280 testiä, tarkka kierto-p rinnalla. Jokaisen ehdokkaan tarkka p on kiertojakauman alaraja (havaittu kaikkien kiertojen yläpuolella) yhtä poikkeusta lukuun ottamatta (fidiesel_ylos → fi95_alas, viive 4, p_tarkka 0,0028). Ehdokkaat eivät siis nojaa pelkkään NB-approksimaation häntään.

| Odotus | Koko jakso | 2005–2015 | 2016–2026 |
|---|---|---|---|
| H1 brent_ylos → fi_ylos (0–2 vk) | löytyi: diesel ja 95, viive 0 | löytyi: diesel ja 95, viive 0 | ei |
| H2 brent_alas → fi_alas (0–3 vk) | ei | ei | ei |
| H3 fi95 ↔ fidiesel, sama suunta, viive 0 | löytyi (4/4) | löytyi (4/4) | löytyi (4/4) |
| H4 fi → brent/fx viiveellä ≥ 1 (väärä positiivinen) | 0 | 0 | 0 |
| H5 fx | brent_alas ↔ fx_ylos viive 0 | sama | ei |

**Tulkintasäännön mukaan:** H1 löytyi ja H4 = 0, joten moottori toimii tällä datalla.

**Odottamaton, ei ennakkokirjattu ("muu"):** pumppuhinnan suunnanvaihto seuraavalla viikolla (fi*_alas → fi*_ylos ja fi*_ylos → fi*_alas, viive 1).
- Toistuu molemmilla puolijaksoilla sekä bensiinissä että dieselissä.
- Ilmiö on negatiivinen autokorrelaatio viikkomuutoksissa.
- Se voi olla vähittäishintojen sykli tai WOB-raportoinnin mittausmelua (maanantain hetkihinta). Tämä koe ei erota näitä.
- Sitä ei kirjattu odotukseksi, joten se on ehdokas eikä löydös.

**H2:n puuttuminen:** Brentin yli 5 %:n viikkolasku ei näy samalla tai 1–3 seuraavalla viikolla yli 3 %:n verottomana pumppuhinnan laskuna. Tulos on yhdenmukainen sen kanssa, että laskut välittyvät hitaammin tai pienempinä kuin nousut ("rockets and feathers"). Kynnyspohjainen aktivaatio ei kuitenkaan näe hidasta välittymistä, joten tämä ei ole testi asymmetriasta.

**H1:n heikkeneminen 2016–2026:** syytä ei selvitetty. Mahdollisia selityksiä ovat jakson suuret shokit (2022, 2026) ja tapahtumamäärien jakautuminen, mutta niitä ei testattu.

**Rajoitteet:**
- Kynnykset (5 %, 2 % ja 3 %) on valittu harkinnalla, eikä niiden herkkyyttä testattu.
- Synapsit ovat assosiaatioita, eivät kausaalisuutta.
- Lag 0 -pari näkyy molempiin suuntiin, joten esimerkiksi fidiesel_ylos → brent_ylos viiveellä 0 ei ole käänteinen kausaalisuus.
