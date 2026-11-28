# Q-004 poikkeama 1 — tulkintasääntö H2:lle ja kuvaileva arvonlisämittari

**Kirjattu:** 28.11.2026, ennen yhtään Q-004:n mittausta. Lukittuja mittareita, kynnyksiä ja
ennakkoehtoa ei muuteta.

## Peruste

Kansainväliset pilvi- ja datakeskusyhtiöt laskuttavat eurooppalaiset asiakkaansa tyypillisesti
Irlannin tai muun pääkonttorimaan konserniyhtiön kautta. Suomalainen datakeskusyhtiö on usein
konsernin sisäinen palveluntuottaja, joka laskuttaa emoaan kustannuksillaan ja pienellä katteella
(cost-plus, ks. SM-023). Silloin voittoa ei kirjaudu Suomeen, eikä sitä makseta Suomesta ulos.
H2:n mittari (FDI-tuotot ulkomaille) jää pieneksi, vaikka arvo ei jää Suomeen.

## Lisäys 1: tulkintasääntö

H2:n kumoutumista ei saa lukea todisteeksi siitä, että datakeskusten arvo jäi Suomeen. Jos H2
kumoutuu, tulos raportoidaan muodossa "FDI-tuotot eivät kasvaneet" yhdessä lisäyksen 2 mittarin
kanssa. Kumpikin seuraava tulkinta on silloin mahdollinen: voittoja ei syntynyt, tai ne kirjattiin
Suomen ulkopuolelle. Tämä aineisto ei erota niitä toisistaan.

## Lisäys 2: kuvaileva mittari (ei kumoamisehtoa)

Toimialat J62_J63 ja L681_L68209_L683, S1, käyvin hinnoin (ntp 15ad), vuodet 2025 ja 2029:

- bruttoarvonlisä B1GPH ja nettotoimintaylijäämä B2N, M€
- kumpikin suhteessa toimialojen kulumisen (P51CK, 15af) muutokseen 2025→2029
- jos TEM040:n datakeskusrekisteristä on saatavilla datakeskusten sähkönkulutus (TWh) vuodelta 2029,
  B1GPH ja B2N per TWh. Arvo syötetään käsin argumenttina, ja lähde kirjataan tulokseen. Jos tietoa
  ei ole, kenttä on "aineisto puutteellinen".

Ajo: `python3 ennakkorekisteroinnit/datakeskus-nkt/q004_poikkeama_1.py KUVAILE [--twh X --lahde "..."]`
