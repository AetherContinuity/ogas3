# Tutkimuskäyttö 1: rekisteri vs lähdeluenta, ja tutkimuskäytön sulkeminen (27.11.2026)

Lähdeluenta: `lahdeluenta.md`, commit c0d36d8, kirjattu ennen raakatuloksen avaamista. Raakatulos: `taytto-kimi.json` (#55). Siinä on 63 esiintymää ja 47 suhdetta: depends_on 35 (24 eksplisiittistä, 11 rekonstruoitua), qualifies 9, same_claim 3, related 0. Suhteet muodostavat 16 erillistä komponenttia. Jokainen alla mainittu suhde on tarkistettu lähdetekstistä. Tulkitsija on sama istunto, joka teki rajauksen ja lähdeluennan.

## Vertailun ehdot (lähdeluennan kohta "Mitä rekisterin pitäisi tehdä näkyväksi")

**1. Linkit erillisinä suhteina.**
- **Osittain.** CN-007:ssä ketju on poimittu kolmena esiintymänä ja kahtena suhteena: CN-007:010 → :009 (eksplisiittinen) ja :009 → :008 (rekonstruoitu). Tämä vastaa tekstiä.
- **SM-009:ssä ei.** Ketju on yksi esiintymä (SM-009:001, tiivistelmä). § 03:n kausaalisarjaa ja otsikkoriviä "→ Structural decay" ei poimittu. SM-009:001 ja CN-007:n ketju eivät ole samassa komponentissa, eikä CN-007:n viittausta SM-009:ään poimittu.
- **Linkki 3 (→ rapautuminen) puuttuu kokonaan.**

**2. Kapasiteettitapauksen jännite.**
- **Ei näy.** CN-007:004 ("Kyse ei ole tiedon puutteesta") on poimittu, ja CN-007:005 ("Selitys on rakenteellinen") nojaa siihen. Niillä ei kuitenkaan ole suhdetta saman paperin mittausvajeeseen (:008, :009).
- SM-009:n "measurement gap closing — or appearing to close" jäi poimimatta.

**3. SM-009:n viittaukset WP-013:een ja WP-015:een.**
- **Poimittu:** S001 (SM-009:002 depends_on WP-013:001) ja S002 (SM-009:003 same_claim WP-015:001).
- **WP-015:n omat rajaukset näkyvät graafissa:** S039 WP-015:013 ("not that collapse is certain or imminent") qualifies WP-015:001, ja S037 ("Its location is not empirically determined"). SM-009:n viittaus johtaa siis rajattuun väitteeseen.
- **WP-013:n "not forecasts" -rajausta ei poimittu.**

**4. Kilpailevat selitykset.**
- **Esiintyminä kyllä:**
  - SM-007:001 sekä SM-007:003–005 (itsekritiikki: "A single framework applied repeatedly will tend to find the same shape it was built to find");
  - CN-004:001–003 (teesit A–C) ja CN-004:004 (D);
  - CN-007:007 (omistajuus ja rationaalinen viivyttely);
  - SM-009:004 ("necessary but not sufficient").
- **Kytköksinä ketjuun ei:** mikään niistä ei ole samassa komponentissa kuin SM-009:001 tai CN-007:n ketju. Tämä vastaa tekstiä, koska SM-009 ei viittaa SM-007:ään eikä CN-004:ään. Rekisteri ei täytä puuttuvaa yhteyttä, kuten pyyntö edellytti.
- **Jäi poimimatta:** SM-007:n "not a shortage of resources, information, or formal authority", CN-004:n spiraalin käänteinen nuoli ja SM-009:n "operate independently of measurement gaps".

**5. Mitä rekisteri löysi, mitä lähdeluenta ei löytänyt:**
- **a.** SM-009:009, § 11 disclosure gap, qualifies ketjun (S007). Muuttuja mitataan, mutta laki sulkee sen päätöksenteon ulottumattomiin, ja seuraus on silti "no signal, no sanction, no correction". Lähdeluenta ei lukenut § 11:tä. Kohta tukee lähdeluennan havaintoa mittausvajeen kahdesta merkityksestä: SM-009 itse erottaa ne nimellä.
- **b.** SM-009:n sisäinen jännite. § 06 sanoo "Measurement is necessary but not sufficient" (SM-009:004, qualifies ketjun). § 07 Track C sanoo "The intervention that breaks this chain is not political will — it is measurement instrument construction" (SM-009:005, nojaa ketjuun). Molemmat kiinnittyvät samaan esiintymään. Lähdeluenta ei lukenut § 07:ää.
- **c.** CN-004:005–006: "The evidence available … is consistent with both" ja "ACI does not currently have sufficient evidence to distinguish between these two regimes". Lähdeluenta ei poiminut tätä.
- **d.** Komponenttirakenne. Yksi tosiasia, kapasiteettimekanismin hallituksen esitys antamatta toukokuussa 2026 (SM-009:006 same_claim CN-007:006), saa kaksi selitystä kahdessa paperissa. SM-009:ssä selitys on "the predicted output of a system with a structural sanction gap" (:008). CN-007:ssä se on "kun kukaan ei omista kokonaisvastuuta ja viivyttely on kullekin toimijalle erikseen rationaalista" (:007). Tarkistettu tekstistä: CN-007:n esimerkkiosio päättyy omistajuusselitykseen, ei kolmen vajeen ketjuun. Lähdeluenta huomasi CN-007:n omistajuuskorostuksen, mutta ei tätä rakennetta.

## Rekisterin virheet ja vinoumat

- **S002 same_claim SM-009:003 – WP-015:001 on liian vahva.** SM-009: "WP-015 documented the mechanism producing the crisis". WP-015: "argues that their combination produces an elasticity collapse". WP-015:n rajaukset tekevät eron selväksi. Oikea suhde olisi depends_on (SM-009 nojaa WP-015:een), ei sama väite.
- **S015 CN-004:001 depends_on SM-007:001 on merkitty rekonstruoiduksi**, vaikka CN-004 viittaa SM-007:ään nimeltä (§ 01: "SM-007 identifies a structural condition …"). Tämä on yksi havainto lisää siitä, ettei `perusta` ole toistettava.

## Tärkein yksittäinen löydös syntyi rekisterin suhteen tarkistuksesta

S001:n (SM-009:002 → WP-013:001) tarkistus lähteestä: SM-009 kirjoittaa "The divergence between scenarios grows nonlinearly — which means the cost of delay is not linear but accelerating". WP-013:ssa ei ole sanoja nonlinear, non-linear, accelerat tai exponential (haettu koko purkuteksti). Paperi vertaa kahta skenaariota yhtenä ajankohtana (2030; kestävyys noin 38 h vs noin 52 h, WP-013:005–006) ja sanoo skenaarioiden olevan "not forecasts; they are diagnostic constructions". Kahden skenaarion vertailu yhtenä ajankohtana ei voi osoittaa epälineaarista erkanemista.

**SM-009:n "Core paradigm finding" ("The ratio of these costs grows nonlinearly with time") ei siis saa tukea paperista, johon SM-009 epälineaarisuuden kohdalla viittaa.**

Suhde S001 on rekisterin säännöillä oikein: SM-009 nojaa WP-013:een, eikä poiminta arvioi pätevyyttä. Lähdeluenta lainasi SM-009:n väitteen tarkistamatta sitä WP-013:sta. Löydös syntyi, kun rekisterin suhde tarkistettiin lähteestä.

## Johtopäätös

- **Rekisteri esitti argumenttia huonosti.** Ketjun keskeinen rakenne jäi poimimatta: SM-009 § 03, linkki 3 ja mittausvajeen jännite tapauksessa.
- **Rekisteri toimi tarkistuslistana hyvin.** Sen 47 suhdetta ovat yksittäin tarkistettavia väitteitä viittauksista ja nojaamisista. Se nosti esiin kolme kohtaa, jotka lähdeluenta ohitti (5a–c), ja yhden rakenteen (5d). Yhden suhteen tarkistus tuotti tutkimuskäytön tärkeimmän löydöksen.
- **Kilpailevien selitysten kohtaamattomuus näkyy erillisinä komponentteina.** Se on yhtä paljon täytön kattavuuden kuin papereiden ominaisuus. Lähdeluenta erotti nämä kaksi, rekisteri ei.

Tutkimuskäyttö 1 suljetaan tähän. Korpukseen kohdistuvat havainnot on kirjattu yllä, eikä korpusta muuteta tässä:
- SM-009:n epälineaarisuusväite vailla tukea;
- mittausvajeen kaksi merkitystä;
- sanktio- ja korjausvajeen samaistuva näyttö tapauksissa;
- WP-015:n luonnehdinta vahvemmin kuin WP-015 itse.

Jos ne viedään SM-009:ään, se tehdään erillisenä korjauksena.
