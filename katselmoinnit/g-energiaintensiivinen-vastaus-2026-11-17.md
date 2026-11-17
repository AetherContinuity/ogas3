# Katselmointi (LLM) — lausunto, ei mittaus

```json
{
 "pyynto": "katselmoinnit/g-energiaintensiivinen-pyynto.txt",
 "pyynto_sha256": "bc45ee47c257af6aa4340a6fba9426a24092254399d094cfd5a1ef2474cefd05",
 "malli": "kimi-k3.1-pro",
 "response_model": "kimi-k3.1-pro",
 "effort": "max",
 "aika": "2026-11-17T12:08:53+00:00",
 "finish_reason": "stop",
 "usage": {
  "prompt_tokens": 10246,
  "completion_tokens": 28415,
  "total_tokens": 38661,
  "completion_tokens_details": {
   "reasoning_tokens": 24311
  },
  "prompt_tokens_details": {
   "cache_write_tokens": 10240
  }
 },
 "hinta_usd": 0.3046
}
```

## Kokonaisarvio

Tuloste ja muistion tulostaulukko ovat keskenään yhtenevät. Keskeisimmät ongelmat eivät ole tulosteen aritmetiikassa, vaan siinä, että **”nettovaikutus” jää osittaiseksi ja päälukemat esitetään lähes yläpään oletuksin**. Ilmoitetut välit ovat ehdollisia herkkyysvälejä, eivät kattavia epävarmuusvälejä.

## 1. Vastaavuus lukittuihin sääntöihin — vakavimmat ensin

- **Kustannuksia puuttuu nettolaskelmasta.** Lisäys 1 määrää energiavarastot kustannuseräksi, mutta skriptissä niitä ei käsitellä lainkaan (rivit 12–21, 39–60). Skenaariokohtaista allokaatiota ei ole dokumentoitu, joten en arvaa euromäärää. Myös suorien tukien parametri ja nolla-oletuksen perustelu puuttuvat (rivit 39–60). Hanketaulukon EU-tuet eivät automaattisesti ole S13:n kustannus; rahoittaja ja kirjaustapa pitää selvittää. Aiemmin nähtyjä 220–400 M€/v-tasolukuja ei puolestaan pidä vähentää sellaisenaan, koska ne eivät ole inkrementaalisia.

- **Säännön 6 erittelyt puuttuvat.** Skripti laskee vain toimipaikkojen vakiintuneen vuoden suoria eriä. Hankintaketjua ja rakennusvaihetta ei arvioida erikseen eikä niiden laskematta jättämistä merkitä tulosrivin yhteyteen (rivit 39–60, 76–85). Tämä rajoittaa tulosten tulkintaa, vaikka niiden summauksen estäminen vakiintuneeseen vuoteen onkin oikein.

- **Työeläkemaksuja ei raportoida omana rivinään.** Rivi 52 yhdistää kaiken yhteen `palkkaverot`-erään 40 %:n S13-osuudella, eikä tulosteessa ole TyEL-riviä (rivit 37, 51–53, 76–79). Aineistosta ei käy ilmi, sisältääkö 40 % TyEL:iä. Jos sisältää, tulevat eläkevastuita vastaava erittely puuttuu; jos ei, 40 %:n sisältö on dokumentoimatta.

- **Hankeputken ylimenevää osaa ei raportoida lisäyksen 2 mukaisesti.** Muuttuja `jaljella` on täyttämättä jäänyt kehys, ei kehykseen mahtumattoman hankeputken suuruus (rivit 23–30). Tulosteessa raportoidaan vain ”kehyksestä jäi” (rivit 57, 73). Tämä ei muuttaa pääsummia, mutta raportointivaatimus jää toteutumatta.

- **Säännön 1 inkrementaalisuus on ehdollinen, ei todennettu.** Rivien 70 arvot vastaavat lisäystä 3, mutta skriptissä ei ole S0-toteutusta eikä tarkistusta siitä, sisältyvätkö valitut ei-datakeskushankkeet jo VM:n perusuraan. Aineisto ei riitä tämän varmistamiseen. Lisäksi vaihtoehtoisen S1-tulkinnan 2,0 TWh:n vuoden 2025 datakeskustaso ilmaantuu vain koodin kommenttiin (rivit 86–87); sen lähdettä tai oletusmerkintää ei ole muistiossa.

- **Vertailueron BKT ei ole osoitettu säännön 5 mukaiseksi.** Rivit 62–65 rakentavat nimellisen BKT:n reaalikasvuista ja 2 %:n deflaattorioletuksesta. Ei käy ilmi, että tulos olisi VM:n saman ennusteen vuoden 2030 nimellinen BKT. Tämä vaikuttaa vain prosenttiosuuksiin, ei euroihin.

- **Pienemmät toteutus- ja dokumentointipoikkeamat:**
  - Osahankkeen täyttö skaalaa sekä hyvityksen että työpaikat lineaarisesti kulutusosuudella (rivi 28). Tätä ei ole lukittu lisäyksissä, eikä se välttämättä kuvaa myönnetyn hyvityksen tai laitostyöpaikkojen käyttäytymistä.
  - Verohyvityksen ”enintään verosta” -raja tehdään hankkeiden yhteenlasketulle P2X-verolle, ei hankkeittain (rivit 48–50, 59). Jos tarkoitus oli hankkeittainen raja, yhteenlaskenta voi aliarvioida veron. Vaikutusta tässä ajossa ei voi päätellä pelkästä tulosteesta.
  - Arctialin 1 000 työpaikkaa (rivi 20) ei saa perustetta lisäyksestä 3 tai hanketaulukosta. Se ei vaikuta esitettyihin pääskenaarioiden täyttöihin, mutta voi tulla mukaan herkkyyslaskentaan.
  - Sähköntuotannon kasvun ehtoa ei toisteta tulosteessa tai tuloskohdassa (rivit 67–91), vaikka sääntö 8 edellyttää sen mainitsemista. Datakeskusten 4,1 GW:n rakenteilla-ristiriita on kirjattu muistioon, mutta sen merkitys jää tulosraportissa avoimeksi.

Sen sijaan sähköverot, huoltovarmuusmaksu, luokan II verotuen ilmoittaminen ilman kaksinkertaista vähennystä, pääskenaarioiden TWh-syötöt, työllisyyden 0/50/100-herkkyys ja NordFuelin poisjättö on toteutettu pääpiirteissään ohjeiden mukaan (rivit 15–20, 33–37, 45–54, 70, 81–85). Kiinteistövero on oikein poissa summasta.

## 2. Tutkijan vapausasteet ja niiden suunnat

1. **P2X-yhteisövero on suurin lisäyksen 3 valinta S1:ssä ja yksi suurimmista S2:ssa.** Päälaskenta käyttää oletuksena metallien jalostuksen ylärajaa (rivit 39, 48–50). S1:n yhteisövero on 44,0 M€ koko 51,5 M€:n tuloksesta; nollaoletus vie sen lähelle ilmoitetun välin alapäätä. Uusien laitosten verotettavan voiton puuttuminen käynnistysvuosina tai jatkuvana heikkona kannattavuutena laskee tulosta. Metallien jalostuksen historiallinen taso ei itsessään osoita P2X:n vuoden 2030 kannattavuutta.

2. **Nettouusien työpaikkojen 100 %:n pääoletus ja bruttokertoimet nostavat erityisesti S2:ta.** S2:n palkkaverot ovat 58,5 M€; 50 %:n nettouusilla tulos on 463 M€ eikä 492 M€. S1:ssä vaikutus on pieni. Nettouusiväli ei kata virheitä itse bruttokertoimissa: datakeskusten 120 työpaikkaa/TWh perustuu yhteen yritykseen ja P2X:n 100 työpaikkaa/laitos on oletus. Niiden suurentaminen nostaa ja pienentäminen laskee tulosta.

3. **S1-tulkinta vaikuttaa selvästi mutta vain S1:ään.** Päätulkinta 3,2 TWh tuottaa 52 M€, vaihtoehto 5,2 TWh 74 M€. Päätulkinta on siis tässä suhteessa alaspäin vievä, ei optimistisempi.

4. **Täyttöjärjestyksen euromääräiselle suunnalle ei ole yksikäsitteistä vastausta.** Kiinteän TWh-katon vuoksi se ei muuta sähköveron tai huoltovarmuusmaksun kokonaispohjaa. Se muuttaa hyvitysten ja työpaikkojen koosta; enemmän hyvitystä laskee veroa, erilainen laitos- ja työpaikkajako voi nostaa tai laskea palkkaveroja. Suurempi ongelma on se, että viivästyneen hankkeen tilalle täyttyy automaattisesti seuraava hanke.

5. **BKT-johto vaikuttaa vain nimittäjään.** Suurempi nimellinen BKT pienentää prosenttiosuuksia, pienempi suurentaa niitä. Ilman vaihtoehtolaskelmia vaikutuksen suuruutta ei kannata arvata.

Lisäyksen 3 ulkopuolella S2:n suurin yksittäinen ehto on aiemmin valittu datakeskusskenaario: 307 M€ eli 62 % tuloksesta on sen sähköveroa.

**Voiko valintoja epäillä tulossuuntautuneiksi?** Yläraja-P2X-veron ja 100 %:n nettouusien valitseminen päälukematuo oli ennalta ennustettavasti ylöspäin vievää, eikä lisäykset lukinneet tätä yhdistelmää nimenomaisesti keskiarvoksi. Toisaalta S1:n päätulkinta on matalampi kuin vaihtoehto, eikä metallien jalostuksen verointensiivisyys ole tasotaulukon korkein. Näin ollen aineisto ei anna perustetta väittää tulokseen tähdättyä valintaa, mutta se osoittaa, että **ennakkokirjaus ei lukinnut raportoitavaa pistearvoa riittävästi**.

## 3. Välit ja puuttuvat epävarmuudet

Rivien 80–85 väli kattaa vain käyttöasteen, nettouusien työpaikkojen ja P2X-yhteisöveron yhdistelmät. Se ei ole todennäköisyyspohjainen luottamusväli.

Erityisesti **käyttöaste ei testaa kokonaiskulutuksen epävarmuutta**: `tayta` pitää skenaarion TWh-määrän kiinteänä, joten käyttöaste muuttaa lähinnä hankkeiden kokoonpanoa, hyvityksiä ja työpaikkoja (rivit 23–30, 40–43, 81–82).

Välistä puuttuvat ainakin:

- Fingrid-kehyksen, S0:n 3,8 TWh:n ja datakeskusten tason epävarmuus; S1-vaihtoehto ja ET-herkkyys on raportoitu vain erillisinä pisteinä.
- Hankkeiden toteutumistodennäköisyys, FID:n puuttuminen, käynnistysvuosi, täysi vuosi 2030 ja kapasiteetin rampaus.
- Datakeskusten 80 %:n käyttöaste, yhteisöveromalli ja työpaikkaintensiteetti sekä P2X:n bruttotyöpaikat, työvoimakustannus ja 40 %:n S13-osuus.
- Suorat tuet, varastokustannus, verohyvitysten toteutuminen ja mahdollinen VM-perusuran päällekkäisyys.
- Nimellisen BKT:n epävarmuus.

Siksi myös alarajat ovat ehdollisia sille, että kulutuslisäykset toteutuvat täysimääräisinä.

## 4. Systemaattiset vääristymäriskit

- **Ylöspäin:** päälukemien P2X-yhteisöveron yläraja ja 100 % nettouusi työ; hankkeiden automaattinen korvaaminen seuraavalla; datakeskusten kiinteä kannattavuus- ja työpaikkamalli; kustannuserien puuttuminen.
- **Hanketoteutuma:** jos Fingrid-kehys toteutuu muista hankkeista, automaattinen täyttö ei itsessään yliarvioi kokonaiskulutusta. Se kuitenkin estää matalamman hanke­toteutuman testaamisen ja antaa nimetyille hankkeille liian varman kuvan.
- **Luokan II verotuki:** vähentämättömyys summassa on säännön 4 mukaan oikein. Summaa ei kuitenkaan pidä lukea verotuksellisen vaihtoehtoiskustannuksen sisältäväksi kokonaisnetoksi; 70/164 M€ on syytä pitää näkyvästi erillään.
- **Kunnat ja valtio:** skripti ei allokoi tuloja S13:n alasektoreille. Kiinteistöveron lukittu poisjättö alentaa erityisesti laajaa kuntatulkintaa, mutta ei ole G:n summan virhe. Tuloksesta ei voi päätellä valtion, kuntien tai hyvinvointialueiden erillisiä rahoitusvaikutuksia.
- **Sähkön hinta ja muu syrjäytyminen:** jäävät lukitun rajausten ulkopuolelle. Niiden vuoksi työllisyys- ja verovaikutusten nettouusia ei voida tulkita koko talouden tasolla pelkän 0/50/100-kertoimen varaan.

## 5. Ehdotukset

**Tuleva työ — G:n erillinen, jälkikäteen merkitty toteutus- ja rajausseloste, ilman lukittujen lukujen muuttamista:**  
Merkitse pääluvut nimenomaisesti 100 %:n nettouusien ja P2X-veron ylärajan laskelmiksi, tulos suoraksi vakiintuneen vuoden arvioksi, välit ehdollisiksi herkkyysväleiksi sekä luettele puuttuvat tuet, varastokustannus, TyEL-erittely, hankintaketju, rakennusvaihe ja S0-varmistus.

**Uusi ennakkokirjaus ennen seuraavaa laskentaa:**  
Lukitse etukäteen keskiarvon tai raportoitavan päälaskelman oletukset, S0:n energetiikan ja hankkeiden kohdistus, toteutumis- ja viivästymisskenaariot, hankkeittaiset tuet ja hyvitykset, S13-alasektoreiden erittely sekä rakennusvaiheen ja hankintaketjun erilliset arviot. Kiinteistövero ja TyEL voidaan arvioida erillisinä laajennuksina muuttamatta G:ta.

**Tarkistettavat lähteet:** Fingridin 9/2025 alkuperäinen kaavio ja tausta-aineisto; VM:n syksyn 2026 nimellinen BKT ja perusuran sisältö; TEM:n mahdollisesti päivitetty datakeskusarvo; Business Finlandin hyvitys- ja tukipäätökset, mukaan lukien varastot ja osahankkeiden ehdot; hankkeiden FID/COD-tiedot YVA-, lupa- ja yritysaineistoista; datakeskusten työpaikat Tuikeen lisäksi muista yritys- ja työllisyysaineistoista. En ole voinut tarkistaa näitä lähteitä enkä esitä niiden sisällöstä uusia faktaväitteitä.
