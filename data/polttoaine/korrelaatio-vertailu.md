# Polttoainekoe 2: korrelaatiovertailu (28.11.2026, JÄLKIKÄTEINEN, ei ennakkokirjattu)

Vertailu tehtiin moottorin tuloksen jälkeen, joten se ei ole koe vaan tarkistus. Raakatulos on `korrelaatio-vertailu.json`, koodi `tools/polttoaine_korrelaatio.py`.
- Aineisto, jaksot, viikkomuutos-% ja aukkosääntö ovat samat kuin moottorilla.
- Sarjoina ovat ne 47 maa × tuote -sarjaa, jotka esiintyvät moottorin ehdottomassa ajossa.
- Vertailuryhmä on lukittu tulos-2.md:stä: LU, DK, SE, BE, DE, EE, FI.
- Testattava ennuste (Claude, 28.11.): matriisi löytää saman ryhmän, ja moottorin lisäarvo on enintään viivetieto.

**V1–V2 Samanaikainen korrelaatio ja klusterointi.**

| | 2005–2015 raaka | 2005–2015 Brent-residuaali | 2016–2026 raaka | 2016–2026 Brent-residuaali |
|---|---|---|---|---|
| Pearson, mediaani kaikista pareista | 0,35 | 0,15 | 0,40 | 0,24 |
| Ryhmän sisällä, eri maat | 0,38 | 0,16 | 0,32 | 0,19 |
| Ryhmä vs muut | 0,31 | 0,11 | 0,33 | 0,19 |
| Paras klusterivastaavuus (Jaccard) | 0,33–0,50 | 0,25–0,29 | 0,17–0,43 | 0,29–0,43 |

Spearman antaa saman kuvan. Brent-residuaalin klusteroinnissa ryhmää ei synny. Esiin tulee vain ydin DK–SE(–NL tai –LU). Jälkimmäisellä jaksolla ryhmän sisäinen korrelaatio on sama kuin ryhmän ja muiden välinen (0,19 / 0,19).

**Valintavaikutus.** Tämä selittää, miksi moottorin "ryhmä" näytti ryhmältä. Brent-suodatetun ajon aktivaatioraja (≥ 20 aktivaatiota kummallakin jaksolla) jätti jäljelle vain 40 sarjaa 14 maasta: BE, DE, DK, EE, FI, FR, HU, IE, LU, LV, NL, SE, SI ja SK. Kaikki seitsemän ryhmän maata ovat näiden joukossa, ja niillä on 3–4 sarjaa kullakin. Ryhmä on siis pääosin maat, joiden verottomissa hinnoissa on usein yli 3 %:n viikkoliikkeitä Brent-viikkojen ulkopuolella. Se ei ole moottorin löytämä erillinen yhteisvaihtelun rakenne. Tulos-2:n tulkinta Luoteis-Euroopan ja Pohjolan ryhmästä yhteisenä tukkuajurina oli liian vahva.

**V3 Viive.** Moottorin kymmenestä viiveellisestä säilyneestä (Brent-suodatus) viidellä viiveellinen Pearson on saman viiveen kaikkien 2 162 parin korrelaatioiden kärjessä:

| Pari | Sija | r |
|---|---|---|
| DK → HU | 3 | 0,46 |
| SE → HU | 9 | 0,41 |
| DK → HU | 11 | 0,41 |
| LU → SI, viive 2 | 7 | 0,28 |
| HU → SI | 65 | 0,29 |

Samanaikainen r on näillä pareilla −0,12…+0,11. Samanaikainen matriisi ei siis näe näitä yhteyksiä, mutta viiveellinen korrelaatioskannaus näkee. Unkarin viikon viive voi johtua raportointipäivästä tai hinnoittelusta; tätä ei tarkistettu.

**Ennusteen arvio.**
- *"Matriisi löytää saman ryhmän"*: ei pitänyt. Pääsyy on kuitenkin se, ettei ryhmä ollut todellinen rakenne vaan valintavaikutus.
- *"Moottorin lisäarvo on enintään viivetieto"*: piti samanaikaiseen matriisiin verrattuna. Viiveellistä korrelaatioskannausta vastaan moottorin viivelöydöt eivät ole ainutlaatuisia.

**Johtopäätös.** Tällä aineistolla moottori ei löytänyt mitään, mitä viiveellinen korrelaatioskannaus ja aktivaatiomäärien tarkastelu eivät olisi löytäneet. Moottorin ryhmätason tulkinta johti harhaan, koska aktivaatioraja valitsi sarjat. Synapsimoottorin lisäarvoa tässä käyttötarkoituksessa ei ole osoitettu.
