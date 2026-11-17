# Katselmointi (LLM) — lausunto, ei mittaus

```json
{
 "pyynto": "katselmoinnit/h-energiaintensiivinen-pyynto.txt",
 "pyynto_sha256": "0a3dbf20a435b1e809dbd21574ec2c6a0778daa347438ca00a9fa32ca271ec32",
 "malli": "kimi-k3.1-pro",
 "response_model": "kimi-k3.1-pro",
 "effort": "max",
 "aika": "2026-11-17T13:17:16+00:00",
 "finish_reason": "stop",
 "usage": {
  "prompt_tokens": 9208,
  "completion_tokens": 26981,
  "total_tokens": 36189,
  "completion_tokens_details": {
   "reasoning_tokens": 23406
  },
  "prompt_tokens_details": {
   "cache_write_tokens": 8960
  }
 },
 "hinta_usd": 0.2882
}
```

**Kokonaisarvio.** Päämatriisin yksiköt, kumulatiiviset P-tasot ja tuloste ovat keskenään yhdenmukaisia; en löytänyt koodin ja tulosteen välistä aritmeettista ristiriitaa. H ja lisäys 1 eivät kuitenkaan toteudu täysin. Pääarvo on käyttökelpoinen nimenomaan ilmoitettuna oletuspisteenä, mutta yhteisöveron ylärajaskenaario ja osa väleistä eivät ole toistettavissa pelkistä lukituista säännöistä.

## Havainnot vakavuusjärjestyksessä

1. **Korkea, ylärajaskenaarion osalta: verohyvityksen vuosittainen käsittely on lukitsematon.**  
   H määrää vain hankekohtaisen vähennyksen, enintään hankkeen veron suuruisena. Koodi lisää tämän lisäksi kertoimen `0.10` ja ajoituskertoimen: `min(brutto, 0.10 * hyv * k)` (rivi 53). Kymmenen prosentin vuosisääntöä tai sen lähdettä ei ole H:ssa eikä lisäyksessä 1.
   - Jos koko hyvitys olisi käytettävissä vuonna 2030, koodi vähentää liian vähän ja **yliarvioi nettoyhteisöveron**.
   - Jos tarkoitus oli jakaa hyvitys usealle vuodelle, peruste pitää dokumentoida; sen oikeellisuutta ei voi arvioida annetusta aineistosta.
   - Pääarvoon tämä ei vaikuta, koska siinä `yv_p2x=0` (rivi 35). Sen sijaan ylärajaskenaario ja erityisesti välien yläpäät riippuvat olennaisesti rivistä 53.

2. **Merkittävä: pistearvon ja parametrien jäädytys on yhä osittainen.**
   - H §5 lukitsee työn, P2X-yhteisöveron, käyttöasteen ja ajoituksen keskiarvot. Sen sijaan ei käy ilmi, että **DC 120 tp/TWh olisi nimenomaisesti lukittu pääarvoksi ennen laskentaa**: lisäyksessä 120 ja 400 ovat rinnakkaisia, ja 120 on vasta funktion oletus (rivi 35). Arvon 400 valinta nostaisi pääarvoa kaikilla D0:ta suuremmilla tasoilla.
   - Sähköverot, huoltovarmuusmaksu ja DC:n yhteisöveromalli (rivit 26–28) eivät ole numeroina H:n lisäyksessä 1. Niiden oikeellisuutta ei voi tarkistaa annetusta H-aineistosta.
   - Hankekohtaisesta liitteestä puuttuvat H §6:n vaatimat liityntä- ja tuotantoriippuvuudet, eikä kaikkia lähteiden päivämääriä ole annettu.
   - Rakennusvaiheen hankintarakenteet on nimenomaisesti tehty `[A, laskentahetkellä]`, eikä H §8:n edellyttämänä oletusvälünä.

3. **Merkittävä raportointipoikkeama: kaikkia yhdistelmiä lasketaan, mutta niitä ei raportoida.**  
   H §5 edellyttää kaikkien yhdistelmien raportoimista ja liitteenä julkaisemista. Koodi laskee ne, mutta säilyttää vain pääarvon sekä minimin ja maksimin (rivit 83–87). Tekstitulosteessa ja JSON-rakenteessa ei ole yhdistelmäkohtaisia oletuksia tai tuloksia. Näin ei voi tarkistaa, mitkä oletukset tuottavat esimerkiksi D0 × P2 -välin 1–112 M€.

4. **P2X:n laskentahetken valinnat vaikuttavat tulokseen eivätkä ole kaikki neutraaleja.**
   - Ajoitus skaalaa kulutuksen lisäksi työpaikat (rivi 57) ja hyvityksen (rivi 53), vaikka H §4 määrää vain vuosikulutuksen ajoituksen. Työpaikkojen skaalaus **pienentää palkkatuloja** verrattuna täysien pysyvien työpaikkojen laskemiseen ja madaltaa P2X:n pääarvoa. Hyvityksen skaalaus puolestaan pienentää vähennystä ja nostaa nettoveroa ylärajaskenaariossa. Oikea ramp-up-profiili ei käy ilmi aineistosta.
   - Käyttöaste vaikuttaa Freijaan, ETFuelsiin ja Plugiin (rivit 16 ja 19–21), mutta ei tuotantomääristä johdettuun Arctic Sisuun tai VolagHyyn (rivit 17–18). Tämä voi olla perusteltu tulkinta, mutta sitä ei ole kirjattu. Jos kaikkien kulutusten oli tarkoitus skaalautua suhteessa 60 %:iin, kiinteä käsittely yliarvioi näiden kulutuksen 40 %:ssa ja aliarvioi 80 %:ssa.
   - Plug Powerin 87/207 MW on johdettu hyvityksistä käyttäen keskiarvoista 2,55 M€/MW-investointia ja 20 %:n hyvitystä. Se edellyttää samaa kustannus- ja hyvitysrakennetta eri sivustoilla. Ilman suoria tehoja **virheen suuntaa ei voi määrittää**. Virhe välittyy kulutukseen ja työpaikkoihin (rivit 20–21); yhteisöveron ylärajassa myös sivustojako vaikuttaa hankekohtaisiin rajoihin.

5. **D-tasojen harmonisointi on pääosin johdonmukainen, mutta riippumattomuus ei ole ratkennut.**
   - D1:n toistojen yhdistäminen yhdeksi tasoksi on oikein. D4:n poisjättö ja kapasiteetin pitäminen hankeputken mittarina noudattavat täsmälleen H §2:ta. Myös D3 on sisäisesti toistettavissa ACI-skenaarioksi.
   - D2:n merkitseminen ET:lle on julkaisulähteen attribuutio, ei osoitus itsenäisestä alkuperästä. Lisäksi 11/18 TWh:n johtaminen 10–15 %:sta ei ole toistettavissa ilman käytettyjä kokonaiskulutusperusteita ja pyöristystä.
   - D0b:n Fingrid-riippuvuus on tunnustettu, mutta myös sen **Suomi-kattavuus** jää aineistossa epäselväksi, koska lähdettä kuvataan pohjoismaiseksi. Lisäksi `~4 TWh` käsitellään tarkkana 4,0:nä (rivit 10–11), josta vähennetään 3,8 TWh (rivi 36). Syntyvä 0,2 TWh:n lisäys voi olla pyöristysherkkää, eikä siitä pitäisi tulkita tarkkaa itsenäistä 5 M€:n vaikutusta.
   - Koska tasoja ei summata eikä niille anneta todennäköisyyksiä, riippuvuudet eivät aiheuta mekaanista tuplalaskentaa. Ne estävät kuitenkin pitämästä tasoja itsenäisinä toisistaan vahvistavina ennusteina.

6. **Erillisarviot toteutuvat vain osittain, mutta eivät vääristä pääsummaa.**
   - Investointien 65/35/52 % kotimaisuusosuuksille ei anneta painoja tai väliä, joten ne eivät ole toistettavissa. Palvelimien mukaanotto laskee kotimaista osuutta korkean tuontiosuuden vuoksi; muuten estimaattien virheen suuntaa ei voi määrittää.
   - Euromääräistä kertaluonteista rakennusvaiheen arviota ei tehty, eikä varastojen kolmea erää eritellä tuloksessa.
   - Kiinteistöveron jättäminen arvioimatta ja varastohäviöiden jättäminen laskematta ovat H §8:n mukaisia, kun lähdettä ei löytynyt. Hankintaketjun kertoimet on raportoitu, mutta euromääräistä arviota ei ole.

## G:n katselmoinnin ongelmat

| Aiempi ongelma | Arvio H:sta |
|---|---|
| Pistearvon lukitus | **Osittain korjattu.** H §5:n neljä valintaa lukittiin; DC 120 tp/TWh:n pääarvoasema ja jotkin laskentasäännöt jäivät auki. |
| Automaattinen korvaaminen | **Korjattu aineiston perusteella.** Hankejoukko on kiinteä eikä pois rajattuja hankkeita korvata muilla (rivit 14–23). Plug Powerin vanhan/epävarman aikataulun tulkitseminen vuodeksi 2030 on silti erikseen tehty oletus. |
| TyEL-rivi | **Korjattu.** TyEL 24,4 % on omalla alasektorillaan (rivit 31–33 ja 58–59) ja näkyy tulosteessa. Eläkevastuuta ei ole netotettu, kuten osittaisessa tulolaskennassa pitääkin ilmoittaa. |
| Alasektorit | **Korjattu.** Valtio, kunnat, työeläkelaitokset ja muut rahastot eritellään; hyvinvointialueille ei jyvitetä tuloja (rivit 37–41, 56 ja 58–59). |
| Hankekohtainen hyvitysraja | **Rakenteeltaan korjattu.** Vähennys tehdään hanke kerrallaan eikä se voi ylittää hankkeen veroa (rivi 53). Lukitsematon 10 %:n ja ajoituksen käsittely jäi kuitenkin uudeksi ongelmaksi. |

## Tulkinta

- **”Tulos määräytyy lähes kokonaan datakeskusten kulutuksesta”** on perusteltu vain pääarvon ja erityisesti korkeampien D-tasojen vertailuna: P0→P2 muuttaa arvoa enintään noin 9 M€, kun D0→D2b muuttaa sitä 378 M€. Väite ei pidä paikkaansa koko matriisissa: D0:ssa kaikki tulee P2X:stä, D0b:ssä P2X on suuri osa kokonaistulosta, ja D0 × P2 -välillä 1–112 M€ P2X-oletukset hallitsevat.
- **”P2X tuottaa pääarvolla alle 10 M€” on tuettu:** D0 × P2 on noin 9,17 M€ ja 3,60 TWh on ajoituspainotettu kulutus. Väite tarvitsee kuitenkin koko oletusketjun: ajoitus 50 %, nettouusi työ 50 %, P2X-yhteisövero 0, käyttöaste 60 % sekä hankekohtainen työpaikkojen skaalaus. Se ei yleisty yhteisöveron ylärajaan eikä tarkoita nettovaikutusta.
- Tuloksessa mainittu 79 M€ on koodissa `p2x_twh * (SV_I − SV_II)` (rivi 62). Se on **laskennallinen ero luokka I -veroon**, ei osoitettu menetys VM:n perusuraan nähden. Sitä ei pidä mekaanisesti vähentää ilman erillistä vastafaktuaalia siitä, mitä kulutus olisi ollut ilman P2X:ää.

## Muistio ja tuleva työ

**Muistiossa** tulisi pitää pääarviot ehdollisina, erottaa ne selvästi osittaisesta nettovaikutuksesta ja mainita, että yhteisöveron ylärajavälit riippuvat H:ssa dokumentoimattomasta hyvityksen vuosikäsittelystä. D0b:tä ei pidä käyttää tarkkana itsenäisenä vahvistuksena. H:n lukittuja sääntöjä ei pidä muuttaa jälkikäteen.

**Tuleva työ:**
1. Julkaista seuraavassa kierroksessa koko oletusavaruus koneellisesti luettavana, mukaan yhdistelmätunnukset ja hankekohtaiset osavaikutukset.
2. Jäädyttää ennen laskentaa myös DC-pistearvon työintensiteetti, veroparametrien lähteet, hyvityksen vuosittainen käyttö, työpaikkojen ramp-up sekä käyttöasteen kohdehankkeet.
3. Varmistaa D0b:n maantieteellinen kattavuus ja tarkka luku, D2:n alkuperä ja laskentaperuste sekä Plug Powerin sivustotehot suorista lähteistä.
4. Dokumentoida rakennusvaiheen hankintapainot ja oletusvälitys sekä eritellä P2X:n perusura ja mahdollinen sähköveron vastafaktuaali ennen nettotulkintoja.
